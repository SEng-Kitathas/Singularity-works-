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


def _callback_state_token_validated(content: str) -> tuple[bool, str]:
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for callback-state monitor"

    failures: list[str] = []
    relevant_seen = False

    def const_str(node: ast.AST | None) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def is_session_target(node: ast.AST) -> bool:
        if isinstance(node, ast.Name) and node.id == "session":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "session":
            return True
        if isinstance(node, ast.Subscript):
            return is_session_target(node.value)
        return False

    def _is_request_state_get(call: ast.Call) -> bool:
        func = call.func
        if not (isinstance(func, ast.Attribute) and func.attr == "get"):
            return False
        key = None
        if call.args:
            key = const_str(call.args[0])
        if key is None:
            for kw in call.keywords:
                if kw.arg in {"key", "name"}:
                    key = const_str(kw.value)
                    if key is not None:
                        break
        if not (isinstance(key, str) and key.lower() in {"state", "csrf", "csrf_token"}):
            return False
        val = func.value
        return isinstance(val, ast.Attribute) and val.attr in {"args", "form", "values", "cookies", "query_params"}

    def _is_session_state_read(node: ast.AST) -> bool:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and is_session_target(node.func.value):
            key = None
            if node.args:
                key = const_str(node.args[0])
            if key is None:
                for kw in node.keywords:
                    if kw.arg in {"key", "name"}:
                        key = const_str(kw.value)
                        if key is not None:
                            break
            return isinstance(key, str) and any(bit in key.lower() for bit in ("state", "csrf"))
        if isinstance(node, ast.Subscript) and is_session_target(node.value):
            sl = node.slice
            return isinstance(sl, ast.Constant) and isinstance(sl.value, str) and any(bit in sl.value.lower() for bit in ("state", "csrf"))
        return False

    def _collect_names(node: ast.AST) -> set[str]:
        return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        state_vars: set[str] = set()
        expected_vars: set[str] = set()
        validation_lines: list[int] = []
        continuation_lines: list[int] = []

        lname = node.name.lower()
        if any(bit in lname for bit in ("callback", "oauth", "authorize", "login", "refresh")):
            relevant_seen = True

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                if len(child.targets) == 1 and isinstance(child.targets[0], ast.Name):
                    tname = child.targets[0].id
                    if isinstance(child.value, ast.Call) and _is_request_state_get(child.value):
                        state_vars.add(tname)
                        relevant_seen = True
                    elif _is_session_state_read(child.value):
                        expected_vars.add(tname)
                        relevant_seen = True
            elif isinstance(child, ast.Call):
                func = child.func
                line = getattr(child, 'lineno', 0)
                if isinstance(func, ast.Name):
                    if func.id in {"exchange_code", "fetch_token", "authorize_access_token", "login_user", "create_access_token", "redirect"}:
                        continuation_lines.append(line)
                        relevant_seen = True
                    elif func.id in {"validate_csrf", "validate_state", "verify_state", "compare_digest"}:
                        names = set()
                        for arg in child.args:
                            names |= _collect_names(arg)
                        for kw in child.keywords:
                            names |= _collect_names(kw.value)
                        if (not state_vars or names & state_vars) and (not expected_vars or names & expected_vars):
                            validation_lines.append(line)
                            relevant_seen = True
                elif isinstance(func, ast.Attribute):
                    attr = func.attr
                    if attr in {"exchange_code", "fetch_token", "authorize_access_token", "create_access_token", "redirect"}:
                        continuation_lines.append(line)
                        relevant_seen = True
                    elif attr in {"validate_csrf", "validate_state", "verify_state"}:
                        validation_lines.append(line)
                        relevant_seen = True
            elif isinstance(child, ast.Compare):
                names = _collect_names(child)
                has_state = bool(names & state_vars) or _is_request_state_get(child.left) or any(_is_request_state_get(c) for c in child.comparators if isinstance(c, ast.Call))
                has_expected = bool(names & expected_vars) or _is_session_state_read(child.left) or any(_is_session_state_read(c) for c in child.comparators)
                if has_state and has_expected:
                    validation_lines.append(getattr(child, 'lineno', 0))
                    relevant_seen = True

        if not state_vars:
            # No state param read — check if this looks like an OAuth callback
            # that simply never reads state at all (the omission IS the vulnerability).
            # Trigger: function has continuation calls (exchange_code, fetch_token, etc.)
            # and the function name or requirement context suggests OAuth/callback.
            _is_oauth_like = (
                any(bit in node.name.lower() for bit in ("callback", "oauth", "authorize"))
                or any(
                    (isinstance(c, ast.Call) and isinstance(c.func, (ast.Name, ast.Attribute))
                     and (c.func.id if isinstance(c.func, ast.Name) else c.func.attr)
                     in {"exchange_code", "fetch_token", "authorize_access_token"})
                    for c in ast.walk(node)
                )
            )
            if _is_oauth_like and continuation_lines:
                failures.append(
                    f"{node.name}: OAuth-style callback has no state/csrf parameter read — "
                    f"missing CSRF protection entirely"
                )
            continue
        if not continuation_lines:
            continue
        first_cont = min(continuation_lines)
        if not validation_lines:
            failures.append(f"{node.name}: callback/request state is consumed without explicit state/csrf validation before sensitive continuation")
            continue
        if not any(v < first_cont for v in validation_lines):
            failures.append(f"{node.name}: state/csrf validation occurs only after callback continuation began")

    if not relevant_seen:
        return True, "no callback-style state/csrf flow found"
    if failures:
        return False, "; ".join(failures[:4])
    return True, "callback/request state is explicitly validated before sensitive continuation"



