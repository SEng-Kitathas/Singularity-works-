from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import time

from .fractal_cycle import FractalEvent, FractalStage
from .models import AppliedTransformation, AssuranceClaim, TransformationCandidate


@dataclass
class GateCountLedger:
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    residual_count: int = 0


@dataclass
class IrisEscalationLedgerPayload:
    artifact_id: str = ""
    requirement_id: str = ""
    classes: list[str] = field(default_factory=list)
    confidence: str = "moderate"
    count: int = 0
    reasoning: str = ""
    linked_requirements: list[str] = field(default_factory=list)


@dataclass
class CouncilValidationLedgerPayload:
    artifact_id: str = ""
    requirement_id: str = ""
    consensus: str = "CHALLENGE"
    confidence: float = 0.0
    downgraded: bool = False
    synthesis: str = ""
    linked_requirements: list[str] = field(default_factory=list)


@dataclass
class SubstrateGateRejectLedgerPayload:
    reason: str = ""
    size_bytes: int = 0
    limit_bytes: int = 0
    requirement_id: str = ""


@dataclass
class SessionStartLedgerPayload:
    mode: str = "run"
    project_tag: str = ""
    requirement_id: str = ""


@dataclass
class PatternSelectedLedgerPayload:
    pattern_id: str = ""
    family: str = ""
    radicals: list[str] = field(default_factory=list)
    requirement_id: str = ""
    linked_laws: list[str] = field(default_factory=list)
    genome_bundle: dict[str, Any] = field(default_factory=dict)
    linked_requirements: list[str] = field(default_factory=list)


@dataclass
class RecoveredStructureLedgerPayload:
    structure_id: str = ""
    requirement_id: str = ""
    type: str = ""
    confidence: str = "moderate"
    radicals: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    linked_requirements: list[str] = field(default_factory=list)


@dataclass
class RecursiveAuditLedgerPayload:
    requirement_id: str = ""
    artifact_id: str = ""
    gate_counts: GateCountLedger = field(default_factory=GateCountLedger)
    recovery_confidence: str = "moderate"
    naivety_flags: list[str] = field(default_factory=list)
    implementation_depth: str = "thin"
    assurance_status: str = "unknown"


@dataclass
class FractalCycleLedgerPayload:
    requirement_id: str = ""
    artifact_id: str = ""
    cycle_id: str = ""
    events: list[FractalEvent] = field(default_factory=list)


@dataclass
class TransformationPlanLedgerPayload:
    requirement_id: str = ""
    artifact_id: str = ""
    linked_requirements: list[str] = field(default_factory=list)
    candidates: list[TransformationCandidate] = field(default_factory=list)


@dataclass
class TransformationApplicationLedgerPayload:
    requirement_id: str = ""
    source_artifact_id: str = ""
    transformed_artifact_id: str = ""
    applied_transformations: list[AppliedTransformation] = field(default_factory=list)


@dataclass
class TraceLinkLedgerPayload:
    source_id: str = ""
    target_id: str = ""
    link_type: str = ""
    confidence: str = "moderate"
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    linked_requirements: list[str] = field(default_factory=list)


@dataclass
class AssuranceClaimLedgerPayload:
    claim_id: str = ""
    claim_text: str = ""
    status: str = "residual"
    claim_type: str = "generic"
    confidence: str = "moderate"
    supported_by: list[str] = field(default_factory=list)
    monitored_by: list[str] = field(default_factory=list)
    residual_risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    responsibility_boundary: str = "software"
    evidence_refs: list[str] = field(default_factory=list)
    parent_claim_id: str = ""
    child_claim_ids: list[str] = field(default_factory=list)
    warrant: str = ""
    requirement_id: str = ""
    artifact_id: str = ""
    linked_requirements: list[str] = field(default_factory=list)
    linked_claims: list[str] = field(default_factory=list)


@dataclass
class AssuranceRollupLedgerPayload:
    requirement_id: str = ""
    artifact_id: str = ""
    status: str = "green"
    discharged: list[str] = field(default_factory=list)
    monitored: list[str] = field(default_factory=list)
    residual: list[str] = field(default_factory=list)
    falsified: list[str] = field(default_factory=list)
    claims: list[AssuranceClaim] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    graph_depth: int = 0
    graph_edges: int = 0
    warrant_coverage: float = 0.0
    warranted_claims: int = 0
    total_claims: int = 0
    linked_requirements: list[str] = field(default_factory=list)


@dataclass
class RiskLedgerPayload:
    risk_id: str = ""
    description: str = ""
    severity: str = "medium"
    linked_requirements: list[str] = field(default_factory=list)
    linked_artifacts: list[str] = field(default_factory=list)
    linked_claims: list[str] = field(default_factory=list)
    requirement_id: str = ""
    artifact_id: str = ""


@dataclass
class MonitorLedgerPayload:
    monitor_id: str = ""
    status: str = "unknown"
    claim_id: str = ""
    message: str = ""
    severity: str = "medium"
    linked_requirements: list[str] = field(default_factory=list)
    linked_claims: list[str] = field(default_factory=list)


