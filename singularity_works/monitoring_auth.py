from __future__ import annotations

import ast

from .ast_primitives import const_str, is_session_target
from .models import Artifact, MonitorSeed
from .monitoring_core import _safe_parse


def _is_redirect_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Name) and func.id == "redirect"
    ) or (
        isinstance(func, ast.Attribute) and func.attr == "redirect"
    )


def _session_established_before_redirect(content: str) -> tuple[bool, str]:
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for auth/session monitor"

    auth_name_keywords = {"login", "signin", "auth", "callback", "oauth", "token"}
    body_keywords = {"password", "passwd", "credential", "token", "session", "request", "form", "authenticate", "check_password"}
    found_relevant = False
    failures: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        session_lines: set[int] = set()
        direct_redirect_lines: set[int] = set()
        body_text_bits: list[str] = []
        response_redirect_vars: dict[str, int] = {}
        response_cookie_lines: dict[str, list[int]] = {}
        response_return_lines: dict[str, list[int]] = {}

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if is_session_target(target):
                        session_lines.add(getattr(child, 'lineno', 0))
                if isinstance(child.value, ast.Call):
                    func = child.value.func
                    if isinstance(func, ast.Name) and func.id == 'make_response':
                        args = getattr(child.value, 'args', [])
                        if args and _is_redirect_call(args[0]):
                            for target in child.targets:
                                if isinstance(target, ast.Name):
                                    response_redirect_vars[target.id] = getattr(child, 'lineno', 0)
                    elif _is_redirect_call(child.value):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                response_redirect_vars[target.id] = getattr(child, 'lineno', 0)
            elif isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name) and func.id == 'login_user':
                    session_lines.add(getattr(child, 'lineno', 0))
                elif isinstance(func, ast.Attribute) and func.attr in {'set_cookie', 'login_user'}:
                    line = getattr(child, 'lineno', 0)
                    session_lines.add(line)
                    if func.attr == 'set_cookie' and isinstance(func.value, ast.Name):
                        response_cookie_lines.setdefault(func.value.id, []).append(line)
                if _is_redirect_call(child):
                    direct_redirect_lines.add(getattr(child, 'lineno', 0))
            elif isinstance(child, ast.Return):
                if _is_redirect_call(child.value):
                    direct_redirect_lines.add(getattr(child, 'lineno', 0))
                elif isinstance(child.value, ast.Name):
                    response_return_lines.setdefault(child.value.id, []).append(getattr(child, 'lineno', 0))
            elif isinstance(child, ast.Name):
                body_text_bits.append(child.id.lower())
            elif isinstance(child, ast.Attribute):
                body_text_bits.append(child.attr.lower())
            elif isinstance(child, ast.Constant) and isinstance(child.value, str):
                body_text_bits.append(child.value.lower())

        has_any_redirect = bool(direct_redirect_lines or response_redirect_vars)
        if not has_any_redirect:
            continue

        name_low = node.name.lower()
        body_low = " ".join(body_text_bits)
        auth_like = any(k in name_low for k in auth_name_keywords) or any(k in body_low for k in body_keywords)
        if not auth_like:
            continue

        found_relevant = True
        response_redirect_line_values = set(response_redirect_vars.values())
        for rline in sorted(direct_redirect_lines):
            if rline in response_redirect_line_values:
                continue
            if not any(sline < rline for sline in session_lines):
                failures.append(f"{node.name}: redirect at line {rline} without prior session/cookie establishment")

        for var, redirect_line in response_redirect_vars.items():
            return_lines = response_return_lines.get(var, [])
            cookie_lines = response_cookie_lines.get(var, [])
            if return_lines:
                for rline in return_lines:
                    ok = any(sline < rline for sline in session_lines) or any(redirect_line < cline < rline for cline in cookie_lines)
                    if not ok:
                        failures.append(f"{node.name}: returning redirect response '{var}' at line {rline} without session/cookie establishment")
            else:
                if not (any(sline < redirect_line for sline in session_lines) or cookie_lines):
                    failures.append(f"{node.name}: redirect response '{var}' without session/cookie establishment")

    if not found_relevant:
        return True, "no auth-like redirect flow found"
    if failures:
        # de-duplicate while preserving order
        uniq = list(dict.fromkeys(failures))
        return False, "; ".join(uniq)
    return True, "auth-like redirects occur only after session/cookie establishment"


def _must_establish_session_before_redirect(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _session_established_before_redirect(artifact.content)


def _transaction_finalized_after_write(content: str) -> tuple[bool, str]:
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for transaction monitor"

    failures: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        write_lines: list[int] = []
        commit_lines: list[int] = []
        rollback_lines: list[int] = []
        tx_context_lines: list[int] = []

        for child in ast.walk(node):
            if isinstance(child, ast.With):
                for item in child.items:
                    ctx = item.context_expr
                    if isinstance(ctx, ast.Call) and isinstance(ctx.func, ast.Attribute) and ctx.func.attr in {"begin", "transaction"}:
                        tx_context_lines.append(getattr(child, "lineno", 0))
                    elif isinstance(ctx, ast.Attribute) and ctx.attr == "transaction":
                        tx_context_lines.append(getattr(child, "lineno", 0))
            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                attr = child.func.attr
                if attr == "commit":
                    commit_lines.append(getattr(child, "lineno", 0))
                elif attr == "rollback":
                    rollback_lines.append(getattr(child, "lineno", 0))
                elif attr in {"add", "delete", "merge", "insert", "update"}:
                    write_lines.append(getattr(child, "lineno", 0))
                elif attr in {"execute", "executemany", "executescript"}:
                    sql_text = ""
                    if child.args:
                        arg0 = child.args[0]
                        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                            sql_text = arg0.value.lower()
                    if any(kw in sql_text for kw in ("insert", "update", "delete", "alter", "create", "drop")):
                        write_lines.append(getattr(child, "lineno", 0))

        if not write_lines:
            continue
        if tx_context_lines:
            continue
        last_write = max(write_lines)
        has_finalize_after = any(line > last_write for line in commit_lines + rollback_lines)
        if not has_finalize_after:
            failures.append(f"{node.name}: database write at/before line {last_write} without later commit/rollback or managed transaction context")

    if failures:
        return False, "; ".join(failures[:3])
    return True, "database writes are followed by commit/rollback or managed transaction context"


def _must_finalize_transaction_after_write(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _transaction_finalized_after_write(artifact.content)


def _auth_cookies_hardened(content: str) -> tuple[bool, str]:
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for auth-cookie monitor"

    sensitive_name_bits = {"session", "auth", "token", "jwt", "access", "refresh", "remember"}
    failures: list[str] = []
    relevant_seen = False

    def _kw_map(call: ast.Call) -> dict[str, ast.AST]:
        return {kw.arg: kw.value for kw in call.keywords if kw.arg}

    def _bool_true(node: ast.AST | None) -> bool:
        return isinstance(node, ast.Constant) and node.value is True

    def _samesite_ok(node: ast.AST | None) -> bool:
        return isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.lower() in {"lax", "strict", "none"}

    for child in ast.walk(tree):
        if not (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "set_cookie"):
            continue
        cookie_name = None
        if child.args:
            cookie_name = const_str(child.args[0])
        if cookie_name is None:
            cookie_name = const_str(_kw_map(child).get("key"))
        body_text = " ".join(
            [cookie_name.lower() if isinstance(cookie_name, str) else ""]
            + [n.id.lower() for n in ast.walk(child) if isinstance(n, ast.Name)]
            + [n.attr.lower() for n in ast.walk(child) if isinstance(n, ast.Attribute)]
            + [n.value.lower() for n in ast.walk(child) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        )
        if not any(bit in body_text for bit in sensitive_name_bits):
            continue
        relevant_seen = True
        kw = _kw_map(child)
        secure_ok = _bool_true(kw.get("secure"))
        httponly_ok = _bool_true(kw.get("httponly"))
        samesite_ok = _samesite_ok(kw.get("samesite"))
        if not (secure_ok and httponly_ok and samesite_ok):
            label = cookie_name or "<dynamic-cookie>"
            missing = []
            if not secure_ok:
                missing.append("secure=True")
            if not httponly_ok:
                missing.append("httponly=True")
            if not samesite_ok:
                missing.append("samesite=(Lax|Strict|None)")
            failures.append(f"line {getattr(child, 'lineno', 0)}: sensitive cookie {label!r} missing " + ", ".join(missing))

    if not relevant_seen:
        return True, "no auth/session/token cookie-setting flow found"
    if failures:
        return False, "; ".join(failures[:4])
    return True, "auth/session/token cookies are hardened with secure, httponly, and samesite"


def _must_harden_auth_cookies(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _auth_cookies_hardened(artifact.content)


def _auth_state_cleared_on_logout(content: str) -> tuple[bool, str]:
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for auth-logout monitor"

    failures: list[str] = []
    relevant_seen = False

    def is_session_target(node: ast.AST) -> bool:
        if isinstance(node, ast.Name) and node.id == "session":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "session":
            return True
        if isinstance(node, ast.Subscript):
            val = node.value
            if isinstance(val, ast.Name) and val.id == "session":
                return True
            if isinstance(val, ast.Attribute) and val.attr == "session":
                return True
        return False

    def _is_relevant_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        name = node.name.lower()
        if any(bit in name for bit in ("logout", "signout", "revoke")):
            return True
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name) and func.id in {"logout_user", "unset_jwt_cookies", "revoke_token", "revoke"}:
                    return True
                if isinstance(func, ast.Attribute):
                    if func.attr in {"delete_cookie", "unset_jwt_cookies", "revoke", "revoke_token"}:
                        return True
                    if func.attr in {"clear", "pop"} and is_session_target(func.value):
                        return True
        return False

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not _is_relevant_function(node):
            continue
        relevant_seen = True

        auth_clear_lines: list[int] = []
        response_delete_cookie_lines: dict[str, list[int]] = {}
        return_redirect_lines: list[int] = []
        return_name_lines: list[tuple[str, int]] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                line = getattr(child, 'lineno', 0)
                if isinstance(func, ast.Name) and func.id in {"logout_user", "unset_jwt_cookies", "revoke_token", "revoke"}:
                    auth_clear_lines.append(line)
                elif isinstance(func, ast.Attribute):
                    if func.attr in {"delete_cookie", "unset_jwt_cookies", "revoke", "revoke_token"}:
                        auth_clear_lines.append(line)
                        if func.attr == "delete_cookie" and isinstance(func.value, ast.Name):
                            response_delete_cookie_lines.setdefault(func.value.id, []).append(line)
                    elif func.attr in {"clear", "pop"} and is_session_target(func.value):
                        auth_clear_lines.append(line)
            elif isinstance(child, ast.Return):
                value = child.value
                line = getattr(child, 'lineno', 0)
                if value is not None and _is_redirect_call(value):
                    return_redirect_lines.append(line)
                elif isinstance(value, ast.Name):
                    return_name_lines.append((value.id, line))

        if not auth_clear_lines:
            failures.append(f"{node.name}: logout/revoke flow without session clear, cookie deletion, or token revocation")
            continue

        for rline in return_redirect_lines:
            if not any(cline < rline for cline in auth_clear_lines):
                failures.append(f"{node.name}: redirect at line {rline} before auth state was cleared")

        for var, rline in return_name_lines:
            var_delete_lines = response_delete_cookie_lines.get(var, [])
            if var_delete_lines:
                if not any(cline < rline for cline in var_delete_lines):
                    failures.append(f"{node.name}: returned response '{var}' before delete_cookie executed")
            else:
                if not any(cline < rline for cline in auth_clear_lines):
                    failures.append(f"{node.name}: returned response '{var}' before auth state was cleared")

    if not relevant_seen:
        return True, "no logout/revoke auth-state flow found"
    if failures:
        return False, "; ".join(failures[:4])
    return True, "logout/revoke flows clear session, delete cookies, or revoke tokens before returning"


