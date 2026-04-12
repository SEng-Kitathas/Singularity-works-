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
                if is_open_call(item.context_expr):
                    if isinstance(item.optional_vars, ast.Name):
                        self.with_managed.add(item.optional_vars.id)
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            if isinstance(node.value, ast.Call) and is_open_call(node.value):
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
    """Detect subprocess.run(shell=True), os.system(), os.popen() â€” shell injection surfaces."""
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
    """Detect eval() and exec() builtins only â€” shell injection handled by ast_shell_injection."""
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
                        f"allows __proto__ writes â€” contaminates every object in the runtime"
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
    # Do NOT early-return on tree=None â€” non-Python content (Rust, Go, etc.)
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

    # IR fallback â€” non-Python SQL injection (Rust format!, Go fmt.Sprintf, etc.)
    # The heuristic front door populates DB_QUERY TrustBoundary with
    # tainted_input="string_construction" for format!("SELECT...{}", var) patterns.
    if not detections and semantic_ir is not None:
        for tb in getattr(semantic_ir, "trust_boundaries", []):
            if (tb.boundary_type == "DB_QUERY"
                    and getattr(tb, "tainted_input", "") == "string_construction"):
                detections.append(_Detection(
                    lineno=tb.sink_line,
                    message=(
                        f"String-built SQL query '{tb.sink_name}' at line {tb.sink_line} â€” "
                        f"format-string interpolation bypasses parameterization"
                    ),
                    evidence={
                        "rewrite_candidate": (
                            "Use parameterized queries: sqlx::query(\"SELECT * FROM users "
                            "WHERE id = ?\").bind(id) â€” never interpolate user input into SQL"
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
    across all calls â€” a classic state-persistence bug.
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
                        message=f"Mutable default argument ({type_name} literal) â€” state persists across calls",
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




