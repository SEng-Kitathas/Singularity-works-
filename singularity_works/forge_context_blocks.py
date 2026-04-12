from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def _block_hash(payload: dict) -> str:
    return _sha256(json.dumps(payload, sort_keys=True))[:16]


# ---------------------------------------------------------------------------
# Epistemic status — promotion states for SMEM nodes
# ---------------------------------------------------------------------------

class EpistemicStatus(str, Enum):
    WITNESS             = "witness"             # observed once, full fidelity
    HYPOTHESIS          = "hypothesis"          # promoted candidate, under eval
    PROVISIONAL_SEMANTIC = "provisional_semantic" # confidence gate passed
    STABLE_SEMANTIC     = "stable_semantic"     # survived contradiction pressure
    CONTRADICTED        = "contradicted"        # explicitly refuted
    SUPERSEDED          = "superseded"          # replaced by newer evidence


# ---------------------------------------------------------------------------
# Bi-temporal block — base structure for all memory objects
# ---------------------------------------------------------------------------

@dataclass
class BiTemporalBlock:
    """
    Zep/Graphiti 4-field bi-temporal model.
    T' (transactional): when CIL created/expired the record.
    T  (event):         when the fact held in the real world.
    """
    # Transactional timeline T'
    t_created: str = field(default_factory=_now)
    t_expired: str | None = None               # set when CIL invalidates

    # Event timeline T
    valid_from: str = field(default_factory=_now)
    valid_until: str | None = None             # set when fact no longer holds

    def expire(self, valid_until: str | None = None) -> None:
        self.t_expired = _now()
        self.valid_until = valid_until or _now()

    def is_active(self) -> bool:
        return self.t_expired is None and self.valid_until is None


# ---------------------------------------------------------------------------
# WitnessBlock — EPMEM entry (raw gate result from a forge session)
# ---------------------------------------------------------------------------

@dataclass
class WitnessBlock:
    """
    Episodic witness: a single observed gate result.
    Full fidelity, append-only. Never mutated — contradiction creates a
    ContradictionBlock pointing to this.
    """
    witness_id: str = field(default_factory=lambda: str(uuid4())[:12])
    session_id: str = ""
    artifact_id: str = ""
    gate_id: str = ""
    status: str = ""                           # pass / warn / fail
    severity: str = ""                         # critical / high / medium / low
    finding_codes: list[str] = field(default_factory=list)
    finding_messages: list[str] = field(default_factory=list)
    radical_tags: list[str] = field(default_factory=list)
    capsule_id: str = ""
    language: str = ""
    confidence: str = ""                       # high / medium / low
    provenance_score: float = 1.0              # 0.0–1.0 source trust
    temporal: BiTemporalBlock = field(default_factory=BiTemporalBlock)
    block_hash: str = ""

    def __post_init__(self) -> None:
        if not self.block_hash:
            payload = {
                "witness_id": self.witness_id,
                "gate_id": self.gate_id,
                "status": self.status,
                "finding_codes": self.finding_codes,
            }
            self.block_hash = _block_hash(payload)


# ---------------------------------------------------------------------------
# SemanticBlock — SMEM entry (promoted belief with epistemic state)
# ---------------------------------------------------------------------------

@dataclass
class SemanticBlock:
    """
    A governed semantic belief: promoted from witnesses, versioned,
    carrying support/contradiction links and a distortion budget.
    """
    semantic_id: str = field(default_factory=lambda: str(uuid4())[:12])
    claim: str = ""                            # human-readable belief
    claim_type: str = ""                       # invariant / prior / axiom / pattern
    radical_family: str = ""                   # TRUST / BOUND / STATE / etc.
    capsule_family: str = ""
    status: EpistemicStatus = EpistemicStatus.HYPOTHESIS
    confidence: float = 0.5
    support_count: int = 0                     # how many witnesses support this
    contradiction_count: int = 0
    support_ids: list[str] = field(default_factory=list)
    contradiction_ids: list[str] = field(default_factory=list)
    provenance_score: float = 1.0
    distortion_budget: float = 0.20            # max allowed per-family residual
    temporal: BiTemporalBlock = field(default_factory=BiTemporalBlock)
    promotion_justification: str = ""
    block_hash: str = ""

    def __post_init__(self) -> None:
        if not self.block_hash:
            self.block_hash = _block_hash({
                "semantic_id": self.semantic_id,
                "claim": self.claim,
                "status": self.status.value if isinstance(self.status, EpistemicStatus) else self.status,
            })

    def promote(self, new_status: EpistemicStatus, justification: str = "") -> None:
        self.status = new_status
        self.promotion_justification = justification
        self.block_hash = _block_hash({
            "semantic_id": self.semantic_id,
            "claim": self.claim,
            "status": new_status.value,
            "justification": justification,
        })


# ---------------------------------------------------------------------------
# ContradictionBlock — explicit negative epistemics
# ---------------------------------------------------------------------------

@dataclass
class ContradictionBlock:
    """
    Records an explicit refutation: a new witness contradicts an existing
    semantic belief. The semantic block is superseded, not deleted.
    Implements Zep's contradiction resolution: sets valid_until of old
    belief = valid_from of contradicting evidence.
    """
    contradiction_id: str = field(default_factory=lambda: str(uuid4())[:12])
    contradicts_semantic_id: str = ""         # the SemanticBlock being refuted
    contradicts_claim: str = ""               # what was believed
    contradicting_witness_id: str = ""        # the evidence that refutes it
    new_claim: str = ""                       # what replaces it (if anything)
    contradiction_type: str = ""             # direct_refutation / evidence_conflict / invariant_violation
    confidence: float = 1.0
    temporal: BiTemporalBlock = field(default_factory=BiTemporalBlock)
    block_hash: str = ""

    def __post_init__(self) -> None:
        if not self.block_hash:
            self.block_hash = _block_hash({
                "contradiction_id": self.contradiction_id,
                "contradicts": self.contradicts_semantic_id,
                "type": self.contradiction_type,
            })


# ---------------------------------------------------------------------------
# SBUF — Volatile Session Buffer
# ---------------------------------------------------------------------------

def _encode_temporal(block: BiTemporalBlock) -> dict[str, Any]:
    return {
        "t_created": block.t_created,
        "t_expired": block.t_expired,
        "valid_from": block.valid_from,
        "valid_until": block.valid_until,
    }


def _decode_temporal(payload: dict[str, Any] | None) -> BiTemporalBlock:
    raw = dict(payload or {})
    return BiTemporalBlock(
        t_created=raw.get("t_created", _now()),
        t_expired=raw.get("t_expired"),
        valid_from=raw.get("valid_from", _now()),
        valid_until=raw.get("valid_until"),
    )


def _encode_witness(witness: WitnessBlock) -> dict[str, Any]:
    return {
        "witness_id": witness.witness_id,
        "session_id": witness.session_id,
        "artifact_id": witness.artifact_id,
        "gate_id": witness.gate_id,
        "status": witness.status,
        "severity": witness.severity,
        "finding_codes": witness.finding_codes,
        "finding_messages": witness.finding_messages[:3],
        "radical_tags": witness.radical_tags,
        "capsule_id": witness.capsule_id,
        "language": witness.language,
        "confidence": witness.confidence,
        "provenance_score": witness.provenance_score,
        "temporal": _encode_temporal(witness.temporal),
        "block_hash": witness.block_hash,
    }


def _decode_witness(payload: dict[str, Any]) -> WitnessBlock:
    raw = dict(payload)
    return WitnessBlock(
        witness_id=raw.get("witness_id", ""),
        session_id=raw.get("session_id", ""),
        artifact_id=raw.get("artifact_id", ""),
        gate_id=raw.get("gate_id", ""),
        status=raw.get("status", ""),
        severity=raw.get("severity", ""),
        finding_codes=list(raw.get("finding_codes", [])),
        finding_messages=list(raw.get("finding_messages", [])),
        radical_tags=list(raw.get("radical_tags", [])),
        capsule_id=raw.get("capsule_id", ""),
        language=raw.get("language", ""),
        confidence=raw.get("confidence", ""),
        provenance_score=float(raw.get("provenance_score", 1.0) or 1.0),
        temporal=_decode_temporal(raw.get("temporal", {
            "t_created": raw.get("t_created"),
            "t_expired": raw.get("t_expired"),
            "valid_from": raw.get("valid_from"),
            "valid_until": raw.get("valid_until"),
        })),
        block_hash=raw.get("block_hash", ""),
    )


def _encode_semantic(block: SemanticBlock) -> dict[str, Any]:
    return {
        "semantic_id": block.semantic_id,
        "claim": block.claim,
        "claim_type": block.claim_type,
        "radical_family": block.radical_family,
        "capsule_family": block.capsule_family,
        "status": block.status.value if isinstance(block.status, EpistemicStatus) else str(block.status),
        "confidence": block.confidence,
        "support_count": block.support_count,
        "contradiction_count": block.contradiction_count,
        "support_ids": block.support_ids,
        "contradiction_ids": block.contradiction_ids,
        "provenance_score": block.provenance_score,
        "distortion_budget": block.distortion_budget,
        "temporal": _encode_temporal(block.temporal),
        "promotion_justification": block.promotion_justification,
        "block_hash": block.block_hash,
    }


