from __future__ import annotations

"""Pure authority-intersection decision engine for Singularity Works Connection Gate v0.1.

This module intentionally performs no I/O and holds no credential secret material.
It decides whether a requested external consequence is permitted by the exact
intersection of independently supplied authority layers.
"""

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Iterable

SCHEMA = "singularity-connection-gate-decision/0.1"
WILDCARD = "*"


class VerificationState(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    UNKNOWN = "UNKNOWN"


class CurrentnessState(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class GrantState(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"


class ConsequenceClass(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    PUBLISH = "PUBLISH"
    ADMIN = "ADMIN"
    DESTRUCTIVE = "DESTRUCTIVE"


class IntentSource(str, Enum):
    OPERATOR = "OPERATOR"
    ARMED_AUTOMATION = "ARMED_AUTOMATION"
    EXTERNAL_CONTENT = "EXTERNAL_CONTENT"
    UNKNOWN = "UNKNOWN"


class AuthorityDecision(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    DENY = "DENY"
    UNARMED = "UNARMED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


_CONSEQUENCE_RANK = {
    ConsequenceClass.READ: 10,
    ConsequenceClass.WRITE: 20,
    ConsequenceClass.PUBLISH: 30,
    ConsequenceClass.ADMIN: 40,
    ConsequenceClass.DESTRUCTIVE: 50,
}


def _norm(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({str(v) for v in values if str(v)}))


def _allows(values: Iterable[str], requested: str) -> bool:
    scope = set(_norm(values))
    return WILDCARD in scope or requested in scope


def _intersection(layers: Iterable[Iterable[str]]) -> tuple[str, ...]:
    normalized = [set(_norm(layer)) for layer in layers]
    if not normalized:
        return ()
    explicit_universe: set[str] = set()
    for layer in normalized:
        explicit_universe.update(v for v in layer if v != WILDCARD)
    if not explicit_universe and all(WILDCARD in layer for layer in normalized):
        return (WILDCARD,)
    allowed = [
        item
        for item in explicit_universe
        if all(WILDCARD in layer or item in layer for layer in normalized)
    ]
    return tuple(sorted(allowed))


def _currentness_decision(states: Iterable[CurrentnessState]) -> AuthorityDecision | None:
    items = tuple(states)
    if CurrentnessState.UNKNOWN in items:
        return AuthorityDecision.UNKNOWN
    if CurrentnessState.STALE in items:
        return AuthorityDecision.STALE
    return None


@dataclass(frozen=True)
class ProviderIdentity:
    provider_id: str
    subject_id: str
    verification: VerificationState
    currentness: CurrentnessState = CurrentnessState.CURRENT


@dataclass(frozen=True)
class CredentialCeiling:
    credential_id: str
    provider_id: str
    subject_id: str
    capabilities: tuple[str, ...]
    resources: tuple[str, ...]
    currentness: CurrentnessState = CurrentnessState.CURRENT


@dataclass(frozen=True)
class ConnectorPolicy:
    policy_id: str
    connector_id: str
    provider_id: str
    capabilities: tuple[str, ...]
    resources: tuple[str, ...]
    max_consequence: ConsequenceClass
    confirmation_at: ConsequenceClass | None = None
    currentness: CurrentnessState = CurrentnessState.CURRENT


@dataclass(frozen=True)
class UserGrant:
    grant_id: str
    principal_id: str
    provider_id: str
    connector_id: str
    capabilities: tuple[str, ...]
    resources: tuple[str, ...]
    max_consequence: ConsequenceClass
    confirmation_at: ConsequenceClass | None = None
    state: GrantState = GrantState.ACTIVE
    currentness: CurrentnessState = CurrentnessState.CURRENT


@dataclass(frozen=True)
class SessionArming:
    arming_id: str
    principal_id: str
    provider_id: str
    connector_id: str
    capabilities: tuple[str, ...]
    resources: tuple[str, ...]
    max_consequence: ConsequenceClass
    confirmation_at: ConsequenceClass | None = None
    armed: bool = True
    manual_approval: bool = True
    currentness: CurrentnessState = CurrentnessState.CURRENT


@dataclass(frozen=True)
class OperationRequest:
    request_id: str
    principal_id: str
    provider_id: str
    connector_id: str
    capability: str
    resource: str
    consequence: ConsequenceClass
    reason: str
    intent_source: IntentSource


@dataclass(frozen=True)
class OperationConfirmation:
    confirmation_id: str
    request_id: str
    principal_id: str
    approved: bool
    currentness: CurrentnessState = CurrentnessState.CURRENT


@dataclass(frozen=True)
class ConnectionDecisionReceipt:
    schema: str
    decision_id: str
    decision: AuthorityDecision
    reasons: tuple[str, ...]
    request_id: str
    principal_id: str
    provider_id: str
    connector_id: str
    capability: str
    resource: str
    consequence: ConsequenceClass
    intent_source: IntentSource
    provider_subject_id: str
    credential_id: str
    policy_id: str
    grant_id: str
    arming_id: str
    confirmation_id: str | None
    effective_capabilities: tuple[str, ...]
    effective_resources: tuple[str, ...]
    receipt_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )


def _receipt(
    decision: AuthorityDecision,
    reasons: Iterable[str],
    *,
    request: OperationRequest,
    provider: ProviderIdentity,
    credential: CredentialCeiling,
    policy: ConnectorPolicy,
    grant: UserGrant,
    arming: SessionArming,
    confirmation: OperationConfirmation | None,
) -> ConnectionDecisionReceipt:
    effective_capabilities = _intersection(
        (credential.capabilities, policy.capabilities, grant.capabilities, arming.capabilities)
    )
    effective_resources = _intersection(
        (credential.resources, policy.resources, grant.resources, arming.resources)
    )
    body = {
        "schema": SCHEMA,
        "decision": decision.value,
        "reasons": tuple(reasons),
        "request_id": request.request_id,
        "principal_id": request.principal_id,
        "provider_id": request.provider_id,
        "connector_id": request.connector_id,
        "capability": request.capability,
        "resource": request.resource,
        "consequence": request.consequence.value,
        "intent_source": request.intent_source.value,
        "provider_subject_id": provider.subject_id,
        "credential_id": credential.credential_id,
        "policy_id": policy.policy_id,
        "grant_id": grant.grant_id,
        "arming_id": arming.arming_id,
        "confirmation_id": confirmation.confirmation_id if confirmation else None,
        "effective_capabilities": effective_capabilities,
        "effective_resources": effective_resources,
        "receipt_authority": "NONE",
    }
    decision_id = "gate-decision-" + hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:24]
    return ConnectionDecisionReceipt(
        schema=SCHEMA,
        decision_id=decision_id,
        decision=decision,
        reasons=tuple(reasons),
        request_id=request.request_id,
        principal_id=request.principal_id,
        provider_id=request.provider_id,
        connector_id=request.connector_id,
        capability=request.capability,
        resource=request.resource,
        consequence=request.consequence,
        intent_source=request.intent_source,
        provider_subject_id=provider.subject_id,
        credential_id=credential.credential_id,
        policy_id=policy.policy_id,
        grant_id=grant.grant_id,
        arming_id=arming.arming_id,
        confirmation_id=confirmation.confirmation_id if confirmation else None,
        effective_capabilities=effective_capabilities,
        effective_resources=effective_resources,
        receipt_authority="NONE",
    )


def evaluate_connection_authority(
    request: OperationRequest,
    *,
    provider: ProviderIdentity,
    credential: CredentialCeiling,
    policy: ConnectorPolicy,
    grant: UserGrant,
    arming: SessionArming,
    confirmation: OperationConfirmation | None = None,
) -> ConnectionDecisionReceipt:
    """Return an authority-NONE decision receipt. No external effect is executed."""

    required_text = (
        request.request_id,
        request.principal_id,
        request.provider_id,
        request.connector_id,
        request.capability,
        request.resource,
        request.reason,
    )
    if any(not value for value in required_text):
        raise ValueError("request identity/capability/resource/reason fields must be non-empty")

    reasons: list[str] = []

    binding_mismatches: list[str] = []
    if provider.provider_id != request.provider_id:
        binding_mismatches.append("provider_identity.provider_id")
    if credential.provider_id != request.provider_id:
        binding_mismatches.append("credential.provider_id")
    if credential.subject_id != provider.subject_id:
        binding_mismatches.append("credential.subject_id")
    if policy.provider_id != request.provider_id or policy.connector_id != request.connector_id:
        binding_mismatches.append("connector_policy")
    if (
        grant.principal_id != request.principal_id
        or grant.provider_id != request.provider_id
        or grant.connector_id != request.connector_id
    ):
        binding_mismatches.append("user_grant")
    if (
        arming.principal_id != request.principal_id
        or arming.provider_id != request.provider_id
        or arming.connector_id != request.connector_id
    ):
        binding_mismatches.append("session_arming")
    if binding_mismatches:
        return _receipt(
            AuthorityDecision.DENY,
            ("identity_binding_mismatch:" + ",".join(sorted(binding_mismatches)),),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    if provider.verification == VerificationState.UNKNOWN:
        return _receipt(
            AuthorityDecision.UNKNOWN,
            ("provider_identity_unknown",),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )
    if provider.verification != VerificationState.VERIFIED:
        return _receipt(
            AuthorityDecision.DENY,
            ("provider_identity_not_verified",),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    currentness = _currentness_decision(
        (provider.currentness, credential.currentness, policy.currentness, grant.currentness, arming.currentness)
    )
    if currentness is not None:
        return _receipt(
            currentness,
            ("authority_layer_currentness_not_current",),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    if grant.state == GrantState.UNKNOWN:
        return _receipt(
            AuthorityDecision.UNKNOWN,
            ("grant_state_unknown",),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )
    if grant.state != GrantState.ACTIVE:
        return _receipt(
            AuthorityDecision.DENY,
            ("grant_not_active",),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    if not arming.armed or not arming.manual_approval:
        return _receipt(
            AuthorityDecision.UNARMED,
            ("session_not_manually_armed",),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    if request.intent_source == IntentSource.UNKNOWN:
        return _receipt(
            AuthorityDecision.UNKNOWN,
            ("intent_source_unknown",),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )
    if request.intent_source == IntentSource.EXTERNAL_CONTENT:
        return _receipt(
            AuthorityDecision.DENY,
            ("external_content_cannot_mint_operator_intent",),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    request_rank = _CONSEQUENCE_RANK[request.consequence]
    max_rank = min(
        _CONSEQUENCE_RANK[policy.max_consequence],
        _CONSEQUENCE_RANK[grant.max_consequence],
        _CONSEQUENCE_RANK[arming.max_consequence],
    )
    if request_rank > max_rank:
        return _receipt(
            AuthorityDecision.DENY,
            ("consequence_exceeds_effective_envelope",),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    cap_layers = (
        ("credential", credential.capabilities),
        ("policy", policy.capabilities),
        ("grant", grant.capabilities),
        ("arming", arming.capabilities),
    )
    denied_caps = [name for name, values in cap_layers if not _allows(values, request.capability)]
    if denied_caps:
        return _receipt(
            AuthorityDecision.DENY,
            ("capability_not_in_effective_intersection:" + ",".join(denied_caps),),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    resource_layers = (
        ("credential", credential.resources),
        ("policy", policy.resources),
        ("grant", grant.resources),
        ("arming", arming.resources),
    )
    denied_resources = [name for name, values in resource_layers if not _allows(values, request.resource)]
    if denied_resources:
        return _receipt(
            AuthorityDecision.DENY,
            ("resource_not_in_effective_intersection:" + ",".join(denied_resources),),
            request=request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )

    thresholds = [
        _CONSEQUENCE_RANK[value]
        for value in (policy.confirmation_at, grant.confirmation_at, arming.confirmation_at)
        if value is not None
    ]
    confirmation_threshold = min(thresholds) if thresholds else None
    if confirmation_threshold is not None and request_rank >= confirmation_threshold:
        if confirmation is None:
            return _receipt(
                AuthorityDecision.REQUIRE_CONFIRMATION,
                ("operation_requires_request_bound_confirmation",),
                request=request,
                provider=provider,
                credential=credential,
                policy=policy,
                grant=grant,
                arming=arming,
                confirmation=None,
            )
        confirmation_currentness = _currentness_decision((confirmation.currentness,))
        if confirmation_currentness is not None:
            return _receipt(
                confirmation_currentness,
                ("confirmation_currentness_not_current",),
                request=request,
                provider=provider,
                credential=credential,
                policy=policy,
                grant=grant,
                arming=arming,
                confirmation=confirmation,
            )
        if (
            confirmation.request_id != request.request_id
            or confirmation.principal_id != request.principal_id
        ):
            return _receipt(
                AuthorityDecision.DENY,
                ("confirmation_not_bound_to_exact_request_and_principal",),
                request=request,
                provider=provider,
                credential=credential,
                policy=policy,
                grant=grant,
                arming=arming,
                confirmation=confirmation,
            )
        if not confirmation.approved:
            return _receipt(
                AuthorityDecision.DENY,
                ("operator_confirmation_denied",),
                request=request,
                provider=provider,
                credential=credential,
                policy=policy,
                grant=grant,
                arming=arming,
                confirmation=confirmation,
            )

    reasons.append("effective_authority_intersection_allows_request")
    return _receipt(
        AuthorityDecision.ALLOW,
        reasons,
        request=request,
        provider=provider,
        credential=credential,
        policy=policy,
        grant=grant,
        arming=arming,
        confirmation=confirmation,
    )
