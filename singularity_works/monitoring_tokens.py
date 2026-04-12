from __future__ import annotations

import ast

from .models import Artifact, MonitorSeed
from .monitoring_core import _safe_parse


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


