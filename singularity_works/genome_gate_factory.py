from __future__ import annotations
# complexity_justified: genome-gate coupling — the genome IS the detection spec.
# Every structured anti_pattern in a capsule generates a Gate here.
# This closes the DERIVE loop: genome selection (PROBE) -> genome gates (DERIVE).

from __future__ import annotations
from .interprocedural import analyze as _interproc_analyze
import ast
import io
import tokenize
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .gates import Gate, GateFinding, GateResult
from .transformer_registry import STRATEGIES, is_auto_applicable

if TYPE_CHECKING:
    from .facts import FactBus
    from .genome import GenomeCapsule, RadicalMapGenome


# ---------------------------------------------------------------------------
# Detection output type
# ---------------------------------------------------------------------------

@dataclass
class _Detection:
    lineno: int
    message: str
    evidence: dict[str, Any]


# ---------------------------------------------------------------------------
# Shared AST utilities
# ---------------------------------------------------------------------------

# Substrate-Sovereign resource limits.
# The forge reads content as inert data — no execution risk —
# but adversarially crafted inputs can cause ReDoS, stack overflow,
# or memory exhaustion in the analysis pipeline itself.
_MAX_CONTENT_BYTES = 2 * 1024 * 1024   # 2 MB hard cap on content analyzed
_MAX_CONTENT_LINES = 50_000             # 50K lines; pathological AST nesting guard
_MAX_REGEX_CONTENT = 500_000            # chars fed to DOTALL regex patterns


def _parse(content: str):
    """Parse Python source to AST with resource guards."""
    if not content.strip():
        return None
    # Size gate: reject oversized inputs before touching the AST machinery.
    # Adversarial: 10MB of deeply nested brackets triggers quadratic AST walk.
    if len(content) > _MAX_CONTENT_BYTES:
        return None
    try:
        return ast.parse(content)
    except SyntaxError:
        return None
    except RecursionError:
        # Pathologically deep nesting (50k nested calls) overflows the C stack
        # inside CPython's parser. Return None — strategies fall through to IR.
        return None
    except MemoryError:
        return None


def _safe_dotall_search(pattern, content: str, flags=0):
    """
    Run a DOTALL regex search with a content-length guard.
    DOTALL patterns with [^}]* quantifiers exhibit O(n^2) backtracking
    We limit the search window to _MAX_REGEX_CONTENT chars and scan in
    overlapping chunks so real matches near the beginning are not missed.
    """
    import re as _re
    if len(content) <= _MAX_REGEX_CONTENT:
        return _re.search(pattern, content, flags)
    # Chunked scan: overlap by 256 chars so matches spanning a boundary are caught
    chunk = _MAX_REGEX_CONTENT
    overlap = 256
    pos = 0
    while pos < len(content):
        window = content[pos:pos + chunk]
        m = _re.search(pattern, window, flags)
        if m:
            return m
        pos += chunk - overlap
    return None


def _safe_dotall_finditer(pattern, content: str, flags=0):
    """Chunked finditer for DOTALL patterns — same backtracking guard."""
    import re as _re
    if len(content) <= _MAX_REGEX_CONTENT:
        yield from _re.finditer(pattern, content, flags)
        return
    chunk = _MAX_REGEX_CONTENT
    overlap = 256
    pos = 0
    seen_starts: set[int] = set()
    while pos < len(content):
        window = content[pos:pos + chunk]
        for m in _re.finditer(pattern, window, flags):
            abs_start = pos + m.start()
            if abs_start not in seen_starts:
                seen_starts.add(abs_start)
                yield m
        pos += chunk - overlap


def _is_open_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (isinstance(func, ast.Name) and func.id == "open") or (
        isinstance(func, ast.Attribute) and func.attr == "open"
    )


def _todo_hits(content: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(content).readline)
        for tok_type, tok_str, start, _end, _line in tokens:
            if tok_type != tokenize.COMMENT:
                continue
            low = tok_str.lower()
            if "todo" in low or "fixme" in low:
                hits.append((start[0], tok_str.strip()))
    except tokenize.TokenError:
        pass
    return hits


# ---------------------------------------------------------------------------
# Detection strategies
# ---------------------------------------------------------------------------

def _detect_resource_lifecycle(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Detect open() without paired close or context manager."""
    tree = _parse(content)
    if tree is None:
        return []

    class _Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.opened: dict[str, int] = {}
            self.closed: set[str] = set()
            self.with_managed: set[str] = set()
            self.detections: list[_Detection] = []

        def visit_With(self, node: ast.With) -> None:
            for item in node.items:
                if _is_open_call(item.context_expr):
                    if isinstance(item.optional_vars, ast.Name):
                        self.with_managed.add(item.optional_vars.id)
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            if isinstance(node.value, ast.Call) and _is_open_call(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.opened[target.id] = node.lineno
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "close":
                if isinstance(func.value, ast.Name):
                    self.closed.add(func.value.id)
            self.generic_visit(node)

        def report(self) -> None:
            for name, lineno in self.opened.items():
                if name not in self.closed and name not in self.with_managed:
                    self.detections.append(_Detection(
                        lineno=lineno,
                        message=f"Resource '{name}' opened without guaranteed close",
                        evidence={
                            "open_names": [name],
                            "rewrite_candidate": (
                                f"with open(path, 'r', encoding='utf-8') as {name}:\n"
                                f"    data = {name}.read()"
                            ),
                        },
                    ))

    v = _Visitor()
    v.visit(tree)
    v.report()
    return v.detections


def _detect_protocol_violation(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Detect resource use after close."""
    tree = _parse(content)
    if tree is None:
        return []

    class _Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.closed: dict[str, int] = {}
            self.detections: list[_Detection] = []

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            if isinstance(func, ast.Attribute):
                if func.attr == "close" and isinstance(func.value, ast.Name):
                    self.closed[func.value.id] = node.lineno
                elif func.attr in ("read", "write", "readline", "readlines"):
                    if isinstance(func.value, ast.Name):
                        name = func.value.id
                        if name in self.closed:
                            self.detections.append(_Detection(
                                lineno=node.lineno,
                                message=f"Resource '{name}' used after close at line {self.closed[name]}",
                                evidence={"closed_at": self.closed[name]},
                            ))
            self.generic_visit(node)

    v = _Visitor()
    v.visit(tree)
    return v.detections


def _detect_shell_injection(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Detect subprocess.run(shell=True), os.system(), os.popen() — shell injection surfaces."""
    tree = _parse(content)
    if tree is None:
        return []
    detections: list[_Detection] = []

    class _Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in ("run", "Popen", "call", "check_call", "check_output"):
                if isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                    shell_true = any(
                        kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                        for kw in node.keywords
                    )
                    if shell_true:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Shell injection: subprocess.{func.attr}(shell=True)"
                                f" at line {node.lineno}"
                            ),
                            evidence={
                                "call": f"subprocess.{func.attr}",
                                "rewrite_candidate": "subprocess.run(shlex.split(cmd)) or explicit arg list",
                            },
                        ))
            elif (
                isinstance(func, ast.Attribute)
                and func.attr in ("system", "popen")
                and isinstance(func.value, ast.Name)
                and func.value.id == "os"
            ):
                detections.append(_Detection(
                    lineno=node.lineno,
                    message=f"Shell execution: os.{func.attr}() at line {node.lineno}",
                    evidence={
                        "call": f"os.{func.attr}",
                        "rewrite_candidate": "subprocess.run([cmd], capture_output=True)",
                    },
                ))
            self.generic_visit(node)

    _Visitor().visit(tree)
    return detections


def _detect_dangerous_calls(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Detect eval() and exec() builtins only — shell injection handled by ast_shell_injection."""
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:

        class _Visitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                # Python builtins: eval() and exec()
                if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
                    is_safe = (
                        func.id == "eval"
                        and any(
                            isinstance(n, ast.Call)
                            and isinstance(n.func, ast.Attribute)
                            and n.func.attr == "literal_eval"
                            for n in ast.walk(node)
                        )
                    )
                    if not is_safe:
                        rewrite = "ast.literal_eval(expr)" if func.id == "eval" else "# replace exec with explicit dispatch"
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=f"Dangerous dynamic execution: {func.id}() at line {node.lineno}",
                            evidence={"call": func.id, "rewrite_candidate": rewrite},
                        ))
                self.generic_visit(node)

        _Visitor().visit(tree)
    # IR fallback: prototype pollution detected by polyglot front door
    if semantic_ir is not None:
        for tb in getattr(semantic_ir, "trust_boundaries", []):
            if tb.boundary_type == "PROTOTYPE_POLLUTION":
                detections.append(_Detection(
                    lineno=tb.sink_line,
                    message=(
                        f"Prototype pollution: key '{tb.sink_name}' at line {tb.sink_line} "
                        f"allows __proto__ writes — contaminates every object in the runtime"
                    ),
                    evidence={
                        "rewrite_candidate": (
                            "Guard key before assignment: "
                            "if (key === '__proto__' || key === 'constructor' || "
                            "key === 'prototype') continue;"
                        ),
                    },
                ))
    return detections


