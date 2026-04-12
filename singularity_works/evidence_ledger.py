from __future__ import annotations
# complexity_justified: evidence ledger runtime built on typed payload and codec surfaces.
from dataclasses import asdict
from pathlib import Path
from typing import Any
import json

from .evidence_rollups import EvidenceLedgerRollupsMixin
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


class EvidenceLedger(EvidenceLedgerRollupsMixin):
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