def _refresh_token_family_integrity(content: str) -> tuple[bool, str]:
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for refresh-family-integrity monitor"

    failures: list[str] = []
    relevant_seen = False

    def _kw_map(call: ast.Call) -> dict[str, ast.AST]:
        return {kw.arg: kw.value for kw in call.keywords if kw.arg}

    def const_str(node: ast.AST | None) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _request_refresh_source(call: ast.Call) -> bool:
        func = call.func
        if isinstance(func, ast.Attribute) and func.attr == "get":
            key = None
            if call.args:
                key = const_str(call.args[0])
            if key is None:
                key = const_str(_kw_map(call).get("key"))
            if isinstance(key, str) and "refresh" in key.lower():
                base = func.value
                if isinstance(base, ast.Attribute) and base.attr in {"cookies", "headers", "args", "form", "json"}:
                    return True
        return False

    def _assign_name(targets: list[ast.expr]) -> str | None:
        for target in targets:
            if isinstance(target, ast.Name):
                return target.id
        return None

    def _collect_names(node: ast.AST | None) -> set[str]:
        found: set[str] = set()
        if node is None:
            return found
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                found.add(child.id)
        return found

    def _is_family_guard_call(call: ast.Call) -> bool:
        func = call.func
        if isinstance(func, ast.Name):
            return func.id in {"revoke_token_family", "invalidate_refresh_family", "mark_refresh_reused", "check_refresh_reuse", "assert_refresh_family", "consume_refresh_token"}
        if isinstance(func, ast.Attribute):
            return func.attr in {"revoke_token_family", "invalidate_refresh_family", "mark_refresh_reused", "check_refresh_reuse", "assert_refresh_family", "consume_refresh_token"}
        return False

    def _is_issue_call(call: ast.Call) -> bool:
        func = call.func
        if isinstance(func, ast.Name):
            return func.id in {"create_refresh_token", "issue_refresh_token", "mint_refresh_token"}
        if isinstance(func, ast.Attribute):
            if func.attr in {"set_refresh_cookie", "set_refresh_cookies", "create_refresh_token", "issue_refresh_token", "mint_refresh_token"}:
                return True
            if func.attr == "set_cookie":
                key = None
                if call.args:
                    key = const_str(call.args[0])
                if key is None:
                    key = const_str(_kw_map(call).get("key"))
                return isinstance(key, str) and "refresh" in key.lower()
        return False

    def _is_rotation_call(call: ast.Call) -> bool:
        func = call.func
        if isinstance(func, ast.Name):
            return func.id in {"revoke_refresh_token", "rotate_refresh_token", "blacklist_token", "blacklist_jti"}
        if isinstance(func, ast.Attribute):
            if func.attr in {"revoke_refresh_token", "rotate_refresh_token", "blacklist_token", "blacklist_jti", "unset_jwt_cookies"}:
                return True
            if func.attr == "delete_cookie":
                key = None
                if call.args:
                    key = const_str(call.args[0])
                if key is None:
                    key = const_str(_kw_map(call).get("key"))
                return isinstance(key, str) and "refresh" in key.lower()
        return False

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        source_vars: set[str] = set()
        derived_vars: set[str] = set()
        issue_lines: list[int] = []
        protection_lines: list[int] = []

        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                target_name = _assign_name(stmt.targets)
                if target_name and _request_refresh_source(stmt.value):
                    source_vars.add(target_name)
                    relevant_seen = True
                elif target_name:
                    names = _collect_names(stmt.value)
                    if names & source_vars and any(bit in target_name.lower() for bit in ("claims", "decoded", "payload", "jti", "family", "token")):
                        derived_vars.add(target_name)
                        relevant_seen = True
            elif isinstance(stmt, ast.Call):
                if _is_issue_call(stmt):
                    issue_lines.append(getattr(stmt, "lineno", 0))
                if _is_rotation_call(stmt) or _is_family_guard_call(stmt):
                    arg_names = set()
                    for arg in stmt.args:
                        arg_names |= _collect_names(arg)
                    for kw in stmt.keywords:
                        arg_names |= _collect_names(kw.value)
                    if not source_vars:
                        # If we haven't seen a request-bound refresh source, this monitor abstains.
                        continue
                    if arg_names & (source_vars | derived_vars) or _is_family_guard_call(stmt):
                        protection_lines.append(getattr(stmt, "lineno", 0))
                        relevant_seen = True
                    elif _is_rotation_call(stmt):
                        relevant_seen = True

        if not source_vars or not issue_lines:
            continue

        if not protection_lines:
            failures.append(f"{node.name}: request-bound refresh token is rotated/reissued without family/reuse protection tied to the presented token")
            continue

        first_issue = min(issue_lines)
        if not any(line < first_issue for line in protection_lines):
            failures.append(f"{node.name}: refresh family/reuse protection occurs only after issuing the new refresh token")

    if not relevant_seen:
        return True, "no request-bound refresh family flow found"
    if failures:
        return False, "; ".join(failures[:4])
    return True, "request-bound refresh flows preserve token-family/reuse integrity before reissue"


def _refresh_tokens_rotated_or_revoked(content: str) -> tuple[bool, str]:
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for refresh-rotation monitor"

    failures: list[str] = []
    relevant_seen = False

    def _kw_map(call: ast.Call) -> dict[str, ast.AST]:
        return {kw.arg: kw.value for kw in call.keywords if kw.arg}

    def const_str(node: ast.AST | None) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _is_refresh_cookie_call(call: ast.Call) -> bool:
        if not (isinstance(call.func, ast.Attribute) and call.func.attr == "set_cookie"):
            return False
        key = None
        if call.args:
            key = const_str(call.args[0])
        if key is None:
            key = const_str(_kw_map(call).get("key"))
        return isinstance(key, str) and "refresh" in key.lower()

    def _is_refresh_delete_call(call: ast.Call) -> bool:
        if not (isinstance(call.func, ast.Attribute) and call.func.attr == "delete_cookie"):
            return False
        key = None
        if call.args:
            key = const_str(call.args[0])
        if key is None:
            key = const_str(_kw_map(call).get("key"))
        return isinstance(key, str) and "refresh" in key.lower()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        issue_lines: list[int] = []
        rotation_lines: list[int] = []
        return_lines: list[int] = []

        name = node.name.lower()
        if any(bit in name for bit in ("refresh", "rotate", "renew")):
            relevant_seen = True

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                line = getattr(child, 'lineno', 0)
                if isinstance(func, ast.Name):
                    if func.id in {"create_refresh_token", "issue_refresh_token", "mint_refresh_token"}:
                        issue_lines.append(line)
                        relevant_seen = True
                    elif func.id in {"revoke_refresh_token", "rotate_refresh_token", "blacklist_token", "blacklist_jti", "revoke_token_family", "invalidate_refresh_family", "mark_refresh_reused", "check_refresh_reuse", "assert_refresh_family", "consume_refresh_token"}:
                        rotation_lines.append(line)
                        relevant_seen = True
                elif isinstance(func, ast.Attribute):
                    attr = func.attr
                    if attr in {"set_refresh_cookie", "set_refresh_cookies", "create_refresh_token", "issue_refresh_token", "mint_refresh_token"}:
                        issue_lines.append(line)
                        relevant_seen = True
                    elif attr in {"revoke_refresh_token", "rotate_refresh_token", "blacklist_token", "blacklist_jti", "unset_jwt_cookies", "revoke_token_family", "invalidate_refresh_family", "mark_refresh_reused", "check_refresh_reuse", "assert_refresh_family", "consume_refresh_token"}:
                        rotation_lines.append(line)
                        relevant_seen = True
                    elif _is_refresh_cookie_call(child):
                        issue_lines.append(line)
                        relevant_seen = True
                    elif _is_refresh_delete_call(child):
                        rotation_lines.append(line)
                        relevant_seen = True
            elif isinstance(child, ast.Return):
                return_lines.append(getattr(child, 'lineno', 0))

        if not issue_lines:
            continue

        if not rotation_lines:
            failures.append(f"{node.name}: refresh token issued without revocation/rotation of the old refresh token")
            continue

        for rline in return_lines:
            if any(iline < rline for iline in issue_lines):
                if not any(rot < rline for rot in rotation_lines):
                    failures.append(f"{node.name}: returned at line {rline} after issuing refresh token but before revoke/rotation")
                    break

    if not relevant_seen:
        return True, "no refresh-token rotation flow found"
    if failures:
        return False, "; ".join(failures[:4])
    return True, "refresh-token issuance is paired with revoke/rotation before returning"