def _detect_verification_disabled(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Detect verify=False keyword argument."""
    tree = _parse(content)
    if tree is None:
        return []
    detections: list[_Detection] = []

    class _Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            for kw in node.keywords:
                if kw.arg == "verify" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=f"TLS verification disabled (verify=False) at line {node.lineno}",
                        evidence={"rewrite_candidate": "verify=True"},
                    ))
            self.generic_visit(node)

    _Visitor().visit(tree)
    return detections


def _detect_query_construction(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Detect string-built SQL queries passed to execute().
    Handles both direct: cursor.execute(f"... {var} ...")
    and variable-assigned: q = f"... {var} ..."; cursor.execute(q)
    """
    tree = _parse(content)
    # Do NOT early-return on tree=None — non-Python content (Rust, Go, etc.)
    # reaches the IR fallback below which reads heuristic trust_boundaries.
    detections: list[_Detection] = []

    _EXECUTE_NAMES = frozenset({"execute", "executemany", "executescript", "raw", "query"})

    def _is_string_build(node: ast.AST) -> bool:
        if isinstance(node, ast.JoinedStr):
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
            return True
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "format":
                return True
        return False

    # First pass: collect variable assignments that are string-builds
    # name -> lineno of the dangerous assignment
    tainted_names: dict[str, int] = {}

    class _AssignVisitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            if _is_string_build(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        tainted_names[target.id] = node.lineno
            self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            if node.value and _is_string_build(node.value):
                if isinstance(node.target, ast.Name):
                    tainted_names[node.target.id] = node.lineno
            self.generic_visit(node)

    _AssignVisitor().visit(tree) if tree is not None else None

    # Second pass: detect execute() with tainted args (direct or via variable)
    class _ExecuteVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            is_execute = (
                (isinstance(func, ast.Attribute) and func.attr in _EXECUTE_NAMES)
                or (isinstance(func, ast.Name) and func.id in _EXECUTE_NAMES)
            )
            if is_execute and node.args:
                has_params = len(node.args) >= 2 or any(
                    kw.arg in ("parameters", "params", "args") for kw in node.keywords
                )
                if not has_params:
                    arg = node.args[0]
                    if _is_string_build(arg):
                        # Direct f-string/format in execute()
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=f"String-built query directly in execute() at line {node.lineno}",
                            evidence={"rewrite_candidate": "cursor.execute(query, (param,))"},
                        ))
                    elif isinstance(arg, ast.Name) and arg.id in tainted_names:
                        # Variable holding a tainted string passed to execute()
                        assign_line = tainted_names[arg.id]
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Tainted query variable '{arg.id}' (built at line {assign_line}) "
                                f"passed to execute() at line {node.lineno}"
                            ),
                            evidence={
                            "rewrite_candidate": "cursor.execute(query, (param,))",
                            "taint_source_line": assign_line,
                        },
                        ))
            self.generic_visit(node)

    _ExecuteVisitor().visit(tree) if tree is not None else None

    # IR fallback — non-Python SQL injection (Rust format!, Go fmt.Sprintf, etc.)
    # The heuristic front door populates DB_QUERY TrustBoundary with
    # tainted_input="string_construction" for format!("SELECT...{}", var) patterns.
    if not detections and semantic_ir is not None:
        for tb in getattr(semantic_ir, "trust_boundaries", []):
            if (tb.boundary_type == "DB_QUERY"
                    and getattr(tb, "tainted_input", "") == "string_construction"):
                detections.append(_Detection(
                    lineno=tb.sink_line,
                    message=(
                        f"String-built SQL query '{tb.sink_name}' at line {tb.sink_line} — "
                        f"format-string interpolation bypasses parameterization"
                    ),
                    evidence={
                        "rewrite_candidate": (
                            "Use parameterized queries: sqlx::query(\"SELECT * FROM users "
                            "WHERE id = ?\").bind(id) — never interpolate user input into SQL"
                        ),
                        "sink_name": tb.sink_name,
                    },
                ))

    return detections


def _detect_placeholders(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Detect TODO/FIXME comment markers."""
    hits = _todo_hits(content)
    return [
        _Detection(
            lineno=lineno,
            message=f"Placeholder marker at line {lineno}: {comment}",
            evidence={"marker": comment, "rewrite_candidate": "# remove placeholder and implement"},
        )
        for lineno, comment in hits
    ]




def _detect_mutable_defaults(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Detect mutable default argument values (list, dict, set literals).
    These are initialized once at function definition time and persist
    across all calls — a classic state-persistence bug.
    """
    tree = _parse(content)
    if tree is None:
        return []
    detections: list[_Detection] = []

    _MUTABLE_TYPES = (ast.List, ast.Dict, ast.Set)

    class _Visitor(ast.NodeVisitor):
        def _check_defaults(self, args: ast.arguments, lineno: int) -> None:
            # defaults align to the LAST N positional args
            all_args = args.args + args.posonlyargs + args.kwonlyargs
            defaults = args.defaults + args.kw_defaults
            for default in defaults:
                if default is None:
                    continue
                if isinstance(default, _MUTABLE_TYPES):
                    type_name = type(default).__name__.replace("ast.", "").lower()
                    detections.append(_Detection(
                        lineno=lineno,
                        message=f"Mutable default argument ({type_name} literal) — state persists across calls",
                        evidence={
                            "rewrite_candidate": "Use None as default and initialise inside the function body",
                            "pattern": (
                                f"def f(arg={type_name}()) ->"
                                f" def f(arg=None): if arg is None: arg = {type_name}()"
                            ),
                        },
                    ))

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._check_defaults(node.args, node.lineno)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._check_defaults(node.args, node.lineno)
            self.generic_visit(node)

    _Visitor().visit(tree)
    return detections



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
                # open() after access — if within 5 lines, flag it
                if isinstance(func, ast.Name) and func.id == "open" and self.access_lines:
                    last_check = self.access_lines[-1]
                    if 0 < node.lineno - last_check <= 5:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"TOCTOU: open() at line {node.lineno} follows "
                                f"access check at line {last_check} — "
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
                        f"TOCTOU: {gap.description} — "
                        f"symlink can be substituted between check at "
                        f"line {gap.check_line} and act at line {gap.act_line}"
                    ),
                    evidence={
                        "rewrite_candidate": (
                            "Use open(path, O_WRONLY|O_NOFOLLOW) directly — "
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
                    # urllib.request.urlopen — val is Attribute(urllib, request)
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
                        "with only partial host validation — attacker bypasses via path "
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
                                f"Weak RNG: random.{func.attr}() is a PRNG not a CSPRNG — "
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
                            f"Weak RNG: non-CSPRNG '{tb.sink_name}' used at line {tb.sink_line} — "
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
                                    f"Float arithmetic on financial value at line {node.lineno} — "
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
                            f"Float arithmetic in financial context at line {tb.sink_line} — "
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
            continue  # guarded — structurally sound
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f"Unsafe raw pointer cast at line {line} without "
                f"verified size or alignment check — potential UB"
            ),
            evidence={"rewrite_candidate": (
                "Assert raw_data.len() >= std::mem::size_of::<Header>() "
                "and verify alignment before cast"
            )},
        ))
    # copy_nonoverlapping in Rust unsafe blocks — only fire if in code context,
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
            continue  # checked arithmetic present — not a blind copy
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f"unsafe copy_nonoverlapping at line {line} — "
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
    # strncpy in C — off-by-one null termination hazard
    strncpy_re = re.compile(r'strncpy\s*\(')
    for m in strncpy_re.finditer(content):
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f"strncpy at line {line} does not guarantee null termination — "
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
    # Skip if the code has proper size + alignment + early-return guards —
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
                            message=f"ctypes memory cast at line {node.lineno} — verify size and alignment",
                            evidence={"rewrite_candidate": "Check ctypes.sizeof() before cast"},
                        ))
                self.generic_visit(node)
        _Visitor().visit(tree)
    return detections



