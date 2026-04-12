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

def _detect_toctou(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Detect TOCTOU: access()/stat() check followed by open() on same path.
    The window between check and act allows symlink swapping.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:

        class _Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.access_lines: list[int] = []

            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                # os.access, os.stat, os.path.exists
                if isinstance(func, ast.Attribute) and func.attr in ("access", "stat"):
                    self.access_lines.append(node.lineno)
                elif isinstance(func, ast.Name) and func.id in ("access", "stat"):
                    self.access_lines.append(node.lineno)
                # open() after access â€” if within 5 lines, flag it
                if isinstance(func, ast.Name) and func.id == "open" and self.access_lines:
                    last_check = self.access_lines[-1]
                    if 0 < node.lineno - last_check <= 5:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"TOCTOU: open() at line {node.lineno} follows "
                                f"access check at line {last_check} â€” "
                                f"symlink can be swapped in the window between"
                            ),
                            evidence={"rewrite_candidate": "Use O_NOFOLLOW flag or atomic open without prior access()"},
                        ))
                self.generic_visit(node)

        v = _Visitor()
        v.visit(tree)
    # IR fallback: temporal gaps detected by polyglot front door
    if not detections and semantic_ir is not None:
        for gap in getattr(semantic_ir, "temporal_gaps", []):
            if gap.gap_type == "TOCTOU":
                detections.append(_Detection(
                    lineno=gap.check_line,
                    message=(
                        f"TOCTOU: {gap.description} â€” "
                        f"symlink can be substituted between check at "
                        f"line {gap.check_line} and act at line {gap.act_line}"
                    ),
                    evidence={
                        "rewrite_candidate": (
                            "Use open(path, O_WRONLY|O_NOFOLLOW) directly â€” "
                            "eliminates the check-act window; "
                            "kernel rejects symlinks atomically"
                        ),
                    },
                ))
    return detections




