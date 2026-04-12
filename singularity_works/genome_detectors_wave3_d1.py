from __future__ import annotations

import ast
import re as _re_ext
import re as _re2
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

def _detect_secret_serialization(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect structs/dicts with credential-named fields being serialized to
    JSON/YAML/XML â€” leaks secrets in API responses or log files.
    Source: gosec G117 secret_serialization.go (Apache-2.0).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    _SERIAL_FNS = frozenset({"dumps", "dump", "encode", "Marshal", "serialize"})
    _SERIAL_MODS = frozenset({"json", "yaml", "xml", "pickle", "marshal"})
    # Require full credential term â€” avoid substring matches like 'max_tokens'â†’'token'
    _CRED_NAMES  = _re2.compile(
        r'\b(?:password|passwd|secret|api_key|private_key|auth_token|'
        r'access_token|bearer_token|client_secret|credentials|'
        r'jwt_secret|signing_key|encryption_key)\b',
        _re2.IGNORECASE,
    )

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                fn   = func.attr if isinstance(func, ast.Attribute) else ""
                mod  = (func.value.id if isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Name) else "")
                if fn in _SERIAL_FNS and mod in _SERIAL_MODS and node.args:
                    arg = node.args[0]
                    # Check if a dict literal with credential key is being serialized
                    if isinstance(arg, ast.Dict):
                        for key in arg.keys:
                            if (isinstance(key, ast.Constant)
                                    and isinstance(key.value, str)
                                    and _CRED_NAMES.search(key.value)):
                                detections.append(_Detection(
                                    lineno=node.lineno,
                                    message=(
                                        f"{mod}.{fn}() serializes credential field "
                                        f"'{key.value}' at line {node.lineno} â€” "
                                        f"may expose secrets in API responses or logs"
                                    ),
                                    evidence={
                                        "rewrite_candidate": (
                                            f"Remove '{key.value}' from serialized output; "
                                            f"use a safe schema that excludes sensitive fields"
                                        ),
                                    },
                                ))
                self.generic_visit(node)
        _V().visit(tree)

    return detections




# â”€â”€ 9. CSRF Exempt Decorator â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_csrf_exempt(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect @csrf_exempt / @csrf.exempt â€” disables CSRF protection on endpoint.
    Source: graudit python.db (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        class _V(ast.NodeVisitor):
            def _check_decorator(self, dec: ast.AST, lineno: int) -> None:
                name = ""
                if isinstance(dec, ast.Name):
                    name = dec.id
                elif isinstance(dec, ast.Attribute):
                    name = dec.attr
                elif isinstance(dec, ast.Call):
                    fn = dec.func
                    name = (fn.attr if isinstance(fn, ast.Attribute)
                            else fn.id if isinstance(fn, ast.Name) else "")
                if "csrf_exempt" in name or ("csrf" in name and "exempt" in name):
                    detections.append(_Detection(
                        lineno=lineno,
                        message=(
                            f"@csrf_exempt at line {lineno} â€” "
                            f"disables CSRF protection; endpoint accepts cross-site requests"
                        ),
                        evidence={
                            "rewrite_candidate": (
                                "Remove @csrf_exempt. If required for API endpoints, "
                                "use token-based authentication (JWT/OAuth) instead of session cookies"
                            ),
                        },
                    ))

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                for dec in node.decorator_list:
                    self._check_decorator(dec, node.lineno)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                for dec in node.decorator_list:
                    self._check_decorator(dec, node.lineno)
                self.generic_visit(node)

        _V().visit(tree)

    # Heuristic â€” non-Python only
    if not detections and tree is None:
        for i, line in enumerate(content.splitlines(), 1):
            if _re2.search(r'csrf[_\.]exempt', line):
                detections.append(_Detection(
                    lineno=i,
                    message=f"CSRF exempt at line {i} â€” disables CSRF protection",
                    evidence={"rewrite_candidate": "Remove csrf_exempt; use token auth for APIs"},
                ))
    return detections




# â”€â”€ 10. Flask Debug Mode â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_flask_debug(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect Flask/Django app running with debug=True in production code.
    Debug mode exposes interactive debugger with remote code execution.
    Source: graudit python.db (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                fn = (func.attr if isinstance(func, ast.Attribute)
                      else func.id if isinstance(func, ast.Name) else "")
                if fn == "run":
                    for kw in node.keywords:
                        if (kw.arg == "debug"
                                and isinstance(kw.value, ast.Constant)
                                and kw.value.value is True):
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"app.run(debug=True) at line {node.lineno} â€” "
                                    f"exposes Werkzeug interactive debugger "
                                    f"(remote code execution)"
                                ),
                                evidence={
                                    "rewrite_candidate":
                                        "app.run(debug=os.getenv('FLASK_DEBUG', 'false') == 'true')"
                                        "  # never hardcode debug=True"
                                },
                            ))
                self.generic_visit(node)
        _V().visit(tree)

    # Heuristic â€” non-Python only
    if not detections and tree is None:
        for i, line in enumerate(content.splitlines(), 1):
            if _re2.search(r'\.run\s*\(.*debug\s*=\s*True', line):
                detections.append(_Detection(
                    lineno=i,
                    message=f"debug=True in app.run() at line {i} â€” RCE via Werkzeug debugger",
                    evidence={"rewrite_candidate": "Gate on environment variable, never hardcode"},
                ))
    return detections




