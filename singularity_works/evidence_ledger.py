from __future__ import annotations
# complexity_justified: evidence ledger runtime built on typed payload and codec surfaces.
from dataclasses import asdict
from pathlib import Path
from typing import Any
import json

from .ledger_payloads import (
    AssuranceClaimLedgerPayload,
    AssuranceRollupLedgerPayload,
    CouncilValidationLedgerPayload,
    EvidenceRecord,
    FractalCycleLedgerPayload,
    GateCountLedger,
    GateLedgerFinding,
    GateLedgerPayload,
    IrisEscalationLedgerPayload,
    MonitorLedgerPayload,
    PatternSelectedLedgerPayload,
    RecursiveAuditLedgerPayload,
    RecoveredStructureLedgerPayload,
    RiskLedgerPayload,
    SessionStartLedgerPayload,
    SubstrateGateRejectLedgerPayload,
    TraceLinkLedgerPayload,
    TransformationApplicationLedgerPayload,
    TransformationPlanLedgerPayload,
    _decode_assurance_claim_payload,
    _decode_assurance_rollup_payload,
    _decode_council_validation_payload,
    _decode_fractal_cycle_payload,
    _decode_gate_payload,
    _decode_iris_escalation_payload,
    _decode_monitor_payload,
    _decode_pattern_selected_payload,
    _decode_recursive_audit_payload,
    _decode_recovered_structure_payload,
    _decode_session_start_payload,
    _decode_risk_payload,
    _payload_dict,
    _decode_substrate_gate_reject_payload,
    _decode_trace_link_payload,
    _decode_transformation_application_payload,
    _decode_transformation_plan_payload,
)


