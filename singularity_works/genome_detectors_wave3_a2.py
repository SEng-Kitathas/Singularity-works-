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

_SECRET_NAMES = _re_ext.compile(
    r'(?i)(api[_-]?key|secret|token|passwd|password|auth[_-]?token|aws_access_key_id|aws_secret_access_key)'
)
_SECRET_VALUE = _re_ext.compile(
    r"""(?i)(?:=|:|=>)\s*["']([A-Za-z0-9_\-\/+=]{16,})["']"""
)

def _detect_hardcoded_secrets(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect hardcoded credentials and secrets assigned to named variables.
    Looks for: secret-named variable = non-empty string literal,
    AWS/GitHub/Stripe key patterns, high-entropy literals in secret contexts.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                val = node.value
                if not isinstance(val, ast.Constant) or not isinstance(val.value, str):
                    self.generic_visit(node)
                    return
                secret = val.value
                if not secret or len(secret) < 8:
                    self.generic_visit(node)
                    return
                # Placeholder values are not real secrets
                if secret.lower() in {
                    "changeme", "your_secret_here", "placeholder",
                    "xxxxxxxx", "todo", "none", "null", "example",
                    "your-secret", "change-me",
                }:
                    self.generic_visit(node)
                    return
                for target in node.targets:
                    name = (
                        target.id if isinstance(target, ast.Name)
                        else target.attr if isinstance(target, ast.Attribute)
                        else None
                    )
                    if name and _SECRET_NAMES.search(name):
                        # Check if value looks like a real secret
                        is_key_pattern = bool(_SECRET_VALUE.search(secret))
                        is_long_opaque  = len(secret) >= 16
                        if is_key_pattern or is_long_opaque:
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"Hardcoded credential '{name}' at line {node.lineno} â€” "
                                    f"secret literals are extractable from source and binaries"
                                ),
                                evidence={
                                    "rewrite_candidate": (
                                        f"{name} = os.environ['{name.upper()}']  "
                                        f"# or use a secrets manager"
                                    ),
                                    "var_name": name,
                                },
                            ))
                self.generic_visit(node)

        _V().visit(tree)

    # Heuristic â€” raw content scan for key patterns (catches non-Python)
    if not detections:
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if _SECRET_NAMES.search(line) and _SECRET_VALUE.search(line):
                # Skip if it looks like a test/example file
                if not any(skip in line for skip in ("#", "//", "test", "example", "TODO")):
                    detections.append(_Detection(
                        lineno=i,
                        message=(
                            f"Possible hardcoded secret at line {i} â€” "
                            f"high-entropy value in credential-named context"
                        ),
                        evidence={
                            "rewrite_candidate":
                                "Load from environment variable or secrets manager",
                        },
                    ))

    return detections




# â”€â”€ Insecure Cookie Flags â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_insecure_cookie(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect set_cookie / response.set_cookie calls missing security flags.
    Flags checked: httponly, secure, samesite.
    Missing httponly â†’ XSS steals session.
    Missing secure â†’ cookie sent over HTTP.
    Missing samesite â†’ CSRF risk.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        _COOKIE_CALLS = frozenset({"set_cookie", "set_signed_cookie", "set_cookie_header"})

        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                call_name = (
                    func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name)
                    else None
                )
                if call_name in _COOKIE_CALLS:
                    kw_names = {kw.arg for kw in node.keywords}
                    # httponly check
                    httponly_ok = (
                        "httponly" in kw_names
                        and any(
                            kw.arg == "httponly"
                            and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True
                            for kw in node.keywords
                        )
                    )
                    secure_ok = (
                        "secure" in kw_names
                        and any(
                            kw.arg == "secure"
                            and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True
                            for kw in node.keywords
                        )
                    )
                    samesite_ok = "samesite" in kw_names

                    missing = []
                    if not httponly_ok:
                        missing.append("httponly=True")
                    if not secure_ok:
                        missing.append("secure=True")
                    if not samesite_ok:
                        missing.append("samesite='Strict'")

                    if missing:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Insecure cookie at line {node.lineno} â€” "
                                f"missing flags: {', '.join(missing)}"
                            ),
                            evidence={
                                "rewrite_candidate": (
                                    f"response.set_cookie(name, value, "
                                    f"httponly=True, secure=True, samesite='Strict')"
                                ),
                                "missing_flags": missing,
                            },
                        ))
                self.generic_visit(node)

        _V().visit(tree)

    return detections




# â”€â”€ CORS Wildcard with Credentials â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_cors_wildcard(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect CORS configured to allow all origins (*) â€” especially dangerous
    when credentials are also allowed. Also catches explicit wildcard in
    response headers.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                call_name = (
                    func.id if isinstance(func, ast.Name)
                    else func.attr if isinstance(func, ast.Attribute)
                    else ""
                )
                # CORS(app, origins="*") or CORS(app, resources={r"/*": {"origins": "*"}})
                if call_name in ("CORS", "cross_origin"):
                    kws = {kw.arg: kw.value for kw in node.keywords}
                    origins_val = kws.get("origins")
                    allow_all = (
                        isinstance(origins_val, ast.Constant) and origins_val.value == "*"
                    ) or (
                        isinstance(origins_val, ast.List) and
                        any(
                            isinstance(e, ast.Constant) and e.value == "*"
                            for e in origins_val.elts
                        )
                    )
                    if allow_all:
                        creds_val = kws.get("supports_credentials") or kws.get("allow_credentials")
                        has_creds = (
                            isinstance(creds_val, ast.Constant) and creds_val.value is True
                        )
                        msg = (
                            f"CORS wildcard origin ('*') with credentials at line {node.lineno} â€” "
                            f"attacker can make authenticated cross-origin requests"
                            if has_creds else
                            f"CORS wildcard origin ('*') at line {node.lineno} â€” "
                            f"any site can read responses; add credentials and this becomes critical"
                        )
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=msg,
                            evidence={
                                "rewrite_candidate": (
                                    "CORS(app, origins=['https://trusted.example.com'], "
                                    "supports_credentials=True)"
                                ),
                            },
                        ))
                self.generic_visit(node)

        _V().visit(tree)

    # Heuristic: raw header scan for non-Python content only.
    # When tree is not None (valid Python), the AST path is authoritative â€”
    # the heuristic would fire on detection literal strings embedded in
    # Python source (e.g. "origins='*'" in rewrite candidates).
    if not detections and tree is None:
        lines = content.splitlines()
        wildcard_pat = _re_ext.compile(
            r'Access-Control-Allow-Origin.*\*|allow.?origins?\s*[=:]\s*["\'\[]\s*\*',
            _re_ext.IGNORECASE,
        )
        for i, line in enumerate(lines, 1):
            if wildcard_pat.search(line):
                detections.append(_Detection(
                    lineno=i,
                    message=(
                        f"CORS wildcard at line {i} â€” "
                        f"'Access-Control-Allow-Origin: *' exposes responses to any origin"
                    ),
                    evidence={
                        "rewrite_candidate":
                            "Restrict to explicit trusted origins; never use * with credentials",
                    },
                ))

    return detections




# â”€â”€ CRLF / Header Injection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