def _must_rotate_or_revoke_refresh_token(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _refresh_tokens_rotated_or_revoked(artifact.content)


def _must_preserve_refresh_token_family_integrity(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _refresh_token_family_integrity(artifact.content)


def _must_validate_state_token_before_callback_use(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _callback_state_token_validated(artifact.content)


def _must_clear_auth_state_on_logout(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _auth_state_cleared_on_logout(artifact.content)


def _recovery_token_protocol_honest(content: str) -> tuple[bool, str]:
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for recovery-token monitor"

    failures: list[str] = []
    relevant_seen = False

    def _request_token_get(call: ast.Call) -> bool:
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "get":
            return False
        owner = call.func.value
        owner_name = owner.id if isinstance(owner, ast.Name) else getattr(owner, "attr", "")
        if owner_name not in {"args", "form", "json", "values"}:
            return False
        if not call.args:
            return False
        key = call.args[0]
        return isinstance(key, ast.Constant) and isinstance(key.value, str) and any(bit in key.value.lower() for bit in ("token", "reset", "verify", "verification", "activation", "code"))

    def _is_sensitive_name(name: str) -> bool:
        return name in {"set_password", "update_password", "reset_password", "change_password", "mark_email_verified", "verify_email", "activate_user", "confirm_email"}

    validation_names = {"validate_reset_token", "verify_reset_token", "check_reset_token", "confirm_token", "validate_email_verification_token", "verify_email_token", "decode_reset_token", "lookup_reset_token", "lookup_verification_token"}
    expiry_names = {"validate_reset_token", "verify_reset_token", "check_reset_token", "confirm_token", "validate_email_verification_token", "verify_email_token", "assert_token_not_expired", "check_token_expiry", "check_token_age", "token_not_expired"}
    consume_names = {"consume_reset_token", "mark_token_used", "invalidate_reset_token", "delete_reset_token", "consume_verification_token", "mark_verification_used", "invalidate_verification_token", "revoke_verification_token"}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        token_vars: set[str] = {arg.arg for arg in node.args.args if any(bit in arg.arg.lower() for bit in ("token", "reset", "verify", "activation", "code"))}
        validation_lines: list[int] = []
        expiry_lines: list[int] = []
        consume_lines: list[int] = []
        sensitive_lines: list[int] = []
        return_lines: list[int] = []
        body_bits: list[str] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                if isinstance(child.value, ast.Call) and _request_token_get(child.value):
                    for t in child.targets:
                        if isinstance(t, ast.Name):
                            token_vars.add(t.id)
                            relevant_seen = True
                for t in child.targets:
                    if isinstance(t, ast.Attribute):
                        attr = t.attr.lower()
                        if attr in {"used", "consumed", "redeemed"} and isinstance(child.value, ast.Constant) and child.value.value is True:
                            consume_lines.append(getattr(child, "lineno", 0))
                            relevant_seen = True
                        if attr in {"email_verified", "verified", "is_verified", "active"} and isinstance(child.value, ast.Constant) and child.value.value is True:
                            sensitive_lines.append(getattr(child, "lineno", 0))
                            relevant_seen = True
            elif isinstance(child, ast.Call):
                line = getattr(child, "lineno", 0)
                func = child.func
                fname = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
                fname_low = fname.lower()
                if fname_low in validation_names:
                    validation_lines.append(line)
                    relevant_seen = True
                if fname_low in expiry_names:
                    expiry_lines.append(line)
                    relevant_seen = True
                if fname_low in consume_names:
                    consume_lines.append(line)
                    relevant_seen = True
                if _is_sensitive_name(fname_low):
                    sensitive_lines.append(line)
                    relevant_seen = True
                if any(bit in fname_low for bit in ("reset", "verify", "activation", "password", "email")):
                    relevant_seen = True
            elif isinstance(child, ast.Compare):
                names = {n.id.lower() for n in ast.walk(child) if isinstance(n, ast.Name)}
                attrs = {a.attr.lower() for a in ast.walk(child) if isinstance(a, ast.Attribute)}
                full = names | attrs
                if token_vars and (full & {tv.lower() for tv in token_vars} or any("token" in item or "reset" in item or "verify" in item for item in full)):
                    validation_lines.append(getattr(child, "lineno", 0))
                    relevant_seen = True
                if any(item in {"expires_at", "expires", "expiry", "expiration", "used", "consumed", "redeemed"} or "expire" in item for item in full):
                    expiry_lines.append(getattr(child, "lineno", 0))
                    relevant_seen = True
            elif isinstance(child, ast.Return):
                return_lines.append(getattr(child, "lineno", 0))
            elif isinstance(child, ast.Name):
                body_bits.append(child.id.lower())
            elif isinstance(child, ast.Attribute):
                body_bits.append(child.attr.lower())
            elif isinstance(child, ast.Constant) and isinstance(child.value, str):
                body_bits.append(child.value.lower())

        body_low = " ".join(body_bits)
        if not relevant_seen and not any(bit in node.name.lower() for bit in ("reset", "verify", "activate", "confirm")):
            continue

        if not sensitive_lines and not any(bit in body_low for bit in ("password", "verified", "verify_email", "activation")):
            continue
        relevant_seen = True
        if not sensitive_lines and any(bit in body_low for bit in ("password", "verified", "activation")):
            sensitive_lines = [getattr(node, "lineno", 0)]

        first_sensitive = min(sensitive_lines) if sensitive_lines else getattr(node, "lineno", 0)
        if not any(line < first_sensitive for line in validation_lines):
            failures.append(f"{node.name}: reset/verification token is not validated before sensitive account action")
            continue
        if not any(line < first_sensitive for line in expiry_lines):
            failures.append(f"{node.name}: reset/verification token has no explicit expiry/validity check before sensitive account action")
            continue

        if return_lines:
            needed_before = min(r for r in return_lines if r > first_sensitive) if any(r > first_sensitive for r in return_lines) else max(return_lines)
            if not any(line < needed_before for line in consume_lines):
                failures.append(f"{node.name}: reset/verification token is not consumed or invalidated before returning from sensitive account action")
                continue
        elif not consume_lines:
            failures.append(f"{node.name}: reset/verification token is not consumed or invalidated in the recovery flow")
            continue

    if not relevant_seen:
        return True, "no password-reset/email-verification token flow found"
    if failures:
        return False, "; ".join(failures[:4])
    return True, "recovery/verification tokens are validated, expiry-checked, and consumed before sensitive account completion"


def _must_validate_and_consume_recovery_token(artifact: Artifact, seed: MonitorSeed) -> tuple[bool, str]:
    return _recovery_token_protocol_honest(artifact.content)


_MONITOR_RUNNERS = {
    "must_contain": _must_contain,
    "must_not_contain": _must_not_contain,
    "must_close_resource": _must_close_resource,
    "must_establish_session_before_redirect": _must_establish_session_before_redirect,
    "must_finalize_transaction_after_write": _must_finalize_transaction_after_write,
    "must_harden_auth_cookies": _must_harden_auth_cookies,
    "must_validate_state_token_before_callback_use": _must_validate_state_token_before_callback_use,
    "must_clear_auth_state_on_logout": _must_clear_auth_state_on_logout,
    "must_rotate_or_revoke_refresh_token": _must_rotate_or_revoke_refresh_token,
    "must_preserve_refresh_token_family_integrity": _must_preserve_refresh_token_family_integrity,
    "must_validate_and_consume_recovery_token": _must_validate_and_consume_recovery_token,
}


class MonitorEngine:
    def run(self, artifact: Artifact, seeds: list[MonitorSeed]) -> list[MonitorEvent]:
        events: list[MonitorEvent] = []
        for seed in seeds:
            runner = _MONITOR_RUNNERS.get(seed.kind)
            if runner is None:
                ok = True
                message = f"unknown monitor kind '{seed.kind}' treated as pass"
            else:
                ok, message = runner(artifact, seed)
            events.append(
                MonitorEvent(
                    seed.monitor_id,
                    seed.requirement_id,
                    seed.severity,
                    "pass" if ok else "fail",
                    message,
                    artifact.artifact_id,
                    seed.claim_id,
                )
            )
        return events


def _auth_endpoint_rate_limited(content: str) -> tuple[bool, str]:
    """
    Auth endpoints must implement rate limiting to prevent brute-force attacks.

    Checks for presence of any rate-limiting signal in auth-like functions:
    - Import of flask_limiter, slowapi, ratelimit, django-ratelimit
    - @limiter.limit / @ratelimit / @throttle decorators
    - sleep() / time.sleep() (cheap man's rate limiting)
    - Any call to check_rate_limit / rate_limit / throttle

    This is a negative check: if an auth function has none of these, it fires.
    """
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for rate-limit monitor"

    _AUTH_FUNC_KEYWORDS = {"login", "signin", "authenticate", "verify_password",
                           "check_password", "validate_credentials"}
    _RATE_LIMIT_IMPORTS = {"flask_limiter", "slowapi", "ratelimit", "limits",
                           "django_ratelimit", "throttle", "redis"}
    _RATE_LIMIT_CALLS  = {"rate_limit", "ratelimit", "throttle", "check_rate_limit",
                          "is_rate_limited", "sleep", "time_sleep"}
    _RATE_LIMIT_DECO   = {"limit", "ratelimit", "throttle", "rate_limit", "shared_limit"}

    # Check imports first — if rate limiting library present anywhere, pass
    import_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_names.add(alias.name.split(".")[0].lower())
        elif isinstance(node, ast.ImportFrom) and node.module:
            import_names.add(node.module.split(".")[0].lower())

    if import_names & _RATE_LIMIT_IMPORTS:
        return True, "rate-limiting library imported"

    # Find auth-like functions and check for rate limiting signals within them
    failures: list[str] = []
    relevant_seen = False

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(k in node.name.lower() for k in _AUTH_FUNC_KEYWORDS):
            continue
        relevant_seen = True

        # Check decorators
        has_rate_limit = False
        for deco in node.decorator_list:
            deco_name = ""
            if isinstance(deco, ast.Name):
                deco_name = deco.id.lower()
            elif isinstance(deco, ast.Attribute):
                deco_name = deco.attr.lower()
            elif isinstance(deco, ast.Call):
                func = deco.func
                deco_name = (func.id if isinstance(func, ast.Name)
                             else func.attr if isinstance(func, ast.Attribute)
                             else "").lower()
            if deco_name in _RATE_LIMIT_DECO:
                has_rate_limit = True
                break

        if has_rate_limit:
            continue

        # Check calls inside function body
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            fname = (func.id if isinstance(func, ast.Name)
                     else func.attr if isinstance(func, ast.Attribute)
                     else "").lower()
            if fname in _RATE_LIMIT_CALLS:
                has_rate_limit = True
                break

        if not has_rate_limit:
            failures.append(
                f"{node.name}: auth function with no rate-limiting — "
                f"vulnerable to brute-force credential stuffing"
            )

    if not relevant_seen:
        return True, "no auth-like function found"
    if failures:
        return False, "; ".join(failures[:3])
    return True, "auth functions have rate-limiting controls"


def _must_rate_limit_auth_endpoint(artifact: "Artifact", seed: "MonitorSeed") -> tuple[bool, str]:
    return _auth_endpoint_rate_limited(artifact.content)


_MONITOR_RUNNERS["must_rate_limit_auth_endpoint"] = _must_rate_limit_auth_endpoint


# ── IDOR / Object Ownership Monitor ──────────────────────────────────────────
#
# Detects: functions that accept a resource ID from an external source
# (request args, route path params) and perform a database access
# without an ownership check — the canonical IDOR pattern.
#
# "User can reach the action" ≠ "User owns the object being acted on."
#
# Ownership signals accepted:
#   - current_user.id comparison
#   - owner_id in DB query filter
#   - abort(403) / PermissionDenied raise
#   - @owner_required decorator
#   - g.user / request.user check

import re as _re

_IDOR_REQUEST_ID = _re.compile(
    r'\b(?:request\.(?:args|form|json|view_args|data|values)\s*'
    r'(?:\.|\.get\s*\(|\[)|request\.get_json\s*\(\s*\))',
    _re.IGNORECASE,
)

_IDOR_ROUTE_DECORATOR = _re.compile(
    r'@(?:app|bp|router|api)\.(?:route|get|post|put|patch|delete)\b|'
    r'@require_http_methods\b',
    _re.IGNORECASE,
)

_IDOR_ROUTE_ID_PARAM = _re.compile(r'\b\w+_id\b')

_IDOR_DB_ACCESS = _re.compile(
    r'\b(?:\.get\s*\(|\.filter_by\s*\(|\.filter\s*\(|'
    r'\.find\s*\(|\.find_one\s*\(|\.query\s*\(|'
    r'\.objects\s*\.|SELECT\b)',
    _re.IGNORECASE,
)

_IDOR_OWNERSHIP = _re.compile(
    r'\b(?:current_user\.id\b|'
    r'g\.user(?:\.id)?\b|'
    r'request\.user(?:\.id)?\b|'
    r'owner_id\b|'
    r'user_id\s*==|'
    r'=\s*current_user\b|'
    r'filter_by\s*\(.*owner|'
    r'\.filter\s*\(.*owner_id\s*==\s*current_user|'
    r'check_ownership\b|verify_ownership\b|is_owner\b|'
    r'@owner_required\b|'
    r'abort\s*\(\s*403\b|'
    r'raise\s+(?:Forbidden|PermissionDenied|Http403|HTTPException))',
    _re.IGNORECASE,
)


def _object_ownership_enforced(content: str) -> tuple[bool, str]:
    """
    Resource access via external ID must enforce object-level ownership.

    Fires when a function:
    1. Receives a resource ID from request args/form/json OR a route path param
    2. Performs a database access
    3. Does NOT have a visible ownership check

    Returns (True, reason) if ownership is enforced or not applicable.
    Returns (False, reason) if IDOR pattern is detected.
    """
    # Quick pass — if no DB access at all, not applicable
    if not _IDOR_DB_ACCESS.search(content):
        return True, "no database access detected"

    has_request_id = bool(_IDOR_REQUEST_ID.search(content))
    has_route_id = (bool(_IDOR_ROUTE_DECORATOR.search(content)) and
                    bool(_IDOR_ROUTE_ID_PARAM.search(content)))

    resource_id_surface = has_request_id or has_route_id

    if not resource_id_surface:
        return True, "no externally-supplied resource ID detected"

    has_ownership = bool(_IDOR_OWNERSHIP.search(content))
    if has_ownership:
        return True, "object-level ownership check detected"

    source = "request parameter" if has_request_id else "route path parameter"
    return (
        False,
        f"resource ID from {source} used in database access "
        f"without visible ownership check — "
        f"any authenticated user may access any object (IDOR)"
    )


def _must_enforce_object_ownership(
    artifact: "Artifact", seed: "MonitorSeed"
) -> tuple[bool, str]:
    return _object_ownership_enforced(artifact.content)


_MONITOR_RUNNERS["must_enforce_object_ownership"] = _must_enforce_object_ownership