class EvidenceLedger:
    def __init__(self, path: str | Path) -> None:
        compatibility_path = Path(path)
        self.compatibility_path = compatibility_path
        self.compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        self.compatibility_path.touch(exist_ok=True)
        self.path = compatibility_path.parent / '.forge' / 'cilnx_bridge' / 'evidence_records.jsonl'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def _iter_paths(self) -> tuple[Path, ...]:
        return (self.path, self.compatibility_path)

    def reset(self) -> None:
        for target in self._iter_paths():
            target.write_text("", encoding="utf-8")

    def append(self, record: EvidenceRecord) -> None:
        payload = json.dumps({
            "record_type": record.record_type,
            "record_id": record.record_id,
            "payload": _payload_dict(record.payload),
            "timestamp": record.timestamp,
        }, ensure_ascii=False)
        # Canonical write goes to the CILNX-backed continuity line; compatibility mirror remains for tools still reading legacy path.
        for target in self._iter_paths():
            with target.open("a", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")

    def load_all(self) -> list[dict[str, Any]]:
        source = self.path if self.path.stat().st_size > 0 else self.compatibility_path
        out: list[dict[str, Any]] = []
        with source.open("r", encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def _matches(self, record: dict[str, Any], **criteria: Any) -> bool:
        from .evidence_queries import matches
        return matches(record, **criteria)

    def filter(self, **criteria: Any) -> list[dict[str, Any]]:
        from .evidence_queries import filter_records
        return filter_records(self, **criteria)

    def _session_records(self, session_id: str | None) -> list[dict[str, Any]]:
        from .evidence_queries import session_records
        return session_records(self, session_id)

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

    def iris_escalations_typed(self, session_id: str | None = None) -> list[IrisEscalationLedgerPayload]:
        return [
            _decode_iris_escalation_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "iris_escalation"
        ]

    def council_validations_typed(self, session_id: str | None = None) -> list[CouncilValidationLedgerPayload]:
        return [
            _decode_council_validation_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "council_validation"
        ]

    def substrate_gate_rejections_typed(self, session_id: str | None = None) -> list[SubstrateGateRejectLedgerPayload]:
        return [
            _decode_substrate_gate_reject_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "substrate_gate_reject"
        ]

    def session_starts_typed(self, session_id: str | None = None) -> list[SessionStartLedgerPayload]:
        return [
            _decode_session_start_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "session_start"
        ]

    def pattern_selections_typed(self, session_id: str | None = None) -> list[PatternSelectedLedgerPayload]:
        return [
            _decode_pattern_selected_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "pattern_selected"
        ]

    def recovered_structures_typed(self, session_id: str | None = None) -> list[RecoveredStructureLedgerPayload]:
        return [
            _decode_recovered_structure_payload(rec.get("payload", {}))
            for rec in self._session_records(session_id)
            if rec.get("record_type") == "recovered_structure"
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
                    else asdict(iris_escalation_payload) if iris_escalation_payload is not None
                    else asdict(council_validation_payload) if council_validation_payload is not None
                    else asdict(substrate_gate_reject_payload) if substrate_gate_reject_payload is not None
                    else asdict(pattern_selected_payload) if pattern_selected_payload is not None
                    else asdict(recovered_structure_payload) if recovered_structure_payload is not None
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
            "iris_escalations": [],
            "council_validations": [],
            "substrate_gate_rejections": [],
            "pattern_selections": [],
            "recovered_structures": [],
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
            "iris_escalation": "iris_escalations",
            "council_validation": "council_validations",
            "substrate_gate_reject": "substrate_gate_rejections",
            "pattern_selected": "pattern_selections",
            "recovered_structure": "recovered_structures",
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
            iris_escalation_payload = _decode_iris_escalation_payload(payload) if rec.get("record_type") == "iris_escalation" else None
            council_validation_payload = _decode_council_validation_payload(payload) if rec.get("record_type") == "council_validation" else None
            substrate_gate_reject_payload = _decode_substrate_gate_reject_payload(payload) if rec.get("record_type") == "substrate_gate_reject" else None
            pattern_selected_payload = _decode_pattern_selected_payload(payload) if rec.get("record_type") == "pattern_selected" else None
            recovered_structure_payload = _decode_recovered_structure_payload(payload) if rec.get("record_type") == "recovered_structure" else None
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
                else iris_escalation_payload.linked_requirements if iris_escalation_payload is not None
                else council_validation_payload.linked_requirements if council_validation_payload is not None
                else [substrate_gate_reject_payload.requirement_id] if substrate_gate_reject_payload is not None and substrate_gate_reject_payload.requirement_id
                else pattern_selected_payload.linked_requirements if pattern_selected_payload is not None
                else recovered_structure_payload.linked_requirements if recovered_structure_payload is not None
                else transformation_plan_payload.linked_requirements if transformation_plan_payload is not None
                else [recursive_audit_payload.requirement_id] if recursive_audit_payload is not None and recursive_audit_payload.requirement_id
                else [fractal_cycle_payload.requirement_id] if fractal_cycle_payload is not None and fractal_cycle_payload.requirement_id
                else payload.get("linked_requirements", [])
            )
            payload_requirement_id = (
                gate_payload.requirement_id if gate_payload is not None
                else risk_payload.requirement_id if risk_payload is not None
                else assurance_claim_payload.requirement_id if assurance_claim_payload is not None
                else assurance_rollup_payload.requirement_id if assurance_rollup_payload is not None
                else iris_escalation_payload.requirement_id if iris_escalation_payload is not None
                else council_validation_payload.requirement_id if council_validation_payload is not None
                else substrate_gate_reject_payload.requirement_id if substrate_gate_reject_payload is not None
                else pattern_selected_payload.requirement_id if pattern_selected_payload is not None
                else recovered_structure_payload.requirement_id if recovered_structure_payload is not None
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
            "iris_escalations": [],
            "council_validations": [],
            "substrate_gate_rejections": [],
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
            iris_escalation_payload = _decode_iris_escalation_payload(payload) if rec.get("record_type") == "iris_escalation" else None
            council_validation_payload = _decode_council_validation_payload(payload) if rec.get("record_type") == "council_validation" else None
            substrate_gate_reject_payload = _decode_substrate_gate_reject_payload(payload) if rec.get("record_type") == "substrate_gate_reject" else None
            recursive_audit_payload = _decode_recursive_audit_payload(payload) if rec.get("record_type") == "recursive_audit" else None
            fractal_cycle_payload = _decode_fractal_cycle_payload(payload) if rec.get("record_type") == "fractal_cycle" else None
            linked_artifact_id = payload.get("linked_artifact_id")
            payload_artifact_id = (
                gate_payload.artifact_id if gate_payload is not None
                else risk_payload.artifact_id if risk_payload is not None
                else iris_escalation_payload.artifact_id if iris_escalation_payload is not None
                else council_validation_payload.artifact_id if council_validation_payload is not None
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
                "iris_escalation": "iris_escalations",
                "council_validation": "council_validations",
                "substrate_gate_reject": "substrate_gate_rejections",
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
                    else asdict(iris_escalation_payload) if iris_escalation_payload is not None
                    else asdict(council_validation_payload) if council_validation_payload is not None
                    else asdict(substrate_gate_reject_payload) if substrate_gate_reject_payload is not None
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
            "session_starts": 0,
            "pattern_selections": 0,
            "recovered_structures": 0,
            "iris_escalations": 0,
            "council_validations": 0,
            "substrate_gate_rejections": 0,
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
            elif rtype == "session_start":
                counts["session_starts"] += 1
            elif rtype == "pattern_selected":
                counts["pattern_selections"] += 1
            elif rtype == "recovered_structure":
                counts["recovered_structures"] += 1
            elif rtype == "iris_escalation":
                counts["iris_escalations"] += 1
            elif rtype == "council_validation":
                counts["council_validations"] += 1
            elif rtype == "substrate_gate_reject":
                counts["substrate_gate_rejections"] += 1
        return counts