def _detect_async_toctou(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Detect async TOCTOU: await check followed by await act without atomic wrapper.
    The window between the two awaits allows concurrent requests to bypass the check.
    Pattern: await db.getX() / if condition: / await db.setX()
    """
    import re
    detections: list[_Detection] = []
    # Look for await <check> then await <act> inside the same function body
    # without transaction/lock keyword
    async_check_act = re.compile(
        r'await\s+\w+[^\n]*(?:get|read|fetch|balance|check)[^\n]*'
        r'[\s\S]{0,600}'
        r'await\s+\w+[^\n]*(?:update|set|write|deduct|withdraw|decrement)',
        re.IGNORECASE
    )
    for m in async_check_act.finditer(content):
        line = content[:m.start()].count('\n') + 1
        has_lock = any(kw in content.lower() for kw in (
            'transaction', 'mutex', 'lock', 'atomic', 'serializable',
            'with_lock', 'for update', 'compare_and_swap', 'cas('
        ))
        if not has_lock:
            detections.append(_Detection(
                lineno=line,
                message=(
                    f"Async TOCTOU at line {line}: check-then-act across two await "
                    f"boundaries without atomic transaction — concurrent requests can "
                    f"both pass the balance check before either deduction commits"
                ),
                evidence={
                    "rewrite_candidate": (
                        "Wrap in a database transaction with SELECT FOR UPDATE, "
                        "or use a compare-and-swap atomic update: "
                        "UPDATE accounts SET balance = balance - amount "
                        "WHERE id = userId AND balance >= amount"
                    ),
                },
            ))
    # IR fallback for temporal gaps
    if not detections and semantic_ir is not None:
        for gap in getattr(semantic_ir, "temporal_gaps", []):
            if gap.gap_type == "ASYNC_ATOMICITY":
                detections.append(_Detection(
                    lineno=gap.check_line,
                    message=f"Async TOCTOU: {gap.description}",
                    evidence={"rewrite_candidate": "Use atomic database transaction or compare-and-swap"},
                ))
    return detections



def _detect_interprocedural_sqli(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Interprocedural: taint from request input flows through function calls into SQL sink."""
    r = _interproc_analyze(content)
    detections = []
    for p in r["taint_paths"]:
        if p["sink_type"] == "db_query":
            detections.append(_Detection(
                lineno=p["sink_line"],
                message=p["description"],
                evidence={"rewrite_candidate": "Parameterize ALL query components; validate table/column names against an allowlist"},
            ))
    return detections


def _detect_invariant_collision(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Semantic collision: Function B writes attribute that Function A whitelists, bypassing the guard."""
    r = _interproc_analyze(content)
    return [
        _Detection(
            lineno=v["line"],
            message=v["description"],
            evidence={"rewrite_candidate": "Route all writes through the guarded setter; make the unguarded setattr path unreachable"},
        )
        for v in r["invariant_violations"]
    ]


def _detect_init_cycle(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Circular initialization dependency between classes."""
    r = _interproc_analyze(content)
    return [
        _Detection(
            lineno=1,
            message=c["description"],
            evidence={"rewrite_candidate": "Use lazy initialization or dependency injection; pass initialized instances rather than calling mediator during __init__"},
        )
        for c in r["init_cycles"]
    ]


def _detect_timing_attack(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Non-constant-time string comparison in security-sensitive context."""
    r = _interproc_analyze(content)
    return [
        _Detection(lineno=t["lineno"], message=t["message"],
                   evidence={"rewrite_candidate": t["rewrite"]})
        for t in r["timing_attacks"]
    ]


def _detect_path_traversal(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Incomplete path traversal sanitization — naive '..' check bypassable via URL encoding."""
    r = _interproc_analyze(content)
    return [
        _Detection(lineno=f["lineno"], message=f["message"],
                   evidence={"rewrite_candidate": f["rewrite"]})
        for f in r["incomplete_sanitization"]
    ]


def _detect_redos(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """ReDoS: regex with nested quantifiers causing exponential backtracking."""
    r = _interproc_analyze(content)
    return [
        _Detection(lineno=f["lineno"], message=f["message"],
                   evidence={"rewrite_candidate": f["rewrite"]})
        for f in r["redos"]
    ]


def _detect_weak_hash(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Weak hash (MD5/SHA1) used in security-sensitive context."""
    r = _interproc_analyze(content)
    # Also check IR for weak_hash tokens (non-Python path)
    extra = []
    if not r["weak_hash"] and semantic_ir is not None:
        tokens = getattr(semantic_ir, "semantic_tokens", set())
        for tok in tokens:
            if tok.startswith("weak_hash:"):
                for tb in getattr(semantic_ir, "trust_boundaries", []):
                    if tb.boundary_type == "WEAK_HASH":
                        extra.append(_Detection(
                            lineno=tb.sink_line,
                            message=f"Weak hash '{tb.sink_name}' at line {tb.sink_line} in security context",
                            evidence={"rewrite_candidate": "Use bcrypt, argon2, or scrypt for passwords; SHA-256+ for digests"},
                        ))
    return [
        _Detection(lineno=f["lineno"], message=f["message"],
                   evidence={"rewrite_candidate": f["rewrite"]})
        for f in r["weak_hash"]
    ] + extra


def _detect_deserialization(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Unsafe deserialization of user input (pickle.loads, yaml.load, etc.)."""
    detections = []
    # Python AST path
    tree = _parse(content)
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if (isinstance(func, ast.Attribute) and func.attr == "loads"
                        and isinstance(func.value, ast.Name) and func.value.id == "pickle"):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=f"pickle.loads at line {node.lineno} executes arbitrary code — attacker controls the deserialized object graph",
                        evidence={"rewrite_candidate": "Use json.loads for structured data; if binary format required, use message-pack or protobuf with schema validation"},
                    ))
                if (isinstance(func, ast.Attribute) and func.attr == "load"
                        and isinstance(func.value, ast.Name) and func.value.id == "yaml"):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=f"yaml.load at line {node.lineno} can execute arbitrary Python via YAML tags",
                        evidence={"rewrite_candidate": "Use yaml.safe_load() which disables tag execution"},
                    ))
                self.generic_visit(node)
        _V().visit(tree)
    # IR fallback
    if not detections and semantic_ir is not None:
        tokens = getattr(semantic_ir, "semantic_tokens", set())
        if "deserialization:pickle_loads" in tokens or "deserialization:unsafe_deserialize" in tokens:
            for tb in getattr(semantic_ir, "trust_boundaries", []):
                if tb.boundary_type == "DESERIALIZATION":
                    detections.append(_Detection(
                        lineno=tb.sink_line,
                        message=f"Unsafe deserialization '{tb.sink_name}' at line {tb.sink_line}",
                        evidence={"rewrite_candidate": "Replace with safe_load or schema-validated binary format"},
                    ))
    return detections


# ---------------------------------------------------------------------------
# Strategy dispatch table
# ---------------------------------------------------------------------------

_STRATEGIES: dict[str, Any] = {
    "ast_resource_lifecycle": _detect_resource_lifecycle,
    "ast_protocol_violation": _detect_protocol_violation,
    "ast_dangerous_calls": _detect_dangerous_calls,
    "ast_shell_injection": _detect_shell_injection,
    "ast_verification_disabled": _detect_verification_disabled,
    "ast_query_construction": _detect_query_construction,
    "ast_mutable_defaults": _detect_mutable_defaults,
    "token_placeholder_check": _detect_placeholders,
    "ast_toctou": _detect_toctou,
    "ast_ssrf": _detect_ssrf,
    "ast_weak_rng": _detect_weak_rng,
    "ast_float_finance": _detect_float_finance,
    "ast_unsafe_memory": _detect_unsafe_memory,
    "ast_async_toctou": _detect_async_toctou,
    "interproc_sqli": _detect_interprocedural_sqli,
    "interproc_invariant_collision": _detect_invariant_collision,
    "interproc_init_cycle": _detect_init_cycle,
    "local_timing_attack": _detect_timing_attack,
    "local_path_traversal": _detect_path_traversal,
    "local_redos": _detect_redos,
    "local_weak_hash": _detect_weak_hash,
    "local_deserialization": _detect_deserialization,
}



# ---------------------------------------------------------------------------
# Gate builder
# ---------------------------------------------------------------------------

def _build_gate(capsule: "GenomeCapsule", ap: dict) -> Gate | None:
    strategy_name = ap.get("detection_strategy", "")
    detect_fn = _STRATEGIES.get(strategy_name)
    if detect_fn is None:
        return None  # unknown strategy — skip, don't fail

    gate_id = f"genome:{capsule.pattern_id}:{ap['id']}"
    severity = ap.get("severity", "medium")
    transformation_axiom = ap.get("transformation_axiom", "")
    auto_apply_base = ap.get("auto_apply", False) and is_auto_applicable(transformation_axiom)
    safety_level = ap.get("safety_level", "review_required")
    discharge_claim = f"capsule:{capsule.pattern_id}:{ap['id']}"

    def run(subject: dict[str, Any], bus: "FactBus | None" = None) -> GateResult:
        content: str = subject.get("content", "")
        # Pass semantic_ir so strategies can use IR tokens as fallback for
        # non-Python content — the IR holds heuristic signals from the
        # polyglot front door that the Python-AST path cannot see.
        semantic_ir = subject.get("semantic_ir")
        detections = detect_fn(content, ap, semantic_ir=semantic_ir)

        if not detections:
            return GateResult(
                gate_id,
                capsule.family,
                "pass",
                discharged_claims=[discharge_claim],
            )

        # Taint-aware compound escalation (trust_boundary + dangerous_exec) deferred
        # until source-to-sink flow tracking exists. Without it, escalation creates
        # circular self-escalation from the same artifact's own signals.
        effective_auto = auto_apply_base
        effective_safety = safety_level

        findings = [
            GateFinding(
                code=ap["id"],
                message=det.message,
                severity=severity,
                evidence={
                    **det.evidence,
                    "transformation_axiom": transformation_axiom,
                    "auto_apply": effective_auto,
                    "safety_level": effective_safety,
                    "linked_laws": capsule.laws,
                    "suggested_fix": det.evidence.get("rewrite_candidate", ""),
                },
            )
            for det in detections
        ]

        return GateResult(
            gate_id,
            capsule.family,
            "fail",
            findings=findings,
            residual_obligations=[f"{ap['id']}_correction"],
        )

    return Gate(gate_id, capsule.family, f"{capsule.summary} — {ap['id']}", run)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def genome_gate_factory(capsule: "GenomeCapsule") -> list[Gate]:
    """
    Generate Gate objects from a capsule's structured anti_pattern specs.
    String-format anti_patterns (legacy) are skipped — they carry no detection spec.
    """
    gates: list[Gate] = []
    for ap in capsule.anti_patterns:
        if not isinstance(ap, dict):
            continue
        gate = _build_gate(capsule, ap)
        if gate is not None:
            gates.append(gate)
    return gates


def genome_gates_from_bundle(
    bundle: dict,
    genome: "RadicalMapGenome",
) -> list[Gate]:
    """
    Given a genome bundle (from RadicalMapGenome.bundle_for_task) and the full
    genome, derive the complete set of gates for this evaluation pass.
    These gates represent the DERIVE step of the PROBE→DERIVE→RECURSE loop.
    """
    gates: list[Gate] = []
    seen_gate_ids: set[str] = set()
    for pattern_summary in bundle.get("selected_patterns", []):
        pid = pattern_summary.get("pattern_id", "")
        capsule = genome.by_id.get(pid)
        if capsule is None:
            continue
        for gate in genome_gate_factory(capsule):
            if gate.gate_id not in seen_gate_ids:
                seen_gate_ids.add(gate.gate_id)
                gates.append(gate)
    return gates

# ---------------------------------------------------------------------------
# New detection strategies — Wave 2-5 assault coverage
# ---------------------------------------------------------------------------

def _detect_getattr_injection(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    getattr(obj, user_input) is eval in disguise.
    Any attribute lookup driven by user data allows invoking arbitrary methods.
    Isomorphism: same source→sink as eval/exec but through the attribute namespace.
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        # Track variables sourced from request.* 
        tainted: set[str] = set()
        class _V(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                if isinstance(node.value, ast.Call):
                    f = node.value.func
                    if (isinstance(f, ast.Attribute) and
                            isinstance(f.value, ast.Attribute) and
                            isinstance(f.value.value, ast.Name) and
                            f.value.value.id == "request"):
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                tainted.add(t.id)
                    elif (isinstance(f, ast.Attribute) and
                            isinstance(f.value, ast.Name) and
                            f.value.id in ("request", "args", "form", "params")):
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                tainted.add(t.id)
                self.generic_visit(node)
            def visit_Call(self, node: ast.Call) -> None:
                if (isinstance(node.func, ast.Name) and node.func.id == "getattr"
                        and len(node.args) >= 2):
                    attr_arg = node.args[1]
                    if isinstance(attr_arg, ast.Name) and (
                            attr_arg.id in tainted or
                            # Heuristic: single-letter variable as attr name = suspicious
                            len(attr_arg.id) <= 3):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"getattr() with variable attribute '{attr_arg.id}' at line "
                                f"{node.lineno} — if user-controlled, any method on the target "
                                f"object can be invoked; equivalent to eval"
                            ),
                            evidence={"rewrite_candidate":
                                "Validate attribute name against an explicit allowlist before "
                                "calling getattr(); e.g. ALLOWED = {'html', 'json', 'text'}; "
                                "getattr(module, fmt) if fmt in ALLOWED else abort(400)"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)
    # IR fallback: semantic_tokens populated by heuristic front door
    if not detections and semantic_ir is not None:
        for t in getattr(semantic_ir, "semantic_tokens", set()):
            if t.startswith("getattr_injection"):
                detections.append(_Detection(
                    lineno=1,
                    message="getattr() with user-controlled attribute name detected",
                    evidence={"rewrite_candidate": "Validate attribute name against allowlist"},
                ))
    return detections


def _detect_tls_default_arg(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    verify=False as a function default silently disables TLS for all callers.
    Worse than a single call-site because it's invisible to callers.
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        class _V(ast.NodeVisitor):
            def _check_defaults(self, fn_node: ast.FunctionDef) -> None:
                args = fn_node.args
                n_args = len(args.args)
                n_def = len(args.defaults)
                for i, default in enumerate(args.defaults):
                    if isinstance(default, ast.Constant) and default.value is False:
                        arg_idx = n_args - n_def + i
                        if arg_idx < n_args:
                            arg_name = args.args[arg_idx].arg
                            if arg_name == "verify":
                                detections.append(_Detection(
                                    lineno=fn_node.lineno,
                                    message=(
                                        f"TLS insecure default: verify=False in function "
                                        f"'{fn_node.name}' signature at line {fn_node.lineno} — "
                                        f"all callers inherit disabled certificate validation"
                                    ),
                                    evidence={"rewrite_candidate":
                                        "Change default to verify=True; require callers to "
                                        "explicitly opt out if needed; add a comment explaining why"},
                                ))
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._check_defaults(node)
                self.generic_visit(node)
            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._check_defaults(node)
                self.generic_visit(node)
        _V().visit(tree)
    # IR fallback
    if not detections and semantic_ir is not None:
        for tb in getattr(semantic_ir, "trust_boundaries", []):
            if tb.boundary_type == "TLS_DISABLED" and "default" in tb.sink_name.lower():
                detections.append(_Detection(
                    lineno=tb.sink_line,
                    message=f"TLS disabled in default argument at line {tb.sink_line}",
                    evidence={"rewrite_candidate": "Change default to verify=True"},
                ))
    return detections


def _detect_template_injection(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Server-side template injection (SSTI): user input flows into a Jinja2 Template()
    constructor as an f-string or concatenation. Allows arbitrary expression evaluation
    including __import__('os').popen('id').read().
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                is_template_call = (
                    (isinstance(func, ast.Name) and func.id == "Template") or
                    (isinstance(func, ast.Attribute) and func.attr == "Template")
                )
                if is_template_call and node.args:
                    arg = node.args[0]
                    # f-string with interpolation = tainted template string
                    if isinstance(arg, ast.JoinedStr):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"SSTI: Template() at line {node.lineno} receives an f-string — "
                                f"user data embedded in the template allows expression evaluation; "
                                f"{{{{7*7}}}} → 49; {{{{''.__class__.__mro__[1].__subclasses__()}}}} → RCE"
                            ),
                            evidence={"rewrite_candidate":
                                "Use a static template string and pass user data as render context: "
                                "Template('Hello, {{ name }}!').render(name=user_input)"},
                        ))
                    # string concat with a Name (variable) is also suspicious
                    elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"SSTI: Template() at line {node.lineno} may receive "
                                f"user-controlled string via concatenation"
                            ),
                            evidence={"rewrite_candidate":
                                "Pass user data as render context variables, not as part of "
                                "the template string itself"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)

        # Pattern 2 (separate pass): only for TOP-LEVEL functions
        # writing to module-level names. Nested functions are excluded
        # because they commonly write to outer-scope algorithm dicts (e.g. color[node]).
        if isinstance(tree, ast.Module):
            # Collect module-level assigned names (not inside any function)
            module_level_names: set[str] = set()
            for stmt in tree.body:
                if isinstance(stmt, ast.Assign):
                    for tgt in stmt.targets:
                        if isinstance(tgt, ast.Name):
                            module_level_names.add(tgt.id)
                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    module_level_names.add(stmt.target.id)
            # Only check top-level FunctionDef nodes
            for stmt in tree.body:
                if not isinstance(stmt, ast.FunctionDef):
                    continue
                param_names = {arg.arg for arg in stmt.args.args}
                for child in ast.walk(stmt):
                    if not isinstance(child, ast.Assign):
                        continue
                    for tgt in child.targets:
                        if (isinstance(tgt, ast.Subscript) and
                                isinstance(tgt.value, ast.Name) and
                                isinstance(tgt.slice, ast.Name) and
                                tgt.slice.id in param_names and
                                tgt.value.id in module_level_names):
                            detections.append(_Detection(
                                lineno=child.lineno,
                                message=(
                                    f"Unvalidated key mutation at line {child.lineno}: "
                                    f"dict['{tgt.slice.id}'] = value where '{tgt.slice.id}' "
                                    f"is a parameter and '{tgt.value.id}' is a module-level "
                                    f"variable — attacker controls which key is mutated"
                                ),
                                evidence={"rewrite_candidate":
                                    "Validate key against an allowlist before assignment"},
                            ))
    return detections