def _detect_ssrf(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Detect SSRF: user-controlled URL flowing into a network request.
    Python path: catches direct request input, tainted URL variables, and
    URL reconstruction from tainted host/path fragments.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        tainted: dict[str, int] = {}

        def _is_request_input_expr(node: ast.AST) -> bool:
            if not isinstance(node, ast.Call):
                return False
            func = node.func
            if not isinstance(func, ast.Attribute):
                return False
            val = func.value
            if isinstance(val, ast.Attribute) and isinstance(val.value, ast.Name):
                return val.value.id in ("request", "req")
            if isinstance(val, ast.Name):
                return val.id in ("request", "req")
            return False

        def _has_tainted_name(node: ast.AST) -> bool:
            return any(isinstance(child, ast.Name) and child.id in tainted for child in ast.walk(node))

        class _Visitor(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                val = node.value
                is_tainted_value = _is_request_input_expr(val) or _has_tainted_name(val)
                if is_tainted_value:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            tainted[target.id] = node.lineno
                self.generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                _net_attrs  = ("get","post","put","delete","request","urlopen","open")
                _net_mods   = ("requests","httpx","urllib","session","aiohttp","client")
                _net_clients = ("AsyncClient","Client","Session")
                is_network = False
                if isinstance(func, ast.Attribute) and func.attr in _net_attrs:
                    val = func.value
                    if isinstance(val, ast.Name) and val.id in _net_mods:
                        is_network = True
                    # urllib.request.urlopen â€” val is Attribute(urllib, request)
                    elif (isinstance(val, ast.Attribute)
                          and isinstance(val.value, ast.Name)
                          and val.value.id in _net_mods):
                        is_network = True
                    # httpx client instances: c.get(), c.post() etc.
                    elif isinstance(val, ast.Name) and val.id in tainted:
                        is_network = True  # treat any tainted var as potential network call
                if is_network:
                    url_arg = node.args[0] if node.args else None
                    if url_arg is None:
                        for kw in node.keywords:
                            if kw.arg == "url":
                                url_arg = kw.value
                                break
                    if url_arg is not None:
                        tainted_name = None
                        if isinstance(url_arg, ast.Name) and url_arg.id in tainted:
                            tainted_name = url_arg.id
                        if tainted_name or _is_request_input_expr(url_arg) or _has_tainted_name(url_arg):
                            source = tainted_name or "direct_request_input"
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"SSRF: user-supplied URL '{source}' reaches network request at "
                                    f"line {node.lineno} without host validation"
                                ),
                                evidence={
                                    "rewrite_candidate": (
                                        "Parse the final URL, validate scheme and hostname against an explicit "
                                        "allowlist, reject private/link-local/loopback targets, and disable redirects"
                                    )
                                },
                            ))
                self.generic_visit(node)

        _Visitor().visit(tree)
    # Non-Python fallback + cross-function taint: consume NETWORK trust_boundaries from IR
    if not detections and semantic_ir is not None:
        tokens = getattr(semantic_ir, "semantic_tokens", set())
        for tb in getattr(semantic_ir, "trust_boundaries", []):
            if tb.boundary_type != "NETWORK":
                continue
            is_direct_ssrf  = "ssrf:user_url_to_network" in tokens
            is_indirect_ssrf = (
                getattr(tb, "tainted_input", "").startswith("indirect_taint:")
                and not getattr(tb, "validated", True)
            )
            if not (is_direct_ssrf or is_indirect_ssrf):
                continue
            indirect_label = (
                f" (cross-function: {tb.tainted_input})"
                if is_indirect_ssrf else ""
            )
            detections.append(_Detection(
                lineno=tb.sink_line,
                message=(
                    f"SSRF: user-supplied URL reaches network sink '{tb.sink_name}' "
                    f"at line {tb.sink_line} without host validation{indirect_label}"
                ),
                evidence={
                    "rewrite_candidate": (
                        "Validate parsed URL host against an allowlist "
                        "(block 169.254.x.x, 10.x.x.x, 172.16-31.x.x, 127.x.x.x) "
                        "before issuing the request"
                    ),
                },
            ))
        # URL reconstruction SSRF: user data assembled into URL with only partial validation.
        # Token TAINTED_STRING:url appears when IR traces a request param to a URL variable.
        if ("TAINTED_STRING:url" in tokens and
                any(lib in content for lib in ["requests", "urllib", "httpx", "axios", "fetch"]) and
                any(call in content for call in ["requests.get", "requests.post",
                                                  ".get(url", "fetch(url", ".get(url)"])):
            # Partial validation fingerprint: checking substring of host but not full allowlist
            has_partial_validation = (
                ("localhost" in content or "127.0.0.1" in content or
                 "in host" in content or "host in " in content) and
                not ("urlparse" in content and "ALLOWED" in content)
            )
            if has_partial_validation and not detections:
                detections.append(_Detection(
                    lineno=1,
                    message=(
                        "SSRF via URL reconstruction: user input is assembled into a URL "
                        "with only partial host validation â€” attacker bypasses via path "
                        "(e.g. evil.com/../../../../admin) or redirect"
                    ),
                    evidence={"rewrite_candidate":
                        "Parse the final URL with urlparse; validate hostname against "
                        "an explicit allowlist; never validate URL components individually"},
                ))
    return detections




