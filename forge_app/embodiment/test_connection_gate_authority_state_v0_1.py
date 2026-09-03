from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from forge_app.connection_gate import (
    AuthorityDecision,
    AuthorityStateError,
    ConnectionAuthorityStateStore,
    ConsequenceClass,
    ConnectorPolicy,
    CredentialCeiling,
    CurrentnessState,
    IntentSource,
    OperationConfirmation,
    OperationRequest,
    OperationStage,
    ProviderIdentity,
    SessionArming,
    UserGrant,
    VerificationState,
)
from forge_app.recovery import AttemptStore


RESOURCE = "github:SEng-Kitathas/Singularity-works-:branch:forge/app-shell-rd"


class ConnectionGateAuthorityStateV01Tests(unittest.TestCase):
    def env(self, td: str):
        store = AttemptStore(Path(td) / "attempt-store")
        state = ConnectionAuthorityStateStore(store)
        provider = ProviderIdentity("github", "subject-1", VerificationState.VERIFIED)
        credential = CredentialCeiling(
            "cred-1",
            "github",
            "subject-1",
            ("repo.read", "repo.push", "repo.admin"),
            ("*",),
        )
        policy = ConnectorPolicy(
            "policy-1",
            "github-app",
            "github",
            ("repo.read", "repo.push"),
            (RESOURCE,),
            ConsequenceClass.WRITE,
            ConsequenceClass.WRITE,
        )
        grant = UserGrant(
            "grant-1",
            "operator-1",
            "github",
            "github-app",
            ("repo.read", "repo.push"),
            (RESOURCE,),
            ConsequenceClass.WRITE,
            ConsequenceClass.WRITE,
        )
        arming = SessionArming(
            "arming-1",
            "operator-1",
            "github",
            "github-app",
            ("repo.read", "repo.push"),
            (RESOURCE,),
            ConsequenceClass.WRITE,
            ConsequenceClass.WRITE,
            True,
            True,
        )
        state.register_provider(provider)
        state.register_credential_ceiling(credential)
        state.register_policy(policy)
        state.register_grant(grant)
        state.register_arming(arming)
        return store, state, provider, credential, policy, grant, arming

    def request(
        self,
        request_id: str,
        *,
        capability: str = "repo.read",
        consequence: ConsequenceClass = ConsequenceClass.READ,
    ) -> OperationRequest:
        return OperationRequest(
            request_id=request_id,
            principal_id="operator-1",
            provider_id="github",
            connector_id="github-app",
            capability=capability,
            resource=RESOURCE,
            consequence=consequence,
            reason="authority state hostile test",
            intent_source=IntentSource.OPERATOR,
        )

    def persisted(
        self,
        state: ConnectionAuthorityStateStore,
        request: OperationRequest,
        *,
        confirmation_id: str | None = None,
    ):
        return state.evaluate_and_persist(
            request,
            provider_subject_id="subject-1",
            credential_id="cred-1",
            policy_id="policy-1",
            grant_id="grant-1",
            arming_id="arming-1",
            confirmation_id=confirmation_id,
        )

    def test_object_exact_replay_is_idempotent_and_conflict_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, state, _, _, _, grant, _ = self.env(td)
            before = store.integrity_summary()["counts"].copy()
            state.register_grant(grant)
            after = store.integrity_summary()["counts"].copy()
            self.assertEqual(before, after)
            with self.assertRaises(Exception):
                state.register_grant(replace(grant, capabilities=("repo.admin",)))
            self.assertEqual(state.read_grant("grant-1").capabilities, grant.capabilities)

    def test_credential_secret_material_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, _, credential, _, _, _ = self.env(td)
            with self.assertRaisesRegex(AuthorityStateError, "NO_SECRET_BYTES"):
                state.register_credential_ceiling(
                    replace(credential, credential_id="cred-secret-probe"),
                    secret_material=b"ghp_do_not_store_me",
                )

    def test_revoke_is_append_only_and_changes_evaluation_without_rewriting_grant(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, state, _, _, _, _, _ = self.env(td)
            grant_attempt = store.read_attempt("authority-object:grant:grant-1")
            blob_before = grant_attempt["blob_sha256"]
            allowed = self.persisted(state, self.request("read-before-revoke"))
            self.assertEqual(allowed.gate_receipt.decision, AuthorityDecision.ALLOW)
            state.revoke_grant("grant-1", revocation_id="revoke-1", reason="manual revoke")
            self.assertEqual(
                store.read_attempt("authority-object:grant:grant-1")["blob_sha256"],
                blob_before,
            )
            denied = self.persisted(state, self.request("read-after-revoke"))
            self.assertEqual(denied.gate_receipt.decision, AuthorityDecision.DENY)
            self.assertEqual(state.read_grant("grant-1").state.value, "REVOKED")

    def test_old_allow_cannot_prepare_operation_after_revoke(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, *_ = self.env(td)
            allowed = self.persisted(state, self.request("read-old-allow"))
            self.assertEqual(allowed.gate_receipt.decision, AuthorityDecision.ALLOW)
            state.revoke_grant("grant-1", revocation_id="revoke-old", reason="user revoked")
            with self.assertRaisesRegex(AuthorityStateError, "OLD_ALLOW_RECEIPT"):
                state.prepare_operation(
                    operation_id="op-after-revoke",
                    request_id="read-old-allow",
                    decision_attempt_id=allowed.attempt_id,
                )

    def test_old_allow_cannot_prepare_after_disarm_or_currentness_change(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, *_ = self.env(td)
            allowed = self.persisted(state, self.request("read-before-disarm"))
            state.disarm("arming-1", disarm_id="disarm-1", reason="manual disarm")
            with self.assertRaisesRegex(AuthorityStateError, "OLD_ALLOW_RECEIPT"):
                state.prepare_operation(
                    operation_id="op-after-disarm",
                    request_id="read-before-disarm",
                    decision_attempt_id=allowed.attempt_id,
                )

        with tempfile.TemporaryDirectory() as td:
            _, state, *_ = self.env(td)
            allowed = self.persisted(state, self.request("read-before-stale"))
            state.set_currentness(
                "policy",
                "policy-1",
                CurrentnessState.STALE,
                currentness_id="policy-stale-1",
                reason="policy currentness expired",
            )
            with self.assertRaisesRegex(AuthorityStateError, "OLD_ALLOW_RECEIPT"):
                state.prepare_operation(
                    operation_id="op-after-stale",
                    request_id="read-before-stale",
                    decision_attempt_id=allowed.attempt_id,
                )
            stale = self.persisted(state, self.request("read-after-stale"))
            self.assertEqual(stale.gate_receipt.decision, AuthorityDecision.STALE)

    def test_exact_unchanged_allow_prepares_operation_with_verified_readback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, state, *_ = self.env(td)
            allowed = self.persisted(state, self.request("read-prepare"))
            prepared = state.prepare_operation(
                operation_id="operation-1",
                request_id="read-prepare",
                decision_attempt_id=allowed.attempt_id,
            )
            self.assertTrue(prepared.verified_readback)
            row = store.read_attempt(prepared.attempt_id)
            self.assertEqual(row["artifact_class"], "security.connection_gate.prepared_operation")
            self.assertEqual(prepared.authority_state_fingerprint, allowed.authority_state_fingerprint)

    def test_non_allow_decision_cannot_prepare_operation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, *_ = self.env(td)
            push = self.persisted(
                state,
                self.request(
                    "push-needs-confirm",
                    capability="repo.push",
                    consequence=ConsequenceClass.WRITE,
                ),
            )
            self.assertEqual(push.gate_receipt.decision, AuthorityDecision.REQUIRE_CONFIRMATION)
            with self.assertRaisesRegex(AuthorityStateError, "requires persisted ALLOW"):
                state.prepare_operation(
                    operation_id="operation-push-unconfirmed",
                    request_id="push-needs-confirm",
                    decision_attempt_id=push.attempt_id,
                )

    def test_request_bound_confirmation_persists_and_allows_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, *_ = self.env(td)
            confirmation = OperationConfirmation(
                "confirmation-1",
                "push-confirmed",
                "operator-1",
                True,
            )
            state.register_confirmation(confirmation)
            allowed = self.persisted(
                state,
                self.request(
                    "push-confirmed",
                    capability="repo.push",
                    consequence=ConsequenceClass.WRITE,
                ),
                confirmation_id="confirmation-1",
            )
            self.assertEqual(allowed.gate_receipt.decision, AuthorityDecision.ALLOW)
            prepared = state.prepare_operation(
                operation_id="operation-confirmed-push",
                request_id="push-confirmed",
                decision_attempt_id=allowed.attempt_id,
            )
            self.assertTrue(prepared.verified_readback)

    def test_operation_stage_replay_is_idempotent_conflict_fails_and_regression_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, state, *_ = self.env(td)
            allowed = self.persisted(state, self.request("read-stage"))
            state.prepare_operation(
                operation_id="operation-stage",
                request_id="read-stage",
                decision_attempt_id=allowed.attempt_id,
            )
            first = state.append_operation_stage(
                "operation-stage",
                OperationStage.SUBMITTED,
                stage_id="submitted-1",
                payload={"transport": "not-executed-test"},
            )
            replay = state.append_operation_stage(
                "operation-stage",
                OperationStage.SUBMITTED,
                stage_id="submitted-1",
                payload={"transport": "not-executed-test"},
            )
            self.assertEqual(first["event_id"], replay["event_id"])
            with self.assertRaises(Exception):
                state.append_operation_stage(
                    "operation-stage",
                    OperationStage.SUBMITTED,
                    stage_id="submitted-1",
                    payload={"transport": "different"},
                )
            state.append_operation_stage(
                "operation-stage",
                OperationStage.STARTED,
                stage_id="started-1",
            )
            with self.assertRaisesRegex(AuthorityStateError, "stage regression"):
                state.append_operation_stage(
                    "operation-stage",
                    OperationStage.SUBMITTED,
                    stage_id="submitted-late",
                )
            events = store.events_for_attempt("authority-operation:operation-stage")
            self.assertEqual(
                len([e for e in events if e["event_type"] == "connection_operation_stage"]),
                2,
            )

    def test_reopen_reconstructs_identical_state_and_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, state, *_ = self.env(td)
            state.set_currentness(
                "credential",
                "cred-1",
                CurrentnessState.CURRENT,
                currentness_id="credential-refresh-1",
                reason="manual provider refresh",
            )
            snapshot1 = state.authority_state_snapshot(
                provider_id="github",
                subject_id="subject-1",
                credential_id="cred-1",
                policy_id="policy-1",
                grant_id="grant-1",
                arming_id="arming-1",
            )
            reopened = ConnectionAuthorityStateStore(AttemptStore(store.root))
            snapshot2 = reopened.authority_state_snapshot(
                provider_id="github",
                subject_id="subject-1",
                credential_id="cred-1",
                policy_id="policy-1",
                grant_id="grant-1",
                arming_id="arming-1",
            )
            self.assertEqual(snapshot1, snapshot2)
            self.assertEqual(reopened.read_grant("grant-1"), state.read_grant("grant-1"))
            self.assertEqual(reopened.read_arming("arming-1"), state.read_arming("arming-1"))

    def test_manual_inspection_lists_authority_objects_without_minting_authority(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, state, *_ = self.env(td)
            objects = state.list_authority_objects(limit=100)
            ids = {item["attempt_id"] for item in objects}
            self.assertIn("authority-object:grant:grant-1", ids)
            inspected = state.inspect_object("grant", "grant-1")
            self.assertEqual(inspected["payload"]["grant_id"], "grant-1")
            self.assertNotIn("token", inspected["payload"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
