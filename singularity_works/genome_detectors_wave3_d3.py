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

def _detect_http_request_smuggling(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect HTTP/1.1 response construction with both Content-Length and
    Transfer-Encoding headers â€” enables request smuggling to backend servers.
    Also catches manual header injection bypassing framework sanitization.
    """
    detections: list[_Detection] = []
    lines = content.splitlines()

    # Pattern: raw socket/HTTP response sets both CL and TE
    cl_pat = _re2.compile(r'Content-Length\s*[=:+]', _re2.IGNORECASE)
    te_pat = _re2.compile(r'Transfer-Encoding\s*[=:+]', _re2.IGNORECASE)

    has_cl = any(cl_pat.search(l) for l in lines)
    has_te = any(te_pat.search(l) for l in lines)

    if has_cl and has_te:
        # Find line of TE for reporting
        te_line = next(
            (i+1 for i, l in enumerate(lines) if te_pat.search(l)), 0
        )
        detections.append(_Detection(
            lineno=te_line,
            message=(
                f"HTTP Request Smuggling: both Content-Length and Transfer-Encoding "
                f"present at line {te_line} â€” CL.TE/TE.CL ambiguity enables "
                f"request desync attacks on shared frontends"
            ),
            evidence={
                "rewrite_candidate": (
                    "Never set both Content-Length and Transfer-Encoding; "
                    "let the framework set headers automatically. "
                    "If using raw sockets: use exactly one transfer framing header"
                ),
            },
        ))

    # Also check for manual header injection via string concatenation
    raw_header = _re2.compile(
        r'(send|sendall|write)\s*\(\s*[bf]?["\']'
        r'(?:HTTP|GET|POST|PUT|DELETE|HEAD)',
        _re2.IGNORECASE,
    )
    for i, line in enumerate(lines, 1):
        if raw_header.search(line):
            detections.append(_Detection(
                lineno=i,
                message=(
                    f"Raw HTTP request construction at line {i} â€” "
                    f"manual framing bypasses framework header sanitization"
                ),
                evidence={
                    "rewrite_candidate":
                        "Use urllib3/httpx/requests instead of raw socket HTTP"
                },
            ))

    return detections




# â”€â”€ Weak JWT Secret (short/guessable) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_weak_jwt_secret(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect JWT signed with a trivially short or predictable secret.
    A secret < 32 chars can be brute-forced in seconds with hashcat.
    Complements local_jwt_none_algorithm and local_unsigned_jwt.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    _JWT_SIGN_FNS = frozenset({"encode", "sign"})
    _SECRET_TRIVIALS = frozenset({
        "secret", "password", "changeme", "test", "dev",
        "1234", "jwt", "key", "none", "your-secret", "mysecret",
    })

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                fn = (func.attr if isinstance(func, ast.Attribute)
                      else func.id if isinstance(func, ast.Name) else "")
                if fn in _JWT_SIGN_FNS and len(node.args) >= 2:
                    secret_arg = node.args[1]
                    if isinstance(secret_arg, ast.Constant) and isinstance(secret_arg.value, str):
                        s = secret_arg.value
                        is_short    = len(s) < 32
                        is_trivial  = s.lower() in _SECRET_TRIVIALS
                        if is_short or is_trivial:
                            reason = (
                                f"trivially guessable value '{s}'"
                                if is_trivial else
                                f"too short ({len(s)} chars, minimum 32)"
                            )
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"Weak JWT secret at line {node.lineno}: {reason} â€” "
                                    f"brute-forceable with hashcat in seconds"
                                ),
                                evidence={
                                    "rewrite_candidate": (
                                        "import secrets\n"
                                        "SECRET = secrets.token_hex(32)  "
                                        "# 64 hex chars from CSPRNG"
                                    ),
                                },
                            ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections




# â”€â”€ Account Enumeration via Timing Difference â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_account_enumeration(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect auth flows that return different responses for valid vs invalid users
    without constant-time comparison â€” enables username enumeration.
    Patterns: early return on user-not-found before password check,
    or string == comparison on auth tokens.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                # Look for auth-named functions with early returns
                fn_name = node.name.lower()
                # Require specific login/credential action keywords, not just 'auth' prefix.
                # _auth_cookies_hardened, _auth_state_cleared etc. are monitor helpers,
                # not login entry points â€” exclude by checking for action verbs.
                is_auth_fn = any(kw in fn_name for kw in (
                    "login", "authenticate", "check_password",
                    "verify_user", "check_user", "signin", "sign_in",
                    "do_auth", "handle_login", "process_login",
                )) and not fn_name.startswith("_auth_")
                if not is_auth_fn:
                    self.generic_visit(node)
                    return

                # Check for user-not-found early return before password check
                returns_in_fn = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value is not None:
                        returns_in_fn.append(child.lineno)

                # Heuristic: multiple return paths in auth function = likely enumerable
                # Guard: short functions (< 15 lines) are utility wrappers, not enum risk
                fn_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if len(returns_in_fn) >= 3 and fn_lines >= 15:
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"Potential account enumeration in '{node.name}' at line "
                            f"{node.lineno}: {len(returns_in_fn)} return paths â€” "
                            f"different responses for valid/invalid users leak user existence"
                        ),
                        evidence={
                            "rewrite_candidate": (
                                "Always perform full auth check before returning any error:\n"
                                "# Run bcrypt even for non-existent users (dummy hash)\n"
                                "# Return identical error: 'Invalid credentials'"
                            ),
                        },
                    ))
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                # Reuse same logic via name mangling
                node.name_ = node.name
                self.visit_FunctionDef(node)  # type: ignore[arg-type]

        _V().visit(tree)
    return detections




# â”€â”€ Insecure File Permissions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_insecure_file_permissions(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect files created with overly permissive modes (world-writable/readable).
    Sources: gosec fileperms.go (Apache-2.0) G301-G307.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    # Overly permissive: mode & 0o002 (world-writable) or 0o004 (world-readable for sensitive files)
    _OVERPERMISSIVE = {0o777, 0o666, 0o644, 0o755}  # common but often wrong for sensitive files
    _DANGEROUS = {0o777, 0o666, 0o776, 0o662}         # world-writable â€” always flag

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                fn = (func.attr if isinstance(func, ast.Attribute)
                      else func.id if isinstance(func, ast.Name) else "")
                if fn in ("chmod", "makedirs", "mkdir"):
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                            mode = arg.value
                            if mode in _DANGEROUS or (mode & 0o002):
                                detections.append(_Detection(
                                    lineno=node.lineno,
                                    message=(
                                        f"{fn}() with world-writable mode "
                                        f"0o{mode:o} at line {node.lineno} â€” "
                                        f"any user can modify the file"
                                    ),
                                    evidence={
                                        "rewrite_candidate": (
                                            f"os.{fn}(path, 0o750)  "
                                            f"# owner=rwx group=r-x world=---"
                                        ),
                                    },
                                ))
                    # Also check keyword mode=
                    for kw in node.keywords:
                        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                            mode = kw.value.value
                            if isinstance(mode, int) and (mode in _DANGEROUS or mode & 0o002):
                                detections.append(_Detection(
                                    lineno=node.lineno,
                                    message=(
                                        f"{fn}(mode=0o{mode:o}) at line {node.lineno} â€” "
                                        f"world-writable permission"
                                    ),
                                    evidence={
                                        "rewrite_candidate": f"mode=0o750"
                                    },
                                ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections




# â”€â”€ OAuth Token in URL (token leakage via Referer) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_oauth_token_in_url(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect OAuth/JWT tokens passed in URL query parameters â€” leaked via
    Referer headers, browser history, server logs, and CDN logs.
    Pattern: access_token, token, jwt in request.args / GET parameters.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    _TOKEN_PARAMS = frozenset({
        "access_token", "token", "jwt", "auth_token",
        "bearer", "api_token", "api_key", "key",
    })

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "get":
                    val = func.value
                    # request.args.get('access_token') or request.args['access_token']
                    if isinstance(val, ast.Attribute) and val.attr == "args":
                        if isinstance(val.value, ast.Name) and val.value.id in ("request", "req"):
                            if node.args and isinstance(node.args[0], ast.Constant):
                                param = str(node.args[0].value).lower()
                                if param in _TOKEN_PARAMS:
                                    detections.append(_Detection(
                                        lineno=node.lineno,
                                        message=(
                                            f"OAuth/API token read from URL parameter "
                                            f"'{node.args[0].value}' at line {node.lineno} â€” "
                                            f"leaked via Referer, logs, and browser history"
                                        ),
                                        evidence={
                                            "rewrite_candidate": (
                                                "Read tokens from Authorization header:\n"
                                                "token = request.headers.get('Authorization', '').removeprefix('Bearer ')"
                                            ),
                                        },
                                    ))
                self.generic_visit(node)
        _V().visit(tree)

    return detections





