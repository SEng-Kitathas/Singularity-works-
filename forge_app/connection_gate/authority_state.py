from __future__ import annotations

"""Durable append-oriented Connection Gate authority state v0.1.

This layer reuses the qualified AttemptStore for persistence. It stores authority
metadata and receipts only; credential/token secret bytes are outside this model.
"""

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

from forge_app.recovery.attempt_store import AttemptStore, AttemptStoreError

from .authority import (
    AuthorityDecision,
    ConnectionDecisionReceipt,
    ConnectorPolicy,
    CredentialCeiling,
    CurrentnessState,
    GrantState,
    OperationConfirmation,
    OperationRequest,
    ProviderIdentity,
    SessionArming,
    UserGrant,
    VerificationState,
    evaluate_connection_authority,
)

OBJECT_SCHEMA = "singularity-authority-object/0.1"
PERSISTED_DECISION_SCHEMA = "singularity-persisted-authority-decision/0.1"
PREPARED_OPERATION_SCHEMA = "singularity-prepared-external-operation/0.1"


class AuthorityStateError(RuntimeError):
    pass


class OperationStage(str, Enum):
    SUBMITTED = "SUBMITTED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    REMOTE_OBSERVED = "REMOTE_OBSERVED"
    FAILED = "FAILED"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"


_STAGE_RANK = {
    OperationStage.SUBMITTED: 20,
    OperationStage.STARTED: 30,
    OperationStage.COMPLETED: 40,
    OperationStage.FAILED: 40,
    OperationStage.UNKNOWN_OUTCOME: 40,
    OperationStage.REMOTE_OBSERVED: 50,
}


@dataclass(frozen=True)
class PersistedDecision:
    attempt_id: str
    decision_id: str
    authority_state_fingerprint: str
    gate_receipt: ConnectionDecisionReceipt
    verified_readback: bool


@dataclass(frozen=True)
class PreparedOperation:
    attempt_id: str
    operation_id: str
    request_id: str
    decision_attempt_id: str
    decision_id: str
    authority_state_fingerprint: str
    verified_readback: bool


