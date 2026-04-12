from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any


def _list() -> list:
    return []


def _dict() -> dict:
    return {}


def _payload(obj: Any) -> dict[str, Any]:
    return asdict(obj)


def _decode(payload_cls, payload: dict[str, Any] | None):
    return payload_cls(**(payload or {}))


@dataclass
class TaintChainPayload:
    source_type: str = "USER_INPUT"
    source_line: int = 0
    boundary_type: str = "UNKNOWN"
    sink_line: int = 0
    hops: int = 1
    directed: bool = True


@dataclass
class TrustBoundaryPayload:
    source: str = "unknown"
    boundary_type: str = "UNKNOWN"
    sink_name: str = ""
    sink_line: int = 0
    tainted_input: str | None = None
    directed: bool = False
    source_line: int = 0
    source_type: str = "UNKNOWN"
    hops: int = 0
    structure_id: str = ""
    dangerous_calls: list[str] = field(default_factory=_list)


@dataclass
class CompoundDerivationPayload:
    rule: str = ""
    fact_type: str = ""
    description: str = ""
    injection_families: list[str] = field(default_factory=_list)
    trust_signal: bool = False


@dataclass
class GateStatusPayload:
    gate_id: str = ""
    status: str = "pass"


@dataclass
class GateFindingPayload:
    gate_id: str = ""
    code: str = ""
    message: str = ""
    severity: str = "medium"
    linked_laws: list[str] = field(default_factory=_list)


@dataclass
class GateResultPayload:
    gate_id: str = ""
    gate_family: str = ""
    status: str = "pass"
    finding_codes: list[str] = field(default_factory=_list)
    finding_messages: list[str] = field(default_factory=_list)
    severity: str = "medium"


@dataclass
class MonitorEventPayload:
    monitor_id: str = ""
    status: str = "unknown"
    claim_id: str = ""
    message: str = ""
    severity: str = "medium"
    linked_requirements: list[str] = field(default_factory=_list)
    linked_claims: list[str] = field(default_factory=_list)


@dataclass
class TransformationCandidatePayload:
    candidate_id: str = ""
    summary: str = ""
    rationale: str = ""
    rewrite_candidate: str = ""
    target_spans: list[list[int]] = field(default_factory=_list)
    source_gate: str = ""
    confidence: str = "moderate"
    safety_level: str = "review_required"
    auto_apply: bool = False
    linked_laws: list[str] = field(default_factory=_list)
    transformation_axiom: str = ""


@dataclass
class SwitchboardDecisionPayload:
    candidate_id: str = ""
    tier: int = 0
    apply: bool = False
    rationale: str = ""


@dataclass
class PropagationPayload:
    rule_id: str = ""
    fact_type: str = ""
    severity: str = "medium"
    rationale: str = ""
    upstream_types: list[str] = field(default_factory=_list)


@dataclass
class DangerousSinkPayload:
    sink_type: str = "unknown"
    structure_id: str = ""


@dataclass
class ResourceLifecyclePayload:
    violations: list[dict[str, Any]] = field(default_factory=_list)


@dataclass
class Fact:
    fact_id: str
    fact_type: str
    scope: str
    confidence: str = "moderate"
    payload: dict[str, Any] = field(default_factory=_dict)
    evidence_refs: list[str] = field(default_factory=_list)
    linked_laws: list[str] = field(default_factory=_list)
    upstream_facts: list[str] = field(default_factory=_list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def _from_payload(
        cls,
        *,
        fact_id: str,
        fact_type: str,
        scope: str,
        confidence: str,
        payload: Any,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls(
            fact_id=fact_id,
            fact_type=fact_type,
            scope=scope,
            confidence=confidence,
            payload=_payload(payload),
            evidence_refs=evidence_refs or [],
            linked_laws=linked_laws or [],
            upstream_facts=upstream_facts or [],
        )

    @classmethod
    def from_gate_status(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: GateStatusPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="gate_status",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_gate_finding(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: GateFindingPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="gate_finding",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_gate_result(
        cls,
        *,
        fact_id: str,
        fact_type: str,
        scope: str,
        confidence: str,
        payload: GateResultPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type=fact_type,
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_monitor_event(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: MonitorEventPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="monitor_event",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_transformation_candidate(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: TransformationCandidatePayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="transformation_candidate",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_switchboard_decision(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: SwitchboardDecisionPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="switchboard_decision",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_propagation(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: PropagationPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type=payload.fact_type,
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_dangerous_sink(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: DangerousSinkPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="dangerous_sink_present",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_resource_lifecycle(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: ResourceLifecyclePayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="resource_lifecycle_incomplete",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_compound_derivation(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: CompoundDerivationPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type=payload.fact_type,
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_trust_boundary(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: TrustBoundaryPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="trust_boundary_crossed",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_taint_chain(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: TaintChainPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="taint_chain",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )


