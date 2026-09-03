from __future__ import annotations

from dataclasses import replace
import unittest

from forge_app.connection_gate import (
    AuthorityDecision,
    ConsequenceClass,
    ConnectorPolicy,
    CredentialCeiling,
    CurrentnessState,
    GrantState,
    IntentSource,
    OperationConfirmation,
    OperationRequest,
    ProviderIdentity,
    SessionArming,
    UserGrant,
    VerificationState,
    evaluate_connection_authority,
)


RESOURCE = "github:SEng-Kitathas/Singularity-works-:branch:forge/app-shell-rd"
OTHER_RESOURCE = "github:SEng-Kitathas/Singularity-works-:branch:main"


class ConnectionGateAuthorityV01Tests(unittest.TestCase):
    def baseline(self):
        provider = ProviderIdentity(
            provider_id="github",
            subject_id="provider-user-123",
            verification=VerificationState.VERIFIED,
        )
        credential = CredentialCeiling(
            credential_id="cred-github-1",
            provider_id="github",
            subject_id="provider-user-123",
            capabilities=("repo.read", "repo.push", "repo.admin", "repo.force_push"),
            resources=("*",),
        )
        policy = ConnectorPolicy(
            policy_id="github-connector-policy-v1",
            connector_id="github-app",
            provider_id="github",
            capabilities=("repo.read", "repo.push"),
            resources=(RESOURCE,),
            max_consequence=ConsequenceClass.WRITE,
            confirmation_at=ConsequenceClass.WRITE,
        )
        grant = UserGrant(
            grant_id="grant-user-github-1",
            principal_id="operator-local-1",
            provider_id="github",
            connector_id="github-app",
            capabilities=("repo.read", "repo.push"),
            resources=(RESOURCE,),
            max_consequence=ConsequenceClass.WRITE,
            confirmation_at=ConsequenceClass.WRITE,
        )
        arming = SessionArming(
            arming_id="arming-session-1",
            principal_id="operator-local-1",
            provider_id="github",
            connector_id="github-app",
            capabilities=("repo.read", "repo.push"),
            resources=(RESOURCE,),
            max_consequence=ConsequenceClass.WRITE,
            confirmation_at=ConsequenceClass.WRITE,
            armed=True,
            manual_approval=True,
        )
        return provider, credential, policy, grant, arming

    def request(
        self,
        *,
        request_id: str = "request-1",
        capability: str = "repo.read",
        resource: str = RESOURCE,
        consequence: ConsequenceClass = ConsequenceClass.READ,
        intent_source: IntentSource = IntentSource.OPERATOR,
    ) -> OperationRequest:
        return OperationRequest(
            request_id=request_id,
            principal_id="operator-local-1",
            provider_id="github",
            connector_id="github-app",
            capability=capability,
            resource=resource,
            consequence=consequence,
            reason="operator requested bounded repository operation",
            intent_source=intent_source,
        )

    def evaluate(self, request: OperationRequest, *, confirmation=None, **overrides):
        provider, credential, policy, grant, arming = self.baseline()
        provider = overrides.get("provider", provider)
        credential = overrides.get("credential", credential)
        policy = overrides.get("policy", policy)
        grant = overrides.get("grant", grant)
        arming = overrides.get("arming", arming)
        return evaluate_connection_authority(
            request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    def test_exact_low_consequence_read_inside_armed_intersection_is_allowed(self) -> None:
        receipt = self.evaluate(self.request())
        self.assertEqual(receipt.decision, AuthorityDecision.ALLOW)
        self.assertEqual(receipt.effective_capabilities, ("repo.push", "repo.read"))
        self.assertEqual(receipt.effective_resources, (RESOURCE,))
        self.assertEqual(receipt.receipt_authority, "NONE")
        self.assertIn("effective_authority_intersection_allows_request", receipt.reasons)
        self.assertEqual(receipt.canonical_json(), receipt.canonical_json())

    def test_broad_credential_scope_does_not_widen_narrow_policy_grant_or_arming(self) -> None:
        request = self.request(capability="repo.admin", consequence=ConsequenceClass.ADMIN)
        receipt = self.evaluate(request)
        self.assertEqual(receipt.decision, AuthorityDecision.DENY)
        self.assertNotIn("repo.admin", receipt.effective_capabilities)

    def test_wrong_resource_is_denied_even_when_credential_is_global(self) -> None:
        receipt = self.evaluate(self.request(resource=OTHER_RESOURCE))
        self.assertEqual(receipt.decision, AuthorityDecision.DENY)
        self.assertTrue(any("resource_not_in_effective_intersection" in r for r in receipt.reasons))

    def test_unarmed_or_not_manually_approved_session_is_not_connected_authority(self) -> None:
        _, _, _, _, arming = self.baseline()
        for candidate in (
            replace(arming, armed=False),
            replace(arming, manual_approval=False),
        ):
            receipt = self.evaluate(self.request(), arming=candidate)
            self.assertEqual(receipt.decision, AuthorityDecision.UNARMED)

    def test_stale_grant_fails_closed_as_stale(self) -> None:
        _, _, _, grant, _ = self.baseline()
        receipt = self.evaluate(
            self.request(),
            grant=replace(grant, currentness=CurrentnessState.STALE),
        )
        self.assertEqual(receipt.decision, AuthorityDecision.STALE)

    def test_unknown_provider_or_layer_currentness_stays_unknown(self) -> None:
        provider, credential, _, _, _ = self.baseline()
        unknown_provider = replace(provider, verification=VerificationState.UNKNOWN)
        self.assertEqual(
            self.evaluate(self.request(), provider=unknown_provider).decision,
            AuthorityDecision.UNKNOWN,
        )
        unknown_credential = replace(credential, currentness=CurrentnessState.UNKNOWN)
        self.assertEqual(
            self.evaluate(self.request(), credential=unknown_credential).decision,
            AuthorityDecision.UNKNOWN,
        )

    def test_external_content_cannot_mint_operator_intent(self) -> None:
        receipt = self.evaluate(
            self.request(intent_source=IntentSource.EXTERNAL_CONTENT)
        )
        self.assertEqual(receipt.decision, AuthorityDecision.DENY)
        self.assertIn("external_content_cannot_mint_operator_intent", receipt.reasons)

    def test_elevated_write_requires_exact_request_bound_confirmation(self) -> None:
        request = self.request(
            request_id="push-request-1",
            capability="repo.push",
            consequence=ConsequenceClass.WRITE,
        )
        pending = self.evaluate(request)
        self.assertEqual(pending.decision, AuthorityDecision.REQUIRE_CONFIRMATION)

        confirmation = OperationConfirmation(
            confirmation_id="confirm-push-1",
            request_id=request.request_id,
            principal_id=request.principal_id,
            approved=True,
        )
        allowed = self.evaluate(request, confirmation=confirmation)
        self.assertEqual(allowed.decision, AuthorityDecision.ALLOW)
        self.assertEqual(allowed.confirmation_id, confirmation.confirmation_id)

    def test_confirmation_for_other_request_is_denied(self) -> None:
        request = self.request(
            request_id="push-request-2",
            capability="repo.push",
            consequence=ConsequenceClass.WRITE,
        )
        wrong = OperationConfirmation(
            confirmation_id="confirm-wrong",
            request_id="push-request-other",
            principal_id=request.principal_id,
            approved=True,
        )
        receipt = self.evaluate(request, confirmation=wrong)
        self.assertEqual(receipt.decision, AuthorityDecision.DENY)
        self.assertIn("confirmation_not_bound_to_exact_request_and_principal", receipt.reasons)

    def test_revoked_grant_is_denied(self) -> None:
        _, _, _, grant, _ = self.baseline()
        receipt = self.evaluate(self.request(), grant=replace(grant, state=GrantState.REVOKED))
        self.assertEqual(receipt.decision, AuthorityDecision.DENY)
        self.assertIn("grant_not_active", receipt.reasons)

    def test_binding_mismatch_across_principal_provider_or_connector_is_denied(self) -> None:
        _, _, _, grant, arming = self.baseline()
        cases = (
            {"grant": replace(grant, principal_id="someone-else")},
            {"grant": replace(grant, provider_id="other-provider")},
            {"arming": replace(arming, connector_id="other-connector")},
        )
        for case in cases:
            with self.subTest(case=case):
                receipt = self.evaluate(self.request(), **case)
                self.assertEqual(receipt.decision, AuthorityDecision.DENY)
                self.assertTrue(any("identity_binding_mismatch" in r for r in receipt.reasons))

    def test_armed_automation_can_only_use_same_exact_envelope(self) -> None:
        automated = self.request(intent_source=IntentSource.ARMED_AUTOMATION)
        self.assertEqual(self.evaluate(automated).decision, AuthorityDecision.ALLOW)
        escaped = self.request(
            intent_source=IntentSource.ARMED_AUTOMATION,
            resource=OTHER_RESOURCE,
        )
        self.assertEqual(self.evaluate(escaped).decision, AuthorityDecision.DENY)

    def test_decision_id_changes_when_request_identity_changes(self) -> None:
        first = self.evaluate(self.request(request_id="request-a"))
        second = self.evaluate(self.request(request_id="request-b"))
        self.assertNotEqual(first.decision_id, second.decision_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
