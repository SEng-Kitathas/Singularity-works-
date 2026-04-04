from __future__ import annotations
# complexity_justified: interprocedural call graph with taint propagation,
# invariant collision detection, and initialization cycle analysis.
# Local analysis has a hard ceiling — vulnerabilities that exist at function
# boundaries are invisible without the call graph. This module crosses that
# boundary. It is the difference between "local correctness checker" and
# "architectural reasoner."
#
# Isomorphism (distributed systems): the call graph is a message-passing
# network; taint propagation is a distributed information-flow protocol.
# Each function is a node; each call site is an edge; taint tokens flow
# along edges like messages through a routing network.
#
# Isomorphism (control theory): the init-cycle detector is a feedback-loop
# detector on the initialization state machine. A cycle means the machine
# has no stable equilibrium — it deadlocks.
#
# Isomorphism (type theory): invariant collision is an unsound subtyping
# relation — function B claims to write the same attribute as function A
# but without A's precondition, so the type contract is violated.

import ast
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CallSite:
    """A call from one function to another, with argument provenance."""
    callee: str             # qualified name of the called function
    args_passed: list[str]  # variable names (or literals) passed as args
    line: int


@dataclass
class TaintSource:
    """A point where untrusted external data enters the function."""
    var_name: str
    source_type: str        # "request_input" | "env" | "file" | "db_result"
    line: int


@dataclass
class TaintSink:
    """A dangerous operation that consumes a function-local variable."""
    sink_type: str          # "db_query" | "shell" | "eval" | "file_write"
    var_name: str           # the variable consumed
    line: int


@dataclass
class WriteOp:
    """A write to an attribute/dict key via setattr or direct assignment."""
    target_attr: str        # e.g. "role" in setattr(obj, "role", val)
    source_var: str         # value being written
    guarded: bool           # is this write inside an if/whitelist check?
    line: int


@dataclass
class FunctionNode:
    """Everything the forge knows about one function from static analysis."""
    func_name: str
    class_name: str | None
    params: list[str]
    taint_sources: list[TaintSource] = field(default_factory=list)
    taint_sinks: list[TaintSink] = field(default_factory=list)
    calls: list[CallSite] = field(default_factory=list)
    writes: list[WriteOp] = field(default_factory=list)
    has_whitelist_check: bool = False
    checked_attrs: set[str] = field(default_factory=set)
    init_method_calls: list[str] = field(default_factory=list)
    line: int = 0


@dataclass
class TaintPath:
    """An interprocedural data-flow path from a taint source to a sink."""
    entry_func: str         # where taint enters
    taint_var: str          # which variable carries the taint
    sink_func: str          # where it reaches a dangerous sink
    sink_type: str          # what kind of sink
    sink_line: int
    call_chain: list[str]   # full path through function calls
    confidence: str = "high"

    def description(self) -> str:
        chain = " → ".join(self.call_chain)
        return (
            f"Interprocedural taint: '{self.taint_var}' from "
            f"'{self.entry_func}' reaches {self.sink_type} sink in "
            f"'{self.sink_func}' (line {self.sink_line}) via [{chain}]"
        )


@dataclass
class InvariantViolation:
    """A bypass of a function-enforced invariant by another function."""
    enforcing_func: str     # function that guards writes to target_attr
    bypass_func: str        # function that writes without the guard
    target_attr: str
    bypass_line: int
    description: str


@dataclass
class InitCycle:
    """A circular initialization dependency between classes."""
    cycle: list[str]        # class names forming the cycle
    description: str


# ---------------------------------------------------------------------------
# AST visitor — builds the call graph
# ---------------------------------------------------------------------------

# Taint sources: names/methods that produce untrusted data
_REQUEST_SOURCES = frozenset({
    "args", "form", "json", "data", "values", "files", "cookies", "headers",
    "body", "params", "query",
})
_INPUT_FUNCTIONS = frozenset({
    "input", "sys.stdin.read", "os.environ.get",
})
# SQL sink methods
_SQL_SINKS = frozenset({
    "execute", "executemany", "executescript", "raw", "query",
    "filter", "extra", "RawSQL",
})
# Shell sink methods/functions
_SHELL_SINKS = frozenset({
    "system", "popen", "call", "run", "Popen", "check_call", "check_output",
})
# Dynamic execution sinks
_EVAL_SINKS = frozenset({"eval", "exec", "compile"})