def _detect_weak_rng(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Detect non-CSPRNG usage in security-sensitive context.
    Python: random.seed(time.*) or random.* used for token/session/password generation.
    Other languages: caught by heuristic patterns in language_front_door.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        _SECURITY_CONTEXTS = frozenset({"token", "session", "password", "secret", "key", "nonce", "salt"})

        class _Visitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == "random" and func.attr in (
                        "random", "randint", "choice", "shuffle", "seed", "getrandbits"
                    ):
                        # Check if the calling context name suggests security use
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Weak RNG: random.{func.attr}() is a PRNG not a CSPRNG â€” "
                                f"use secrets module for security-sensitive values"
                            ),
                            evidence={"rewrite_candidate": "secrets.token_hex(32) or secrets.randbelow(n)"},
                        ))
                self.generic_visit(node)

        _Visitor().visit(tree)
    # Non-Python fallback: consume IR token
    if not detections and semantic_ir is not None:
        tokens = getattr(semantic_ir, "semantic_tokens", set())
        if "weak_rng:non_csprng" in tokens:
            for tb in getattr(semantic_ir, "trust_boundaries", []):
                if tb.boundary_type == "WEAK_RNG":
                    detections.append(_Detection(
                        lineno=tb.sink_line,
                        message=(
                            f"Weak RNG: non-CSPRNG '{tb.sink_name}' used at line {tb.sink_line} â€” "
                            f"output is deterministic if seed is known; "
                            f"brute-forceable session tokens"
                        ),
                        evidence={
                            "rewrite_candidate": (
                                "Replace with SecureRandom (Java), secrets.token_hex() (Python), "
                                "or crypto.randomBytes() (Node.js)"
                            ),
                        },
                    ))
    return detections




def _detect_float_finance(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Detect float arithmetic on financial values.
    Looks for float literals multiplied with names suggestive of money/rates.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        _FINANCE_NAMES = frozenset({
            "balance", "amount", "price", "rate", "interest", "discount",
            "tax", "fee", "cost", "total", "subtotal", "revenue",
        })

        class _Visitor(ast.NodeVisitor):
            def visit_BinOp(self, node: ast.BinOp) -> None:
                def _has_finance_name(n: ast.AST) -> bool:
                    if isinstance(n, ast.Name):
                        return any(k in n.id.lower() for k in _FINANCE_NAMES)
                    return False
                if isinstance(node.op, (ast.Mult, ast.Div, ast.Add, ast.Sub)):
                    if _has_finance_name(node.left) or _has_finance_name(node.right):
                        # Check if either operand involves float
                        def _is_float_expr(n: ast.AST) -> bool:
                            if isinstance(n, ast.Constant) and isinstance(n.value, float):
                                return True
                            if isinstance(n, ast.BinOp):
                                return _is_float_expr(n.left) or _is_float_expr(n.right)
                            return False
                        if _is_float_expr(node):
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"Float arithmetic on financial value at line {node.lineno} â€” "
                                    f"binary floats cannot represent most decimal fractions exactly"
                                ),
                                evidence={"rewrite_candidate": "Use decimal.Decimal for monetary arithmetic"},
                            ))
                self.generic_visit(node)

        _Visitor().visit(tree)
    # Non-Python fallback: consume IR token
    if not detections and semantic_ir is not None:
        tokens = getattr(semantic_ir, "semantic_tokens", set())
        if "float_finance:precision_risk" in tokens:
            for tb in getattr(semantic_ir, "trust_boundaries", []):
                if tb.boundary_type == "NUMERIC_PRECISION":
                    detections.append(_Detection(
                        lineno=tb.sink_line,
                        message=(
                            f"Float arithmetic in financial context at line {tb.sink_line} â€” "
                            f"binary floats accumulate rounding error across transactions"
                        ),
                        evidence={
                            "rewrite_candidate": (
                                "Use decimal.Decimal (Python), BigDecimal (Java), "
                                "or a fixed-point library for all monetary values"
                            ),
                        },
                    ))
    return detections