@dataclass
class GateLedgerFinding:
    code: str = ""
    message: str = ""
    severity: str = "medium"
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class GateLedgerPayload:
    requirement_id: str = ""
    artifact_id: str = ""
    status: str = "residual"
    gate_id: str = ""
    gate_family: str = ""
    discharged_claims: list[str] = field(default_factory=list)
    residual_obligations: list[str] = field(default_factory=list)
    findings: list[GateLedgerFinding] = field(default_factory=list)
    linked_requirements: list[str] = field(default_factory=list)
    linked_claims: list[str] = field(default_factory=list)


@dataclass
class EvidenceRecord:
    record_type: str
    record_id: str
    payload: dict[str, Any]
    timestamp: float = field(default_factory=time.time)


def _payload_dict(payload: Any) -> dict[str, Any]:
    return asdict(payload) if hasattr(payload, "__dataclass_fields__") else payload


def _decode(payload_cls, payload: dict[str, Any] | None):
    return payload_cls(**(payload or {}))


def _decode_gate_payload(payload: dict[str, Any] | None) -> GateLedgerPayload:
    raw = dict(payload or {})
    findings = [
        _decode(GateLedgerFinding, item)
        for item in raw.get("findings", [])
    ]
    raw["findings"] = findings
    return GateLedgerPayload(**raw)


def _decode_monitor_payload(payload: dict[str, Any] | None) -> MonitorLedgerPayload:
    return MonitorLedgerPayload(**(payload or {}))


def _decode_risk_payload(payload: dict[str, Any] | None) -> RiskLedgerPayload:
    return RiskLedgerPayload(**(payload or {}))


def _decode_assurance_claim_payload(payload: dict[str, Any] | None) -> AssuranceClaimLedgerPayload:
    return AssuranceClaimLedgerPayload(**(payload or {}))


def _decode_trace_link_payload(payload: dict[str, Any] | None) -> TraceLinkLedgerPayload:
    return TraceLinkLedgerPayload(**(payload or {}))


def _decode_iris_escalation_payload(payload: dict[str, Any] | None) -> IrisEscalationLedgerPayload:
    return IrisEscalationLedgerPayload(**(payload or {}))


def _decode_council_validation_payload(payload: dict[str, Any] | None) -> CouncilValidationLedgerPayload:
    return CouncilValidationLedgerPayload(**(payload or {}))


def _decode_substrate_gate_reject_payload(payload: dict[str, Any] | None) -> SubstrateGateRejectLedgerPayload:
    return SubstrateGateRejectLedgerPayload(**(payload or {}))


def _decode_session_start_payload(payload: dict[str, Any] | None) -> SessionStartLedgerPayload:
    return SessionStartLedgerPayload(**(payload or {}))


def _decode_pattern_selected_payload(payload: dict[str, Any] | None) -> PatternSelectedLedgerPayload:
    return PatternSelectedLedgerPayload(**(payload or {}))


def _decode_recovered_structure_payload(payload: dict[str, Any] | None) -> RecoveredStructureLedgerPayload:
    return RecoveredStructureLedgerPayload(**(payload or {}))


def _decode_recursive_audit_payload(payload: dict[str, Any] | None) -> RecursiveAuditLedgerPayload:
    raw = dict(payload or {})
    raw["gate_counts"] = GateCountLedger(
        pass_count=int((raw.get("gate_counts") or {}).get("pass", 0) or 0),
        warn_count=int((raw.get("gate_counts") or {}).get("warn", 0) or 0),
        fail_count=int((raw.get("gate_counts") or {}).get("fail", 0) or 0),
        residual_count=int((raw.get("gate_counts") or {}).get("residual", 0) or 0),
    )
    return RecursiveAuditLedgerPayload(**raw)


def _decode_fractal_cycle_payload(payload: dict[str, Any] | None) -> FractalCycleLedgerPayload:
    raw = dict(payload or {})
    raw["events"] = [
        FractalEvent(
            stage=FractalStage(item.get("stage", "PROBE")),
            status=item.get("status", "unknown"),
            details=item.get("details", {}),
        )
        for item in raw.get("events", [])
    ]
    return FractalCycleLedgerPayload(**raw)


def _decode_transformation_plan_payload(payload: dict[str, Any] | None) -> TransformationPlanLedgerPayload:
    raw = dict(payload or {})
    raw["candidates"] = [TransformationCandidate(**item) for item in raw.get("candidates", [])]
    return TransformationPlanLedgerPayload(**raw)


def _decode_transformation_application_payload(payload: dict[str, Any] | None) -> TransformationApplicationLedgerPayload:
    raw = dict(payload or {})
    raw["applied_transformations"] = [AppliedTransformation(**item) for item in raw.get("applied_transformations", [])]
    return TransformationApplicationLedgerPayload(**raw)


def _decode_assurance_rollup_payload(payload: dict[str, Any] | None) -> AssuranceRollupLedgerPayload:
    raw = dict(payload or {})
    raw["claims"] = [AssuranceClaim(**item) for item in raw.get("claims", [])]
    return AssuranceRollupLedgerPayload(**raw)