def _detect_open_redirect(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Open redirect: redirect() called with user-supplied URL without allowlist validation.
    Enables phishing (attacker spoofs trusted domain in redirect) and OAuth token theft.
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        tainted: set[str] = set()
        class _V(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                if isinstance(node.value, ast.Call):
                    f = node.value.func
                    # Handle: request.args.get(), request.form.get(), etc.
                    is_request_source = False
                    if isinstance(f, ast.Attribute):
                        v = f.value
                        # request.something (direct)
                        if isinstance(v, ast.Name) and v.id == "request":
                            is_request_source = True
                        # request.args.get / request.form.get (nested)
                        elif (isinstance(v, ast.Attribute) and
                              isinstance(v.value, ast.Name) and
                              v.value.id == "request"):
                            is_request_source = True
                    if is_request_source:
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                tainted.add(t.id)
                self.generic_visit(node)
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                is_redirect = (
                    (isinstance(func, ast.Name) and func.id == "redirect") or
                    (isinstance(func, ast.Attribute) and func.attr in ("redirect", "Redirect"))
                )
                if is_redirect and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Name) and arg.id in tainted:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Open redirect at line {node.lineno}: redirect() receives "
                                f"user-supplied URL '{arg.id}' without allowlist validation — "
                                f"attacker can redirect to any external site"
                            ),
                            evidence={"rewrite_candidate":
                                "Validate target against a list of safe paths, or use url_for() "
                                "for internal redirects; reject targets with external hosts"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections



def _detect_injection_patterns(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Structured query injection: XPATH, LDAP, XXE, shelve.
    Taint-aware: tracks f-string assignments before they reach query calls.
    """
    import re as _re
    detections: list[_Detection] = []

    def _line_is_comment(pos: int) -> bool:
        ls = content.rfind('\n', 0, pos) + 1
        return content[ls:pos].lstrip().startswith('#')

    def _extract_fstring_tainted(tree) -> set[str]:
        """Variables assigned from f-strings that include other variables."""
        tainted_fstrings: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.JoinedStr):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            tainted_fstrings.add(t.id)
        return tainted_fstrings

    # XPATH: .xpath(f"...") OR .xpath(tainted_variable)
    tree = _parse(content)
    if tree is not None:
        tainted_fstrs = _extract_fstring_tainted(tree)
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                is_xpath = isinstance(func, ast.Attribute) and func.attr == 'xpath'
                if is_xpath and node.args:
                    arg = node.args[0]
                    # Direct f-string in call
                    if isinstance(arg, ast.JoinedStr):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"XPath injection at line {node.lineno}: "
                                f"f-string directly in xpath() call — user data enables auth bypass"
                            ),
                            evidence={"rewrite_candidate": "Use XPath parameter binding"},
                        ))
                    # Variable that was assigned from an f-string
                    elif isinstance(arg, ast.Name) and arg.id in tainted_fstrs:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"XPath injection at line {node.lineno}: "
                                f"variable '{arg.id}' (built from f-string) used in xpath() — "
                                f"attacker can inject XPath logic"
                            ),
                            evidence={"rewrite_candidate": "Use XPath parameter binding; escape user input"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)

    # XXE: etree.XMLParser(resolve_entities=True)
    for m in _re.finditer(r'XMLParser\s*\(', content):
        if _line_is_comment(m.start()):
            continue
        pre20 = content[max(0, m.start()-20):m.start()]
        if '.' not in pre20:
            continue
        call_window = content[m.start():m.start()+200]
        if 'resolve_entities' not in call_window or '=True' not in call_window:
            continue
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f"XXE injection at line {line}: XMLParser(resolve_entities=True) allows "
                f"external entity expansion — reads local files, enables SSRF"
            ),
            evidence={"rewrite_candidate": "Use XMLParser(resolve_entities=False) or defusedxml"},
        ))

    # LDAP: .search() where arg is a tainted variable OR inline f-string
    if tree is not None:
        tainted_fstrs2 = _extract_fstring_tainted(tree)
        class _V2(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                is_ldap_search = (isinstance(func, ast.Attribute) and
                                  func.attr == 'search' and
                                  not (isinstance(func.value, ast.Name) and
                                       func.value.id in ('re', '_re', 'regex')))
                if is_ldap_search and len(node.args) >= 2:
                    filter_arg = node.args[1]
                    # Inline f-string
                    if isinstance(filter_arg, ast.JoinedStr):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"LDAP injection at line {node.lineno}: "
                                f"f-string directly in search() filter — user can bypass auth"
                            ),
                            evidence={"rewrite_candidate": "Use ldap3 escape_filter_chars() on user input"},
                        ))
                    # Tainted variable
                    elif isinstance(filter_arg, ast.Name) and filter_arg.id in tainted_fstrs2:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"LDAP injection at line {node.lineno}: "
                                f"variable '{filter_arg.id}' (built from f-string) used in "
                                f"search() filter — attacker can inject filter logic"
                            ),
                            evidence={"rewrite_candidate": "Use ldap3 escape_filter_chars() on all user values"},
                        ))
                self.generic_visit(node)
        _V2().visit(tree)

    # shelve: shelve.open() with user-controlled data in scope
    for m in _re.finditer(r'shelve\s*[.]\s*open\s*\(', content):
        if _line_is_comment(m.start()):
            continue
        pre3 = content[max(0, m.start()-3):m.start()]
        if "r'" in pre3 or 'r"' in pre3:
            continue
        ctx = content[max(0, m.start()-500):m.start()+500]
        if any(kw in ctx for kw in ['cookies', 'request.', 'args.get', 'form.get']):
            line = content[:m.start()].count('\n') + 1
            detections.append(_Detection(
                lineno=line,
                message=(
                    f"Unsafe deserialization via shelve at line {line}: shelve uses pickle "
                    f"internally — user-controlled data enables arbitrary code execution"
                ),
                evidence={"rewrite_candidate": "Replace shelve with json-backed storage"},
            ))

    return detections


def _detect_mass_assignment(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Mass assignment: user-controlled key used to mutate objects without allowlist.
    Catches:
    1. setattr() in loop over dict.items() — classic mass assignment
    2. dict[param_key] = value where param_key is a function parameter
    3. setattr(obj, param_key, value) where param_key is a function parameter
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                param_names = {arg.arg for arg in node.args.args}
                # Pattern 1: for key, value in data.items(): setattr(obj, key, value)
                for child in ast.walk(node):
                    if not isinstance(child, ast.For):
                        continue
                    has_setattr = any(
                        isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        and n.func.id == 'setattr'
                        for n in ast.walk(child)
                    )
                    is_dict_items = (
                        isinstance(child.iter, ast.Call) and
                        isinstance(child.iter.func, ast.Attribute) and
                        child.iter.func.attr == 'items'
                    )
                    if has_setattr and is_dict_items:
                        detections.append(_Detection(
                            lineno=child.lineno,
                            message=(
                                f"Mass assignment at line {child.lineno}: setattr() over "
                                f"dict.items() without allowlist — attackers can set arbitrary attributes"
                            ),
                            evidence={"rewrite_candidate":
                                "Use an explicit ALLOWED set; check key in ALLOWED before setattr()"},
                        ))

                # Pattern 2: module_dict[param] = value.
                # Only fires for TOP-LEVEL functions writing to module-level dicts.
                # Skips nested functions (where dict is from enclosing scope — normal algo pattern).
                self.generic_visit(node)  # handled separately below

                # Pattern 3: setattr(obj, param_key, value) — non-loop single call
                for child in ast.walk(node):
                    if not isinstance(child, ast.Expr):
                        continue
                    if not isinstance(child.value, ast.Call):
                        continue
                    call = child.value
                    if (isinstance(call.func, ast.Name) and call.func.id == 'setattr'
                            and len(call.args) >= 2
                            and isinstance(call.args[1], ast.Name)
                            and call.args[1].id in param_names):
                        detections.append(_Detection(
                            lineno=child.lineno,
                            message=(
                                f"Unvalidated setattr at line {child.lineno}: "
                                f"setattr(obj, '{call.args[1].id}', value) where attribute "
                                f"name is a function parameter — attacker controls which "
                                f"attribute is set"
                            ),
                            evidence={"rewrite_candidate":
                                "Validate attribute name against an explicit allowlist"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections




def _detect_format_string_c(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    C format string vulnerability: printf/fprintf/sprintf called with a
    user-controlled format string (not a string literal). Allows %n writes,
    stack reads, and arbitrary memory access.
    """
    import re as _re
    detections: list[_Detection] = []
    # printf/fprintf/etc where first meaningful arg is NOT a string literal
    # Pattern: printf(variable) or printf(param_name) — no literal first arg
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
                f"Format string vulnerability: {fn_name}({first_arg}) at line {line} — "
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
                f"malloc({arg1} * {arg2}) — if either value is attacker-controlled, "
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
                    f"int result = {arg1} * {arg2} — signed int multiplication can overflow "
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
    but bare return on error — blocked forever on error path.
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
                    f"but returns without sending on error — caller blocks forever on error path"
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
                    f"Object.keys() skips __proto__ but NOT 'constructor' — "
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
# Late strategy registrations — all functions defined above must exist before here
# ---------------------------------------------------------------------------
_STRATEGIES["local_getattr_injection"] = _detect_getattr_injection
_STRATEGIES["local_tls_default"] = _detect_tls_default_arg
_STRATEGIES["local_template_injection"] = _detect_template_injection
_STRATEGIES["local_open_redirect"] = _detect_open_redirect
_STRATEGIES["local_injection_patterns"] = _detect_injection_patterns
_STRATEGIES["local_mass_assignment"] = _detect_mass_assignment
_STRATEGIES["local_format_string_c"] = _detect_format_string_c
_STRATEGIES["local_integer_overflow_alloc"] = _detect_integer_overflow_alloc
_STRATEGIES["local_goroutine_leak"] = _detect_goroutine_leak
_STRATEGIES["local_prototype_constructor"] = _detect_prototype_constructor_pollution


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
                f'with non-literal class name — attacker loads arbitrary classes'
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
    Isomorphism: same as deserialize-and-trust — arbitrary attacker data becomes
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
                    f"role/admin/scope without cryptographic signature verification — "
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
_STRATEGIES["local_reflection_injection"] = _detect_reflection_injection
_STRATEGIES["local_unsigned_jwt"] = _detect_unsigned_jwt


# ---------------------------------------------------------------------------
# IRIS-mode escalation
# Isomorphism: IRIS (arXiv 2405.17238) goes LLM→formal→LLM.
# The forge goes heuristic→gate→LLM.
# When IR confidence is low, the forge escalates to IRIS-mode:
# the REASONER infers source/sink specs as a DynamicCapsule,
# which is then treated as a first-class genome capsule for this artifact.
# ---------------------------------------------------------------------------

def build_iris_prompt(content: str, language: str, vulnerability_hint: str = "") -> str:
    """
    Build the IRIS-style taint spec inference prompt.
    The REASONER returns JSON: { sources, sinks, sanitizers, assessment }
    """
    return f"""You are a security-focused static analyzer. Analyze the following {language} code.

Your task: identify taint flow vectors for security vulnerability detection.

Respond ONLY with JSON in this exact format:
{{
  "sources": [
    {{"name": "function_or_param_name", "type": "user_input|env|file|network", "line_hint": 0}}
  ],
  "sinks": [
    {{"name": "function_or_call", "type": "exec|query|network|deserialize|path|template|reflect", "line_hint": 0}}
  ],
  "sanitizers": [
    {{"name": "function_or_pattern", "type": "escape|validate|parameterize|allowlist"}}
  ],
  "assessment": {{
    "vulnerability_classes": ["list of CWE-style names if any"],
    "confidence": "high|medium|low",
    "reasoning": "brief explanation"
  }}
}}

{"Focus on: " + vulnerability_hint if vulnerability_hint else ""}

CODE:
```{language}
{content[:3000]}
```"""


@dataclass
class DynamicCapsule:
    """
    A runtime-generated genome capsule from IRIS-mode LLM inference.
    Treated identically to a static genome capsule during gate evaluation.
    """
    artifact_id: str
    language: str
    sources: list[dict]
    sinks: list[dict]
    sanitizers: list[dict]
    vulnerability_classes: list[str]
    confidence: str
    reasoning: str

    def to_detections(self, content: str) -> list[_Detection]:
        """
        Convert IRIS-inferred specs into detections by checking
        whether sources reach sinks without sanitizers in the content.
        """
        import re as _re
        detections: list[_Detection] = []

        # Build sets from inferred specs
        source_names = {s["name"] for s in self.sources}
        sink_names = {s["name"] for s in self.sinks}
        sanitizer_names = {s["name"] for s in self.sanitizers}

        # For each sink, check if a source flows into it without sanitizer
        for sink in self.sinks:
            sink_name = sink["name"]
            sink_type = sink.get("type", "unknown")

            # Find the sink call in content
            pattern = _re.compile(
                r'\b' + _re.escape(sink_name) + r'\s*\(',
                _re.IGNORECASE
            )
            for m in pattern.finditer(content):
                # Look backward 500 chars for source signals
                context = content[max(0, m.start() - 500):m.start() + 200]
                has_source = any(src in context for src in source_names)
                has_sanitizer = any(san in context for san in sanitizer_names)

                if has_source and not has_sanitizer:
                    line = content[:m.start()].count("\n") + 1
                    detections.append(_Detection(
                        lineno=line,
                        message=(
                            f"[IRIS] Taint flow at line {line}: "
                            f"user-controlled source reaches {sink_type} sink '{sink_name}' "
                            f"without sanitization — {', '.join(self.vulnerability_classes[:2]) or 'potential vulnerability'}"
                        ),
                        evidence={
                            "rewrite_candidate": f"Validate/escape all inputs before passing to {sink_name}",
                            "confidence": self.confidence,
                            "iris_reasoning": self.reasoning[:200],
                            "inferred_sources": [s["name"] for s in self.sources],
                            "inferred_sinks": [sink_name],
                        },
                    ))
                    break  # one detection per sink

        return detections


def _parse_iris_response(raw: str) -> dict | None:
    """Parse the REASONER's IRIS JSON response, tolerating markdown fences."""
    import re as _re, json as _json
    # Strip markdown fences if present
    raw = _re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=_re.MULTILINE)
    raw = _re.sub(r"```$", "", raw.strip(), flags=_re.MULTILINE)
    try:
        return _json.loads(raw.strip())
    except Exception:
        return None


def iris_escalate(
    content: str,
    artifact_id: str,
    language: str,
    semantic_ir: "Any | None",
    lm_base_url: str = "http://localhost:1234/v1",
    model: str = "qwen3.5-35b",
    vulnerability_hint: str = "",
) -> DynamicCapsule | None:
    """
    IRIS-mode escalation: call the local REASONER to infer taint specs
    when the static IR confidence is low. Returns a DynamicCapsule
    or None if the LLM is unavailable or returns invalid output.

    Called by the orchestrator when ir.confidence == "low" and
    gate_summary has no high/critical findings.
    """
    import json as _json
    try:
        import urllib.request as _req
        prompt = build_iris_prompt(content, language, vulnerability_hint)
        payload = _json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.1,
        }).encode()
        headers = {"Content-Type": "application/json"}
        request = _req.Request(
            f"{lm_base_url}/chat/completions",
            data=payload,
            headers=headers,
            method="POST",
        )
        with _req.urlopen(request, timeout=15) as resp:
            data = _json.loads(resp.read())
        raw = data["choices"][0]["message"]["content"]
        parsed = _parse_iris_response(raw)
        if not parsed:
            return None

        assessment = parsed.get("assessment", {})
        return DynamicCapsule(
            artifact_id=artifact_id,
            language=language,
            sources=parsed.get("sources", []),
            sinks=parsed.get("sinks", []),
            sanitizers=parsed.get("sanitizers", []),
            vulnerability_classes=assessment.get("vulnerability_classes", []),
            confidence=assessment.get("confidence", "medium"),
            reasoning=assessment.get("reasoning", ""),
        )
    except Exception:
        # Never let escalation failure break the forge — it's best-effort
        return None