def _detect_unsafe_memory(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Detect unsafe memory operations without bounds/alignment verification.
    Heuristic for non-Python: catches unsafe {} blocks in source.
    Python: catches ctypes pointer arithmetic without size checks.
    """
    # Primary: heuristic regex (works for Rust, C, C++)
    detections: list[_Detection] = []
    import re
    # unsafe block containing pointer cast without preceding size check
    for m in _safe_dotall_finditer(r'unsafe\s*\{[^}]*as_ptr\(\)\s+as\s+\*const', content, re.DOTALL):
        # Suppress if 500 chars before the block contain size + align guards with early return.
        # Properly guarded unsafe: check size_of, align_of, return None/Err on failure.
        ctx = content[max(0, m.start()-500):m.end()]
        if ('size_of' in ctx or '.len()' in ctx) and            ('align_of' in ctx or '% align' in ctx) and            ('return None' in ctx or 'return Err' in ctx or 'return false' in ctx):
            continue  # guarded â€” structurally sound
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f"Unsafe raw pointer cast at line {line} without "
                f"verified size or alignment check â€” potential UB"
            ),
            evidence={"rewrite_candidate": (
                "Assert raw_data.len() >= std::mem::size_of::<Header>() "
                "and verify alignment before cast"
            )},
        ))
    # copy_nonoverlapping in Rust unsafe blocks â€” only fire if in code context,
    # not inside a string literal (which would be a false positive on the
    # forge's own detection patterns).
    for m in _safe_dotall_finditer(r'unsafe\s*\{[^}]*copy_nonoverlapping', content, re.DOTALL):
        prefix = content[max(0, m.start()-2):m.start()]
        if '"' in prefix or "'" in prefix:
            continue
        # Suppress if bounds are checked via arithmetic or slice bounds before the call
        ctx = content[max(0, m.start()-300):m.end()]
        if ('len <=' in ctx or '<= src.len()' in ctx or '<= dest.len()' in ctx or
                'checked_mul' in ctx or 'checked_add' in ctx):
            continue  # checked arithmetic present â€” not a blind copy
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f"unsafe copy_nonoverlapping at line {line} â€” "
                f"if len is derived from an overflow-prone path the write "
                f"extends into unallocated memory"
            ),
            evidence={
                "rewrite_candidate": (
                    "Assert len <= src.len() && len <= dest.len() with "
                    "checked arithmetic, or use slice::copy_from_slice() "
                    "which panics on length mismatch"
                ),
            },
        ))
    # strncpy in C â€” off-by-one null termination hazard
    strncpy_re = re.compile(r'strncpy\s*\(')
    for m in strncpy_re.finditer(content):
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f"strncpy at line {line} does not guarantee null termination â€” "
                f"if source length equals buffer size the destination has no null byte; "
                f"printf/strlen will over-read"
            ),
            evidence={
                "rewrite_candidate": (
                    "Use strlcpy(dest, src, sizeof(dest)) which always null-terminates, "
                    "or manually set dest[sizeof(dest)-1] = '\\0' after strncpy"
                ),
            },
        ))
    # IR fallback: UNSAFE_MEMORY trust boundary.
    # Skip if the code has proper size + alignment + early-return guards â€”
    # those are structurally sound unsafe blocks, not vulnerabilities.
    _has_size_guard = 'size_of' in content or ('.len()' in content and 'return None' in content)
    _has_align_guard = 'align_of' in content or '% align' in content
    _has_return_guard = 'return None' in content or 'return Err' in content
    _fully_guarded = _has_size_guard and _has_align_guard and _has_return_guard
    if semantic_ir is not None and not _fully_guarded:
        for tb in getattr(semantic_ir, "trust_boundaries", []):
            if tb.boundary_type == "UNSAFE_MEMORY" and tb.sink_name not in (
                det.evidence.get("sink_name", "") for det in detections
            ):
                detections.append(_Detection(
                    lineno=tb.sink_line,
                    message=(
                        f"Unsafe memory operation '{tb.sink_name}' at line {tb.sink_line} "
                        f"without verified bounds or alignment"
                    ),
                    evidence={"rewrite_candidate": "Add size/alignment assertions before unsafe block"},
                ))
    # Also Python ctypes
    tree = _parse(content)
    if tree is not None:
        class _Visitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in (
                    "cast", "from_address", "from_buffer", "from_buffer_copy"
                ):
                    if isinstance(func.value, ast.Name) and func.value.id == "ctypes":
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=f"ctypes memory cast at line {node.lineno} â€” verify size and alignment",
                            evidence={"rewrite_candidate": "Check ctypes.sizeof() before cast"},
                        ))
                self.generic_visit(node)
        _Visitor().visit(tree)
    return detections





