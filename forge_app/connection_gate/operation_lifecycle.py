from __future__ import annotations

"""Durable external-operation lifecycle / reconciliation semantics v0.1.

No network I/O occurs in this module. Remote observations are injected evidence
with authority NONE; provider adapters are a later boundary.
"""

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from forge_app.recovery.attempt_store import AttemptStore

from .authority import AuthorityDecision
from .authority_state import AuthorityStateError, ConnectionAuthorityStateStore

OPERATION_SCHEMA = "singularity-external-operation/0.1"
OBSERVATION_SCHEMA = "singularity-external-operation-observation/0.1"


class OperationLifecycleError(RuntimeError):
    pass


class LifecycleState(str, Enum):
    PREPARED = "PREPARED"
    SUBMITTED = "SUBMITTED"
    STARTED = "STARTED"
    COMPLETED_LOCAL = "COMPLETED_LOCAL"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    REMOTE_OBSERVED_COMMITTED = "REMOTE_OBSERVED_COMMITTED"
    REMOTE_OBSERVED_ABSENT = "REMOTE_OBSERVED_ABSENT"
    FAILED_LOCAL = "FAILED_LOCAL"


class RemoteOutcome(str, Enum):
    COMMITTED = "COMMITTED"
    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"


_ALLOWED_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.PREPARED: {
        LifecycleState.SUBMITTED,
        LifecycleState.FAILED_LOCAL,
    },
    LifecycleState.SUBMITTED: {
        LifecycleState.STARTED,
        LifecycleState.COMPLETED_LOCAL,
        LifecycleState.UNKNOWN_OUTCOME,
        LifecycleState.FAILED_LOCAL,
    },
    LifecycleState.STARTED: {
        LifecycleState.COMPLETED_LOCAL,
        LifecycleState.UNKNOWN_OUTCOME,
        LifecycleState.FAILED_LOCAL,
    },
    LifecycleState.COMPLETED_LOCAL: {
        LifecycleState.REMOTE_OBSERVED_COMMITTED,
        LifecycleState.UNKNOWN_OUTCOME,
    },
    LifecycleState.UNKNOWN_OUTCOME: {
        LifecycleState.REMOTE_OBSERVED_COMMITTED,
        LifecycleState.REMOTE_OBSERVED_ABSENT,
    },
    LifecycleState.REMOTE_OBSERVED_ABSENT: set(),
    LifecycleState.REMOTE_OBSERVED_COMMITTED: set(),
    LifecycleState.FAILED_LOCAL: set(),
}


@dataclass(frozen=True)
class ExternalOperation:
    attempt_id: str
    operation_id: str
    prepared_operation_attempt_id: str
    request_id: str
    decision_attempt_id: str
    decision_id: str
    authority_state_fingerprint: str
    idempotency_key: str
    provider_id: str
    connector_id: str
    resource: str
    capability: str
    effect_fingerprint: str
    authority: str = "NONE"


@dataclass(frozen=True)
class LifecycleView:
    operation: ExternalOperation
    state: LifecycleState
    replay_authorized: bool
    lifecycle_event_count: int
    observation_count: int
    authority: str = "NONE"


def _normalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
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


def _stable_idempotency_key(operation_id: str, effect_fingerprint: str) -> str:
    body = f"{operation_id}\n{effect_fingerprint}\n".encode("utf-8")
    return "sw-op-" + hashlib.sha256(body).hexdigest()[:32]