# ---------------------------------------------------------------------------
# JWT Algorithm Confusion Detection
# CWE-347: Improper Verification of Cryptographic Signature
# Pattern: jwt.decode(token, secret) without algorithms= parameter
#          or with algorithms=["none"] / algorithms=["HS256"] with asymmetric key
# ---------------------------------------------------------------------------

def _detect_jwt_algorithm_confusion(
    content: str,
    _spec: dict,
    *,
    semantic_ir: "Any | None" = None,
) -> list[_Detection]:
    """
    JWT algorithm confusion: jwt.decode() called without explicit algorithms=[],
    or with algorithms=['none'], allows attackers to strip signature verification.

    CVE-2015-9235 class. python-jwt, PyJWT < 2.4.0 all vulnerable without algorithms=.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is None:
        return detections

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "decode":
            continue
        # Check caller is jwt-like
        caller = func.value
        caller_name = (caller.id if isinstance(caller, ast.Name)
                       else caller.attr if isinstance(caller, ast.Attribute)
                       else "")
        if "jwt" not in caller_name.lower() and "token" not in caller_name.lower():
            continue

        kw_map = {kw.arg: kw.value for kw in node.keywords if kw.arg}
        algo_node = kw_map.get("algorithms")
        options_node = kw_map.get("options")

        # No algorithms= kwarg at all
        if algo_node is None:
            detections.append(_Detection(
                lineno=node.lineno,
                message=(
                    f"JWT algorithm confusion at line {node.lineno}: "
                    f"jwt.decode() called without explicit algorithms= parameter — "
                    f"attacker can supply 'none' algorithm or switch RS256→HS256"
                ),
                evidence={
                    "rewrite_candidate": (
                        "Always specify algorithms=[\"HS256\"] or [\"RS256\"] — "
                        "never allow the token header to dictate the algorithm"
                    ),
                },
            ))
            continue

        # algorithms=['none'] or ["None"]
        if isinstance(algo_node, ast.List):
            for elt in algo_node.elts:
                if isinstance(elt, ast.Constant) and str(elt.value).lower() in ("none", ""):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"JWT algorithm confusion at line {node.lineno}: "
                            f"algorithms=['none'] explicitly permits unsigned tokens"
                        ),
                        evidence={
                            "rewrite_candidate": "Remove 'none' from algorithms= list",
                        },
                    ))

        # options={'verify_signature': False}
        if isinstance(options_node, ast.Dict):
            for k, v in zip(options_node.keys, options_node.values):
                if (isinstance(k, ast.Constant) and k.value == "verify_signature"
                        and isinstance(v, ast.Constant) and v.value is False):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"JWT verification disabled at line {node.lineno}: "
                            f"options={{\"verify_signature\": False}} skips signature check"
                        ),
                        evidence={
                            "rewrite_candidate": "Remove verify_signature=False; always verify",
                        },
                    ))

    return detections


_STRATEGIES["local_jwt_algorithm_confusion"] = _detect_jwt_algorithm_confusion


# ---------------------------------------------------------------------------
# HTTP Non-TLS Internal Call Detection
# CWE-319: Cleartext Transmission of Sensitive Information
# Pattern: requests.get("http://...") / http:// literal in network call
# ---------------------------------------------------------------------------

def _detect_http_no_tls(
    content: str,
    _spec: dict,
    *,
    semantic_ir: "Any | None" = None,
) -> list[_Detection]:
    """
    Detect cleartext HTTP (non-TLS) in internal or hardcoded network calls.
    requests.get("http://..."), urllib.request.urlopen("http://...") etc.
    Does NOT flag user-controlled URLs (those are SSRF territory).
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is None:
        return detections

    _NET_ATTRS = frozenset({"get", "post", "put", "delete", "patch", "request", "urlopen"})
    _NET_MODS  = frozenset({"requests", "httpx", "urllib", "aiohttp", "session"})

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in _NET_ATTRS:
            continue
        caller = func.value
        caller_name = (caller.id if isinstance(caller, ast.Name)
                       else caller.attr if isinstance(caller, ast.Attribute)
                       else "")
        # Also handle urllib.request.urlopen
        if caller_name not in _NET_MODS:
            if isinstance(caller, ast.Attribute) and isinstance(caller.value, ast.Name):
                if caller.value.id not in _NET_MODS:
                    continue
            else:
                continue

        # Check if the first argument is a string literal starting with http://
        url_arg = node.args[0] if node.args else None
        if url_arg is None:
            for kw in node.keywords:
                if kw.arg in ("url",):
                    url_arg = kw.value
                    break
        if url_arg is None:
            continue

        # Only flag LITERAL strings (not variables — those are SSRF, not cleartext)
        if not isinstance(url_arg, ast.Constant) or not isinstance(url_arg.value, str):
            continue
        if not url_arg.value.startswith("http://"):
            continue

        detections.append(_Detection(
            lineno=node.lineno,
            message=(
                f"Cleartext HTTP at line {node.lineno}: "
                f"hardcoded 'http://' URL in network call — "
                f"use https:// to prevent credential/data interception"
            ),
            evidence={
                "url": url_arg.value[:80],
                "rewrite_candidate": "Change http:// to https:// and enforce TLS verification",
            },
        ))

    return detections


