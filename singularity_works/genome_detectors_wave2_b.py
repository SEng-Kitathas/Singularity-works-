from __future__ import annotations

import ast
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

def _detect_format_string_c(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    C format string vulnerability: printf/fprintf/sprintf called with a
    user-controlled format string (not a string literal). Allows %n writes,
    stack reads, and arbitrary memory access.
    """
    import re as _re
    detections: list[_Detection] = []
    # printf/fprintf/etc where first meaningful arg is NOT a string literal
    # Pattern: printf(variable) or printf(param_name) â€” no literal first arg
    printf_re = _re.compile(r'\b(printf|fprintf|sprintf|snprintf|vprintf)\s*\(\s*(\w+)\s*[,)]')
    for m in printf_re.finditer(content):
        # Skip if inside a string/comment context (docstrings, detection pattern strings)
        ls = content.rfind('\n', 0, m.start()) + 1
        stripped = content[ls:m.start()].lstrip()
        if stripped.startswith(('#', '"', "'", 'f"', "f'", 'r"', "r'", '//')):
            continue
        fn_name = m.group(1)
        first_arg = m.group(2)
        if first_arg in ('stdout', 'stderr', 'stdin'):
            continue
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f"Format string vulnerability: {fn_name}({first_arg}) at line {line} â€” "
                f"if '{first_arg}' contains user input, attacker controls format specifiers; "
                f"%n enables arbitrary write, %x/%p leak stack memory"
            ),
            evidence={"rewrite_candidate":
                f"Use a literal format string: {fn_name}(\"%s\", {first_arg}); "
                "never pass user input as the format argument"},
        ))
    return detections



def _detect_integer_overflow_alloc(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Integer overflow in allocation: count * element_size can wrap to a small
    number with large inputs, causing under-allocation followed by overflow write.
    Pattern: malloc/calloc with multiplication in argument.
    """
    import re as _re
    detections: list[_Detection] = []
    # malloc with arithmetic expression containing multiplication
    malloc_re = _re.compile(r'\bmalloc\s*\(\s*(\w+)\s*\*\s*(\w+)\s*\)')
    for m in malloc_re.finditer(content):
        arg1, arg2 = m.group(1), m.group(2)
        line = content[:m.start()].count('\n') + 1
        # Skip if arguments are constants (all digits)
        if arg1.isdigit() and arg2.isdigit():
            continue
        detections.append(_Detection(
            lineno=line,
            message=(
                f"Integer overflow in malloc at line {line}: "
                f"malloc({arg1} * {arg2}) â€” if either value is attacker-controlled, "
                f"multiplication can overflow to a small value causing under-allocation"
            ),
            evidence={"rewrite_candidate":
                f"Use checked_mul or assert no overflow: "
                f"if ({arg1} > SIZE_MAX / {arg2}) abort(); "
                f"or use calloc({arg1}, {arg2}) which handles overflow internally"},
        ))
    # Also catch: count * element_size stored to int before malloc
    int_mult_re = _re.compile(r'\bint\s+\w+\s*=\s*(\w+)\s*\*\s*(\w+)\s*;')
    for m in int_mult_re.finditer(content):
        arg1, arg2 = m.group(1), m.group(2)
        if arg1.isdigit() and arg2.isdigit():
            continue
        # Check if malloc is called nearby with the result
        ctx = content[m.start():m.start()+200]
        if 'malloc' in ctx or 'alloc' in ctx:
            line = content[:m.start()].count('\n') + 1
            detections.append(_Detection(
                lineno=line,
                message=(
                    f"Integer overflow risk at line {line}: "
                    f"int result = {arg1} * {arg2} â€” signed int multiplication can overflow "
                    f"to negative value before passing to malloc"
                ),
                evidence={"rewrite_candidate":
                    "Use size_t for allocation arithmetic; add overflow check before multiply"},
            ))
    return detections



def _detect_goroutine_leak(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Go goroutine leak: goroutine launched with a channel send but no
    error/cancel path that also sends. Goroutine blocks forever on error.
    Detects the pattern where goroutine body has channel send on success
    but bare return on error â€” blocked forever on error path.
    """
    import re as _re
    detections: list[_Detection] = []
    # Find goroutine launches with channel operations
    for m in _safe_dotall_finditer(r'\bgo\s+func\s*\(\s*\)', content, _re.DOTALL):
        # Extract goroutine body up to the closing }
        body_start = content.find('{', m.start())
        if body_start == -1:
            continue
        # Find matching close brace (simple depth count)
        depth = 0
        body_end = body_start
        for i in range(body_start, min(body_start + 1000, len(content))):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    body_end = i
                    break
        body = content[body_start:body_end]
        has_channel_send = '<-' in body and 'ch' in body
        has_error_path = 'err != nil' in body or 'if err' in body
        # Bug: error path returns WITHOUT sending to channel
        has_bare_return_in_error = _re.search(r'if err[^{]*\{[^}]*\breturn\b[^}]*\}', body)
        # Skip if this goroutine is in a string context (forge self-scan guard)
        pre_char = content[max(0, m.start()-1):m.start()]
        in_string = pre_char in ('"', "'")
        if in_string:
            continue
        is_go = ('package ' in content[:400] or 'import "' in content
                 or content.lstrip().startswith('package '))
        if not is_go:
            continue
        if has_channel_send and has_error_path and has_bare_return_in_error:
            line = content[:m.start()].count('\n') + 1
            detections.append(_Detection(
                lineno=line,
                message=(
                    f"Goroutine leak at line {line}: goroutine sends to channel on success "
                    f"but returns without sending on error â€” caller blocks forever on error path"
                ),
                evidence={"rewrite_candidate":
                    "On error path, send zero value or use context cancellation: "
                    "if err != nil { ch <- \"\"; return } "
                    "or use a select with context.Done() to unblock caller"},
            ))
    return detections



def _detect_prototype_constructor_pollution(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Prototype pollution via constructor.prototype: iterating over Object.keys()
    skips __proto__ but NOT 'constructor'. Setting target['constructor'] then
    target['constructor']['prototype'] pollutes the global Object prototype.
    """
    import re as _re
    detections: list[_Detection] = []
    # Object.keys() iteration without guarding 'constructor'
    keys_iter = _re.compile(r'Object\.keys\s*\([^)]+\)\.forEach|for\s*\(.*of\s+Object\.keys')
    for m in keys_iter.finditer(content):
        context = content[m.start():m.start()+500]
        # No constructor guard
        has_constructor_guard = 'constructor' in context and ('==' in context or '===' in context)
        if not has_constructor_guard:
            line = content[:m.start()].count('\n') + 1
            detections.append(_Detection(
                lineno=line,
                message=(
                    f"Prototype pollution via constructor at line {line}: "
                    f"Object.keys() skips __proto__ but NOT 'constructor' â€” "
                    f"attacker can set target['constructor']['prototype']['isAdmin'] = true"
                ),
                evidence={"rewrite_candidate":
                    "Guard all three dangerous keys: "
                    "if (key === '__proto__' || key === 'constructor' || "
                    "key === 'prototype') continue; "
                    "or use Object.create(null) for safe accumulation"},
            ))
    return detections

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------



def _detect_reflection_injection(content, _spec, *, semantic_ir=None):
    import re as _re
    detections = []

    def _is_real_code(pos):
        ls = content.rfind('\n', 0, pos) + 1
        prefix = content[ls:pos].lstrip()
        return not (prefix.startswith('#') or prefix[:1] in ('"', "'"))

    for m in _re.finditer(r'\bClass\.forName\s*\(\s*(\w+)\s*\)', content):
        if not _is_real_code(m.start()):
            continue
        arg = m.group(1)
        if arg in ('String', 'Class', 'className'):
            continue
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f'Reflection injection at line {line}: Class.forName({arg}) '
                f'with non-literal class name â€” attacker loads arbitrary classes'
            ),
            evidence={'rewrite_candidate':
                'Validate class name against an allowlist; '
                'never use user input as Class.forName() argument'},
        ))

    for m in _re.finditer(r'\bgetDeclaredMethod\s*\(\s*(\w+)\s*[,)]', content):
        if not _is_real_code(m.start()):
            continue
        arg = m.group(1)
        if len(arg) < 2:
            continue
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f'Reflection injection at line {line}: getDeclaredMethod({arg}) '
                f'with non-literal method name'
            ),
            evidence={'rewrite_candidate': 'Validate method name against an allowlist'},
        ))

    return detections


