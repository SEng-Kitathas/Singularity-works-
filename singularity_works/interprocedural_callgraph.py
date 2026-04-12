from __future__ import annotations

import ast

from .interprocedural_builder import _GraphBuilder
from .interprocedural_types import InitCycle, InvariantViolation, TaintPath

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