class _GraphBuilder(ast.NodeVisitor):
    """Single-pass AST visitor that builds a CallGraph."""

    def __init__(self, graph: "CallGraph") -> None:
        self.graph = graph
        self._func_stack: list[FunctionNode] = []
        self._class_stack: list[str] = []
        self._inside_if_depth: int = 0
        self._whitelist_seen: bool = False

    # ── context helpers ────────────────────────────────────────────────

    @property
    def _current_func(self) -> FunctionNode | None:
        return self._func_stack[-1] if self._func_stack else None

    @property
    def _current_class(self) -> str | None:
        return self._class_stack[-1] if self._class_stack else None

    # ── class and function entry ───────────────────────────────────────

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_stack.append(node.name)
        self.graph.classes.setdefault(node.name, [])
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_function(node)

    def _enter_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        cls = self._current_class
        qname = f"{cls}.{node.name}" if cls else node.name
        params = [a.arg for a in node.args.args if a.arg != "self"]
        fn = FunctionNode(
            func_name=qname,
            class_name=cls,
            params=params,
            line=node.lineno,
        )
        self.graph.functions[qname] = fn
        if cls:
            self.graph.classes.setdefault(cls, []).append(node.name)
            if node.name == "__init__":
                self.graph.class_inits[cls] = fn
        self._func_stack.append(fn)
        old_wl = self._whitelist_seen
        self._whitelist_seen = False
        self.generic_visit(node)
        self._whitelist_seen = old_wl
        self._func_stack.pop()

    # ── if-statement tracking (for guarded writes) ─────────────────────

    def visit_If(self, node: ast.If) -> None:
        # Detect whitelist checks like: if role in ["user", "admin"]
        test_src = ast.unparse(node.test) if hasattr(ast, "unparse") else ""
        if " in " in test_src or "not in" in test_src:
            fn = self._current_func
            if fn is not None:
                fn.has_whitelist_check = True
                self._whitelist_seen = True
        self._inside_if_depth += 1
        self.generic_visit(node)
        self._inside_if_depth -= 1

    # ── assignment: detect taint sources and variable tracking ────────

    def visit_Assign(self, node: ast.Assign) -> None:
        fn = self._current_func
        if fn is None:
            return
        val = node.value
        # Taint source: request.args.get(...)
        if isinstance(val, ast.Call):
            if self._is_request_input(val):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        fn.taint_sources.append(TaintSource(
                            var_name=target.id,
                            source_type="request_input",
                            line=node.lineno,
                        ))
        # Track f-string / format assignments for downstream SQL detection
        if isinstance(val, ast.JoinedStr):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    fn.taint_sources.append(TaintSource(
                        var_name=target.id,
                        source_type="string_interpolation",
                        line=node.lineno,
                    ))
        self.generic_visit(node)

    def _is_request_input(self, node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr in ("get", "getlist"):
                val = func.value
                if isinstance(val, ast.Attribute) and val.attr in _REQUEST_SOURCES:
                    if isinstance(val.value, ast.Name) and val.value.id == "request":
                        return True
            if isinstance(func.value, ast.Attribute):
                if (isinstance(func.value.value, ast.Name)
                        and func.value.value.id == "request"
                        and func.value.attr in _REQUEST_SOURCES):
                    return True
        return False

    # ── call expressions: sinks, call sites, setattr ──────────────────

    def visit_Call(self, node: ast.Call) -> None:
        fn = self._current_func
        if fn is None:
            self.generic_visit(node)
            return

        func = node.func

        # ── SQL sinks ──────────────────────────────────────────────────
        if isinstance(func, ast.Attribute) and func.attr in _SQL_SINKS:
            if node.args:
                arg = node.args[0]
                # f-string or string concat → tainted query
                if isinstance(arg, ast.JoinedStr) or self._is_string_concat(arg):
                    fn.taint_sinks.append(TaintSink(
                        sink_type="db_query",
                        var_name=ast.unparse(arg) if hasattr(ast, "unparse") else "query",
                        line=node.lineno,
                    ))
                elif isinstance(arg, ast.Name):
                    # Variable: may be tainted; record for propagation
                    fn.taint_sinks.append(TaintSink(
                        sink_type="db_query",
                        var_name=arg.id,
                        line=node.lineno,
                    ))

        # ── eval/exec sinks ────────────────────────────────────────────
        if isinstance(func, ast.Name) and func.id in _EVAL_SINKS:
            if node.args and isinstance(node.args[0], ast.Name):
                fn.taint_sinks.append(TaintSink(
                    sink_type="eval",
                    var_name=node.args[0].id,
                    line=node.lineno,
                ))

        # ── shell sinks ────────────────────────────────────────────────
        if isinstance(func, ast.Attribute) and func.attr in _SHELL_SINKS:
            if node.args and isinstance(node.args[0], ast.Name):
                fn.taint_sinks.append(TaintSink(
                    sink_type="shell",
                    var_name=node.args[0].id,
                    line=node.lineno,
                ))

        # ── setattr(obj, key, val) ─────────────────────────────────────
        if isinstance(func, ast.Name) and func.id == "setattr":
            if len(node.args) >= 3:
                key_node = node.args[1]
                val_node = node.args[2]
                key = (key_node.value if isinstance(key_node, ast.Constant)
                       and isinstance(key_node.value, str) else "dynamic")
                val_name = val_node.id if isinstance(val_node, ast.Name) else "expr"
                guarded = self._inside_if_depth > 0 and self._whitelist_seen
                fn.writes.append(WriteOp(
                    target_attr=key,
                    source_var=val_name,
                    guarded=guarded,
                    line=node.lineno,
                ))
                if guarded and fn.has_whitelist_check:
                    fn.checked_attrs.add(key)

        # ── regular call site (for interprocedural propagation) ────────
        callee_name = self._resolve_callee(func)
        if callee_name:
            args_passed = []
            for a in node.args:
                if isinstance(a, ast.Name):
                    args_passed.append(a.id)
                elif isinstance(a, ast.Constant):
                    args_passed.append(repr(a.value))
                else:
                    args_passed.append("__expr__")
            fn.calls.append(CallSite(
                callee=callee_name,
                args_passed=args_passed,
                line=node.lineno,
            ))
            # Track init-time method calls (for cycle detection)
            if fn.func_name.endswith(".__init__"):
                fn.init_method_calls.append(callee_name)

        self.generic_visit(node)

    def _resolve_callee(self, func: ast.expr) -> str | None:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name):
                return f"{func.value.id}.{func.attr}"
            if isinstance(func.value, ast.Attribute):
                outer = self._resolve_callee(func.value)
                if outer:
                    return f"{outer}.{func.attr}"
        return None

    @staticmethod
    def _is_string_concat(node: ast.expr) -> bool:
        if isinstance(node, ast.JoinedStr):
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
                return True
        return False


# ---------------------------------------------------------------------------
# Call graph
# ---------------------------------------------------------------------------

class CallGraph:
    """
    Interprocedural call graph for Python.

    Build once from an AST, then query:
        propagate_taint()         → interprocedural taint paths
        find_invariant_bypasses() → setattr bypasses of guarded setters
        find_init_cycles()        → circular class initialization
    """

    def __init__(self) -> None:
        self.functions: dict[str, FunctionNode] = {}
        self.classes: dict[str, list[str]] = {}
        self.class_inits: dict[str, FunctionNode] = {}

    def build(self, tree: ast.AST) -> None:
        _GraphBuilder(self).visit(tree)

    # ── taint propagation ──────────────────────────────────────────────

    def propagate_taint(self, depth: int = 3) -> list[TaintPath]:
        """
        BFS taint propagation: follow tainted variables through call chains
        up to `depth` hops and record every path that reaches a dangerous sink.
        """
        paths: list[TaintPath] = []
        # Seed: all local taint sources in every function
        worklist: list[tuple[str, str, list[str]]] = []  # (func, var, chain)
        for fname, fn in self.functions.items():
            for src in fn.taint_sources:
                worklist.append((fname, src.var_name, [fname]))

        visited: set[tuple[str, str]] = set()
        while worklist:
            fname, taint_var, chain = worklist.pop(0)
            if (fname, taint_var) in visited or len(chain) > depth:
                continue
            visited.add((fname, taint_var))
            fn = self.functions.get(fname)
            if fn is None:
                continue
            # Check local sinks
            for sink in fn.taint_sinks:
                if sink.var_name == taint_var:
                    paths.append(TaintPath(
                        entry_func=chain[0],
                        taint_var=chain[0].split(".")[-1] + "." + taint_var
                                  if len(chain) > 1 else taint_var,
                        sink_func=fname,
                        sink_type=sink.sink_type,
                        sink_line=sink.line,
                        call_chain=chain,
                    ))
            # Propagate to callees
            for callsite in fn.calls:
                if taint_var in callsite.args_passed:
                    arg_idx = callsite.args_passed.index(taint_var)
                    callee = self.functions.get(callsite.callee)
                    if callee is not None and arg_idx < len(callee.params):
                        tainted_param = callee.params[arg_idx]
                        worklist.append((
                            callsite.callee,
                            tainted_param,
                            chain + [callsite.callee],
                        ))
                    else:
                        # Callee not found locally — still record the call
                        # so the forge knows taint escaped into an opaque sink
                        worklist.append((
                            callsite.callee,
                            taint_var,
                            chain + [callsite.callee],
                        ))
        return paths

    # ── invariant bypass (semantic collision) ──────────────────────────

    def find_invariant_bypasses(self) -> list[InvariantViolation]:
        """
        Find functions that enforce a whitelist guard on an attribute write,
        and other functions that write the same attribute without that guard.

        Isomorphism to SEMANTIC_COLL: Function A (set_user_role) whitelists
        the 'role' attribute. Function B (bulk_update) uses setattr to write
        any attribute key — including 'role' — without going through A's check.
        """
        violations: list[InvariantViolation] = []
        # Functions with guarded writes: they enforce a whitelist
        guarded: dict[str, tuple[str, set[str]]] = {}
        for fname, fn in self.functions.items():
            if fn.has_whitelist_check and fn.checked_attrs:
                guarded[fname] = (fname, fn.checked_attrs)

        # Functions with unguarded writes to the same attributes
        for guard_func, (_, checked) in guarded.items():
            for fname, fn in self.functions.items():
                if fname == guard_func:
                    continue
                for write in fn.writes:
                    if not write.guarded:
                        # Unguarded write — if attribute matches or is dynamic
                        # (dynamic setattr can write any attr), flag it
                        if write.target_attr == "dynamic" or write.target_attr in checked:
                            violations.append(InvariantViolation(
                                enforcing_func=guard_func,
                                bypass_func=fname,
                                target_attr=write.target_attr,
                                bypass_line=write.line,
                                description=(
                                    f"Invariant bypass: '{guard_func}' enforces "
                                    f"whitelist on {checked} but '{fname}' writes "
                                    f"'{write.target_attr}' at line {write.line} "
                                    f"via unguarded setattr — whitelist can be bypassed"
                                ),
                            ))
        return violations

    # ── initialization cycles ──────────────────────────────────────────

    def find_init_cycles(self) -> list[InitCycle]:
        """
        Detect circular initialization dependencies between classes.

        In the CIRCULAR_DEP case:
            ComponentA.__init__ calls mediator.get_component_b() → needs B
            ComponentB.__init__ calls mediator.get_component_a() → needs A
        This is a deadlock: neither can initialize without the other.

        Isomorphism: deadlock in operating systems; feedback loop without
        dampening factor in control theory.
        """
        # Build init-dependency adjacency: class → set of classes it needs
        deps: dict[str, set[str]] = {c: set() for c in self.class_inits}
        class_names_lower = {c.lower(): c for c in self.class_inits}

        for class_name, init_fn in self.class_inits.items():
            for call in init_fn.init_method_calls:
                # Normalize to remove underscores for matching:
                # "get_component_b" matches class "ComponentB" → "componentb"
                call_flat = call.lower().replace("_", "").replace(".", "")
                for other_lower, other_name in class_names_lower.items():
                    if other_name == class_name:
                        continue
                    other_flat = other_lower.replace("_", "")
                    # Match if class name (without underscores) appears anywhere
                    # in the normalized call string
                    if other_flat in call_flat:
                        deps[class_name].add(other_name)

        # DFS cycle detection
        cycles: list[InitCycle] = []
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {c: WHITE for c in deps}
        path: list[str] = []

        def dfs(node: str) -> None:
            color[node] = GRAY
            path.append(node)
            for nbr in deps.get(node, set()):
                if color.get(nbr, BLACK) == GRAY:
                    start = path.index(nbr)
                    cycle_nodes = path[start:] + [nbr]
                    cycles.append(InitCycle(
                        cycle=cycle_nodes,
                        description=(
                            f"Circular initialization: "
                            + " → ".join(cycle_nodes)
                            + " — no stable construction order exists"
                        ),
                    ))
                elif color.get(nbr, BLACK) == WHITE:
                    dfs(nbr)
            path.pop()
            color[node] = BLACK

        for c in list(deps):
            if color[c] == WHITE:
                dfs(c)

        return cycles


