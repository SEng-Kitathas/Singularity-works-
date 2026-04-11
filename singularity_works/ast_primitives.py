from __future__ import annotations

import ast


def const_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def is_open_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Name) and func.id == "open"
    ) or (
        isinstance(func, ast.Attribute) and func.attr == "open"
    )


def close_name_from_call(node: ast.Call) -> str | None:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr != "close":
        return None
    value = func.value
    return value.id if isinstance(value, ast.Name) else None


def is_session_target(node: ast.AST, *, include_direct: bool = False) -> bool:
    if include_direct:
        if isinstance(node, ast.Name) and node.id == "session":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "session":
            return True
    if isinstance(node, ast.Subscript):
        value = node.value
        if isinstance(value, ast.Name) and value.id == "session":
            return True
        if isinstance(value, ast.Attribute) and value.attr == "session":
            return True
    return False
