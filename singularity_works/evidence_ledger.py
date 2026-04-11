from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
import json
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


class EvidenceLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def reset(self) -> None:
        self.path.write_text("", encoding="utf-8")

    def append(self, record: EvidenceRecord) -> None:
        payload = json.dumps({
            "record_type": record.record_type,
            "record_id": record.record_id,
            "payload": _payload_dict(record.payload),
            "timestamp": record.timestamp,
        }, ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")

    def load_all(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def _matches(self, record: dict[str, Any], **criteria: Any) -> bool:
        payload = record.get("payload", {})
        for key, value in criteria.items():
            if record.get(key) != value and payload.get(key) != value:
                return False
        return True

    def filter(self, **criteria: Any) -> list[dict[str, Any]]:
        return [r for r in self.load_all() if self._matches(r, **criteria)]

    def _session_records(self, session_id: str | None) -> list[dict[str, Any]]:
        records = self.load_all()
        if not session_id:
            return records
        return [r for r in records if session_id in str(r.get("record_id", ""))]

    def gate_results_typed(self, session_id: str | None = None) -> list[GateLedgerPayload]:
        return [
            _decode_gate_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "gate_result"
        ]

    def monitor_events_typed(self, session_id: str | None = None) -> list[MonitorLedgerPayload]:
        return [
            _decode_monitor_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "monitor_event"
        ]

    def risks_typed(self, session_id: str | None = None) -> list[RiskLedgerPayload]:
        return [
            _decode_risk_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "risk"
        ]

    def assurance_rollups_typed(self, session_id: str | None = None) -> list[AssuranceRollupLedgerPayload]:
        return [
            _decode_assurance_rollup_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "assurance_rollup"
        ]

    def assurance_claims_typed(self, session_id: str | None = None) -> list[AssuranceClaimLedgerPayload]:
        return [
            _decode_assurance_claim_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "assurance_claim"
        ]

    def trace_links_typed(self, session_id: str | None = None) -> list[TraceLinkLedgerPayload]:
        return [
            _decode_trace_link_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "trace_link"
        ]

    def transformation_plans_typed(self, session_id: str | None = None) -> list[TransformationPlanLedgerPayload]:
        return [
            _decode_transformation_plan_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "transformation_plan"
        ]

    def transformation_applications_typed(self, session_id: str | None = None) -> list[TransformationApplicationLedgerPayload]:
        return [
            _decode_transformation_application_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "transformation_application"
        ]

    def recursive_audits_typed(self, session_id: str | None = None) -> list[RecursiveAuditLedgerPayload]:
        return [
            _decode_recursive_audit_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "recursive_audit"
        ]

    def fractal_cycles_typed(self, session_id: str | None = None) -> list[FractalCycleLedgerPayload]:
        return [
            _decode_fractal_cycle_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "fractal_cycle"
        ]

    def rollup_status_counts(self, session_id: str | None = None) -> dict[str, int]:
        counts = {"pass": 0, "warn": 0, "fail": 0, "residual": 0}
        for payload in self.gate_results_typed(session_id):
            counts[payload.status] = counts.get(payload.status, 0) + 1
        return counts

    def rollup_claim(self, claim_id: str, session_id: str | None = None) -> dict[str, Any]:
        out = {
            "claim_id": claim_id,
            "gate_results": [],
            "monitor_events": [],
            "assurance_claims": [],
            "status": "residual",
        }
        for rec in self._session_records(session_id):
            payload = rec.get("payload", {})
            gate_payload = _decode_gate_payload(payload) if rec.get("record_type") == "gate_result" else None
            monitor_payload = _decode_monitor_payload(payload) if rec.get("record_type") == "monitor_event" else None
            risk_payload = _decode_risk_payload(payload) if rec.get("record_type") == "risk" else None
            assurance_claim_payload = _decode_assurance_claim_payload(payload) if rec.get("record_type") == "assurance_claim" else None
            assurance_rollup_payload = _decode_assurance_rollup_payload(payload) if rec.get("record_type") == "assurance_rollup" else None
            linked_claims = (
                gate_payload.linked_claims if gate_payload is not None
                else monitor_payload.linked_claims if monitor_payload is not None
                else risk_payload.linked_claims if risk_payload is not None
                else assurance_claim_payload.linked_claims if assurance_claim_payload is not None
                else payload.get("linked_claims", [])
            )
            discharged_claims = gate_payload.discharged_claims if gate_payload is not None else payload.get("discharged_claims", [])
            payload_claim_id = (
                monitor_payload.claim_id if monitor_payload is not None
                else assurance_claim_payload.claim_id if assurance_claim_payload is not None
                else payload.get("claim_id")
            )
            matches = (
                claim_id in discharged_claims
                or claim_id in linked_claims
                or payload_claim_id == claim_id
            )
            if not matches:
                continue
            bucket = {
                "gate_result": "gate_results",
                "monitor_event": "monitor_events",
                "assurance_claim": "assurance_claims",
            }.get(rec.get("record_type"))
            if bucket:
                out[bucket].append(
                    asdict(gate_payload) if gate_payload is not None
                    else asdict(monitor_payload) if monitor_payload is not None
                    else asdict(risk_payload) if risk_payload is not None
                    else asdict(assurance_claim_payload) if assurance_claim_payload is not None
                    else asdict(assurance_rollup_payload) if assurance_rollup_payload is not None
                    else asdict(trace_link_payload) if trace_link_payload is not None
                    else asdict(transformation_plan_payload) if transformation_plan_payload is not None
                    else asdict(transformation_application_payload) if transformation_application_payload is not None
                    else asdict(recursive_audit_payload) if recursive_audit_payload is not None
                    else asdict(fractal_cycle_payload) if fractal_cycle_payload is not None
                    else payload
                )
        if any(x.get("status") == "fail" for x in out["monitor_events"]):
            out["status"] = "falsified"
        elif any(x.get("status") == "falsified" for x in out["assurance_claims"]):
            out["status"] = "falsified"
        elif out["assurance_claims"] and all(
            x.get("status") in {"discharged", "monitored"}
            for x in out["assurance_claims"]
        ):
            out["status"] = "discharged"
        elif any(out.values()):
            out["status"] = "monitored"
        return out

    def rollup_requirement(
        self,
        requirement_id: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        out = {
            "requirement_id": requirement_id,
            "session_id": session_id,
            "gate_results": [],
            "monitor_events": [],
            "risks": [],
            "assurance": [],
            "trace_links": [],
            "transformation_plans": [],
            "transformation_applications": [],
            "recursive_audits": [],
            "fractal_cycles": [],
            "claim_rollups": [],
        }
        claim_ids: set[str] = set()
        buckets = {
            "gate_result": "gate_results",
            "monitor_event": "monitor_events",
            "risk": "risks",
            "assurance_rollup": "assurance",
            "assurance_claim": "assurance",
            "trace_link": "trace_links",
            "transformation_plan": "transformation_plans",
            "transformation_application": "transformation_applications",
            "recursive_audit": "recursive_audits",
            "fractal_cycle": "fractal_cycles",
        }
        for rec in self._session_records(session_id):
            payload = rec.get("payload", {})
            gate_payload = _decode_gate_payload(payload) if rec.get("record_type") == "gate_result" else None
            monitor_payload = _decode_monitor_payload(payload) if rec.get("record_type") == "monitor_event" else None
            risk_payload = _decode_risk_payload(payload) if rec.get("record_type") == "risk" else None
            assurance_claim_payload = _decode_assurance_claim_payload(payload) if rec.get("record_type") == "assurance_claim" else None
            assurance_rollup_payload = _decode_assurance_rollup_payload(payload) if rec.get("record_type") == "assurance_rollup" else None
            trace_link_payload = _decode_trace_link_payload(payload) if rec.get("record_type") == "trace_link" else None
            transformation_plan_payload = _decode_transformation_plan_payload(payload) if rec.get("record_type") == "transformation_plan" else None
            transformation_application_payload = _decode_transformation_application_payload(payload) if rec.get("record_type") == "transformation_application" else None
            recursive_audit_payload = _decode_recursive_audit_payload(payload) if rec.get("record_type") == "recursive_audit" else None
            fractal_cycle_payload = _decode_fractal_cycle_payload(payload) if rec.get("record_type") == "fractal_cycle" else None
            linked_requirements = (
                gate_payload.linked_requirements if gate_payload is not None
                else monitor_payload.linked_requirements if monitor_payload is not None
                else risk_payload.linked_requirements if risk_payload is not None
                else assurance_claim_payload.linked_requirements if assurance_claim_payload is not None
                else assurance_rollup_payload.linked_requirements if assurance_rollup_payload is not None
                else trace_link_payload.linked_requirements if trace_link_payload is not None
                else transformation_plan_payload.linked_requirements if transformation_plan_payload is not None
                else [recursive_audit_payload.requirement_id] if recursive_audit_payload is not None and recursive_audit_payload.requirement_id else [fractal_cycle_payload.requirement_id] if fractal_cycle_payload is not None and fractal_cycle_payload.requirement_id else payload.get("linked_requirements", [])
            )
            payload_requirement_id = (
                gate_payload.requirement_id if gate_payload is not None
                else risk_payload.requirement_id if risk_payload is not None
                else assurance_claim_payload.requirement_id if assurance_claim_payload is not None
                else assurance_rollup_payload.requirement_id if assurance_rollup_payload is not None
                else transformation_plan_payload.requirement_id if transformation_plan_payload is not None
                else transformation_application_payload.requirement_id if transformation_application_payload is not None
                else recursive_audit_payload.requirement_id if recursive_audit_payload is not None
                else fractal_cycle_payload.requirement_id if fractal_cycle_payload is not None
                else payload.get("requirement_id")
            )
            if payload_requirement_id != requirement_id and requirement_id not in linked_requirements:
                continue
            bucket = buckets.get(rec.get("record_type"))
            if bucket:
                out[bucket].append(
                    asdict(gate_payload) if gate_payload is not None
                    else asdict(monitor_payload) if monitor_payload is not None
                    else asdict(risk_payload) if risk_payload is not None
                    else asdict(assurance_claim_payload) if assurance_claim_payload is not None
                    else asdict(assurance_rollup_payload) if assurance_rollup_payload is not None
                    else asdict(trace_link_payload) if trace_link_payload is not None
                    else payload
                )
            claim_ids.update(
                gate_payload.linked_claims if gate_payload is not None
                else monitor_payload.linked_claims if monitor_payload is not None
                else risk_payload.linked_claims if risk_payload is not None
                else assurance_claim_payload.linked_claims if assurance_claim_payload is not None
                else payload.get("linked_claims", [])
            )
            payload_claim_id = (
                monitor_payload.claim_id if monitor_payload is not None
                else assurance_claim_payload.claim_id if assurance_claim_payload is not None
                else payload.get("claim_id")
            )
            if payload_claim_id:
                claim_ids.add(payload_claim_id)
        out["claim_rollups"] = [
            self.rollup_claim(claim_id, session_id)
            for claim_id in sorted(claim_ids)
        ]
        return out

    def rollup_artifact(self, artifact_id: str) -> dict[str, Any]:
        out = {
            "artifact_id": artifact_id,
            "gate_results": [],
            "monitor_events": [],
            "risks": [],
            "transformation_plans": [],
            "transformation_applications": [],
            "recursive_audits": [],
            "fractal_cycles": [],
        }
        for rec in self.load_all():
            payload = rec.get("payload", {})
            gate_payload = _decode_gate_payload(payload) if rec.get("record_type") == "gate_result" else None
            monitor_payload = _decode_monitor_payload(payload) if rec.get("record_type") == "monitor_event" else None
            risk_payload = _decode_risk_payload(payload) if rec.get("record_type") == "risk" else None
            transformation_plan_payload = _decode_transformation_plan_payload(payload) if rec.get("record_type") == "transformation_plan" else None
            transformation_application_payload = _decode_transformation_application_payload(payload) if rec.get("record_type") == "transformation_application" else None
            recursive_audit_payload = _decode_recursive_audit_payload(payload) if rec.get("record_type") == "recursive_audit" else None
            fractal_cycle_payload = _decode_fractal_cycle_payload(payload) if rec.get("record_type") == "fractal_cycle" else None
            linked_artifact_id = payload.get("linked_artifact_id")
            payload_artifact_id = (
                gate_payload.artifact_id if gate_payload is not None
                else risk_payload.artifact_id if risk_payload is not None
                else transformation_plan_payload.artifact_id if transformation_plan_payload is not None
                else transformation_application_payload.transformed_artifact_id if transformation_application_payload is not None
                else recursive_audit_payload.artifact_id if recursive_audit_payload is not None
                else fractal_cycle_payload.artifact_id if fractal_cycle_payload is not None
                else payload.get("artifact_id")
            )
            if payload_artifact_id != artifact_id and linked_artifact_id != artifact_id:
                continue
            bucket = {
                "gate_result": "gate_results",
                "monitor_event": "monitor_events",
                "risk": "risks",
                "transformation_plan": "transformation_plans",
                "transformation_application": "transformation_applications",
                "recursive_audit": "recursive_audits",
                "fractal_cycle": "fractal_cycles",
            }.get(rec.get("record_type"))
            if bucket:
                out[bucket].append(
                    asdict(gate_payload) if gate_payload is not None
                    else asdict(monitor_payload) if monitor_payload is not None
                    else asdict(risk_payload) if risk_payload is not None
                    else asdict(transformation_plan_payload) if transformation_plan_payload is not None
                    else asdict(transformation_application_payload) if transformation_application_payload is not None
                    else asdict(recursive_audit_payload) if recursive_audit_payload is not None
                    else asdict(fractal_cycle_payload) if fractal_cycle_payload is not None
                    else payload
                )
        return out

    def rollup_session(self, session_id: str) -> dict[str, Any]:
        records = self._session_records(session_id)
        counts = {
            "session_id": session_id,
            "records": len(records),
            "gate_status": self.rollup_status_counts(session_id),
            "risks": 0,
            "monitor_failures": 0,
            "assurance_red": 0,
            "assurance_claims": 0,
        }
        for rec in records:
            rtype = rec.get("record_type")
            payload = rec.get("payload", {})
            assurance_rollup_payload = _decode_assurance_rollup_payload(payload) if rtype == "assurance_rollup" else None
            if rtype == "risk":
                counts["risks"] += 1
            elif rtype == "monitor_event" and payload.get("status") == "fail":
                counts["monitor_failures"] += 1
            elif rtype == "assurance_rollup" and assurance_rollup_payload is not None and assurance_rollup_payload.status == "red":
                counts["assurance_red"] += 1
            elif rtype == "assurance_claim":
                counts["assurance_claims"] += 1
        return counts