# ---------------------------------------------------------------------------
# Standalone local analyzers (patterns requiring deeper semantic awareness)
# ---------------------------------------------------------------------------

def find_timing_attacks(content: str) -> list[dict[str, Any]]:
    """
    Detect non-constant-time string comparison in security-sensitive contexts.
    Isomorphism: a timing oracle is a side channel — the inequality branch
    leaks information about the secret through measured execution time.
    """
    findings: list[dict[str, Any]] = []
    tree = _try_parse(content)
    if tree is None:
        return findings

    _SECURITY_NAMES = frozenset({
        "token", "secret", "password", "auth", "key", "nonce",
        "verify", "check", "compare", "validate", "authenticate",
    })

    class _V(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            fname = node.name.lower()
            is_security = any(s in fname for s in _SECURITY_NAMES)
            if not is_security:
                self.generic_visit(node)
                return
            # Look for == comparison involving parameters
            params = {a.arg for a in node.args.args}
            has_digest = False

            class _CompVisitor(ast.NodeVisitor):
                def visit_Call(self, n: ast.Call) -> None:
                    func = n.func
                    if isinstance(func, ast.Attribute) and func.attr in (
                        "compare_digest",
                    ):
                        nonlocal has_digest
                        has_digest = True
                    self.generic_visit(n)

                def visit_Compare(self, n: ast.Compare) -> None:
                    for op in n.ops:
                        if isinstance(op, ast.Eq):
                            # Left or right references a parameter
                            left_is_param = (
                                isinstance(n.left, ast.Name)
                                and n.left.id in params
                            )
                            right_is_param = any(
                                isinstance(c, ast.Name) and c.id in params
                                for c in n.comparators
                            )
                            if left_is_param or right_is_param:
                                findings.append({
                                    "lineno": n.lineno,
                                    "func": node.name,
                                    "message": (
                                        f"Non-constant-time comparison in security "
                                        f"function '{node.name}' at line {n.lineno} — "
                                        f"use hmac.compare_digest() to prevent timing oracle"
                                    ),
                                    "rewrite": (
                                        "import hmac\n"
                                        "return hmac.compare_digest(user_token, secret_token)"
                                    ),
                                })
                    self.generic_visit(n)

            cv = _CompVisitor()
            cv.visit(node)
            if has_digest:
                # Remove findings from this function if compare_digest is present
                findings[:] = [f for f in findings if f.get("func") != node.name]
            self.generic_visit(node)

    _V().visit(tree)
    return findings


def find_incomplete_sanitization(content: str) -> list[dict[str, Any]]:
    """
    Detect path traversal checks that are incomplete:
    the function checks for '..' but does not normalize the path
    (URL-encoded traversal like %2e%2e%2f bypasses the check).
    """
    findings: list[dict[str, Any]] = []
    tree = _try_parse(content)
    if tree is None:
        return findings

    class _V(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            has_dotdot_check = False
            has_normalization = False
            has_path_join = False
            join_line = 0

            class _Inner(ast.NodeVisitor):
                def visit_Compare(self, n: ast.Compare) -> None:
                    nonlocal has_dotdot_check
                    for c in [n.left] + n.comparators:
                        if isinstance(c, ast.Constant) and ".." in str(c.value):
                            has_dotdot_check = True
                    self.generic_visit(n)

                def visit_Call(self, n: ast.Call) -> None:
                    nonlocal has_normalization, has_path_join, join_line
                    func = n.func
                    if isinstance(func, ast.Attribute):
                        if func.attr in ("abspath", "realpath", "resolve", "unquote",
                                         "unquote_plus"):
                            has_normalization = True
                        if func.attr == "join" and isinstance(func.value, ast.Attribute):
                            if func.value.attr == "path":
                                has_path_join = True
                                join_line = n.lineno
                    if isinstance(func, ast.Name) and func.id in (
                        "abspath", "realpath", "unquote"
                    ):
                        has_normalization = True
                    self.generic_visit(n)

            _Inner().visit(node)
            if has_dotdot_check and has_path_join and not has_normalization:
                findings.append({
                    "lineno": join_line,
                    "func": node.name,
                    "message": (
                        f"Incomplete path traversal check in '{node.name}': "
                        f"checks for '..' but does not decode URL encoding first — "
                        f"'%2e%2e%2f' bypasses the check; "
                        f"os.path.join at line {join_line} may traverse outside base"
                    ),
                    "rewrite": (
                        "from urllib.parse import unquote\n"
                        "path = unquote(path)\n"
                        "full = os.path.realpath(os.path.join(BASE_DIR, path))\n"
                        "if not full.startswith(os.path.realpath(BASE_DIR)):\n"
                        "    raise ValueError('Path traversal')"
                    ),
                })
            self.generic_visit(node)

    _V().visit(tree)
    return findings


def find_redos(content: str) -> list[dict[str, Any]]:
    """
    Detect ReDoS: regex patterns with nested quantifiers that cause
    catastrophic backtracking on adversarial input.
    Isomorphism: exponential branching factor in a nondeterministic finite
    automaton — the NFA backtracks through 2^n states for n-char input.
    """
    import re as _re
    findings: list[dict[str, Any]] = []
    tree = _try_parse(content)
    if tree is None:
        return findings

    def _is_dangerous_regex(pattern: str) -> bool:
        """
        Detect catastrophic backtracking potential in a regex pattern.
        Key patterns:
          (X+)+ / (X+)* / ((X)+Y?)* — multiple quantified groups nested
          (a|b)+ — alternation under quantifier
        Strategy: count occurrences of )[+*?] — if two or more exist,
        nested quantification is present regardless of nesting depth.
        """
        # Find all "closing paren followed by quantifier" tokens
        # Note: use r'\)' NOT r'\\)' — we want the regex pattern
        # \) which matches a literal ) in the target string.
        close_quants = _re.findall(r'\)[+*?]', pattern)
        if len(close_quants) >= 2:
            return True
        # Alternation under quantifier: (a|b)+
        if _re.search(r'\([^()]*\|[^()]*\)[+*]', pattern):
            return True
        # Adjacent quantifiers (x++ possessive-like)
        if _re.search(r'[+*][+*]', pattern):
            return True
        return False

    # First pass: collect string variable assignments (pattern = r"...")
    _string_vars: dict[str, str] = {}

    class _CollectVars(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        _string_vars[t.id] = node.value.value
            self.generic_visit(node)

    _CollectVars().visit(tree)

    class _V(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            is_re_call = (
                isinstance(func, ast.Attribute)
                and func.attr in ("compile", "match", "search", "fullmatch", "findall")
                and isinstance(func.value, ast.Name)
                and func.value.id == "re"
            )
            if is_re_call and node.args:
                arg = node.args[0]
                pattern_str = None
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    pattern_str = arg.value
                elif isinstance(arg, ast.Name) and arg.id in _string_vars:
                    # Resolve variable → string value from first-pass collection
                    pattern_str = _string_vars[arg.id]
                if pattern_str and _is_dangerous_regex(pattern_str):
                    findings.append({
                        "lineno": node.lineno,
                        "message": (
                            f"ReDoS: regex at line {node.lineno} contains nested "
                            f"quantifiers — adversarial input can cause exponential "
                            f"backtracking: {pattern_str[:60]!r}"
                        ),
                        "rewrite": (
                            "Use re2 (google-re2) which guarantees O(n) matching, "
                            "or rewrite pattern to eliminate nested quantifiers"
                        ),
                    })
            self.generic_visit(node)

    _V().visit(tree)
    return findings


def find_weak_hash_usage(content: str) -> list[dict[str, Any]]:
    """
    Detect MD5/SHA1 used in security-sensitive contexts (passwords, tokens).
    Isomorphism: a cryptographic hash is a one-way function; MD5/SHA1 are
    no longer one-way for practical adversaries — collision and preimage
    attacks exist.
    """
    findings: list[dict[str, Any]] = []
    tree = _try_parse(content)
    if tree is None:
        return findings

    _SECURITY_CONTEXT = frozenset({
        "password", "passwd", "secret", "token", "auth", "credential",
        "hash", "store", "register", "secure",
    })
    _WEAK = frozenset({"md5", "sha1", "sha_1", "MD5", "SHA1"})

    class _V(ast.NodeVisitor):
        def __init__(self) -> None:
            self._func_name = ""

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._func_name = node.name.lower()
            self.generic_visit(node)
            self._func_name = ""

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            alg = None
            if isinstance(func, ast.Attribute) and func.attr in _WEAK:
                if isinstance(func.value, ast.Name) and func.value.id == "hashlib":
                    alg = func.attr
            if alg and any(s in self._func_name for s in _SECURITY_CONTEXT):
                findings.append({
                    "lineno": node.lineno,
                    "alg": alg,
                    "message": (
                        f"Weak hash: hashlib.{alg} at line {node.lineno} in "
                        f"security context '{self._func_name}' — "
                        f"{alg.upper()} is broken for security use"
                    ),
                    "rewrite": (
                        "import bcrypt\n"
                        "hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())\n"
                        "# Or: passlib.hash.argon2.hash(password)"
                    ),
                })
            self.generic_visit(node)

    _V().visit(tree)
    return findings


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def analyze(content: str) -> dict[str, Any]:
    """
    Run the full interprocedural analysis suite on Python content.
    Returns structured findings across all analyzers.
    """
    tree = _try_parse(content)
    results: dict[str, Any] = {
        "taint_paths": [],
        "invariant_violations": [],
        "init_cycles": [],
        "timing_attacks": [],
        "incomplete_sanitization": [],
        "redos": [],
        "weak_hash": [],
    }
    if tree is None:
        return results

    cg = CallGraph()
    cg.build(tree)

    results["taint_paths"] = [
        {"description": p.description(), "confidence": p.confidence,
         "sink_type": p.sink_type, "sink_line": p.sink_line,
         "chain": p.call_chain}
        for p in cg.propagate_taint()
    ]
    results["invariant_violations"] = [
        {"description": v.description, "enforcing": v.enforcing_func,
         "bypass": v.bypass_func, "attr": v.target_attr, "line": v.bypass_line}
        for v in cg.find_invariant_bypasses()
    ]
    results["init_cycles"] = [
        {"description": c.description, "cycle": c.cycle}
        for c in cg.find_init_cycles()
    ]
    results["timing_attacks"] = find_timing_attacks(content)
    results["incomplete_sanitization"] = find_incomplete_sanitization(content)
    results["redos"] = find_redos(content)
    results["weak_hash"] = find_weak_hash_usage(content)
    return results


def _try_parse(content: str) -> ast.AST | None:
    try:
        return ast.parse(content)
    except SyntaxError:
        return None
