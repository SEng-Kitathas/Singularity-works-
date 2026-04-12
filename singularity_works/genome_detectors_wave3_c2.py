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

def _detect_jwt_none_algorithm(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect JWT decoded/verified with algorithms=['none'] or no algorithm check.
    Also catches UnsafeAllowNoneSignatureType, verify=False, verify_signature=False.
    Sources: graudit jwt.db (MIT), PayloadsAllTheThings JWT (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    _NONE_VARIANTS = frozenset({"none", "None", "NONE"})

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                call_name = (
                    func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name)
                    else ""
                )
                if call_name in ("decode", "verify"):
                    for kw in node.keywords:
                        # algorithms=['none'] or algorithms=[]
                        if kw.arg == "algorithms":
                            val = kw.value
                            if isinstance(val, ast.List):
                                for elt in val.elts:
                                    if (isinstance(elt, ast.Constant)
                                            and str(elt.value).lower() == "none"):
                                        detections.append(_Detection(
                                            lineno=node.lineno,
                                            message=(
                                                f"JWT decoded with algorithms=['none'] at "
                                                f"line {node.lineno} â€” "
                                                f"signature verification bypassed completely"
                                            ),
                                            evidence={
                                                "rewrite_candidate":
                                                    "jwt.decode(token, key, algorithms=['HS256'])"
                                                    "  # always specify expected algorithm"
                                            },
                                        ))
                            if isinstance(val, ast.List) and not val.elts:
                                detections.append(_Detection(
                                    lineno=node.lineno,
                                    message=(
                                        f"JWT decoded with algorithms=[] at line {node.lineno} "
                                        f"â€” empty algorithm list disables verification"
                                    ),
                                    evidence={
                                        "rewrite_candidate":
                                            "jwt.decode(token, key, algorithms=['HS256'])"
                                    },
                                ))
                        # options={'verify_signature': False}
                        if kw.arg == "options" and isinstance(kw.value, ast.Dict):
                            for k, v in zip(kw.value.keys, kw.value.values):
                                if (isinstance(k, ast.Constant)
                                        and k.value == "verify_signature"
                                        and isinstance(v, ast.Constant)
                                        and v.value is False):
                                    detections.append(_Detection(
                                        lineno=node.lineno,
                                        message=(
                                            f"JWT signature verification disabled via "
                                            f"options at line {node.lineno}"
                                        ),
                                        evidence={
                                            "rewrite_candidate":
                                                "Remove options={'verify_signature': False}; "
                                                "always verify"
                                        },
                                    ))
                self.generic_visit(node)

        _V().visit(tree)

    # Heuristic â€” multi-language (graudit jwt.db patterns, MIT).
    # Gate behind tree is None: Python files contain these pattern strings
    # as literals in the detector source, causing self-referential FPs.
    if not detections and tree is None:
        patterns = [
            (_re2.compile(r'algorithms?\s*=\s*\[?\s*["\']none["\']', _re2.IGNORECASE),
             "JWT algorithm set to 'none'"),
            (_re2.compile(r'UnsafeAllowNoneSignatureType', _re2.IGNORECASE),
             "JWT UnsafeAllowNoneSignatureType used"),
            (_re2.compile(r'verify_signature["\']?\s*[=:]\s*[Ff]alse'),
             "JWT verify_signature disabled"),
            (_re2.compile(r'ValidateLifetime\s*=\s*false', _re2.IGNORECASE),
             "JWT lifetime validation disabled"),
            (_re2.compile(r'ParseUnverified\s*\('),
             "JWT ParseUnverified called â€” token not verified"),
        ]
        for i, line in enumerate(content.splitlines(), 1):
            for pat, msg in patterns:
                if pat.search(line):
                    detections.append(_Detection(
                        lineno=i,
                        message=f"{msg} at line {i}",
                        evidence={
                            "rewrite_candidate": "Always verify JWT with expected algorithm and secret"
                        },
                    ))
                    break

    return detections




# â”€â”€ 5. SSTI â€” Jinja2 render_template_string â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_ssti_render_template_string(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect Server-Side Template Injection via render_template_string() with
    non-literal argument (user input flows into template engine).
    Also catches Jinja2 Environment with autoescape=False.
    Source: graudit python.db (MIT), PayloadsAllTheThings SSTI (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    _REQUEST_SOURCES = frozenset({"request", "req"})
    _REQUEST_ATTRS   = frozenset({"args", "form", "json", "data", "params", "values"})

    if tree is not None:
        tainted: dict[str, int] = {}

        def _is_req(node: ast.AST) -> bool:
            if not isinstance(node, ast.Call):
                return False
            f = node.func
            if isinstance(f, ast.Attribute):
                v = f.value
                if isinstance(v, ast.Attribute):
                    return (isinstance(v.value, ast.Name)
                            and v.value.id in _REQUEST_SOURCES
                            and v.attr in _REQUEST_ATTRS)
                if isinstance(v, ast.Name) and v.id in _REQUEST_SOURCES:
                    return True
            return False

        def _is_tainted(node: ast.AST) -> bool:
            return _is_req(node) or any(
                isinstance(ch, ast.Name) and ch.id in tainted
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
                fn = (func.attr if isinstance(func, ast.Attribute)
                      else func.id if isinstance(func, ast.Name) else "")
                # render_template_string with tainted arg
                if fn == "render_template_string" and node.args:
                    if _is_tainted(node.args[0]):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"SSTI: render_template_string() with user-controlled "
                                f"template at line {node.lineno} â€” "
                                f"attacker can execute arbitrary code via {{{{7*7}}}}"
                            ),
                            evidence={
                                "rewrite_candidate": (
                                    "Never pass user input as the template string itself.\n"
                                    "Use: render_template('fixed_template.html', value=user_input)"
                                ),
                            },
                        ))
                # Jinja2 Environment with autoescape=False
                if fn == "Environment":
                    for kw in node.keywords:
                        if (kw.arg == "autoescape"
                                and isinstance(kw.value, ast.Constant)
                                and kw.value.value is False):
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"Jinja2 Environment(autoescape=False) at line "
                                    f"{node.lineno} â€” XSS if any user data rendered"
                                ),
                                evidence={
                                    "rewrite_candidate":
                                        "Environment(autoescape=True)  # or use select_autoescape()"
                                },
                            ))
                self.generic_visit(node)

        _Taint().visit(tree)
        _Sink().visit(tree)

    # Heuristic
    if not detections:
        for i, line in enumerate(content.splitlines(), 1):
            if _re2.search(r'render_template_string\s*\(', line):
                if _re2.search(r'request\.|req\.', line):
                    detections.append(_Detection(
                        lineno=i,
                        message=f"Potential SSTI: render_template_string with request data at line {i}",
                        evidence={"rewrite_candidate": "Use render_template() with a fixed template file"},
                    ))
    return detections