def _normalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_normalize(v) for v in value]
    return value


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            _normalize(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _object_attempt_id(kind: str, object_id: str) -> str:
    return f"authority-object:{kind}:{object_id}"


def _decision_from_dict(data: Mapping[str, Any]) -> ConnectionDecisionReceipt:
    from .authority import ConsequenceClass, IntentSource

    return ConnectionDecisionReceipt(
        schema=str(data["schema"]),
        decision_id=str(data["decision_id"]),
        decision=AuthorityDecision(str(data["decision"])),
        reasons=tuple(str(v) for v in data["reasons"]),
        request_id=str(data["request_id"]),
        principal_id=str(data["principal_id"]),
        provider_id=str(data["provider_id"]),
        connector_id=str(data["connector_id"]),
        capability=str(data["capability"]),
        resource=str(data["resource"]),
        consequence=ConsequenceClass(str(data["consequence"])),
        intent_source=IntentSource(str(data["intent_source"])),
        provider_subject_id=str(data["provider_subject_id"]),
        credential_id=str(data["credential_id"]),
        policy_id=str(data["policy_id"]),
        grant_id=str(data["grant_id"]),
        arming_id=str(data["arming_id"]),
        confirmation_id=(str(data["confirmation_id"]) if data.get("confirmation_id") is not None else None),
        effective_capabilities=tuple(str(v) for v in data["effective_capabilities"]),
        effective_resources=tuple(str(v) for v in data["effective_resources"]),
        receipt_authority=str(data.get("receipt_authority") or "NONE"),
    )


class ConnectionAuthorityStateStore:
    """Authority metadata/state wrapper over an existing qualified AttemptStore."""

    def __init__(self, store: AttemptStore) -> None:
        self.store = store

    def _capture_object(self, kind: str, object_id: str, payload: Mapping[str, Any]) -> str:
        if not kind or not object_id:
            raise ValueError("kind and object_id are required")
        document = {
            "schema": OBJECT_SCHEMA,
            "kind": kind,
            "object_id": object_id,
            "payload": _normalize(payload),
        }
        attempt_id = _object_attempt_id(kind, object_id)
        self.store.capture(
            _canonical_bytes(document),
            artifact_class=f"security.connection_gate.{kind}",
            producer="singularity-works:connection-gate-authority-state-v0.1",
            intent=f"preserve immutable Connection Gate {kind} {object_id}",
            metadata={"schema": OBJECT_SCHEMA, "kind": kind, "object_id": object_id},
            attempt_id=attempt_id,
        )
        readback = self.store.read_attempt(attempt_id)
        if json.loads(readback["payload"].decode("utf-8")) != document:
            raise AuthorityStateError(f"authority object readback mismatch: {attempt_id}")
        return attempt_id

    def _read_object(self, kind: str, object_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        attempt_id = _object_attempt_id(kind, object_id)
        row = self.store.read_attempt(attempt_id)
        expected_class = f"security.connection_gate.{kind}"
        if row["artifact_class"] != expected_class:
            raise AuthorityStateError(
                f"authority object class mismatch: expected={expected_class} actual={row['artifact_class']}"
            )
        doc = json.loads(row["payload"].decode("utf-8"))
        if (
            doc.get("schema") != OBJECT_SCHEMA
            or doc.get("kind") != kind
            or doc.get("object_id") != object_id
            or not isinstance(doc.get("payload"), dict)
        ):
            raise AuthorityStateError(f"authority object envelope mismatch: {attempt_id}")
        return dict(doc["payload"]), row

    def register_provider(self, provider: ProviderIdentity) -> str:
        object_id = f"{provider.provider_id}:{provider.subject_id}"
        return self._capture_object("provider", object_id, asdict(provider))

    def register_credential_ceiling(self, credential: CredentialCeiling, *, secret_material: object | None = None) -> str:
        if secret_material is not None:
            raise AuthorityStateError("NO_SECRET_BYTES_IN_AUTHORITY_STATE_STORE")
        return self._capture_object("credential", credential.credential_id, asdict(credential))

    def register_policy(self, policy: ConnectorPolicy) -> str:
        return self._capture_object("policy", policy.policy_id, asdict(policy))

    def register_grant(self, grant: UserGrant) -> str:
        return self._capture_object("grant", grant.grant_id, asdict(grant))

    def register_arming(self, arming: SessionArming) -> str:
        return self._capture_object("arming", arming.arming_id, asdict(arming))

    def register_confirmation(self, confirmation: OperationConfirmation) -> str:
        return self._capture_object("confirmation", confirmation.confirmation_id, asdict(confirmation))

    def revoke_grant(self, grant_id: str, *, revocation_id: str, reason: str) -> dict[str, Any]:
        attempt_id = _object_attempt_id("grant", grant_id)
        self.store.read_attempt(attempt_id)
        receipt = self.store.append_event(
            "authority_grant_revoked",
            attempt_id=attempt_id,
            payload={"grant_id": grant_id, "revocation_id": revocation_id, "reason": reason},
            event_id=f"authority-grant-revoked:{grant_id}:{revocation_id}",
        )
        return receipt.as_dict()

    def disarm(self, arming_id: str, *, disarm_id: str, reason: str) -> dict[str, Any]:
        attempt_id = _object_attempt_id("arming", arming_id)
        self.store.read_attempt(attempt_id)
        receipt = self.store.append_event(
            "authority_arming_disarmed",
            attempt_id=attempt_id,
            payload={"arming_id": arming_id, "disarm_id": disarm_id, "reason": reason},
            event_id=f"authority-arming-disarmed:{arming_id}:{disarm_id}",
        )
        return receipt.as_dict()

    def set_currentness(
        self,
        kind: str,
        object_id: str,
        currentness: CurrentnessState,
        *,
        currentness_id: str,
        reason: str,
    ) -> dict[str, Any]:
        attempt_id = _object_attempt_id(kind, object_id)
        self.store.read_attempt(attempt_id)
        receipt = self.store.append_event(
            "authority_currentness_set",
            attempt_id=attempt_id,
            payload={
                "kind": kind,
                "object_id": object_id,
                "currentness": currentness.value,
                "currentness_id": currentness_id,
                "reason": reason,
            },
            event_id=f"authority-currentness:{kind}:{object_id}:{currentness_id}",
        )
        return receipt.as_dict()

    def _lifecycle_events(self, kind: str, object_id: str) -> list[dict[str, Any]]:
        attempt_id = _object_attempt_id(kind, object_id)
        return self.store.events_for_attempt(attempt_id)

    def _latest_currentness(self, kind: str, object_id: str, default: CurrentnessState) -> CurrentnessState:
        latest: dict[str, Any] | None = None
        for event in self._lifecycle_events(kind, object_id):
            if event["event_type"] != "authority_currentness_set":
                continue
            payload = event["payload"]
            if payload.get("kind") == kind and payload.get("object_id") == object_id:
                latest = event
        if latest is None:
            return default
        return CurrentnessState(str(latest["payload"]["currentness"]))

    def read_provider(self, provider_id: str, subject_id: str) -> ProviderIdentity:
        object_id = f"{provider_id}:{subject_id}"
        data, _ = self._read_object("provider", object_id)
        value = ProviderIdentity(
            provider_id=str(data["provider_id"]),
            subject_id=str(data["subject_id"]),
            verification=VerificationState(str(data["verification"])),
            currentness=CurrentnessState(str(data["currentness"])),
        )
        return replace(value, currentness=self._latest_currentness("provider", object_id, value.currentness))

    def read_credential_ceiling(self, credential_id: str) -> CredentialCeiling:
        data, _ = self._read_object("credential", credential_id)
        value = CredentialCeiling(
            credential_id=str(data["credential_id"]),
            provider_id=str(data["provider_id"]),
            subject_id=str(data["subject_id"]),
            capabilities=tuple(str(v) for v in data["capabilities"]),
            resources=tuple(str(v) for v in data["resources"]),
            currentness=CurrentnessState(str(data["currentness"])),
        )
        return replace(value, currentness=self._latest_currentness("credential", credential_id, value.currentness))

    def read_policy(self, policy_id: str) -> ConnectorPolicy:
        from .authority import ConsequenceClass

        data, _ = self._read_object("policy", policy_id)
        value = ConnectorPolicy(
            policy_id=str(data["policy_id"]),
            connector_id=str(data["connector_id"]),
            provider_id=str(data["provider_id"]),
            capabilities=tuple(str(v) for v in data["capabilities"]),
            resources=tuple(str(v) for v in data["resources"]),
            max_consequence=ConsequenceClass(str(data["max_consequence"])),
            confirmation_at=(
                ConsequenceClass(str(data["confirmation_at"]))
                if data.get("confirmation_at") is not None
                else None
            ),
            currentness=CurrentnessState(str(data["currentness"])),
        )
        return replace(value, currentness=self._latest_currentness("policy", policy_id, value.currentness))

    def read_grant(self, grant_id: str) -> UserGrant:
        from .authority import ConsequenceClass

        data, _ = self._read_object("grant", grant_id)
        value = UserGrant(
            grant_id=str(data["grant_id"]),
            principal_id=str(data["principal_id"]),
            provider_id=str(data["provider_id"]),
            connector_id=str(data["connector_id"]),
            capabilities=tuple(str(v) for v in data["capabilities"]),
            resources=tuple(str(v) for v in data["resources"]),
            max_consequence=ConsequenceClass(str(data["max_consequence"])),
            confirmation_at=(
                ConsequenceClass(str(data["confirmation_at"]))
                if data.get("confirmation_at") is not None
                else None
            ),
            state=GrantState(str(data["state"])),
            currentness=CurrentnessState(str(data["currentness"])),
        )
        events = self._lifecycle_events("grant", grant_id)
        if any(e["event_type"] == "authority_grant_revoked" for e in events):
            value = replace(value, state=GrantState.REVOKED)
        return replace(value, currentness=self._latest_currentness("grant", grant_id, value.currentness))

    def read_arming(self, arming_id: str) -> SessionArming:
        from .authority import ConsequenceClass

        data, _ = self._read_object("arming", arming_id)
        value = SessionArming(
            arming_id=str(data["arming_id"]),
            principal_id=str(data["principal_id"]),
            provider_id=str(data["provider_id"]),
            connector_id=str(data["connector_id"]),
            capabilities=tuple(str(v) for v in data["capabilities"]),
            resources=tuple(str(v) for v in data["resources"]),
            max_consequence=ConsequenceClass(str(data["max_consequence"])),
            confirmation_at=(
                ConsequenceClass(str(data["confirmation_at"]))
                if data.get("confirmation_at") is not None
                else None
            ),
            armed=bool(data["armed"]),
            manual_approval=bool(data["manual_approval"]),
            currentness=CurrentnessState(str(data["currentness"])),
        )
        events = self._lifecycle_events("arming", arming_id)
        if any(e["event_type"] == "authority_arming_disarmed" for e in events):
            value = replace(value, armed=False)
        return replace(value, currentness=self._latest_currentness("arming", arming_id, value.currentness))

    def read_confirmation(self, confirmation_id: str) -> OperationConfirmation:
        data, _ = self._read_object("confirmation", confirmation_id)
        value = OperationConfirmation(
            confirmation_id=str(data["confirmation_id"]),
            request_id=str(data["request_id"]),
            principal_id=str(data["principal_id"]),
            approved=bool(data["approved"]),
            currentness=CurrentnessState(str(data["currentness"])),
        )
        return replace(
            value,
            currentness=self._latest_currentness("confirmation", confirmation_id, value.currentness),
        )

    def _component(self, kind: str, object_id: str) -> dict[str, Any]:
        _, row = self._read_object(kind, object_id)
        events = [
            {
                "seq": int(e["seq"]),
                "event_id": str(e["event_id"]),
                "event_type": str(e["event_type"]),
                "payload": e["payload"],
            }
            for e in self._lifecycle_events(kind, object_id)
            if e["event_type"]
            in {"authority_grant_revoked", "authority_arming_disarmed", "authority_currentness_set"}
        ]
        return {
            "attempt_id": row["attempt_id"],
            "blob_sha256": row["blob_sha256"],
            "events": events,
        }

    def authority_state_snapshot(
        self,
        *,
        provider_id: str,
        subject_id: str,
        credential_id: str,
        policy_id: str,
        grant_id: str,
        arming_id: str,
        confirmation_id: str | None = None,
    ) -> dict[str, Any]:
        components = {
            "provider": self._component("provider", f"{provider_id}:{subject_id}"),
            "credential": self._component("credential", credential_id),
            "policy": self._component("policy", policy_id),
            "grant": self._component("grant", grant_id),
            "arming": self._component("arming", arming_id),
        }
        if confirmation_id is not None:
            components["confirmation"] = self._component("confirmation", confirmation_id)
        envelope = {"schema": "singularity-authority-state-snapshot/0.1", "components": components}
        return {**envelope, "fingerprint": _hash(envelope)}

    def evaluate_and_persist(
        self,
        request: OperationRequest,
        *,
        provider_subject_id: str,
        credential_id: str,
        policy_id: str,
        grant_id: str,
        arming_id: str,
        confirmation_id: str | None = None,
    ) -> PersistedDecision:
        provider = self.read_provider(request.provider_id, provider_subject_id)
        credential = self.read_credential_ceiling(credential_id)
        policy = self.read_policy(policy_id)
        grant = self.read_grant(grant_id)
        arming = self.read_arming(arming_id)
        confirmation = self.read_confirmation(confirmation_id) if confirmation_id is not None else None
        snapshot = self.authority_state_snapshot(
            provider_id=request.provider_id,
            subject_id=provider_subject_id,
            credential_id=credential_id,
            policy_id=policy_id,
            grant_id=grant_id,
            arming_id=arming_id,
            confirmation_id=confirmation_id,
        )
        gate = evaluate_connection_authority(
            request,
            provider=provider,
            credential=credential,
            policy=policy,
            grant=grant,
            arming=arming,
            confirmation=confirmation,
        )
        persisted = {
            "schema": PERSISTED_DECISION_SCHEMA,
            "authority_state_fingerprint": snapshot["fingerprint"],
            "authority_inputs": {
                "provider_id": request.provider_id,
                "provider_subject_id": provider_subject_id,
                "credential_id": credential_id,
                "policy_id": policy_id,
                "grant_id": grant_id,
                "arming_id": arming_id,
                "confirmation_id": confirmation_id,
            },
            "gate_receipt": gate.as_dict(),
        }
        attempt_id = (
            f"authority-decision:{gate.decision_id}:{snapshot['fingerprint'][:16]}"
        )
        self.store.capture(
            _canonical_bytes(persisted),
            artifact_class="security.connection_gate.persisted_decision",
            producer="singularity-works:connection-gate-authority-state-v0.1",
            intent=f"persist Connection Gate decision for request {request.request_id}",
            metadata={
                "schema": PERSISTED_DECISION_SCHEMA,
                "request_id": request.request_id,
                "decision_id": gate.decision_id,
                "authority_state_fingerprint": snapshot["fingerprint"],
            },
            attempt_id=attempt_id,
        )
        row = self.store.read_attempt(attempt_id)
        if row["payload"] != _canonical_bytes(persisted):
            raise AuthorityStateError("persisted decision readback mismatch")
        return PersistedDecision(
            attempt_id=attempt_id,
            decision_id=gate.decision_id,
            authority_state_fingerprint=snapshot["fingerprint"],
            gate_receipt=gate,
            verified_readback=True,
        )

    def read_persisted_decision(self, attempt_id: str) -> PersistedDecision:
        row = self.store.read_attempt(attempt_id)
        if row["artifact_class"] != "security.connection_gate.persisted_decision":
            raise AuthorityStateError(f"not a persisted Connection Gate decision: {attempt_id}")
        doc = json.loads(row["payload"].decode("utf-8"))
        if doc.get("schema") != PERSISTED_DECISION_SCHEMA:
            raise AuthorityStateError("persisted decision schema mismatch")
        gate = _decision_from_dict(doc["gate_receipt"])
        return PersistedDecision(
            attempt_id=attempt_id,
            decision_id=gate.decision_id,
            authority_state_fingerprint=str(doc["authority_state_fingerprint"]),
            gate_receipt=gate,
            verified_readback=True,
        )

    def _persisted_decision_document(self, attempt_id: str) -> dict[str, Any]:
        row = self.store.read_attempt(attempt_id)
        if row["artifact_class"] != "security.connection_gate.persisted_decision":
            raise AuthorityStateError(f"not a persisted decision: {attempt_id}")
        doc = json.loads(row["payload"].decode("utf-8"))
        if doc.get("schema") != PERSISTED_DECISION_SCHEMA:
            raise AuthorityStateError("persisted decision schema mismatch")
        return doc

    def prepare_operation(
        self,
        *,
        operation_id: str,
        request_id: str,
        decision_attempt_id: str,
    ) -> PreparedOperation:
        doc = self._persisted_decision_document(decision_attempt_id)
        gate = _decision_from_dict(doc["gate_receipt"])
        if gate.decision != AuthorityDecision.ALLOW:
            raise AuthorityStateError(
                f"operation requires persisted ALLOW decision; got {gate.decision.value}"
            )
        if gate.request_id != request_id:
            raise AuthorityStateError("operation request_id does not match persisted decision")
        inputs = doc["authority_inputs"]
        current = self.authority_state_snapshot(
            provider_id=str(inputs["provider_id"]),
            subject_id=str(inputs["provider_subject_id"]),
            credential_id=str(inputs["credential_id"]),
            policy_id=str(inputs["policy_id"]),
            grant_id=str(inputs["grant_id"]),
            arming_id=str(inputs["arming_id"]),
            confirmation_id=(str(inputs["confirmation_id"]) if inputs.get("confirmation_id") is not None else None),
        )
        previous_fingerprint = str(doc["authority_state_fingerprint"])
        if current["fingerprint"] != previous_fingerprint:
            raise AuthorityStateError(
                "OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY: authority state changed; re-evaluate"
            )
        prepared = {
            "schema": PREPARED_OPERATION_SCHEMA,
            "operation_id": operation_id,
            "request_id": request_id,
            "decision_attempt_id": decision_attempt_id,
            "decision_id": gate.decision_id,
            "authority_state_fingerprint": previous_fingerprint,
            "stage": "PLANNED",
        }
        attempt_id = f"authority-operation:{operation_id}"
        self.store.capture(
            _canonical_bytes(prepared),
            artifact_class="security.connection_gate.prepared_operation",
            producer="singularity-works:connection-gate-authority-state-v0.1",
            intent=f"prepare consequence-bearing external operation {operation_id}",
            metadata={
                "schema": PREPARED_OPERATION_SCHEMA,
                "operation_id": operation_id,
                "request_id": request_id,
                "decision_attempt_id": decision_attempt_id,
            },
            attempt_id=attempt_id,
        )
        row = self.store.read_attempt(attempt_id)
        if row["payload"] != _canonical_bytes(prepared):
            raise AuthorityStateError("prepared operation readback mismatch")
        return PreparedOperation(
            attempt_id=attempt_id,
            operation_id=operation_id,
            request_id=request_id,
            decision_attempt_id=decision_attempt_id,
            decision_id=gate.decision_id,
            authority_state_fingerprint=previous_fingerprint,
            verified_readback=True,
        )

    def append_operation_stage(
        self,
        operation_id: str,
        stage: OperationStage,
        *,
        stage_id: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        attempt_id = f"authority-operation:{operation_id}"
        row = self.store.read_attempt(attempt_id)
        if row["artifact_class"] != "security.connection_gate.prepared_operation":
            raise AuthorityStateError(f"not a prepared operation: {operation_id}")
        existing_stages = [
            e
            for e in self.store.events_for_attempt(attempt_id)
            if e["event_type"] == "connection_operation_stage"
        ]
        if existing_stages:
            last_stage = OperationStage(str(existing_stages[-1]["payload"]["stage"]))
            if _STAGE_RANK[stage] < _STAGE_RANK[last_stage]:
                raise AuthorityStateError(
                    f"operation stage regression: {last_stage.value} -> {stage.value}"
                )
        receipt = self.store.append_event(
            "connection_operation_stage",
            attempt_id=attempt_id,
            payload={
                "operation_id": operation_id,
                "stage": stage.value,
                "stage_id": stage_id,
                "detail": _normalize(payload or {}),
            },
            event_id=f"connection-operation-stage:{operation_id}:{stage_id}",
        )
        return receipt.as_dict()

    def inspect_object(self, kind: str, object_id: str) -> dict[str, Any]:
        payload, row = self._read_object(kind, object_id)
        return {
            "kind": kind,
            "object_id": object_id,
            "attempt_id": row["attempt_id"],
            "blob_sha256": row["blob_sha256"],
            "payload": payload,
            "events": self._lifecycle_events(kind, object_id),
        }

    def list_authority_objects(self, *, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.store.latest_attempts(max(1, limit))
        result = []
        for row in rows:
            artifact_class = str(row["artifact_class"])
            if not artifact_class.startswith("security.connection_gate."):
                continue
            result.append(
                {
                    "attempt_id": row["attempt_id"],
                    "artifact_class": artifact_class,
                    "blob_sha256": row["blob_sha256"],
                    "intent": row["intent"],
                    "created_at": row["created_at"],
                }
            )
        return result
