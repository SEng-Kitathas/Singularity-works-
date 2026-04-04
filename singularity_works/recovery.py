from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import dataclass, field
import ast

from .models import MonitorSeed, RecoveryArtifact, Requirement



def _is_open_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Name) and func.id == "open"
    ) or (
        isinstance(func, ast.Attribute) and func.attr == "open"
    )


@dataclass
class RecoveryOutput:
    structures: list[RecoveryArtifact] = field(default_factory=list)
    monitor_seeds: list[MonitorSeed] = field(default_factory=list)
    radicals: list[str] = field(default_factory=list)
    family: str = "generic"
    confidence: str = "moderate"
    rationale: list[str] = field(default_factory=list)


class _ProtocolVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.transitions: dict[str, list[tuple[str, int]]] = {}
        self.dangerous_calls: list[str] = []
        self.has_open = False
        self.has_close = False
        self.has_with_open = False
        self.has_try_finally_close = False
        self.tokens: set[str] = set()
        self.session_lines: list[int] = []
        self.redirect_lines: list[int] = []
        self.cookie_lines: list[int] = []
        self.cookie_delete_lines: list[int] = []
        self.session_clear_lines: list[int] = []
        self.token_revoke_lines: list[int] = []
        self.logout_lines: list[int] = []
        self.refresh_issue_lines: list[int] = []
        self.refresh_rotation_lines: list[int] = []
        self.refresh_family_protect_lines: list[int] = []
        self.recovery_token_input_lines: list[int] = []
        self.recovery_token_validation_lines: list[int] = []
        self.recovery_token_expiry_lines: list[int] = []
        self.recovery_token_consume_lines: list[int] = []
        self.recovery_token_sensitive_use_lines: list[int] = []
        self.transaction_write_lines: list[int] = []
        self.commit_lines: list[int] = []
        self.rollback_lines: list[int] = []
        self.transaction_context_lines: list[int] = []
        self.state_input_lines: list[int] = []
        self.state_expected_lines: list[int] = []
        self.state_validation_lines: list[int] = []
        self.state_sensitive_use_lines: list[int] = []

    def _is_session_target(self, node: ast.AST) -> bool:
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

    def _const_str(self, node: ast.AST | None) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _is_request_state_get(self, call: ast.Call) -> bool:
        func = call.func
        if not (isinstance(func, ast.Attribute) and func.attr == "get"):
            return False
        key = None
        if call.args:
            key = self._const_str(call.args[0])
        if key is None:
            for kw in call.keywords:
                if kw.arg in {"key", "name"}:
                    key = self._const_str(kw.value)
                    if key is not None:
                        break
        if not (isinstance(key, str) and key.lower() in {"state", "csrf", "csrf_token"}):
            return False
        val = func.value
        if isinstance(val, ast.Attribute) and val.attr in {"args", "form", "values", "cookies", "query_params"}:
            return True
        return False

    def _is_session_state_read(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and self._is_session_target(node.func.value):
            key = None
            if node.args:
                key = self._const_str(node.args[0])
            if key is None:
                for kw in node.keywords:
                    if kw.arg in {"key", "name"}:
                        key = self._const_str(kw.value)
                        if key is not None:
                            break
            return isinstance(key, str) and any(bit in key.lower() for bit in ("state", "csrf"))
        if isinstance(node, ast.Subscript) and self._is_session_target(node.value):
            sl = node.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                return any(bit in sl.value.lower() for bit in ("state", "csrf"))
        return False

    def _is_request_token_get(self, call: ast.Call) -> bool:
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "get":
            return False
        owner = call.func.value
        owner_name = owner.id if isinstance(owner, ast.Name) else getattr(owner, "attr", "")
        if owner_name not in {"args", "form", "json", "values", "cookies", "headers"}:
            return False
        if not call.args:
            return False
        key = call.args[0]
        if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
            return False
        key_low = key.value.lower()
        return any(bit in key_low for bit in ("token", "reset", "verify", "verification", "activation", "code"))

    def _is_recovery_sensitive_call(self, name: str) -> bool:
        return name in {"set_password", "update_password", "reset_password", "change_password", "mark_email_verified", "verify_email", "activate_user", "confirm_email"}

    def _record(self, name: str, action: str, lineno: int) -> None:
        self.transitions.setdefault(name, []).append((action, lineno))
        self.tokens.add(action)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            ctx = item.context_expr
            if _is_open_call(ctx):
                self.has_with_open = True
                self.has_open = True
                if isinstance(item.optional_vars, ast.Name):
                    self._record(item.optional_vars.id, "open", node.lineno)
                    self._record(item.optional_vars.id, "close", getattr(node, "end_lineno", node.lineno))
            if isinstance(ctx, ast.Call) and isinstance(ctx.func, ast.Attribute):
                if ctx.func.attr in {"begin", "transaction"}:
                    self.transaction_context_lines.append(node.lineno)
                    self.tokens.add("transaction_context")
            elif isinstance(ctx, ast.Attribute) and ctx.attr in {"transaction"}:
                self.transaction_context_lines.append(node.lineno)
                self.tokens.add("transaction_context")
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        if node.finalbody:
            module = ast.Module(body=node.finalbody, type_ignores=[])
            for child in ast.walk(module):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    if child.func.attr == "close":
                        self.has_try_finally_close = True
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "open":
            self.has_open = True
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self._record(target.id, "open", node.lineno)
        for target in node.targets:
            if self._is_session_target(target):
                self.session_lines.append(node.lineno)
                self.tokens.add("session_write")
            if isinstance(target, ast.Name) and any(bit in target.id.lower() for bit in ("token", "reset", "verify", "activation", "code")):
                if isinstance(value, ast.Call) and self._is_request_token_get(value):
                    self.recovery_token_input_lines.append(node.lineno)
                    self.tokens.add("recovery_token_input")
            if isinstance(target, ast.Attribute):
                attr_low = target.attr.lower()
                if attr_low in {"used", "consumed", "redeemed"} and isinstance(value, ast.Constant) and value.value is True:
                    self.recovery_token_consume_lines.append(node.lineno)
                    self.tokens.add("recovery_token_consume")
                if attr_low in {"email_verified", "verified", "is_verified", "active"} and isinstance(value, ast.Constant) and value.value is True:
                    self.recovery_token_sensitive_use_lines.append(node.lineno)
                    self.tokens.add("recovery_sensitive_use")
        if isinstance(value, ast.Call) and self._is_request_state_get(value):
            self.state_input_lines.append(node.lineno)
            self.tokens.add("state_input")
        if self._is_session_state_read(value):
            self.state_expected_lines.append(node.lineno)
            self.tokens.add("state_expected")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name):
            self.tokens.add(func.id)
            if func.id in {"eval", "exec"}:
                self.dangerous_calls.append(func.id)
            if func.id == "redirect":
                self.redirect_lines.append(node.lineno)
                self.tokens.add("redirect")
            if func.id == "login_user":
                self.session_lines.append(node.lineno)
                self.tokens.add("session_write")
            if func.id in {"logout_user", "unset_jwt_cookies", "revoke_token", "revoke"}:
                self.logout_lines.append(node.lineno)
                self.token_revoke_lines.append(node.lineno)
                self.tokens.add("auth_clear")
            if func.id in {"create_refresh_token", "issue_refresh_token", "mint_refresh_token"}:
                self.refresh_issue_lines.append(node.lineno)
                self.tokens.add("refresh_issue")
            if func.id in {"exchange_code", "fetch_token", "authorize_access_token", "login_user", "create_access_token"}:
                self.state_sensitive_use_lines.append(node.lineno)
                self.tokens.add("state_sensitive_use")
            if func.id in {"validate_csrf", "validate_state", "verify_state", "compare_digest"}:
                self.state_validation_lines.append(node.lineno)
                self.tokens.add("state_validation")
            if func.id in {"revoke_refresh_token", "rotate_refresh_token", "blacklist_token", "blacklist_jti"}:
                self.refresh_rotation_lines.append(node.lineno)
                self.tokens.add("refresh_rotate")
            if func.id in {"revoke_token_family", "invalidate_refresh_family", "mark_refresh_reused", "check_refresh_reuse", "assert_refresh_family", "consume_refresh_token"}:
                self.refresh_family_protect_lines.append(node.lineno)
                self.tokens.add("refresh_family_protect")
            if func.id in {"validate_reset_token", "verify_reset_token", "check_reset_token", "confirm_token", "validate_email_verification_token", "verify_email_token", "decode_reset_token", "assert_token_not_expired", "check_token_expiry", "check_token_age"}:
                self.recovery_token_validation_lines.append(node.lineno)
                self.recovery_token_expiry_lines.append(node.lineno)
                self.tokens.add("recovery_token_validation")
                self.tokens.add("recovery_token_expiry")
            if func.id in {"consume_reset_token", "mark_token_used", "invalidate_reset_token", "delete_reset_token", "consume_verification_token", "mark_verification_used", "invalidate_verification_token", "revoke_verification_token"}:
                self.recovery_token_consume_lines.append(node.lineno)
                self.tokens.add("recovery_token_consume")
            if self._is_recovery_sensitive_call(func.id):
                self.recovery_token_sensitive_use_lines.append(node.lineno)
                self.tokens.add("recovery_sensitive_use")
        elif isinstance(func, ast.Attribute):
            action = func.attr
            self.tokens.add(action)
            if action == "close":
                self.has_close = True
            if action == "set_cookie":
                self.cookie_lines.append(node.lineno)
                self.tokens.add("cookie_set")
                cookie_name = None
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    cookie_name = node.args[0].value.lower()
                for kw in node.keywords:
                    if kw.arg == "key" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        cookie_name = kw.value.value.lower()
                if cookie_name and "refresh" in cookie_name:
                    self.refresh_issue_lines.append(node.lineno)
                    self.tokens.add("refresh_issue")
            if action == "delete_cookie":
                self.cookie_delete_lines.append(node.lineno)
                self.tokens.add("cookie_delete")
                cookie_name = None
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    cookie_name = node.args[0].value.lower()
                for kw in node.keywords:
                    if kw.arg == "key" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        cookie_name = kw.value.value.lower()
                if cookie_name and "refresh" in cookie_name:
                    self.refresh_rotation_lines.append(node.lineno)
                    self.tokens.add("refresh_rotate")
            if action == "redirect":
                self.redirect_lines.append(node.lineno)
                self.tokens.add("redirect")
            if action in {"clear", "pop"} and self._is_session_target(func.value):
                self.session_clear_lines.append(node.lineno)
                self.logout_lines.append(node.lineno)
                self.tokens.add("auth_clear")
            if action in {"unset_jwt_cookies", "revoke", "revoke_token"}:
                self.token_revoke_lines.append(node.lineno)
                self.logout_lines.append(node.lineno)
                self.tokens.add("auth_clear")
            if action in {"set_refresh_cookie", "set_refresh_cookies", "create_refresh_token", "issue_refresh_token", "mint_refresh_token"}:
                self.refresh_issue_lines.append(node.lineno)
                self.tokens.add("refresh_issue")
            if action in {"exchange_code", "fetch_token", "authorize_access_token", "create_access_token"}:
                self.state_sensitive_use_lines.append(node.lineno)
                self.tokens.add("state_sensitive_use")
            if action in {"validate_csrf", "validate_state", "verify_state"}:
                self.state_validation_lines.append(node.lineno)
                self.tokens.add("state_validation")
            if action in {"revoke_refresh_token", "rotate_refresh_token", "blacklist_token", "blacklist_jti"}:
                self.refresh_rotation_lines.append(node.lineno)
                self.tokens.add("refresh_rotate")
            if action in {"revoke_token_family", "invalidate_refresh_family", "mark_refresh_reused", "check_refresh_reuse", "assert_refresh_family", "consume_refresh_token"}:
                self.refresh_family_protect_lines.append(node.lineno)
                self.tokens.add("refresh_family_protect")
            if action in {"validate_reset_token", "verify_reset_token", "check_reset_token", "confirm_token", "validate_email_verification_token", "verify_email_token", "decode_reset_token", "assert_token_not_expired", "check_token_expiry", "check_token_age"}:
                self.recovery_token_validation_lines.append(node.lineno)
                self.recovery_token_expiry_lines.append(node.lineno)
                self.tokens.add("recovery_token_validation")
                self.tokens.add("recovery_token_expiry")
            if action in {"consume_reset_token", "mark_token_used", "invalidate_reset_token", "delete_reset_token", "consume_verification_token", "mark_verification_used", "invalidate_verification_token", "revoke_verification_token"}:
                self.recovery_token_consume_lines.append(node.lineno)
                self.tokens.add("recovery_token_consume")
            if self._is_recovery_sensitive_call(action):
                self.recovery_token_sensitive_use_lines.append(node.lineno)
                self.tokens.add("recovery_sensitive_use")
            if action == "commit":
                self.commit_lines.append(node.lineno)
                self.tokens.add("transaction_commit")
            if action == "rollback":
                self.rollback_lines.append(node.lineno)
                self.tokens.add("transaction_rollback")
            if action in {"add", "delete", "merge", "insert", "update"}:
                self.transaction_write_lines.append(node.lineno)
                self.tokens.add("transaction_write")
            if action in {"execute", "executemany", "executescript"}:
                sql_text = ""
                if node.args:
                    arg0 = node.args[0]
                    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                        sql_text = arg0.value.lower()
                if any(kw in sql_text for kw in ("insert", "update", "delete", "alter", "create", "drop")):
                    self.transaction_write_lines.append(node.lineno)
                    self.tokens.add("transaction_write")
            value = func.value
            if isinstance(value, ast.Name):
                self._record(value.id, action, node.lineno)
        for keyword in node.keywords:
            if keyword.arg == "verify" and isinstance(keyword.value, ast.Constant):
                if keyword.value.value is False:
                    self.dangerous_calls.append("verify_false")
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        test = node.test
        if isinstance(test, ast.Compare):
            left_state = self._is_session_state_read(test.left) or (isinstance(test.left, ast.Name) and "state" in test.left.id.lower())
            rights = list(test.comparators)
            right_state = any(self._is_session_state_read(r) or (isinstance(r, ast.Name) and "state" in r.id.lower()) for r in rights)
            if left_state and right_state:
                self.state_validation_lines.append(node.lineno)
                self.tokens.add("state_validation")
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        names = {n.id.lower() for n in ast.walk(node) if isinstance(n, ast.Name)}
        attrs = {a.attr.lower() for a in ast.walk(node) if isinstance(a, ast.Attribute)}
        full = names | attrs
        left_state = self._is_session_state_read(node.left) or (isinstance(node.left, ast.Name) and "state" in node.left.id.lower())
        right_state = any(self._is_session_state_read(r) or (isinstance(r, ast.Name) and "state" in r.id.lower()) for r in node.comparators)
        if left_state and right_state:
            self.state_validation_lines.append(getattr(node, "lineno", 0))
            self.tokens.add("state_validation")
        if any(bit in item for item in full for bit in ("token", "reset", "verify", "activation")):
            self.recovery_token_validation_lines.append(getattr(node, "lineno", 0))
            self.tokens.add("recovery_token_validation")
        if any(item in {"expires_at", "expires", "expiry", "expiration", "used", "consumed", "redeemed"} or "expire" in item for item in full):
            self.recovery_token_expiry_lines.append(getattr(node, "lineno", 0))
            self.tokens.add("recovery_token_expiry")
        self.generic_visit(node)


class RecoveryEngine:
    def _safe_parse(self, content: str):
        try:
            return ast.parse(content) if content.strip() else None
        except SyntaxError:
            return None

    def _requirement_flags(self, low: str) -> dict[str, bool]:
        return {
            "protocol": any(k in low for k in ["protocol", "state", "transition", "handshake"]),
            "parser": any(k in low for k in ["parse", "parser", "parsing", "grammar", "input", "literal_eval"]),
            "resource": any(k in low for k in ["close", "release", "cleanup", "file", "file handle", "connection pool", "socket", "open file"]),
            "danger": any(k in low for k in ["dangerous", "eval", "exec", "unsafe"]),
            "verification": any(k in low for k in ["verify", "verification", "certificate", "tls", "ssl"]),
            "todo_forbidden": "todo" in low,
            "auth": any(k in low for k in ["auth", "login", "logout", "signout", "session", "cookie", "token", "redirect", "revoke"]),
            "transaction": any(k in low for k in ["transaction", "commit", "rollback", "database", "db write", "atomic", "sql"]),
            "recovery_token": any(k in low for k in ["password reset", "reset token", "email verification", "verify email", "activation token", "one-time token", "recovery token", "password change", "account verification"]),
            "rate_limit": any(k in low for k in ["rate limit", "rate-limit", "brute force", "brute-force", "throttle", "slow down", "attempts", "lockout"]),
            "idor": any(k in low for k in ["idor", "insecure direct object", "object ownership", "ownership", "access control", "authorization", "owns", "owner", "belong", "permission"]),
        }

    def _append_structure(
        self,
        structures: list[RecoveryArtifact],
        structure_id: str,
        structure_type: str,
        confidence: str,
        requirement: Requirement,
        radicals: list[str],
        payload: dict,
    ) -> None:
        structures.append(
            RecoveryArtifact(
                structure_id,
                structure_type,
                confidence,
                [requirement.requirement_id],
                radicals,
                payload,
            )
        )

    def _monitor_seed(
        self,
        requirement: Requirement,
        suffix: str,
        kind: str,
        expr: str,
        severity: str,
        claim: str,
    ) -> MonitorSeed:
        return MonitorSeed(
            f"monitor:{requirement.requirement_id}:{suffix}",
            requirement.requirement_id,
            kind,
            expr,
            severity,
            ["artifact.content"],
            claim,
            "high",
        )

    def _protocol_analysis(self, tree) -> dict:
        out = {
            "has_open": False,
            "has_close": False,
            "has_with_open": False,
            "has_try_finally_close": False,
            "dangerous_calls": [],
            "tokens": set(),
            "transition_graph": {},
            "session_lines": [],
            "redirect_lines": [],
            "cookie_lines": [],
            "cookie_delete_lines": [],
            "session_clear_lines": [],
            "token_revoke_lines": [],
            "logout_lines": [],
            "refresh_issue_lines": [],
            "refresh_rotation_lines": [],
            "refresh_family_protect_lines": [],
            "recovery_token_input_lines": [],
            "recovery_token_validation_lines": [],
            "recovery_token_expiry_lines": [],
            "recovery_token_consume_lines": [],
            "recovery_token_sensitive_use_lines": [],
            "transaction_write_lines": [],
            "commit_lines": [],
            "rollback_lines": [],
            "transaction_context_lines": [],
            "state_input_lines": [],
            "state_expected_lines": [],
            "state_validation_lines": [],
            "state_sensitive_use_lines": [],
        }
        if tree is None:
            return out
        visitor = _ProtocolVisitor()
        visitor.visit(tree)
        out["has_open"] = visitor.has_open
        out["has_close"] = visitor.has_close
        out["has_with_open"] = visitor.has_with_open
        out["has_try_finally_close"] = visitor.has_try_finally_close
        out["dangerous_calls"] = visitor.dangerous_calls
        out["tokens"] = visitor.tokens
        out["transition_graph"] = {
            name: [action for action, _ in seq]
            for name, seq in visitor.transitions.items()
        }
        out["session_lines"] = visitor.session_lines
        out["redirect_lines"] = visitor.redirect_lines
        out["cookie_lines"] = visitor.cookie_lines
        out["cookie_delete_lines"] = visitor.cookie_delete_lines
        out["session_clear_lines"] = visitor.session_clear_lines
        out["token_revoke_lines"] = visitor.token_revoke_lines
        out["logout_lines"] = visitor.logout_lines
        out["refresh_issue_lines"] = visitor.refresh_issue_lines
        out["refresh_rotation_lines"] = visitor.refresh_rotation_lines
        out["refresh_family_protect_lines"] = visitor.refresh_family_protect_lines
        out["recovery_token_input_lines"] = visitor.recovery_token_input_lines
        out["recovery_token_validation_lines"] = visitor.recovery_token_validation_lines
        out["recovery_token_expiry_lines"] = visitor.recovery_token_expiry_lines
        out["recovery_token_consume_lines"] = visitor.recovery_token_consume_lines
        out["recovery_token_sensitive_use_lines"] = visitor.recovery_token_sensitive_use_lines
        out["transaction_write_lines"] = visitor.transaction_write_lines
        out["commit_lines"] = visitor.commit_lines
        out["rollback_lines"] = visitor.rollback_lines
        out["transaction_context_lines"] = visitor.transaction_context_lines
        out["state_input_lines"] = visitor.state_input_lines
        out["state_expected_lines"] = visitor.state_expected_lines
        out["state_validation_lines"] = visitor.state_validation_lines
        out["state_sensitive_use_lines"] = visitor.state_sensitive_use_lines
        return out

    def _baseline_structures(
        self,
        flags: dict[str, bool],
        requirement: Requirement,
        structures: list[RecoveryArtifact],
        radicals: list[str],
        rationale: list[str],
    ) -> tuple[str, int]:
        family = "generic"
        gain = 0
        if flags["protocol"]:
            radicals += ["STATE", "TRUST"]
            family = "protocol"
            self._append_structure(
                structures,
                "recovered:protocol",
                "protocol",
                "moderate",
                requirement,
                ["STATE"],
                {"kind": "protocol_hint"},
            )
            rationale.append("requirement mentions protocol/state concepts")
            gain += 1
        if flags["parser"]:
            radicals += ["PARSE", "STATE"]
            family = "parser"
            self._append_structure(
                structures,
                "recovered:grammar",
                "grammar",
                "moderate",
                requirement,
                ["PARSE"],
                {"kind": "grammar_hint"},
            )
            rationale.append("requirement mentions parsing/grammar concepts")
            gain += 1
        if flags["auth"]:
            radicals += ["STATE", "TRUST"]
            if family == "generic":
                family = "auth_protocol"
            self._append_structure(
                structures,
                "recovered:auth_protocol",
                "auth_protocol",
                "moderate",
                requirement,
                ["STATE", "TRUST"],
                {"kind": "auth_session_redirect_hint"},
            )
            rationale.append("requirement mentions auth/session/redirect concepts")
            gain += 1
        if flags.get("recovery_token"):
            radicals += ["STATE", "TRUST", "VERIFY"]
            if family == "generic":
                family = "auth_protocol"
            self._append_structure(
                structures,
                "recovered:recovery_token_protocol",
                "auth_protocol",
                "moderate",
                requirement,
                ["STATE", "TRUST", "VERIFY"],
                {"kind": "reset_verify_token_hint"},
            )
            rationale.append("requirement mentions password-reset/email-verification token protocol")
            gain += 1
        if flags["resource"]:
            radicals += ["RESOURCE", "TRUST"]
            self._append_structure(
                structures,
                "recovered:resource",
                "resource_protocol",
                "high",
                requirement,
                ["RESOURCE"],
                {"kind": "resource_hint"},
            )
            rationale.append("requirement mentions resource discipline")
            gain += 1
        if flags["danger"]:
            # Security-semantic requirement: well-defined, recoverable from text
            radicals += ["TRUST"]
            rationale.append("requirement defines dangerous-execution safety contract")
            gain += 1
        if flags["verification"]:
            # Verification-semantic requirement: explicit trust chain contract
            radicals += ["TRUST"]
            rationale.append("requirement defines verification/trust-chain contract")
            gain += 1
        return family, gain

    def _code_structures(
        self,
        analysis: dict,
        flags: dict[str, bool],
        requirement: Requirement,
        structures: list[RecoveryArtifact],
        radicals: list[str],
        rationale: list[str],
    ) -> int:
        gain = 0
        tokens = {token.lower() for token in analysis["tokens"]}
        if flags["protocol"] and (tokens & {"state", "transition", "handshake", "connect", "close"}):
            rationale.append("candidate code reflects protocol/state terminology")
            gain += 1
        if flags["parser"] and (tokens & {"literal_eval", "parse", "loads"}):
            rationale.append("candidate code reflects parser/safe parsing terminology")
            gain += 1
        if analysis["has_open"]:
            radicals += ["RESOURCE"]
            resource_conf = "high" if (
                analysis["has_close"]
                or analysis["has_with_open"]
                or analysis["has_try_finally_close"]
            ) else "moderate"
            self._append_structure(
                structures,
                "recovered:resource_from_code",
                "resource_protocol",
                resource_conf,
                requirement,
                ["RESOURCE"],
                {
                    "from_code": True,
                    "protocol_kind": "resource_lifecycle",
                    "allowed_edges": [
                        ["open", "read"], ["open", "write"], ["open", "close"],
                        ["read", "read"], ["read", "write"], ["read", "close"],
                        ["write", "write"], ["write", "read"], ["write", "close"],
                    ],
                    "forbidden_edges": [["close", "read"], ["close", "write"], ["close", "close"]],
                    "transition_graph": analysis["transition_graph"],
                    "close_seen": analysis["has_close"],
                    "with_open_seen": analysis["has_with_open"],
                    "try_finally_close_seen": analysis["has_try_finally_close"],
                },
            )
            rationale.append("candidate code exposes a resource lifecycle")
            gain += 1 + (1 if resource_conf == "high" else 0)
        if analysis["dangerous_calls"]:
            radicals += ["TRUST"]
            self._append_structure(
                structures,
                "recovered:trust_boundary",
                "trust_boundary",
                "moderate",
                requirement,
                ["TRUST"],
                {"dangerous_calls": sorted(set(analysis["dangerous_calls"]))},
            )
            rationale.append("candidate code contains dangerous execution primitives")
            gain += 1  # characterizing security-relevant behavior is a recovery signal
        elif flags["danger"] and not analysis["dangerous_calls"]:
            # Danger-flagged requirement, code is clean — strong compliance signal
            radicals += ["TRUST"]
            rationale.append("candidate code is clean against danger-flagged requirement")
            gain += 1
        if flags["danger"] and "literal_eval" in tokens:
            radicals += ["TRUST", "PARSE"]
            self._append_structure(
                structures,
                "recovered:safe_literal_eval",
                "trust_boundary",
                "high",
                requirement,
                ["TRUST", "PARSE"],
                {"safe_call": "literal_eval", "dangerous_calls": []},
            )
            rationale.append("candidate code uses literal_eval instead of dangerous execution")
            gain += 2
        if flags.get("transaction") and analysis.get("transaction_write_lines"):
            tx_conf = "high" if (analysis.get("commit_lines") or analysis.get("rollback_lines") or analysis.get("transaction_context_lines")) else "moderate"
            self._append_structure(
                structures,
                "recovered:transaction_flow",
                "transaction_protocol",
                tx_conf,
                requirement,
                ["STATE", "RESOURCE", "TRUST"],
                {
                    "transaction_write_lines": analysis.get("transaction_write_lines", []),
                    "commit_lines": analysis.get("commit_lines", []),
                    "rollback_lines": analysis.get("rollback_lines", []),
                    "transaction_context_lines": analysis.get("transaction_context_lines", []),
                },
            )
            rationale.append("candidate code exposes database write / transaction flow")
            gain += 1 + (1 if tx_conf == "high" else 0)
        if flags["auth"] and analysis.get("redirect_lines"):
            auth_conf = "high" if (analysis.get("session_lines") or analysis.get("cookie_lines")) else "moderate"
            self._append_structure(
                structures,
                "recovered:auth_session_flow",
                "auth_protocol",
                auth_conf,
                requirement,
                ["STATE", "TRUST"],
                {
                    "session_lines": analysis.get("session_lines", []),
                    "redirect_lines": analysis.get("redirect_lines", []),
                    "cookie_lines": analysis.get("cookie_lines", []),
                },
            )
            rationale.append("candidate code exposes auth/session/redirect flow")
            gain += 1 + (1 if auth_conf == "high" else 0)
        if flags["auth"] and analysis.get("cookie_lines"):
            cookie_conf = "high"
            self._append_structure(
                structures,
                "recovered:auth_cookie_surface",
                "auth_protocol",
                cookie_conf,
                requirement,
                ["TRUST", "VERIFY"],
                {
                    "cookie_lines": analysis.get("cookie_lines", []),
                    "tokens": sorted(analysis.get("tokens", set())),
                },
            )
            rationale.append("candidate code exposes auth/session/token cookie surface")
            gain += 1
        return gain  # total gain feeds confidence_score in derive()

    def derive(self, requirement: Requirement, candidate_content: str = "") -> RecoveryOutput:
        low = requirement.text.lower()
        flags = self._requirement_flags(low)
        radicals: list[str] = []
        structures: list[RecoveryArtifact] = []
        monitor_seeds: list[MonitorSeed] = []
        rationale: list[str] = []
        confidence_score = 1

        tree = self._safe_parse(candidate_content)
        if candidate_content.strip() and tree is None:
            rationale.append("candidate content did not parse during recovery")
        analysis = self._protocol_analysis(tree)

        family, gain = self._baseline_structures(flags, requirement, structures, radicals, rationale)
        confidence_score += gain
        confidence_score += self._code_structures(
            analysis, flags, requirement, structures, radicals, rationale
        )

        radicals = sorted(set(radicals or ["TRUST"]))
        contains_map = {
            "must not contain todo": ("must_not_contain", "todo", "high"),
            "must not contain eval": ("must_not_contain", "eval(", "high"),
            "dangerous execution primitives should be absent": ("must_not_contain", "exec(", "high"),
        }
        for phrase, (kind, expr, sev) in contains_map.items():
            if phrase not in low:
                continue
            suffix = expr.replace("(", "").replace(" ", "_")
            claim_id = f"claim:{requirement.requirement_id}:{suffix}"
            monitor_seeds.append(
                self._monitor_seed(requirement, suffix, kind, expr, sev, claim_id)
            )

        if flags["resource"] or (analysis["has_open"] and "close" in low):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "resource_close",
                    "must_close_resource",
                    "resource-close",
                    "high",
                    f"claim:{requirement.requirement_id}:resource_close",
                )
            )

        if flags["danger"]:
            for suffix, expr in [("no_eval", "eval("), ("no_exec", "exec(")]:
                monitor_seeds.append(
                    self._monitor_seed(
                        requirement,
                        suffix,
                        "must_not_contain",
                        expr,
                        "high",
                        f"claim:{requirement.requirement_id}:{suffix}",
                    )
                )
            if not analysis["dangerous_calls"]:
                rationale.append("candidate code avoids dangerous execution primitives")
                confidence_score += 1

        if flags["verification"]:
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "verify_enabled",
                    "must_not_contain",
                    "verify=False",
                    "high",
                    f"claim:{requirement.requirement_id}:verify_enabled",
                )
            )
            if "verify_false" not in analysis["dangerous_calls"]:
                rationale.append("candidate code keeps verification enabled")
                confidence_score += 1


        is_logout_like = any(k in low for k in ["logout", "signout", "revoke"])

        if flags["auth"] and not is_logout_like and (("redirect" in low and "session" in low) or "login" in low or "auth" in low):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "auth_session_before_redirect",
                    "must_establish_session_before_redirect",
                    "auth-session-before-redirect",
                    "high",
                    f"claim:{requirement.requirement_id}:auth_session_before_redirect",
                )
            )
            if analysis.get("redirect_lines") and (analysis.get("session_lines") or analysis.get("cookie_lines")):
                rationale.append("candidate code establishes session/cookie before auth redirect")
                confidence_score += 1

        if flags["auth"] and ("cookie" in low or "token" in low or analysis.get("cookie_lines")):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "auth_cookie_hardening",
                    "must_harden_auth_cookies",
                    "auth-cookie-hardening",
                    "high",
                    f"claim:{requirement.requirement_id}:auth_cookie_hardening",
                )
            )
            if analysis.get("cookie_lines"):
                rationale.append("candidate code sets cookies in an auth/session/token context")
                confidence_score += 1

        if flags["auth"] and (any(k in low for k in ["refresh", "rotate", "renew"]) or analysis.get("refresh_issue_lines") or analysis.get("refresh_rotation_lines")):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "refresh_rotation",
                    "must_rotate_or_revoke_refresh_token",
                    "refresh-token-rotation",
                    "high",
                    f"claim:{requirement.requirement_id}:refresh_rotation",
                )
            )
            if analysis.get("refresh_issue_lines"):
                rationale.append("candidate code participates in refresh-token issuance/rotation flow")
                confidence_score += 1

        if flags["auth"] and (any(k in low for k in ["refresh", "family", "reuse", "replay"]) or analysis.get("refresh_family_protect_lines")):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "refresh_family_integrity",
                    "must_preserve_refresh_token_family_integrity",
                    "refresh-token-family-integrity",
                    "high",
                    f"claim:{requirement.requirement_id}:refresh_family_integrity",
                )
            )
            if analysis.get("refresh_issue_lines") or analysis.get("refresh_family_protect_lines"):
                rationale.append("candidate code participates in refresh-token family/reuse integrity flow")
                confidence_score += 1


        if flags["auth"] and (any(k in low for k in ["state", "csrf", "callback", "oauth"]) or analysis.get("state_input_lines") or analysis.get("state_sensitive_use_lines")):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "callback_state_validation",
                    "must_validate_state_token_before_callback_use",
                    "callback-state-validation",
                    "high",
                    f"claim:{requirement.requirement_id}:callback_state_validation",
                )
            )
            if analysis.get("state_input_lines") and analysis.get("state_validation_lines"):
                rationale.append("candidate code reads callback state and performs explicit state/csrf validation before sensitive continuation")
                confidence_score += 1

        if (flags.get("recovery_token") or analysis.get("recovery_token_input_lines") or analysis.get("recovery_token_sensitive_use_lines")):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "recovery_token_protocol",
                    "must_validate_and_consume_recovery_token",
                    "recovery-token-protocol",
                    "high",
                    f"claim:{requirement.requirement_id}:recovery_token_protocol",
                )
            )
            if analysis.get("recovery_token_validation_lines") and analysis.get("recovery_token_consume_lines"):
                rationale.append("candidate code validates and consumes reset/verification token in a sensitive account-recovery flow")
                confidence_score += 1

        if flags["auth"] and (any(k in low for k in ["logout", "signout", "revoke"]) or analysis.get("cookie_delete_lines") or analysis.get("session_clear_lines") or analysis.get("token_revoke_lines") or analysis.get("logout_lines")):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "auth_logout_clearance",
                    "must_clear_auth_state_on_logout",
                    "auth-logout-clearance",
                    "high",
                    f"claim:{requirement.requirement_id}:auth_logout_clearance",
                )
            )
            if analysis.get("cookie_delete_lines") or analysis.get("session_clear_lines") or analysis.get("token_revoke_lines"):
                rationale.append("candidate code clears session/cookies or revokes tokens in an auth logout/revoke context")
                confidence_score += 1

        if flags.get("transaction") and (analysis.get("transaction_write_lines") or "database" in low or "sql" in low):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "transaction_finalized",
                    "must_finalize_transaction_after_write",
                    "transaction-finalized",
                    "high",
                    f"claim:{requirement.requirement_id}:transaction_finalized",
                )
            )
            if analysis.get("transaction_write_lines") and (analysis.get("commit_lines") or analysis.get("rollback_lines") or analysis.get("transaction_context_lines")):
                rationale.append("candidate code finalizes transaction after database write or uses a managed transaction context")
                confidence_score += 1

        if flags.get("rate_limit") and flags.get("auth"):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "auth_rate_limiting",
                    "must_rate_limit_auth_endpoint",
                    "auth-rate-limiting",
                    "high",
                    f"claim:{requirement.requirement_id}:auth_rate_limiting",
                )
            )

        if flags.get("idor"):
            monitor_seeds.append(
                self._monitor_seed(
                    requirement,
                    "object_ownership",
                    "must_enforce_object_ownership",
                    "object-ownership",
                    "high",
                    f"claim:{requirement.requirement_id}:object_ownership",
                )
            )

        if flags["todo_forbidden"] and "todo" not in candidate_content.lower():
            rationale.append("candidate code avoids todo markers")
            confidence_score += 1

        confidence = "low"
        if confidence_score >= 5:
            confidence = "high"
        elif confidence_score >= 3:
            confidence = "moderate"

        return RecoveryOutput(
            structures=structures,
            monitor_seeds=monitor_seeds,
            radicals=radicals,
            family=family,
            confidence=confidence,
            rationale=rationale,
        )
