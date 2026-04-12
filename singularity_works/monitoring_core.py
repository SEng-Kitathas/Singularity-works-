from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import dataclass
import ast

from .ast_primitives import close_name_from_call, const_str, is_open_call, is_session_target
from .models import Artifact, MonitorSeed


@dataclass
class MonitorEvent:
    monitor_id: str
    requirement_id: str
    severity: str
    status: str
    message: str
    linked_artifact_id: str
    claim_id: str = ""


def _safe_parse(content: str):
    try:
        return ast.parse(content)
    except SyntaxError:
        return None



def _with_open(node: ast.With) -> bool:
    return any(is_open_call(item.context_expr) for item in node.items)


def _assigned_open_names(node: ast.Assign) -> list[str]:
    value = node.value
    if not isinstance(value, ast.Call):
        return []
    func = value.func
    if not is_open_call(value):
        return []
    return [target.id for target in node.targets if isinstance(target, ast.Name)]


def _iter_close_names(nodes) -> set[str]:
    closes: set[str] = set()
    for child in ast.walk(ast.Module(body=list(nodes), type_ignores=[])):
        if isinstance(child, ast.Call):
            name = close_name_from_call(child)
            if name:
                closes.add(name)
    return closes


def _resource_closed(content: str) -> bool:
    tree = _safe_parse(content)
    if tree is None:
        return False
    open_names: set[str] = set()
    close_names: set[str] = set()
    safe_with_open = False
    safe_try_finally = False

    for node in ast.walk(tree):
        if isinstance(node, ast.With):
            safe_with_open = safe_with_open or _with_open(node)
        elif isinstance(node, ast.Try) and node.finalbody:
            safe_try_finally = safe_try_finally or bool(_iter_close_names(node.finalbody))
        elif isinstance(node, ast.Assign):
            open_names.update(_assigned_open_names(node))
        elif isinstance(node, ast.Call):
            name = close_name_from_call(node)
            if name:
                close_names.add(name)

    return safe_with_open or safe_try_finally or bool(open_names and open_names.issubset(close_names))


def _contains(content_low: str, expression: str) -> bool:
    return expression.lower() in content_low


def _dangerous_call_names(content: str) -> set[str]:
    tree = _safe_parse(content)
    if tree is None:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in {"eval", "exec"}:
            names.add(func.id)
    return names


def _has_verify_false(content: str) -> bool:
    tree = _safe_parse(content)
    if tree is None:
        return "verify=false" in content.lower()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg == "verify" and isinstance(keyword.value, ast.Constant):
                if keyword.value.value is False:
                    return True
    return False


def _must_contain(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _contains(artifact.content.lower(), seed.expression), f"content must contain '{seed.expression}'"


def _must_not_contain(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    expr = seed.expression.strip()
    message = f"content must not contain '{expr}'"
    if expr == "eval(":
        return ("eval" not in _dangerous_call_names(artifact.content), message)
    if expr == "exec(":
        return ("exec" not in _dangerous_call_names(artifact.content), message)
    if expr.lower() == "verify=false":
        return (not _has_verify_false(artifact.content), message)
    return (not _contains(artifact.content.lower(), expr), message)


def _must_close_resource(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _resource_closed(artifact.content), "opened resources must be closed or context-managed"