_STRATEGIES["local_http_no_tls"] = _detect_http_no_tls


# ---------------------------------------------------------------------------
# Capsule expansion v1.29.1 — Bug bounty coverage
# Detectors: XXE, hardcoded secrets, insecure cookie, CORS wildcard,
# CRLF header injection, IDOR gate (wires existing capsules)
# ---------------------------------------------------------------------------

import re as _re_ext  # alias to avoid shadowing the ast-path _re used above


# ── XXE — XML External Entity Injection ────────────────────────────────────

def _detect_xxe(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect unsafe XML parsing that allows external entity expansion.
    Covers: stdlib xml.etree / xml.sax / minidom, lxml without resolve_entities=False,
    expat without entity handlers disabled. defusedxml is the safe alternative.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        _UNSAFE_XML_MODS = frozenset({
            "xml", "minidom", "ElementTree", "sax", "expat",
        })
        _UNSAFE_XML_CALLS = frozenset({
            "parse", "fromstring", "XML", "fromstringlist",
            "ParseCreate", "ParserCreate", "create_parser",
        })

        class _V(ast.NodeVisitor):
            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    if alias.name.startswith("xml.") and "defusedxml" not in alias.name:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Unsafe XML import '{alias.name}' at line {node.lineno} — "
                                f"stdlib xml parsers expand external entities by default"
                            ),
                            evidence={
                                "rewrite_candidate":
                                    "Use defusedxml: import defusedxml.ElementTree as ET",
                            },
                        ))
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                mod = node.module or ""
                if mod.startswith("xml.") and "defusedxml" not in mod:
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"Unsafe XML import from '{mod}' at line {node.lineno} — "
                            f"external entity expansion not disabled"
                        ),
                        evidence={
                            "rewrite_candidate":
                                "Use defusedxml: from defusedxml import ElementTree",
                        },
                    ))
                self.generic_visit(node)

        _V().visit(tree)

    # Heuristic fallback — catches Rust/Go/Java XML parsers
    if not detections and semantic_ir is not None:
        tokens = getattr(semantic_ir, "semantic_tokens", set())
        if "xxe:unsafe_xml_parse" in tokens:
            detections.append(_Detection(
                lineno=0,
                message="Unsafe XML parsing detected — external entity expansion risk",
                evidence={"rewrite_candidate": "Disable DTD/entity processing before parsing"},
            ))
    return detections


_STRATEGIES["local_xxe"] = _detect_xxe


# ── Hardcoded Secrets / Credentials ────────────────────────────────────────

_SECRET_NAMES = _re_ext.compile(
    r'\b(?:password|passwd|secret|api_key|apikey|access_token|auth_token|'
    r'private_key|client_secret|database_url|db_password|jwt_secret|'
    r'encryption_key|signing_key|bearer_token|credentials)\b',
    _re_ext.IGNORECASE,
)
_SECRET_VALUE = _re_ext.compile(
    r'(?:'
    # AWS
    r'AKIA[0-9A-Z]{16}|'
    # GitHub PAT
    r'ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}|'
    # Stripe
    r'sk_live_[A-Za-z0-9]{24,}|'
    # Generic high-entropy string (32+ hex chars or long base64)
    r'[0-9a-fA-F]{32,}|'
    r'[A-Za-z0-9+/]{40,}={0,2}'
    r')'
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
                                    f"Hardcoded credential '{name}' at line {node.lineno} — "
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

    # Heuristic — raw content scan for key patterns (catches non-Python)
    if not detections:
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if _SECRET_NAMES.search(line) and _SECRET_VALUE.search(line):
                # Skip if it looks like a test/example file
                if not any(skip in line for skip in ("#", "//", "test", "example", "TODO")):
                    detections.append(_Detection(
                        lineno=i,
                        message=(
                            f"Possible hardcoded secret at line {i} — "
                            f"high-entropy value in credential-named context"
                        ),
                        evidence={
                            "rewrite_candidate":
                                "Load from environment variable or secrets manager",
                        },
                    ))

    return detections


_STRATEGIES["local_hardcoded_secrets"] = _detect_hardcoded_secrets


# ── Insecure Cookie Flags ──────────────────────────────────────────────────

def _detect_insecure_cookie(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect set_cookie / response.set_cookie calls missing security flags.
    Flags checked: httponly, secure, samesite.
    Missing httponly → XSS steals session.
    Missing secure → cookie sent over HTTP.
    Missing samesite → CSRF risk.
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
                                f"Insecure cookie at line {node.lineno} — "
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


_STRATEGIES["local_insecure_cookie"] = _detect_insecure_cookie


# ── CORS Wildcard with Credentials ────────────────────────────────────────

def _detect_cors_wildcard(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect CORS configured to allow all origins (*) — especially dangerous
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
                            f"CORS wildcard origin ('*') with credentials at line {node.lineno} — "
                            f"attacker can make authenticated cross-origin requests"
                            if has_creds else
                            f"CORS wildcard origin ('*') at line {node.lineno} — "
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
    # When tree is not None (valid Python), the AST path is authoritative —
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
                        f"CORS wildcard at line {i} — "
                        f"'Access-Control-Allow-Origin: *' exposes responses to any origin"
                    ),
                    evidence={
                        "rewrite_candidate":
                            "Restrict to explicit trusted origins; never use * with credentials",
                    },
                ))

    return detections