# â”€â”€ 6. RSA Key < 2048 bits â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_weak_rsa_key(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect RSA key generation with fewer than 2048 bits.
    Source: gosec rsa.go (Apache-2.0) G403.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    _MIN_RSA_BITS = 2048

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                # rsa.generate_private_key(public_exponent=65537, key_size=1024, ...)
                # Crypto.PublicKey.RSA.generate(1024)
                if isinstance(func, ast.Attribute) and func.attr in (
                    "generate_private_key", "generate", "generate_key"
                ):
                    # Check positional args
                    for arg in node.args:
                        if (isinstance(arg, ast.Constant)
                                and isinstance(arg.value, int)
                                and 0 < arg.value < _MIN_RSA_BITS):
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"RSA key size {arg.value} bits at line {node.lineno} "
                                    f"is below minimum 2048 bits â€” brute-forceable"
                                ),
                                evidence={
                                    "rewrite_candidate":
                                        "rsa.generate_private_key(public_exponent=65537, key_size=4096)"
                                },
                            ))
                    # Check key_size kwarg
                    for kw in node.keywords:
                        if (kw.arg in ("key_size", "bits", "keysize")
                                and isinstance(kw.value, ast.Constant)
                                and isinstance(kw.value.value, int)
                                and 0 < kw.value.value < _MIN_RSA_BITS):
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"RSA key_size={kw.value.value} bits at line "
                                    f"{node.lineno} â€” minimum is 2048"
                                ),
                                evidence={
                                    "rewrite_candidate":
                                        "key_size=4096  # 2048 minimum, 4096 recommended"
                                },
                            ))
                self.generic_visit(node)
        _V().visit(tree)

    # Heuristic â€” non-Python only
    if not detections and tree is None:
        for i, line in enumerate(content.splitlines(), 1):
            if _re2.search(r'(?:RSA|rsa|generate_key|GenerateKey)', line):
                m = _re2.search(r'\b(512|768|1024)\b', line)
                if m:
                    detections.append(_Detection(
                        lineno=i,
                        message=(
                            f"RSA key size {m.group(1)} bits at line {i} â€” "
                            f"below 2048-bit minimum"
                        ),
                        evidence={"rewrite_candidate": "Use minimum 2048 bits (4096 recommended)"},
                    ))
    return detections




# â”€â”€ 7. GraphQL Introspection Enabled â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_graphql_introspection(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect GraphQL configured with introspection enabled in production.
    Introspection leaks the full schema to attackers.
    Source: PayloadsAllTheThings GraphQL Injection (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                fn = (func.id if isinstance(func, ast.Name)
                      else func.attr if isinstance(func, ast.Attribute) else "")
                # GraphQL(schema, introspection=True) or GraphQLSchema without middleware
                if fn in ("GraphQL", "GraphQLSchema", "Ariadne", "strawberry"):
                    for kw in node.keywords:
                        if (kw.arg == "introspection"
                                and isinstance(kw.value, ast.Constant)
                                and kw.value.value is True):
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"GraphQL introspection=True at line {node.lineno} â€” "
                                    f"leaks full schema to unauthenticated attackers"
                                ),
                                evidence={
                                    "rewrite_candidate": (
                                        "GraphQL(schema, introspection=os.getenv('DEBUG')=='true')\n"
                                        "# Disable in production; enable only in development"
                                    ),
                                },
                            ))
                self.generic_visit(node)
        _V().visit(tree)

    # Heuristic â€” non-Python only
    if not detections and tree is None:
        for i, line in enumerate(content.splitlines(), 1):
            if _re2.search(r'introspection\s*[=:]\s*[Tt]rue', line):
                detections.append(_Detection(
                    lineno=i,
                    message=f"GraphQL introspection enabled at line {i} â€” disable in production",
                    evidence={"rewrite_candidate": "Set introspection=False or gate on DEBUG env var"},
                ))
    return detections




# â”€â”€ 8. Secret Serialization â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