# â”€â”€ 11. Bind All Interfaces â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_bind_all_interfaces(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect server bound to 0.0.0.0 â€” exposes service on all network interfaces.
    Source: gosec bind.go (Apache-2.0) G102.
    """
    detections: list[_Detection] = []
    bind_pat = _re2.compile(
        r'(?:listen|bind|serve|run)\s*\(\s*["\']'
        r'(?:0\.0\.0\.0|::)(?::\d+)?["\']',
        _re2.IGNORECASE,
    )
    host_pat = _re2.compile(
        r'host\s*[=:]\s*["\']0\.0\.0\.0["\']',
        _re2.IGNORECASE,
    )
    for i, line in enumerate(content.splitlines(), 1):
        if bind_pat.search(line) or host_pat.search(line):
            detections.append(_Detection(
                lineno=i,
                message=(
                    f"Service bound to 0.0.0.0 at line {i} â€” "
                    f"exposed on all network interfaces including external"
                ),
                evidence={
                    "rewrite_candidate":
                        "Bind to 127.0.0.1 for local services; "
                        "use a reverse proxy for external access"
                },
            ))
    return detections




# â”€â”€ 12. LDAP Injection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_ldap_injection(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect LDAP queries constructed with user input â€” allows auth bypass via
    )(uid=*))(|(uid=* injection. Source: PayloadsAllTheThings LDAP (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    _LDAP_SINKS = frozenset({"search", "search_s", "search_st", "search_ext",
                              "search_ext_s", "simple_bind_s", "bind_s"})
    _REQUEST_SOURCES = frozenset({"request", "req"})

    if tree is not None:
        tainted: dict[str, int] = {}

        def _is_req(node: ast.AST) -> bool:
            return any(
                isinstance(ch, ast.Name) and ch.id in _REQUEST_SOURCES
                for ch in ast.walk(node)
            )

        def _is_tainted(node: ast.AST) -> bool:
            return _is_req(node) or any(
                isinstance(ch, ast.Name) and ch.id in tainted
                for ch in ast.walk(node)
            )

        class _Taint(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                if _is_tainted(node.value) or isinstance(node.value, (ast.JoinedStr, ast.BinOp)):
                    if _is_tainted(node.value):
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                tainted[t.id] = node.lineno
                self.generic_visit(node)

        class _Sink(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                method = func.attr if isinstance(func, ast.Attribute) else ""
                if method in _LDAP_SINKS:
                    for arg in node.args:
                        if _is_tainted(arg):
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"LDAP injection: user-controlled value in "
                                    f".{method}() at line {node.lineno} â€” "
                                    f"auth bypass via )(uid=*))(|(uid=*"
                                ),
                                evidence={
                                    "rewrite_candidate": (
                                        "from ldap3.utils.conv import escape_filter_chars\n"
                                        "safe_user = escape_filter_chars(username)\n"
                                        "conn.search(base, f'(uid={safe_user})')"
                                    ),
                                },
                            ))
                self.generic_visit(node)

        _Taint().visit(tree)
        _Sink().visit(tree)

    return detections




# â”€â”€ 13. CSV / Formula Injection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_csv_injection(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect CSV formula injection: user data written to CSV without sanitizing
    leading =, +, -, @ characters that Excel/Sheets execute as formulas.
    Source: PayloadsAllTheThings CSV Injection (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    _CSV_WRITE_METHODS = frozenset({"writerow", "writerows", "write"})
    _REQUEST_SOURCES   = frozenset({"request", "req"})

    if tree is not None:
        tainted: dict[str, int] = {}

        def _is_tainted(node: ast.AST) -> bool:
            return any(
                isinstance(ch, ast.Name)
                and (ch.id in tainted or ch.id in _REQUEST_SOURCES)
                for ch in ast.walk(node)
            )

        class _Taint(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                if _is_tainted(node.value):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            tainted[t.id] = node.lineno
                self.generic_visit(node)

        class _Sink(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                method = func.attr if isinstance(func, ast.Attribute) else ""
                if method in _CSV_WRITE_METHODS and node.args:
                    if _is_tainted(node.args[0]):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"CSV injection: user-controlled data written to CSV "
                                f"at line {node.lineno} â€” "
                                f"Excel/Sheets executes values starting with =,+,-,@"
                            ),
                            evidence={
                                "rewrite_candidate": (
                                    "def sanitize_csv(value):\n"
                                    "    if str(value).startswith(('=','+','-','@','\\t','\\r')):\n"
                                    "        return \"'\" + str(value)  # prefix with single quote\n"
                                    "    return value"
                                ),
                            },
                        ))
                self.generic_visit(node)

        _Taint().visit(tree)
        _Sink().visit(tree)

    return detections




# â”€â”€ 14. Paramiko AutoAddPolicy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



