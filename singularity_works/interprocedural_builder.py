from __future__ import annotations

import ast

from .interprocedural_types import (
    CallSite,
    FunctionNode,
    TaintSink,
    TaintSource,
    WriteOp,
)

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


