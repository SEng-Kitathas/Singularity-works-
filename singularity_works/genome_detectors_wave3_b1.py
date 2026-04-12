from __future__ import annotations

import ast
import re as _re2
import re as _re_ext
from typing import Any

from .genome_detection_common import (
    DetectionEvidence,
    SubjectView,
    _Detection,
    _interproc_analyze,
    _parse,
    _safe_dotall_finditer,
    _safe_dotall_search,
    _todo_hits,
    is_open_call,
)

def _detect_crlf_injection(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect user-controlled input flowing into HTTP response headers.
    Tracks taint through variable assignments:
      url = request.args.get("next"); redirect(url)  <- fires
    Also catches direct header subscript writes.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        _REQUEST_INPUT   = frozenset({"request", "req"})
        _REQUEST_ATTRS   = frozenset({
            "args", "form", "json", "data", "params",
            "values", "headers", "cookies", "query_string",
        })
        _HEADER_ATTRS    = frozenset({"headers", "set_header", "add_header"})
        _SENSITIVE_HDRS  = frozenset({
            "location", "content-type", "content-disposition",
            "x-frame-options", "set-cookie", "refresh",
        })

        # â”€â”€ Pass 1: taint propagation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        tainted: dict[str, int] = {}   # var_name -> assignment lineno

        def _is_req_call(node: ast.AST) -> bool:
            """True if node is request.*.get(...) / req.*.get(...) style."""
            if not isinstance(node, ast.Call):
                return False
            func = node.func
            if not isinstance(func, ast.Attribute):
                return False
            val = func.value
            if isinstance(val, ast.Attribute):
                return (
                    isinstance(val.value, ast.Name)
                    and val.value.id in _REQUEST_INPUT
                    and val.attr in _REQUEST_ATTRS
                )
            if isinstance(val, ast.Name) and val.id in _REQUEST_INPUT:
                return True
            return False

        def _is_tainted_expr(node: ast.AST) -> bool:
            return _is_req_call(node) or (
                isinstance(node, ast.Name) and node.id in tainted
            )

        class _TaintCollector(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                if _is_tainted_expr(node.value):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            tainted[t.id] = node.lineno
                self.generic_visit(node)

        _TaintCollector().visit(tree)

        # â”€â”€ Pass 2: sink detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        class _SinkDetector(ast.NodeVisitor):
            def visit_Subscript(self, node: ast.Subscript) -> None:
                pv = node.value
                if (isinstance(pv, ast.Attribute)
                        and pv.attr in _HEADER_ATTRS):
                    key = node.slice
                    if (isinstance(key, ast.Constant)
                            and isinstance(key.value, str)
                            and key.value.lower() in _SENSITIVE_HDRS):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Sensitive header '{key.value}' assigned at "
                                f"line {node.lineno} â€” verify value is not "
                                f"user-controlled (CRLF injection risk)"
                            ),
                            evidence={
                                "rewrite_candidate": (
                                    "Strip newlines before assignment: "
                                    "value = value.replace('\r','').replace('\n','')"
                                ),
                            },
                        ))
                self.generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                name = (
                    func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name)
                    else ""
                )
                if name == "redirect" and node.args:
                    arg = node.args[0]
                    if _is_tainted_expr(arg):
                        src = (tainted.get(arg.id, node.lineno)
                               if isinstance(arg, ast.Name) else node.lineno)
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"redirect() with user-controlled URL at line "
                                f"{node.lineno} (tainted from line {src}) â€” "
                                f"CRLF injection if newlines not stripped"
                            ),
                            evidence={
                                "rewrite_candidate": (
                                    "Strip: url=url.replace('\r','').replace('\n',''); "
                                    "validate against allowlist"
                                ),
                            },
                        ))
                self.generic_visit(node)

        _SinkDetector().visit(tree)

    return detections




