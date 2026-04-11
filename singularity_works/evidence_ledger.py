from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
import json
import time


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
            linked_claims = gate_payload.linked_claims if gate_payload is not None else payload.get("linked_claims", [])
            discharged_claims = gate_payload.discharged_claims if gate_payload is not None else payload.get("discharged_claims", [])
            matches = (
                claim_id in discharged_claims
                or claim_id in linked_claims
                or payload.get("claim_id") == claim_id
            )
            if not matches:
                continue
            bucket = {
                "gate_result": "gate_results",
                "monitor_event": "monitor_events",
                "assurance_claim": "assurance_claims",
            }.get(rec.get("record_type"))
            if bucket:
                out[bucket].append(asdict(gate_payload) if gate_payload is not None else payload)
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
        }
        for rec in self._session_records(session_id):
            payload = rec.get("payload", {})
            gate_payload = _decode_gate_payload(payload) if rec.get("record_type") == "gate_result" else None
            linked_requirements = gate_payload.linked_requirements if gate_payload is not None else payload.get("linked_requirements", [])
            payload_requirement_id = gate_payload.requirement_id if gate_payload is not None else payload.get("requirement_id")
            if payload_requirement_id != requirement_id and requirement_id not in linked_requirements:
                continue
            bucket = buckets.get(rec.get("record_type"))
            if bucket:
                out[bucket].append(asdict(gate_payload) if gate_payload is not None else payload)
            claim_ids.update(gate_payload.linked_claims if gate_payload is not None else payload.get("linked_claims", []))
            if payload.get("claim_id"):
                claim_ids.add(payload["claim_id"])
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
        }
        for rec in self.load_all():
            payload = rec.get("payload", {})
            gate_payload = _decode_gate_payload(payload) if rec.get("record_type") == "gate_result" else None
            linked_artifact_id = payload.get("linked_artifact_id")
            payload_artifact_id = gate_payload.artifact_id if gate_payload is not None else payload.get("artifact_id")
            if payload_artifact_id != artifact_id and linked_artifact_id != artifact_id:
                continue
            bucket = {
                "gate_result": "gate_results",
                "monitor_event": "monitor_events",
                "risk": "risks",
            }.get(rec.get("record_type"))
            if bucket:
                out[bucket].append(asdict(gate_payload) if gate_payload is not None else payload)
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
            if rtype == "risk":
                counts["risks"] += 1
            elif rtype == "monitor_event" and payload.get("status") == "fail":
                counts["monitor_failures"] += 1
            elif rtype == "assurance_rollup" and payload.get("status") == "red":
                counts["assurance_red"] += 1
            elif rtype == "assurance_claim":
                counts["assurance_claims"] += 1
        return counts
