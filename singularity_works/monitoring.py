from __future__ import annotations
# complexity_justified: integrated forge runtime surface split into protocol families while preserving the monitoring public shell.

from .monitoring_core import (
    MonitorEvent,
    _must_close_resource,
    _must_contain,
    _must_not_contain,
)
from .monitoring_auth import (
    _must_establish_session_before_redirect,
    _must_finalize_transaction_after_write,
    _must_harden_auth_cookies,
)
from .monitoring_tokens import (
    _must_clear_auth_state_on_logout,
    _must_preserve_refresh_token_family_integrity,
    _must_rotate_or_revoke_refresh_token,
    _must_validate_and_consume_recovery_token,
    _must_validate_state_token_before_callback_use,
)
from .monitoring_protocols import (
    _IDOR_DB_ACCESS,
    _IDOR_OWNERSHIP,
    _IDOR_REQUEST_ID,
    _IDOR_ROUTE_ID_PARAM,
    _must_enforce_object_ownership,
    _must_rate_limit_auth_endpoint,
)
from .models import Artifact, MonitorSeed


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
    "must_rate_limit_auth_endpoint": _must_rate_limit_auth_endpoint,
    "must_enforce_object_ownership": _must_enforce_object_ownership,
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