# â”€â”€ IDOR Gate â€” wires existing access_control capsules â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_idor_missing_ownership(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Gate-version of the IDOR ownership monitor.
    Fires when: external ID from request + DB access without ownership check.
    Reuses the monitor's pattern set but emits GateFindings for the gate fabric.

    Web-framework guard: only fires when a web framework is imported.
    Non-web modules (forge internals, libraries) contain ORM method names
    as string literals in detection patterns â€” the heuristic would produce
    false positives on its own source. Requiring a web import eliminates that.
    """
    # Web-framework import guard â€” non-web modules cannot have IDOR routes.
    # Catches flask, django, fastapi, starlette, sanic, aiohttp, tornado.
    _WEB_IMPORTS = _re_ext.compile(
        r'from\s+(?:flask|django|fastapi|starlette|sanic|aiohttp|tornado|bottle|falcon)'
        r'|import\s+(?:flask|django|fastapi|starlette|sanic|aiohttp|tornado|bottle|falcon)',
        _re_ext.IGNORECASE,
    )
    if not _WEB_IMPORTS.search(content):
        return []

    # Reuse the compiled patterns from monitoring.py
    try:
        from .monitoring import (
            _IDOR_REQUEST_ID,
            _IDOR_DB_ACCESS,
            _IDOR_OWNERSHIP,
            _IDOR_ROUTE_ID_PARAM,
        )
    except ImportError:
        return []

    detections: list[_Detection] = []

    # Requires DB access to be relevant
    if not _IDOR_DB_ACCESS.search(content):
        return []

    has_request_id = bool(_IDOR_REQUEST_ID.search(content))
    has_route_id   = bool(_IDOR_ROUTE_ID_PARAM.search(content))

    if not (has_request_id or has_route_id):
        return []

    if _IDOR_OWNERSHIP.search(content):
        return []  # ownership enforced â€” clean

    # Find approximate line of the DB access
    lines = content.splitlines()
    hit_line = 0
    for i, line in enumerate(lines, 1):
        if _IDOR_DB_ACCESS.search(line):
            hit_line = i
            break

    detections.append(_Detection(
        lineno=hit_line,
        message=(
            f"IDOR: resource accessed by external ID at line {hit_line} "
            f"without object-level ownership check â€” any authenticated user "
            f"can read/modify any record by guessing IDs"
        ),
        evidence={
            "rewrite_candidate": (
                "Add: if resource.owner_id != current_user.id: abort(403)\n"
                "Or use a scoped query: "
                "Resource.query.filter_by(id=id, owner_id=current_user.id).first_or_404()"
            ),
        },
    ))
    return detections





# ---------------------------------------------------------------------------
# Bandit-derived detectors v1.32.1 (Apache-2.0 pattern concepts)
# ---------------------------------------------------------------------------



def _detect_insecure_tempfile(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect tempfile.mktemp â€” TOCTOU race between name generation and open.
    Safe alternatives: tempfile.mkstemp() or tempfile.NamedTemporaryFile().
    (Bandit B306 equivalent)
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if (isinstance(func, ast.Attribute) and func.attr == "mktemp"
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "tempfile"):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"tempfile.mktemp() at line {node.lineno} is a TOCTOU race â€” "
                            f"the name is returned before the file is created"
                        ),
                        evidence={
                            "rewrite_candidate":
                                "fd, path = tempfile.mkstemp()  # atomic creation"
                        },
                    ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections






def _detect_unverified_ssl_context(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect ssl._create_unverified_context() â€” disables certificate verification.
    (Bandit B323 equivalent)
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in (
                    "_create_unverified_context", "create_default_context"
                ):
                    if isinstance(func.value, ast.Name) and func.value.id == "ssl":
                        # create_default_context is safe; _create_unverified_context is not
                        if func.attr == "_create_unverified_context":
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"ssl._create_unverified_context() at line {node.lineno} â€” "
                                    f"certificate verification disabled, MITM possible"
                                ),
                                evidence={
                                    "rewrite_candidate":
                                        "ssl.create_default_context()  # verifies by default"
                                },
                            ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections






def _detect_cleartext_protocol(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect import of cleartext protocol modules: telnetlib, ftplib.
    These transmit credentials unencrypted. (Bandit B401/B402 equivalent)
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    _CLEARTEXT_MODS = {"telnetlib": "SSH/paramiko", "ftplib": "paramiko SFTP or ftplib with TLS"}
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in _CLEARTEXT_MODS:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Cleartext protocol module '{alias.name}' imported at "
                                f"line {node.lineno} â€” credentials transmitted unencrypted"
                            ),
                            evidence={
                                "rewrite_candidate":
                                    f"Use {_CLEARTEXT_MODS[mod]} for encrypted transport"
                            },
                        ))
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                mod = (node.module or "").split(".")[0]
                if mod in _CLEARTEXT_MODS:
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"Cleartext protocol '{node.module}' imported at line {node.lineno}"
                        ),
                        evidence={
                            "rewrite_candidate":
                                f"Use {_CLEARTEXT_MODS.get(mod, 'an encrypted alternative')}"
                        },
                    ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections






