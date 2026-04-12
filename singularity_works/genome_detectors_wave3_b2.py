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

def _detect_pycrypto_import(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect import of pycrypto/Crypto â€” unmaintained library with known CVEs.
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
                            f"pycrypto/Crypto module '{mod}' at line {lineno} â€” "
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






def _detect_django_mark_safe(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect django.utils.safestring.mark_safe() with non-constant argument.
    Bypasses Django's auto-escaping â€” stored XSS if user data reaches it.
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
                                f"mark_safe() with non-constant argument at line {node.lineno} â€” "
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
                                f"{node.lineno} â€” bypasses parameterization, SQL injection risk"
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
                        f"Raw SQL construction at line {tb.sink_line} â€” "
                        f"parameterize all user-supplied values"
                    ),
                    evidence={"rewrite_candidate": "Use parameterized queries"},
                ))
    return detections






def _detect_marshal_deserialize(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect marshal.load / marshal.loads â€” arbitrary code execution on untrusted data.
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
                            f"marshal.{func.attr}() at line {node.lineno} â€” "
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





# ---------------------------------------------------------------------------
# Remaining bandit-derived detectors (B506, B602/603, B503/504)
# ---------------------------------------------------------------------------



def _detect_yaml_unsafe_load(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect yaml.load() without Loader= argument â€” executes arbitrary Python.
    yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader) is safe.
    (Bandit B506 equivalent)
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if (isinstance(func, ast.Attribute) and func.attr == "load"
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "yaml"):
                    # Check if Loader kwarg is present
                    has_loader = any(kw.arg == "Loader" for kw in node.keywords)
                    if not has_loader:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"yaml.load() without Loader= at line {node.lineno} â€” "
                                f"deserializes arbitrary Python via YAML tags"
                            ),
                            evidence={
                                "rewrite_candidate":
                                    "yaml.safe_load(data)  # or yaml.load(data, Loader=yaml.SafeLoader)"
                            },
                        ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections






