from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from forge_app.connection_gate import (
    AuthorityDecision,
    ConnectionAuthorityStateStore,
    ConsequenceClass,
    ConnectorPolicy,
    CredentialCeiling,
    ExternalOperationLifecycleStore,
    IntentSource,
    LifecycleState,
    OperationLifecycleError,
    OperationRequest,
    ProviderIdentity,
    RemoteOutcome,
    SessionArming,
    UserGrant,
    VerificationState,
)
from forge_app.recovery import AttemptStore


RESOURCE = "github:SEng-Kitathas/Singularity-works-:branch:forge/app-shell-rd"


class OperationLifecycleReconciliationV01Tests(unittest.TestCase):
    def env(self, td: str):
        store = AttemptStore(Path(td) / "store")
        state = ConnectionAuthorityStateStore(store)
        state.register_provider(ProviderIdentity("github", "subject-1", VerificationState.VERIFIED))
        state.register_credential_ceiling(
            CredentialCeiling("cred-1", "github", "subject-1", ("repo.read", "repo.push"), ("*",))
        )
        state.register_policy(
            ConnectorPolicy("policy-1", "github-app", "github", ("repo.read",), (RESOURCE,), ConsequenceClass.READ)
        )
        state.register_grant(
            UserGrant("grant-1", "operator-1", "github", "github-app", ("repo.read",), (RESOURCE,), ConsequenceClass.READ)
        )
        state.register_arming(
            SessionArming("arming-1", "operator-1", "github", "github-app", ("repo.read",), (RESOURCE,), ConsequenceClass.READ, None, True, True)
        )
        lifecycle = ExternalOperationLifecycleStore(state)
        return store, state, lifecycle

    def prepare(self, state: ConnectionAuthorityStateStore, lifecycle: ExternalOperationLifecycleStore, operation_id: str):
        request_id = f"request-{operation_id}"
        request = OperationRequest(
            request_id,
            "operator-1",
            "github",
            "github-app",
            "repo.read",
            RESOURCE,
            ConsequenceClass.READ,
            "operation lifecycle hostile test",
            IntentSource.OPERATOR,
        )
        decision = state.evaluate_and_persist(
            request,
            provider_subject_id="subject-1",
            credential_id="cred-1",
            policy_id="policy-1",
            grant_id="grant-1",
            arming_id="arming-1",
        )
        self.assertEqual(decision.gate_receipt.decision, AuthorityDecision.ALLOW)
        prepared = state.prepare_operation(
            operation_id=operation_id,
            request_id=request_id,
            decision_attempt_id=decision.attempt_id,
        )
        operation = lifecycle.register_operation(
            operation_id=operation_id,
            prepared_operation_attempt_id=prepared.attempt_id,
            provider_id="github",
            connector_id="github-app",
            resource=RESOURCE,
            capability="repo.read",
            effect_fingerprint=f"effect:{operation_id}:v1",
        )
        return decision, prepared, operation

    def test_exact_transition_replay_idempotent_and_conflict_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, lifecycle = self.env(td)
            self.prepare(state, lifecycle, "op-replay")
            first = lifecycle.transition("op-replay", LifecycleState.SUBMITTED, transition_id="submit-1", detail={"transport":"sim"})
            replay = lifecycle.transition("op-replay", LifecycleState.SUBMITTED, transition_id="submit-1", detail={"transport":"sim"})
            self.assertEqual(first["event_id"], replay["event_id"])
            with self.assertRaisesRegex(OperationLifecycleError, "transition ID conflict"):
                lifecycle.transition("op-replay", LifecycleState.SUBMITTED, transition_id="submit-1", detail={"transport":"different"})

    def test_illegal_terminal_branch_switch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, lifecycle = self.env(td)
            self.prepare(state, lifecycle, "op-failed")
            lifecycle.transition("op-failed", LifecycleState.SUBMITTED, transition_id="submit")
            lifecycle.transition("op-failed", LifecycleState.FAILED_LOCAL, transition_id="failed")
            with self.assertRaisesRegex(OperationLifecycleError, "illegal lifecycle transition"):
                lifecycle.transition("op-failed", LifecycleState.COMPLETED_LOCAL, transition_id="completed-late")

    def test_authority_revoke_after_prepared_blocks_submission(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, lifecycle = self.env(td)
            self.prepare(state, lifecycle, "op-revoke")
            state.revoke_grant("grant-1", revocation_id="revoke-before-submit", reason="manual revoke")
            with self.assertRaisesRegex(OperationLifecycleError, "OLD_ALLOW_RECEIPT"):
                lifecycle.transition("op-revoke", LifecycleState.SUBMITTED, transition_id="submit")
            self.assertEqual(lifecycle.inspect("op-revoke").state, LifecycleState.PREPARED)

    def test_unknown_outcome_blocks_blind_resubmission(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, lifecycle = self.env(td)
            _, _, op = self.prepare(state, lifecycle, "op-unknown")
            lifecycle.transition("op-unknown", LifecycleState.SUBMITTED, transition_id="submit")
            lifecycle.transition("op-unknown", LifecycleState.UNKNOWN_OUTCOME, transition_id="unknown")
            with self.assertRaisesRegex(OperationLifecycleError, "blind resubmission"):
                lifecycle.transition("op-unknown", LifecycleState.SUBMITTED, transition_id="submit-again")
            self.assertTrue(op.idempotency_key.startswith("sw-op-"))

    def test_unknown_committed_reconciliation_closes_operation_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, lifecycle = self.env(td)
            _, _, op = self.prepare(state, lifecycle, "op-committed")
            lifecycle.transition("op-committed", LifecycleState.SUBMITTED, transition_id="submit")
            lifecycle.transition("op-committed", LifecycleState.UNKNOWN_OUTCOME, transition_id="unknown")
            lifecycle.observe_remote(
                "op-committed", RemoteOutcome.COMMITTED,
                observation_id="observe-committed", observed_idempotency_key=op.idempotency_key,
                source="simulated-provider-ledger", remote_identity={"remote_id":"remote-1"},
            )
            self.assertEqual(lifecycle.inspect("op-committed").state, LifecycleState.REMOTE_OBSERVED_COMMITTED)
            with self.assertRaisesRegex(OperationLifecycleError, "blind resubmission|illegal lifecycle"):
                lifecycle.transition("op-committed", LifecycleState.SUBMITTED, transition_id="retry")

    def test_absent_reconciliation_requires_explicit_replay_authorization_and_same_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, lifecycle = self.env(td)
            _, _, op = self.prepare(state, lifecycle, "op-absent")
            lifecycle.transition("op-absent", LifecycleState.SUBMITTED, transition_id="submit-1")
            lifecycle.transition("op-absent", LifecycleState.UNKNOWN_OUTCOME, transition_id="unknown-1")
            lifecycle.observe_remote(
                "op-absent", RemoteOutcome.ABSENT,
                observation_id="observe-absent", observed_idempotency_key=op.idempotency_key,
                source="simulated-provider-ledger",
            )
            self.assertEqual(lifecycle.inspect("op-absent").state, LifecycleState.REMOTE_OBSERVED_ABSENT)
            with self.assertRaisesRegex(OperationLifecycleError, "RETRY_AFTER_UNKNOWN"):
                lifecycle.transition("op-absent", LifecycleState.SUBMITTED, transition_id="retry-before-auth")
            auth1 = lifecycle.authorize_replay_after_absence("op-absent", authorization_id="replay-auth-1", reason="remote absence proven")
            auth2 = lifecycle.authorize_replay_after_absence("op-absent", authorization_id="replay-auth-1", reason="remote absence proven")
            self.assertEqual(auth1["event_id"], auth2["event_id"])
            lifecycle.transition("op-absent", LifecycleState.SUBMITTED, transition_id="submit-2")
            after = lifecycle.inspect("op-absent")
            self.assertEqual(after.state, LifecycleState.SUBMITTED)
            self.assertEqual(after.operation.idempotency_key, op.idempotency_key)
            self.assertEqual(after.operation.operation_id, op.operation_id)

    def test_stale_authority_blocks_replay_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, lifecycle = self.env(td)
            _, _, op = self.prepare(state, lifecycle, "op-stale-replay")
            lifecycle.transition("op-stale-replay", LifecycleState.SUBMITTED, transition_id="submit")
            lifecycle.transition("op-stale-replay", LifecycleState.UNKNOWN_OUTCOME, transition_id="unknown")
            lifecycle.observe_remote(
                "op-stale-replay", RemoteOutcome.ABSENT,
                observation_id="absent", observed_idempotency_key=op.idempotency_key,
                source="simulated-provider-ledger",
            )
            state.revoke_grant("grant-1", revocation_id="revoke-before-replay", reason="manual revoke")
            with self.assertRaisesRegex(OperationLifecycleError, "OLD_ALLOW_RECEIPT"):
                lifecycle.authorize_replay_after_absence("op-stale-replay", authorization_id="auth", reason="should fail")

    def test_wrong_remote_idempotency_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, lifecycle = self.env(td)
            self.prepare(state, lifecycle, "op-wrong-remote")
            lifecycle.transition("op-wrong-remote", LifecycleState.SUBMITTED, transition_id="submit")
            lifecycle.transition("op-wrong-remote", LifecycleState.UNKNOWN_OUTCOME, transition_id="unknown")
            with self.assertRaisesRegex(OperationLifecycleError, "idempotency identity mismatch"):
                lifecycle.observe_remote(
                    "op-wrong-remote", RemoteOutcome.COMMITTED,
                    observation_id="bad", observed_idempotency_key="wrong-key",
                    source="simulated-provider-ledger",
                )

    def test_reopen_reconstructs_identical_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, state, lifecycle = self.env(td)
            self.prepare(state, lifecycle, "op-reopen")
            lifecycle.transition("op-reopen", LifecycleState.SUBMITTED, transition_id="submit")
            lifecycle.transition("op-reopen", LifecycleState.UNKNOWN_OUTCOME, transition_id="unknown")
            before = lifecycle.inspect("op-reopen")
            reopened_state = ConnectionAuthorityStateStore(AttemptStore(store.root))
            reopened = ExternalOperationLifecycleStore(reopened_state)
            after = reopened.inspect("op-reopen")
            self.assertEqual(before, after)

    def test_receipts_and_remote_observations_have_no_authority_and_no_network(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, lifecycle = self.env(td)
            _, _, op = self.prepare(state, lifecycle, "op-authority-none")
            self.assertEqual(op.authority, "NONE")
            lifecycle.transition("op-authority-none", LifecycleState.SUBMITTED, transition_id="submit")
            lifecycle.transition("op-authority-none", LifecycleState.UNKNOWN_OUTCOME, transition_id="unknown")
            receipt = lifecycle.observe_remote(
                "op-authority-none", RemoteOutcome.UNKNOWN,
                observation_id="observe-unknown", observed_idempotency_key=op.idempotency_key,
                source="injected-zero-authority-observation",
            )
            self.assertEqual(receipt["payload"]["authority"], "NONE")
            self.assertEqual(lifecycle.inspect("op-authority-none").state, LifecycleState.UNKNOWN_OUTCOME)


if __name__ == "__main__":
    unittest.main(verbosity=2)