def _decode_semantic(payload: dict[str, Any]) -> SemanticBlock:
    raw = dict(payload)
    return SemanticBlock(
        semantic_id=raw.get("semantic_id", ""),
        claim=raw.get("claim", ""),
        claim_type=raw.get("claim_type", ""),
        radical_family=raw.get("radical_family", ""),
        capsule_family=raw.get("capsule_family", ""),
        status=EpistemicStatus(raw.get("status", EpistemicStatus.HYPOTHESIS.value)),
        confidence=float(raw.get("confidence", 0.5) or 0.5),
        support_count=int(raw.get("support_count", 0) or 0),
        contradiction_count=int(raw.get("contradiction_count", 0) or 0),
        support_ids=list(raw.get("support_ids", [])),
        contradiction_ids=list(raw.get("contradiction_ids", [])),
        provenance_score=float(raw.get("provenance_score", 1.0) or 1.0),
        distortion_budget=float(raw.get("distortion_budget", 0.20) or 0.20),
        temporal=_decode_temporal(raw.get("temporal", {})),
        promotion_justification=raw.get("promotion_justification", ""),
        block_hash=raw.get("block_hash", ""),
    )


def _encode_contradiction(block: ContradictionBlock) -> dict[str, Any]:
    return {
        "contradiction_id": block.contradiction_id,
        "contradicts_semantic_id": block.contradicts_semantic_id,
        "contradicts_claim": block.contradicts_claim,
        "contradicting_witness_id": block.contradicting_witness_id,
        "new_claim": block.new_claim,
        "contradiction_type": block.contradiction_type,
        "confidence": block.confidence,
        "temporal": _encode_temporal(block.temporal),
        "block_hash": block.block_hash,
    }


def _decode_contradiction(payload: dict[str, Any]) -> ContradictionBlock:
    raw = dict(payload)
    return ContradictionBlock(
        contradiction_id=raw.get("contradiction_id", ""),
        contradicts_semantic_id=raw.get("contradicts_semantic_id", ""),
        contradicts_claim=raw.get("contradicts_claim", ""),
        contradicting_witness_id=raw.get("contradicting_witness_id", ""),
        new_claim=raw.get("new_claim", ""),
        contradiction_type=raw.get("contradiction_type", ""),
        confidence=float(raw.get("confidence", 1.0) or 1.0),
        temporal=_decode_temporal(raw.get("temporal", {
            "t_created": raw.get("t_created"),
            "valid_from": raw.get("valid_from"),
        })),
        block_hash=raw.get("block_hash", ""),
    )


class SBUF:
    """
    Hippocampal fast-write working memory.
    Stores active gate results, provisional warrants, routing state.
    Cleared after successful consolidation into EPMEM.
    Never persisted directly — EPMEM gets the durable copies.
    """

    def __init__(self) -> None:
        self._witnesses: list[WitnessBlock] = []
        self._provisional: dict[str, Any] = {}   # key → working hypothesis
        self._routing_state: dict[str, str] = {}  # model assignments
        self._task_context: dict[str, Any] = {}

    def push_witness(self, w: WitnessBlock) -> None:
        self._witnesses.append(w)

    def set_routing(self, role: str, model_id: str) -> None:
        self._routing_state[role] = model_id

    def set_task_context(self, key: str, value: Any) -> None:
        self._task_context[key] = value

    def witnesses(self) -> list[WitnessBlock]:
        return list(self._witnesses)

    def clear(self) -> None:
        self._witnesses.clear()
        self._provisional.clear()
        self._routing_state.clear()

    def summary(self) -> dict:
        return {
            "witness_count": len(self._witnesses),
            "routing": dict(self._routing_state),
            "task_context_keys": list(self._task_context.keys()),
        }


# ---------------------------------------------------------------------------
# Consolidation gates
# ---------------------------------------------------------------------------

def _consolidation_gates(
    witness: WitnessBlock,
    existing_smem: list[SemanticBlock],
    config: dict,
) -> str:
    """
    Apply write-time promotion gates. Returns one of:
      Promote / Defer / ShadowStore / Discard / Contradict
    """
    min_confidence_threshold = config.get("min_confidence_for_promotion", 0.6)
    min_support_for_stable = config.get("min_support_for_stable", 3)

    # Discard gate: low severity warnings that aren't security relevant
    if witness.status == "warn" and witness.severity in ("low", "info"):
        return "Discard"

    # Confidence gate: low-confidence IR findings need accumulation
    if witness.confidence == "low" and witness.provenance_score < min_confidence_threshold:
        return "Defer"

    # Coherence gate: does this contradict an existing stable belief?
    for block in existing_smem:
        if (block.status == EpistemicStatus.STABLE_SEMANTIC and
                block.radical_family in witness.radical_tags and
                block.capsule_family == witness.capsule_id):
            # Same family, different verdict — contradiction signal
            if witness.status == "fail" and "safe" in block.claim.lower():
                return "Contradict"
            if witness.status == "pass" and "vulnerable" in block.claim.lower():
                return "Contradict"

    # Novelty gate: don't accumulate redundant failures
    existing_codes = set()
    for block in existing_smem:
        if block.status not in (EpistemicStatus.CONTRADICTED, EpistemicStatus.SUPERSEDED):
            existing_codes.update(block.support_ids)

    if witness.witness_id in existing_codes:
        return "Discard"

    # Promote
    return "Promote"


# ---------------------------------------------------------------------------
# ForgeContext v4.0
# ---------------------------------------------------------------------------