class ExternalOperationLifecycleStore:
    def __init__(self, authority_state: ConnectionAuthorityStateStore) -> None:
        self.authority_state = authority_state
        self.store: AttemptStore = authority_state.store

    def register_operation(
        self,
        *,
        operation_id: str,
        prepared_operation_attempt_id: str,
        provider_id: str,
        connector_id: str,
        resource: str,
        capability: str,
        effect_fingerprint: str,
        idempotency_key: str | None = None,
    ) -> ExternalOperation:
        if not all(
            (operation_id, prepared_operation_attempt_id, provider_id, connector_id, resource, capability, effect_fingerprint)
        ):
            raise ValueError("operation identity/effect fields must be non-empty")
        prepared_row = self.store.read_attempt(prepared_operation_attempt_id)
        if prepared_row["artifact_class"] != "security.connection_gate.prepared_operation":
            raise OperationLifecycleError("external operation requires a qualified prepared-operation receipt")
        prepared = json.loads(prepared_row["payload"].decode("utf-8"))
        if str(prepared.get("operation_id")) != operation_id:
            raise OperationLifecycleError("prepared operation ID mismatch")
        decision_attempt_id = str(prepared["decision_attempt_id"])
        decision = self.authority_state.read_persisted_decision(decision_attempt_id)
        if decision.gate_receipt.decision != AuthorityDecision.ALLOW:
            raise OperationLifecycleError("prepared operation does not reference an ALLOW decision")
        if decision.gate_receipt.provider_id != provider_id:
            raise OperationLifecycleError("provider identity mismatch")
        if decision.gate_receipt.connector_id != connector_id:
            raise OperationLifecycleError("connector identity mismatch")
        if decision.gate_receipt.resource != resource:
            raise OperationLifecycleError("resource identity mismatch")
        if decision.gate_receipt.capability != capability:
            raise OperationLifecycleError("capability identity mismatch")
        key = idempotency_key or _stable_idempotency_key(operation_id, effect_fingerprint)
        document = {
            "schema": OPERATION_SCHEMA,
            "operation_id": operation_id,
            "prepared_operation_attempt_id": prepared_operation_attempt_id,
            "request_id": str(prepared["request_id"]),
            "decision_attempt_id": decision_attempt_id,
            "decision_id": decision.decision_id,
            "authority_state_fingerprint": decision.authority_state_fingerprint,
            "idempotency_key": key,
            "provider_id": provider_id,
            "connector_id": connector_id,
            "resource": resource,
            "capability": capability,
            "effect_fingerprint": effect_fingerprint,
            "authority": "NONE",
        }
        attempt_id = f"external-operation:{operation_id}"
        self.store.capture(
            _canonical_bytes(document),
            artifact_class="security.connection_gate.external_operation",
            producer="singularity-works:operation-lifecycle-v0.1",
            intent=f"preserve external operation identity before submission {operation_id}",
            metadata={
                "schema": OPERATION_SCHEMA,
                "operation_id": operation_id,
                "idempotency_key": key,
                "decision_attempt_id": decision_attempt_id,
            },
            attempt_id=attempt_id,
        )
        row = self.store.read_attempt(attempt_id)
        if row["payload"] != _canonical_bytes(document):
            raise OperationLifecycleError("external operation readback mismatch")
        return self.read_operation(operation_id)

    def read_operation(self, operation_id: str) -> ExternalOperation:
        row = self.store.read_attempt(f"external-operation:{operation_id}")
        if row["artifact_class"] != "security.connection_gate.external_operation":
            raise OperationLifecycleError(f"not an external operation: {operation_id}")
        doc = json.loads(row["payload"].decode("utf-8"))
        if doc.get("schema") != OPERATION_SCHEMA or doc.get("operation_id") != operation_id:
            raise OperationLifecycleError("external operation envelope mismatch")
        return ExternalOperation(
            attempt_id=row["attempt_id"],
            operation_id=operation_id,
            prepared_operation_attempt_id=str(doc["prepared_operation_attempt_id"]),
            request_id=str(doc["request_id"]),
            decision_attempt_id=str(doc["decision_attempt_id"]),
            decision_id=str(doc["decision_id"]),
            authority_state_fingerprint=str(doc["authority_state_fingerprint"]),
            idempotency_key=str(doc["idempotency_key"]),
            provider_id=str(doc["provider_id"]),
            connector_id=str(doc["connector_id"]),
            resource=str(doc["resource"]),
            capability=str(doc["capability"]),
            effect_fingerprint=str(doc["effect_fingerprint"]),
            authority=str(doc.get("authority") or "NONE"),
        )

    def _events(self, operation_id: str) -> list[dict[str, Any]]:
        return self.store.events_for_attempt(f"external-operation:{operation_id}")

    def inspect(self, operation_id: str) -> LifecycleView:
        operation = self.read_operation(operation_id)
        state = LifecycleState.PREPARED
        replay_authorized = False
        lifecycle_count = 0
        observation_count = 0
        for event in self._events(operation_id):
            if event["event_type"] == "external_operation_lifecycle":
                state = LifecycleState(str(event["payload"]["to_state"]))
                lifecycle_count += 1
                if state == LifecycleState.SUBMITTED:
                    replay_authorized = False
            elif event["event_type"] == "external_operation_replay_authorized":
                replay_authorized = True
            elif event["event_type"] == "external_operation_remote_observation":
                observation_count += 1
        return LifecycleView(
            operation=operation,
            state=state,
            replay_authorized=replay_authorized,
            lifecycle_event_count=lifecycle_count,
            observation_count=observation_count,
            authority="NONE",
        )

    def _decision_inputs_and_current_fingerprint(self, operation: ExternalOperation) -> tuple[dict[str, Any], str]:
        doc = self.authority_state._persisted_decision_document(operation.decision_attempt_id)
        if str(doc["gate_receipt"]["decision_id"]) != operation.decision_id:
            raise OperationLifecycleError("decision identity mismatch")
        inputs = doc["authority_inputs"]
        current = self.authority_state.authority_state_snapshot(
            provider_id=str(inputs["provider_id"]),
            subject_id=str(inputs["provider_subject_id"]),
            credential_id=str(inputs["credential_id"]),
            policy_id=str(inputs["policy_id"]),
            grant_id=str(inputs["grant_id"]),
            arming_id=str(inputs["arming_id"]),
            confirmation_id=(str(inputs["confirmation_id"]) if inputs.get("confirmation_id") is not None else None),
        )
        return doc, str(current["fingerprint"])

    def _assert_authority_current(self, operation: ExternalOperation) -> None:
        doc, current = self._decision_inputs_and_current_fingerprint(operation)
        expected = str(doc["authority_state_fingerprint"])
        if expected != operation.authority_state_fingerprint:
            raise OperationLifecycleError("operation/decision authority fingerprint mismatch")
        if current != expected:
            raise OperationLifecycleError(
                "OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY: authority changed before consequence"
            )

    def transition(
        self,
        operation_id: str,
        to_state: LifecycleState,
        *,
        transition_id: str,
        detail: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        event_id = f"external-operation-lifecycle:{operation_id}:{transition_id}"
        requested_detail = _normalize(detail or {})
        for existing in self._events(operation_id):
            if existing["event_id"] != event_id:
                continue
            payload = existing["payload"]
            if str(payload.get("to_state")) != to_state.value or payload.get("detail") != requested_detail:
                raise OperationLifecycleError("lifecycle transition ID conflict with different immutable observation")
            return existing
        view = self.inspect(operation_id)
        from_state = view.state
        if to_state == LifecycleState.SUBMITTED:
            if from_state == LifecycleState.REMOTE_OBSERVED_ABSENT:
                if not view.replay_authorized:
                    raise OperationLifecycleError("RETRY_AFTER_UNKNOWN_REQUIRES_RECONCILIATION_AND_REPLAY_AUTHORIZATION")
            elif from_state != LifecycleState.PREPARED:
                raise OperationLifecycleError(f"blind resubmission rejected from {from_state.value}")
            self._assert_authority_current(view.operation)
        allowed = set(_ALLOWED_TRANSITIONS[from_state])
        if from_state == LifecycleState.REMOTE_OBSERVED_ABSENT and view.replay_authorized:
            allowed.add(LifecycleState.SUBMITTED)
        if to_state not in allowed:
            raise OperationLifecycleError(f"illegal lifecycle transition: {from_state.value} -> {to_state.value}")
        receipt = self.store.append_event(
            "external_operation_lifecycle",
            attempt_id=view.operation.attempt_id,
            payload={
                "operation_id": operation_id,
                "idempotency_key": view.operation.idempotency_key,
                "from_state": from_state.value,
                "to_state": to_state.value,
                "transition_id": transition_id,
                "detail": requested_detail,
                "authority": "NONE",
            },
            event_id=event_id,
        )
        return receipt.as_dict()

    def observe_remote(
        self,
        operation_id: str,
        outcome: RemoteOutcome,
        *,
        observation_id: str,
        observed_idempotency_key: str,
        source: str,
        remote_identity: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        view = self.inspect(operation_id)
        op = view.operation
        if observed_idempotency_key != op.idempotency_key:
            raise OperationLifecycleError("remote observation idempotency identity mismatch")
        if view.state not in {LifecycleState.UNKNOWN_OUTCOME, LifecycleState.COMPLETED_LOCAL}:
            raise OperationLifecycleError(f"remote observation invalid from {view.state.value}")
        document = {
            "schema": OBSERVATION_SCHEMA,
            "operation_id": operation_id,
            "idempotency_key": op.idempotency_key,
            "provider_id": op.provider_id,
            "connector_id": op.connector_id,
            "resource": op.resource,
            "observation_id": observation_id,
            "source": source,
            "outcome": outcome.value,
            "remote_identity": _normalize(remote_identity or {}),
            "authority": "NONE",
        }
        receipt = self.store.append_event(
            "external_operation_remote_observation",
            attempt_id=op.attempt_id,
            payload=document,
            event_id=f"external-operation-observation:{operation_id}:{observation_id}",
        )
        if outcome == RemoteOutcome.COMMITTED:
            self.transition(
                operation_id,
                LifecycleState.REMOTE_OBSERVED_COMMITTED,
                transition_id=f"observation-{observation_id}-committed",
                detail={"observation_id": observation_id},
            )
        elif outcome == RemoteOutcome.ABSENT:
            self.transition(
                operation_id,
                LifecycleState.REMOTE_OBSERVED_ABSENT,
                transition_id=f"observation-{observation_id}-absent",
                detail={"observation_id": observation_id},
            )
        return receipt.as_dict()

    def authorize_replay_after_absence(
        self,
        operation_id: str,
        *,
        authorization_id: str,
        reason: str,
    ) -> dict[str, Any]:
        view = self.inspect(operation_id)
        if view.state != LifecycleState.REMOTE_OBSERVED_ABSENT:
            raise OperationLifecycleError("replay authorization requires reconciled remote absence")
        self._assert_authority_current(view.operation)
        receipt = self.store.append_event(
            "external_operation_replay_authorized",
            attempt_id=view.operation.attempt_id,
            payload={
                "operation_id": operation_id,
                "idempotency_key": view.operation.idempotency_key,
                "authorization_id": authorization_id,
                "reason": reason,
                "authority_state_fingerprint": view.operation.authority_state_fingerprint,
                "authority": "NONE",
            },
            event_id=f"external-operation-replay-authorization:{operation_id}:{authorization_id}",
        )
        return receipt.as_dict()