_STRATEGIES["local_cors_wildcard"] = _detect_cors_wildcard


# ── CRLF / Header Injection ───────────────────────────────────────────────

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

        # ── Pass 1: taint propagation ──────────────────────────────────────
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

        # ── Pass 2: sink detection ─────────────────────────────────────────
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
                                f"line {node.lineno} — verify value is not "
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
                                f"{node.lineno} (tainted from line {src}) — "
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


_STRATEGIES["local_crlf_injection"] = _detect_crlf_injection


# ── IDOR Gate — wires existing access_control capsules ────────────────────

def _detect_idor_missing_ownership(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Gate-version of the IDOR ownership monitor.
    Fires when: external ID from request + DB access without ownership check.
    Reuses the monitor's pattern set but emits GateFindings for the gate fabric.

    Web-framework guard: only fires when a web framework is imported.
    Non-web modules (forge internals, libraries) contain ORM method names
    as string literals in detection patterns — the heuristic would produce
    false positives on its own source. Requiring a web import eliminates that.
    """
    # Web-framework import guard — non-web modules cannot have IDOR routes.
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
        return []  # ownership enforced — clean

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
            f"without object-level ownership check — any authenticated user "
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


_STRATEGIES["must_enforce_object_ownership"] = _detect_idor_missing_ownership



# ---------------------------------------------------------------------------
# Bandit-derived detectors v1.32.1 (Apache-2.0 pattern concepts)
# ---------------------------------------------------------------------------

def _detect_insecure_tempfile(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect tempfile.mktemp — TOCTOU race between name generation and open.
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
                            f"tempfile.mktemp() at line {node.lineno} is a TOCTOU race — "
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


_STRATEGIES["local_insecure_tempfile"] = _detect_insecure_tempfile


def _detect_unverified_ssl_context(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect ssl._create_unverified_context() — disables certificate verification.
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
                                    f"ssl._create_unverified_context() at line {node.lineno} — "
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


_STRATEGIES["local_unverified_ssl_context"] = _detect_unverified_ssl_context


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
                                f"line {node.lineno} — credentials transmitted unencrypted"
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


_STRATEGIES["local_cleartext_protocol"] = _detect_cleartext_protocol


def _detect_pycrypto_import(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect import of pycrypto/Crypto — unmaintained library with known CVEs.
    Cryptodome (pycryptodome) is an acceptable fork; cryptography package is preferred.
    (Bandit B413 equivalent)
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        class _V(ast.NodeVisitor):
            def _check_mod(self, mod: str, lineno: int) -> None:
                if mod.startswith("Crypto.") and not mod.startswith("Cryptodome"):
                    detections.append(_Detection(
                        lineno=lineno,
                        message=(
                            f"pycrypto/Crypto module '{mod}' at line {lineno} — "
                            f"unmaintained library with known CVEs"
                        ),
                        evidence={
                            "rewrite_candidate":
                                "from cryptography.hazmat.primitives import ...  "
                                "# actively maintained"
                        },
                    ))

            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    self._check_mod(alias.name, node.lineno)
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                self._check_mod(node.module or "", node.lineno)
                self.generic_visit(node)
        _V().visit(tree)
    return detections


_STRATEGIES["local_pycrypto_import"] = _detect_pycrypto_import


def _detect_django_mark_safe(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect django.utils.safestring.mark_safe() with non-constant argument.
    Bypasses Django's auto-escaping — stored XSS if user data reaches it.
    (Bandit B308 equivalent, extended with variable argument check)
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                name = (
                    func.id if isinstance(func, ast.Name)
                    else func.attr if isinstance(func, ast.Attribute)
                    else ""
                )
                if name == "mark_safe" and node.args:
                    arg = node.args[0]
                    # Constant string is usually safe; variable arg is the risk
                    if not isinstance(arg, ast.Constant):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"mark_safe() with non-constant argument at line {node.lineno} — "
                                f"bypasses Django auto-escaping; XSS if user data reaches this"
                            ),
                            evidence={
                                "rewrite_candidate":
                                    "Use template tags instead of mark_safe(); "
                                    "if unavoidable, escape first: mark_safe(escape(user_input))"
                            },
                        ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections


_STRATEGIES["local_django_mark_safe"] = _detect_django_mark_safe


def _detect_orm_raw_injection(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect Django ORM .raw() and .extra() with format-string / f-string arguments.
    Bypasses Django's ORM parameterization.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                method = func.attr if isinstance(func, ast.Attribute) else ""
                if method in ("raw", "extra") and node.args:
                    arg = node.args[0]
                    is_dynamic = (
                        isinstance(arg, ast.JoinedStr)
                        or (isinstance(arg, ast.BinOp)
                            and isinstance(arg.op, (ast.Add, ast.Mod)))
                        or (isinstance(arg, ast.Call)
                            and isinstance(arg.func, ast.Attribute)
                            and arg.func.attr == "format")
                    )
                    if is_dynamic:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"ORM.{method}() with string interpolation at line "
                                f"{node.lineno} — bypasses parameterization, SQL injection risk"
                            ),
                            evidence={
                                "rewrite_candidate":
                                    f"Use .{method}('SELECT ... WHERE id = %s', [user_id]) "
                                    f"with params argument"
                            },
                        ))
                self.generic_visit(node)
        _V().visit(tree)

    # IR fallback: DB_QUERY boundary from heuristic path
    if not detections and semantic_ir is not None:
        for tb in getattr(semantic_ir, "trust_boundaries", []):
            if tb.boundary_type == "DB_QUERY":
                detections.append(_Detection(
                    lineno=tb.sink_line,
                    message=(
                        f"Raw SQL construction at line {tb.sink_line} — "
                        f"parameterize all user-supplied values"
                    ),
                    evidence={"rewrite_candidate": "Use parameterized queries"},
                ))
    return detections


_STRATEGIES["local_orm_raw_injection"] = _detect_orm_raw_injection


def _detect_marshal_deserialize(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect marshal.load / marshal.loads — arbitrary code execution on untrusted data.
    (Bandit B302 equivalent)
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if (isinstance(func, ast.Attribute)
                        and func.attr in ("load", "loads")
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "marshal"):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"marshal.{func.attr}() at line {node.lineno} — "
                            f"deserializes arbitrary Python bytecode; use json with schema"
                        ),
                        evidence={
                            "rewrite_candidate":
                                "import json; data = json.loads(raw)  "
                                "# with schema validation"
                        },
                    ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections


_STRATEGIES["local_marshal_deserialize"] = _detect_marshal_deserialize