def _detect_unsigned_jwt(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Unsigned / hand-rolled JWT: base64.b64decode() on a token header/cookie
    followed by json.loads() followed by trusting the role/is_admin/scope fields.
    No cryptographic signature verification.
    Isomorphism: same as deserialize-and-trust â€” arbitrary attacker data becomes
    trusted identity claims.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        # Look for: b64decode followed by json.loads, then field access for role/admin
        has_b64decode = False
        has_json_loads = False
        has_role_check = False
        b64_line = 0

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            # base64.b64decode or b64decode
            is_b64 = (
                (isinstance(func, ast.Attribute) and func.attr in ('b64decode', 'urlsafe_b64decode')) or
                (isinstance(func, ast.Name) and func.id in ('b64decode', 'urlsafe_b64decode'))
            )
            if is_b64:
                has_b64decode = True
                b64_line = node.lineno
            # json.loads
            is_json = (
                (isinstance(func, ast.Attribute) and func.attr == 'loads' and
                 isinstance(func.value, ast.Name) and func.value.id == 'json')
            )
            if is_json:
                has_json_loads = True

        # Check for role/admin/scope/permission field access from decoded payload
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Constant):
                    key = str(node.slice.value).lower()
                    if key in ('role', 'is_admin', 'admin', 'scope', 'permission', 'permissions'):
                        has_role_check = True
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == 'get':
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            key = str(arg.value).lower()
                            if key in ('role', 'is_admin', 'admin', 'scope'):
                                has_role_check = True

        if has_b64decode and has_json_loads and has_role_check:
            detections.append(_Detection(
                lineno=b64_line,
                message=(
                    f"Unsigned token at line {b64_line}: base64-decoded JSON is trusted for "
                    f"role/admin/scope without cryptographic signature verification â€” "
                    f"attacker encodes arbitrary claims and escalates privileges"
                ),
                evidence={"rewrite_candidate":
                    "Use a proper JWT library with signature verification: "
                    "jwt.decode(token, secret, algorithms=['HS256']); "
                    "never trust base64-decoded token contents without verifying HMAC/RSA signature"},
            ))

    # Heuristic fallback: detect pattern in non-Python
    import re as _re
    if not detections:
        # base64 decode + JSON parse in same function + role/admin check
        has_decode = bool(_re.search(r'base64|b64decode|atob\(', content, _re.IGNORECASE))
        has_parse = bool(_re.search(r'JSON\.parse|json\.loads|JSON\.decode', content))
        has_role = bool(_re.search(r'"role"|"admin"|"is_admin"|"scope"|role\s*==', content))
        has_no_verify = not bool(_re.search(r'verify|signature|sign|hmac|jwt\.decode', content, _re.IGNORECASE))
        if has_decode and has_parse and has_role and has_no_verify:
            detections.append(_Detection(
                lineno=1,
                message=(
                    "Unsigned token: base64-decoded payload is trusted for authorization "
                    "without cryptographic signature verification"
                ),
                evidence={"rewrite_candidate":
                    "Use a verified JWT library; never trust base64-decoded token contents "
                    "without signature verification"},
            ))
    return detections


# ---------------------------------------------------------------------------
# IRIS-mode escalation
# Isomorphism: IRIS (arXiv 2405.17238) goes LLMâ†’formalâ†’LLM.
# The forge goes heuristicâ†’gateâ†’LLM.
# When IR confidence is low, the forge escalates to IRIS-mode:
# the REASONER infers source/sink specs as a DynamicCapsule,
# which is then treated as a first-class genome capsule for this artifact.
# ---------------------------------------------------------------------------


