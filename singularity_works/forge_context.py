#!/usr/bin/env python3
"""
Singularity Works — Forge Context Manager v4.0

Implements the CIL vNext memory architecture for the Python forge:

  SBUF  — volatile session buffer (hippocampal fast-write layer)
  EPMEM — episodic memory (Zep 4-field bi-temporal witness ledger)
  SMEM  — semantic memory (governed promotion, epistemic states)
  ContradictionBlock — explicit supersession + negative epistemics
  Consolidation — write-time promotion gates
  Retrieval Compiler — task-conditioned context packing

Timestamps follow Zep/Graphiti bi-temporal model (arXiv 2501.13956):
  t_created / t_expired   ∈ T' — transactional timeline (when CIL saw it)
  valid_from / valid_until ∈ T  — event timeline (when it held in the world)

Backward compatible: v3.0 files migrated on load.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
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

class ForgeContext:
    """
    Project cognitive ledger for a Singularity Works session.

    Memory layers:
      SBUF  — volatile session buffer (cleared after consolidation)
      EPMEM — episodic witness ledger (Zep 4-field bi-temporal, append-only)
      SMEM  — semantic memory (governed promotion, epistemic states)
      ContradictionBlocks — explicit negative epistemics

    Isomorphisms with the broader CIL vNext architecture:
      SBUF  ↔  CIL Layer 5A (hippocampal fast-write)
      EPMEM ↔  CIL Layer 5B (durable witness ledger)
      SMEM  ↔  CIL Layer 5C (neocortical slow-learning)
      Contradiction ↔ CIL Layer 3 Contradiction Graph
    """

    VERSION = "4.0.0"

    # Consolidation configuration
    CONSOLIDATION_CONFIG = {
        "min_confidence_for_promotion": 0.6,
        "min_support_for_stable": 3,
        "max_sessions": 50,
        "max_epmem_entries": 5000,
        "max_smem_entries": 500,
    }

    def __init__(self, path: str | Path = ".forge-context.json") -> None:
        self.path = Path(path)
        self._ctx: dict[str, Any] = {}
        self.sbuf = SBUF()

    # ── Persistence ───────────────────────────────────────────────────

    def init(
        self,
        project_name: str,
        project_root: str = ".",
        project_type: str = "unknown",
        description: str = "",
    ) -> None:
        timeline_id = str(uuid4())
        self._ctx = {
            "version": self.VERSION,
            "project": {
                "name": project_name,
                "root": str(Path(project_root).absolute()),
                "type": project_type,
                "description": description,
                "goals": [],
                "constraints": [],
            },
            "codebase": {"key_files": [], "conventions": {}, "dependencies": []},

            # CIL memory layers
            "epmem": [],        # list[WitnessBlock as dict]
            "smem": [],         # list[SemanticBlock as dict]
            "contradictions": [],  # list[ContradictionBlock as dict]

            # Legacy forge fields (v3.0 compatible)
            "forge": {
                "genome_priors": {},
                "sessions": [],
                "proven_axioms": [],
                "derived_fact_history": [],
            },

            "models": {
                "routing_prefs": {"reasoner": None, "coder": None, "ghost": None},
                "last_seen": {},
            },
            "shadow_docs": {
                "trace_matrix": None,
                "research_crosswalk": None,
                "custom_docs": [],
            },
            "log": {"tasks": [], "decisions": [], "issues": []},
            "timelines": [{
                "id": timeline_id, "name": "main", "parent": None,
                "created": _now(), "status": "active",
            }],
            "active_timeline": timeline_id,
            "session_id": str(uuid4()),
            "created": _now(),
            "updated": _now(),
            "integrity": {"hash": ""},
        }
        self._rehash()

    def load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"No context at {self.path}")
        self._ctx = json.loads(self.path.read_text(encoding="utf-8"))
        v = self._ctx.get("version", "")
        if v.startswith("2."):
            self._migrate_v2()
        elif v.startswith("3."):
            self._migrate_v3()

    def save(self) -> None:
        self._ctx["updated"] = _now()
        self._rehash()
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._ctx, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def _rehash(self) -> None:
        body = {k: v for k, v in self._ctx.items() if k != "integrity"}
        self._ctx["integrity"] = {
            "hash": _sha256(json.dumps(body, sort_keys=True)),
            "timestamp": _now(),
        }

    def verify(self) -> bool:
        body = {k: v for k, v in self._ctx.items() if k != "integrity"}
        expected = _sha256(json.dumps(body, sort_keys=True))
        return self._ctx.get("integrity", {}).get("hash") == expected

    def _migrate_v2(self) -> None:
        old = self._ctx
        project = old.get("singletonState", {}).get("project", {})
        log = old.get("logState", {})
        self.init(
            project_name=project.get("name", "migrated"),
            project_root=project.get("root", "."),
            project_type=project.get("type", "unknown"),
            description=project.get("description", ""),
        )
        self._ctx["log"]["tasks"] = log.get("tasks", [])
        self._ctx["log"]["decisions"] = log.get("decisions", [])
        self._ctx["log"]["issues"] = log.get("issues", [])

    def _migrate_v3(self) -> None:
        """Migrate v3.0 to v4.0: add CIL memory layers if absent."""
        if "epmem" not in self._ctx:
            self._ctx["epmem"] = []
        if "smem" not in self._ctx:
            self._ctx["smem"] = []
        if "contradictions" not in self._ctx:
            self._ctx["contradictions"] = []
        self._ctx["version"] = self.VERSION

    # ── SBUF — volatile session buffer ───────────────────────────────

    def sbuf_push(
        self,
        session_id: str,
        artifact_id: str,
        gate_id: str,
        status: str,
        severity: str,
        finding_codes: list[str],
        finding_messages: list[str],
        radical_tags: list[str],
        capsule_id: str,
        language: str = "",
        confidence: str = "high",
        valid_from: str | None = None,
    ) -> WitnessBlock:
        """
        Push a raw gate result into SBUF.
        Does NOT touch EPMEM — call consolidate() after a session.
        valid_from: when the vulnerability/observation held (event time).
                    Defaults to now if not provided.
        """
        w = WitnessBlock(
            session_id=session_id,
            artifact_id=artifact_id,
            gate_id=gate_id,
            status=status,
            severity=severity,
            finding_codes=finding_codes,
            finding_messages=finding_messages,
            radical_tags=radical_tags,
            capsule_id=capsule_id,
            language=language,
            confidence=confidence,
            temporal=BiTemporalBlock(
                t_created=_now(),
                valid_from=valid_from or _now(),
            ),
        )
        self.sbuf.push_witness(w)
        return w

    # ── EPMEM — episodic witness ledger ───────────────────────────────

    def epmem_commit(self, witness: WitnessBlock) -> None:
        """Commit a WitnessBlock to durable EPMEM. Append-only."""
        entry = {
            "witness_id": witness.witness_id,
            "session_id": witness.session_id,
            "artifact_id": witness.artifact_id,
            "gate_id": witness.gate_id,
            "status": witness.status,
            "severity": witness.severity,
            "finding_codes": witness.finding_codes,
            "finding_messages": witness.finding_messages[:3],  # trim for storage
            "radical_tags": witness.radical_tags,
            "capsule_id": witness.capsule_id,
            "language": witness.language,
            "confidence": witness.confidence,
            "provenance_score": witness.provenance_score,
            "t_created": witness.temporal.t_created,
            "t_expired": witness.temporal.t_expired,
            "valid_from": witness.temporal.valid_from,
            "valid_until": witness.temporal.valid_until,
            "block_hash": witness.block_hash,
        }
        epmem = self._ctx["epmem"]
        epmem.append(entry)
        # Rolling window: keep last N entries
        max_e = self.CONSOLIDATION_CONFIG["max_epmem_entries"]
        if len(epmem) > max_e:
            self._ctx["epmem"] = epmem[-max_e:]

    def epmem_query(
        self,
        radical_family: str | None = None,
        capsule_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Query EPMEM by radical family, capsule, or status."""
        results = []
        for entry in reversed(self._ctx["epmem"]):
            if radical_family and radical_family not in entry.get("radical_tags", []):
                continue
            if capsule_id and entry.get("capsule_id") != capsule_id:
                continue
            if status and entry.get("status") != status:
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    # ── SMEM — semantic memory ────────────────────────────────────────

    def smem_promote(
        self,
        claim: str,
        claim_type: str,
        radical_family: str,
        capsule_family: str,
        supporting_witness_ids: list[str],
        confidence: float = 0.7,
        justification: str = "",
    ) -> SemanticBlock:
        """
        Promote a pattern to SMEM. Starts at HYPOTHESIS; caller can
        call smem_advance() to move through the epistemic states.
        """
        block = SemanticBlock(
            claim=claim,
            claim_type=claim_type,
            radical_family=radical_family,
            capsule_family=capsule_family,
            status=EpistemicStatus.HYPOTHESIS,
            confidence=confidence,
            support_count=len(supporting_witness_ids),
            support_ids=supporting_witness_ids,
            temporal=BiTemporalBlock(valid_from=_now()),
            promotion_justification=justification,
        )
        self._ctx["smem"].append({
            **vars(block),
            "status": block.status.value,
            "temporal": {
                "t_created": block.temporal.t_created,
                "t_expired": block.temporal.t_expired,
                "valid_from": block.temporal.valid_from,
                "valid_until": block.temporal.valid_until,
            },
        })
        return block

    def smem_advance(self, semantic_id: str, new_status: EpistemicStatus, justification: str = "") -> bool:
        """Advance a SMEM block to the next epistemic state."""
        for block in self._ctx["smem"]:
            if block.get("semantic_id") == semantic_id:
                block["status"] = new_status.value
                block["promotion_justification"] = justification
                block["block_hash"] = _block_hash({
                    "semantic_id": semantic_id,
                    "status": new_status.value,
                })
                return True
        return False

    def smem_query(
        self,
        radical_family: str | None = None,
        status: EpistemicStatus | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Query SMEM by radical family and/or epistemic status."""
        results = []
        active_statuses = {
            EpistemicStatus.STABLE_SEMANTIC.value,
            EpistemicStatus.PROVISIONAL_SEMANTIC.value,
            EpistemicStatus.HYPOTHESIS.value,
        }
        for block in self._ctx["smem"]:
            if block.get("status") not in active_statuses:
                continue
            if radical_family and block.get("radical_family") != radical_family:
                continue
            if status and block.get("status") != status.value:
                continue
            results.append(block)
            if len(results) >= limit:
                break
        return results

    def smem_get_priors(self) -> dict[str, dict]:
        """
        Return stable SMEM beliefs as genome priors with calibrated distortion budgets.

        Distortion budget calibration (isomorphism: arXiv 2509.24431 temperature→gap):
          High support density → tighter centroid → lower budget
          High confidence spread → looser centroid → higher budget
        """
        import math as _math
        priors: dict[str, dict] = {}

        # Calibrate per radical family
        family_groups: dict[str, list] = {}
        for block in self._ctx["smem"]:
            if block.get("status") in (
                EpistemicStatus.STABLE_SEMANTIC.value,
                EpistemicStatus.PROVISIONAL_SEMANTIC.value,
            ):
                fam = block.get("radical_family", "UNKNOWN")
                family_groups.setdefault(fam, []).append(block)

        calibrated: dict[str, float] = {}
        for fam, blocks in family_groups.items():
            supports = [b.get("support_count", 1) for b in blocks]
            confs = [b.get("confidence", 0.5) for b in blocks]
            avg_sup = sum(supports) / len(supports)
            mean_c = sum(confs) / len(confs)
            std_dev = (_math.sqrt(sum((c - mean_c) ** 2 for c in confs) / len(confs))
                       if len(confs) > 1 else 0.0)
            density_factor = 1.0 / (1.0 + _math.log1p(avg_sup / 5.0))
            spread_factor = 1.0 + std_dev * 0.5
            calibrated[fam] = max(0.05, min(0.50, 0.20 * density_factor * spread_factor))

        for block in self._ctx["smem"]:
            if block.get("status") in (
                EpistemicStatus.STABLE_SEMANTIC.value,
                EpistemicStatus.PROVISIONAL_SEMANTIC.value,
            ):
                cid = block.get("capsule_family", "")
                if cid:
                    fam = block.get("radical_family", "UNKNOWN")
                    priors[cid] = {
                        "fires": block.get("support_count", 1),
                        "confidence": block.get("confidence", 0.5),
                        "status": block.get("status"),
                        "claim": block.get("claim", ""),
                        "radical_family": fam,
                        "distortion_budget": calibrated.get(fam, 0.20),
                    }

        for cid, data in self._ctx["forge"]["genome_priors"].items():
            if cid not in priors:
                priors[cid] = {
                    "fires": data.get("fires", 0), "confidence": 0.5,
                    "status": "legacy", "distortion_budget": 0.20,
                }
        return priors

    def record_contradiction(
        self,
        contradicts_semantic_id: str,
        contradicting_witness_id: str,
        contradiction_type: str,
        new_claim: str = "",
    ) -> ContradictionBlock:
        """
        Record a contradiction.
        Invalidates the targeted SemanticBlock using Zep's mechanism:
        sets valid_until of old belief = valid_from of new evidence.
        """
        contradicts_claim = ""
        for block in self._ctx["smem"]:
            if block.get("semantic_id") == contradicts_semantic_id:
                contradicts_claim = block.get("claim", "")
                # Zep mechanism: set valid_until = now (valid_from of contradicting evidence)
                if "temporal" in block:
                    block["temporal"]["valid_until"] = _now()
                    block["temporal"]["t_expired"] = _now()
                block["status"] = EpistemicStatus.CONTRADICTED.value
                block["contradiction_count"] = block.get("contradiction_count", 0) + 1
                break

        cb = ContradictionBlock(
            contradicts_semantic_id=contradicts_semantic_id,
            contradicts_claim=contradicts_claim,
            contradicting_witness_id=contradicting_witness_id,
            new_claim=new_claim,
            contradiction_type=contradiction_type,
        )
        self._ctx["contradictions"].append({
            "contradiction_id": cb.contradiction_id,
            "contradicts_semantic_id": cb.contradicts_semantic_id,
            "contradicts_claim": cb.contradicts_claim,
            "contradicting_witness_id": cb.contradicting_witness_id,
            "new_claim": cb.new_claim,
            "contradiction_type": cb.contradiction_type,
            "confidence": cb.confidence,
            "t_created": cb.temporal.t_created,
            "valid_from": cb.temporal.valid_from,
            "block_hash": cb.block_hash,
        })
        return cb

    # ── Contradiction Graph queries (TM-006) ─────────────────────────
    # The flat contradiction list acts as an adjacency list:
    # each ContradictionBlock encodes one directed edge (contradicted → contradicting).
    # These methods provide the same query interface as the Rust ContradictionGraph,
    # enabling drop-in replacement once a proper DiGraph is warranted.

    def contradiction_active_roots(self) -> list[dict]:
        """
        Return SMEM blocks that have no incoming contradiction edges AND are not
        contradicted. These represent the current worldview — what CIL believes now.
        Mirrors Rust ContradictionGraph.active_roots().
        """
        contradicted_ids = {
            c["contradicts_semantic_id"]
            for c in self._ctx.get("contradictions", [])
        }
        return [
            b for b in self._ctx.get("smem", [])
            if b.get("semantic_id") not in contradicted_ids
            and b.get("status") != EpistemicStatus.CONTRADICTED.value
        ]

    def contradiction_chain(self, semantic_id: str) -> list[dict]:
        """
        Return all contradictions reachable from a given semantic_id
        (full refutation ancestry via DFS over the contradiction list).
        Mirrors Rust ContradictionGraph.contradiction_chain().
        """
        visited: set[str] = set()
        result: list[dict] = []
        queue = [semantic_id]
        contradictions = self._ctx.get("contradictions", [])
        while queue:
            sid = queue.pop()
            if sid in visited:
                continue
            visited.add(sid)
            for c in contradictions:
                if c.get("contradicts_semantic_id") == sid:
                    result.append(c)
                    # Follow chain: the contradicting_witness may point to a newer belief
                    # Look for any SMEM block that introduced this contradicting witness
                    for b in self._ctx.get("smem", []):
                        if b.get("semantic_id") == c.get("contradicting_witness_id"):
                            queue.append(b["semantic_id"])
        return result

    def contradiction_summary(self) -> dict:
        """
        Return a summary suitable for the compile_context Retrieval Compiler.
        Mirrors Rust ContradictionGraph.summary().
        """
        contradictions = self._ctx.get("contradictions", [])
        smem = self._ctx.get("smem", [])
        active_roots = self.contradiction_active_roots()
        contradicted = [b for b in smem if b.get("status") == EpistemicStatus.CONTRADICTED.value]
        return {
            "total_beliefs": len(smem),
            "active_beliefs": len(active_roots),
            "contradicted_beliefs": len(contradicted),
            "contradiction_edges": len(contradictions),
            "summary": (
                f"ContradictionGraph: {len(active_roots)}/{len(smem)} active beliefs "
                f"| {len(contradictions)} contradiction edges"
            ),
        }

    # ── Consolidation — SBUF → EPMEM → SMEM ──────────────────────────

    def consolidate(self, session_id: str, final_status: str) -> dict:
        """
        Run the consolidation cycle:
        1. Commit all SBUF witnesses to EPMEM
        2. Apply promotion gates
        3. Promote qualifying patterns to SMEM
        4. Detect contradictions against existing SMEM
        5. Clear SBUF (hippocampal reset)
        Returns a summary of what was committed and promoted.
        """
        witnesses = self.sbuf.witnesses()
        if not witnesses:
            return {"committed": 0, "promoted": 0, "contradictions": 0}

        existing_smem = [
            SemanticBlock(**{
                k: (EpistemicStatus(v) if k == "status" else v)
                for k, v in b.items()
                if k not in ("temporal", "block_hash")
            })
            for b in self._ctx["smem"]
        ]

        committed = 0
        promoted = 0
        contradictions_found = 0
        capsule_hits: dict[str, list[str]] = {}

        for w in witnesses:
            # Always commit to EPMEM — full fidelity witness
            self.epmem_commit(w)
            committed += 1

            # Apply promotion gates
            decision = _consolidation_gates(w, existing_smem, self.CONSOLIDATION_CONFIG)

            if decision == "Contradict":
                # Find the semantic block this contradicts
                for smem_block in existing_smem:
                    if (smem_block.radical_family and
                            any(r in w.radical_tags for r in [smem_block.radical_family]) and
                            smem_block.status == EpistemicStatus.STABLE_SEMANTIC):
                        self.record_contradiction(
                            contradicts_semantic_id=smem_block.semantic_id,
                            contradicting_witness_id=w.witness_id,
                            contradiction_type="evidence_conflict",
                            new_claim=f"Gate {w.gate_id} produced {w.status} — contradicts prior belief",
                        )
                        contradictions_found += 1
                        break

            elif decision == "Promote" and w.status == "fail" and w.finding_codes:
                # Accumulate by capsule for batch promotion
                key = w.capsule_id or w.gate_id
                if key not in capsule_hits:
                    capsule_hits[key] = []
                capsule_hits[key].append(w.witness_id)

        # Batch promote capsules that accumulated enough evidence
        min_support = self.CONSOLIDATION_CONFIG["min_support_for_stable"]
        for capsule_id, witness_ids in capsule_hits.items():
            # Find the radical family from the witnesses
            radical_tags = []
            for w in witnesses:
                if (w.capsule_id or w.gate_id) == capsule_id:
                    radical_tags.extend(w.radical_tags)
            radical_family = radical_tags[0] if radical_tags else "UNKNOWN"

            # Check if already in SMEM
            already = any(
                b.get("capsule_family") == capsule_id and
                b.get("status") not in (EpistemicStatus.CONTRADICTED.value, EpistemicStatus.SUPERSEDED.value)
                for b in self._ctx["smem"]
            )

            if not already:
                # Find the most common finding code
                finding_summary = ", ".join(
                    w.finding_codes[0] for w in witnesses
                    if (w.capsule_id or w.gate_id) == capsule_id and w.finding_codes
                )[:80]
                self.smem_promote(
                    claim=f"Capsule '{capsule_id}' fires reliably ({finding_summary})",
                    claim_type="capsule_prior",
                    radical_family=radical_family,
                    capsule_family=capsule_id,
                    supporting_witness_ids=witness_ids,
                    confidence=min(0.5 + len(witness_ids) * 0.1, 0.9),
                    justification=f"Promoted from {len(witness_ids)} witness(es) in session {session_id}",
                )
                promoted += 1
            else:
                # Strengthen existing belief
                for block in self._ctx["smem"]:
                    if block.get("capsule_family") == capsule_id:
                        block["support_count"] = block.get("support_count", 0) + len(witness_ids)
                        block["support_ids"] = block.get("support_ids", []) + witness_ids
                        # Advance to stable if enough support
                        if (block.get("status") == EpistemicStatus.HYPOTHESIS.value and
                                block["support_count"] >= min_support):
                            block["status"] = EpistemicStatus.PROVISIONAL_SEMANTIC.value
                            promoted += 1
                        elif (block.get("status") == EpistemicStatus.PROVISIONAL_SEMANTIC.value and
                                block["support_count"] >= min_support * 2):
                            block["status"] = EpistemicStatus.STABLE_SEMANTIC.value

        # Update legacy genome_priors (backward compat)
        for w in witnesses:
            if w.capsule_id:
                priors = self._ctx["forge"]["genome_priors"]
                if w.capsule_id not in priors:
                    priors[w.capsule_id] = {"fires": 0, "green_after_fix": 0}
                priors[w.capsule_id]["fires"] += 1

        # Clear SBUF (hippocampal reset)
        self.sbuf.clear()

        return {
            "committed": committed,
            "promoted": promoted,
            "contradictions": contradictions_found,
            "session_id": session_id,
            "final_status": final_status,
        }

    # ── Retrieval Compiler ────────────────────────────────────────────

    def compile_context(
        self,
        radical_hints: list[str] | None = None,
        max_witnesses: int = 10,
        max_semantic: int = 15,
        include_contradictions: bool = True,
    ) -> str:
        """
        Task-conditioned context packet.
        Assembles: recent witnesses, stable SMEM beliefs, open contradictions.
        This is what gets injected into the model context — not raw storage.

        Isomorphism: the Retrieval Compiler in CIL Layer 5E.
        """
        parts: list[str] = []

        # 1. Stable SMEM beliefs (project knowledge)
        stable = [
            b for b in self._ctx["smem"]
            if b.get("status") in (
                EpistemicStatus.STABLE_SEMANTIC.value,
                EpistemicStatus.PROVISIONAL_SEMANTIC.value,
            )
        ]
        if radical_hints:
            stable = [
                b for b in stable
                if b.get("radical_family") in radical_hints
            ]
        if stable:
            parts.append("## Project Semantic Memory (Stable Beliefs)")
            for b in stable[:max_semantic]:
                status_tag = "✓ STABLE" if b["status"] == EpistemicStatus.STABLE_SEMANTIC.value else "~ PROVISIONAL"
                parts.append(
                    f"  [{status_tag}] {b['claim']} "
                    f"(family={b.get('radical_family','?')}, "
                    f"confidence={b.get('confidence',0):.2f}, "
                    f"support={b.get('support_count',0)})"
                )

        # 2. Recent EPMEM witnesses (what the forge has actually seen)
        recent_epmem = list(reversed(self._ctx["epmem"]))[:max_witnesses]
        if recent_epmem:
            parts.append("\n## Recent Episodic Witnesses (Gate Results)")
            for e in recent_epmem:
                codes = ", ".join(e.get("finding_codes", []))
                parts.append(
                    f"  [{e.get('status','?').upper()}] {e.get('gate_id','?')} "
                    f"| codes: {codes or 'none'} "
                    f"| capsule: {e.get('capsule_id','?')} "
                    f"| lang: {e.get('language','?')}"
                )

        # 3. Open contradictions (unresolved tensions)
        if include_contradictions and self._ctx["contradictions"]:
            # Use graph query for active-roots view (TM-006)
            c_summary = self.contradiction_summary()
            sections.append(f"## Contradiction Graph\n  {c_summary['summary']}")
            if c_summary["contradicted_beliefs"] > 0:
                sections.append(f"  ({c_summary['contradicted_beliefs']} beliefs currently contradicted)")
            recent_contradictions = self._ctx["contradictions"][-5:]
            parts.append("\n## Open Contradictions (Unresolved)")
            for c in recent_contradictions:
                parts.append(
                    f"  [CONTRADICTION] {c.get('contradiction_type','?')}: "
                    f"'{c.get('contradicts_claim','?')[:80]}'"
                )

        # 4. Top genome priors
        priors = self.smem_get_priors()
        top = sorted(priors.items(), key=lambda x: x[1].get("fires", 0), reverse=True)[:8]
        if top:
            parts.append("\n## Genome Priors (Project-Specific Capsule Weights)")
            for cid, data in top:
                parts.append(
                    f"  {cid}: fires={data.get('fires',0)} "
                    f"confidence={data.get('confidence',0):.2f}"
                )

        return "\n".join(parts) if parts else "(no prior context for this project)"

    # ── Forge session (v3.0 compat + v4.0 consolidation) ─────────────

    def record_forge_session(
        self,
        session_id: str,
        files_analyzed: list[str],
        gate_counts: dict[str, int],
        findings: list[dict],
        genome_capsules_fired: list[str],
        transformation_candidates: list[dict],
        applied_transformations: int,
        final_status: str,
        rounds: int = 0,
        auto_consolidate: bool = True,
    ) -> None:
        """
        Record a complete forge session.
        If auto_consolidate=True, also runs the SBUF → EPMEM consolidation.
        """
        session = {
            "id": session_id,
            "timestamp": _now(),
            "files": files_analyzed,
            "gate_counts": gate_counts,
            "finding_count": len(findings),
            "high_critical": sum(
                1 for f in findings if f.get("severity") in ("critical", "high")
            ),
            "capsules_fired": genome_capsules_fired,
            "candidates": len(transformation_candidates),
            "applied": applied_transformations,
            "status": final_status,
            "dialect_rounds": rounds,
        }
        sessions = self._ctx["forge"]["sessions"]
        sessions.append(session)
        if len(sessions) > self.CONSOLIDATION_CONFIG["max_sessions"]:
            self._ctx["forge"]["sessions"] = sessions[-self.CONSOLIDATION_CONFIG["max_sessions"]:]

        # Push findings to SBUF for consolidation
        for f in findings:
            self.sbuf_push(
                session_id=session_id,
                artifact_id=f.get("artifact_id", session_id),
                gate_id=f.get("gate_id", "unknown"),
                status=f.get("status", "fail"),
                severity=f.get("severity", "medium"),
                finding_codes=f.get("finding_codes", []),
                finding_messages=[f.get("message", "")],
                radical_tags=f.get("radical_tags", []),
                capsule_id=f.get("capsule_id", ""),
                language=f.get("language", ""),
                confidence=f.get("confidence", "high"),
            )

        # Proven axioms
        for tc in transformation_candidates:
            axiom = tc.get("transformation_axiom") or tc.get("axiom")
            if axiom and final_status == "green":
                proven = self._ctx["forge"]["proven_axioms"]
                if axiom not in proven:
                    proven.append(axiom)

        if auto_consolidate:
            self.consolidate(session_id, final_status)

    # ── v3.0 compat methods ───────────────────────────────────────────

    def get_genome_priors(self) -> dict[str, dict]:
        return self.smem_get_priors()

    def top_capsules(self, n: int = 5) -> list[str]:
        priors = self.smem_get_priors()
        return sorted(priors, key=lambda k: priors[k].get("fires", 0), reverse=True)[:n]

    def update_model_preference(self, role: str, model_id: str) -> None:
        self._ctx["models"]["routing_prefs"][role] = model_id
        self._ctx["models"]["last_seen"][model_id] = _now()

    def get_preferred_models(self) -> dict[str, str | None]:
        return self._ctx["models"]["routing_prefs"]

    def link_shadow_doc(self, doc_type: str, path: str) -> None:
        sd = self._ctx["shadow_docs"]
        if doc_type == "trace_matrix":
            sd["trace_matrix"] = str(path)
        elif doc_type == "research_crosswalk":
            sd["research_crosswalk"] = str(path)
        else:
            custom = sd["custom_docs"]
            entry = {"type": doc_type, "path": str(path), "linked": _now()}
            custom[:] = [c for c in custom if c["path"] != str(path)]
            custom.append(entry)

    def get_shadow_context(self) -> str:
        parts = []
        sd = self._ctx["shadow_docs"]
        for key in ("trace_matrix", "research_crosswalk"):
            p = sd.get(key)
            if p and Path(p).exists():
                content = Path(p).read_text(encoding="utf-8", errors="replace")
                parts.append(f"=== {key.upper().replace('_',' ')} ===\n{content[:4000]}")
        for custom in sd.get("custom_docs", []):
            p = custom.get("path")
            if p and Path(p).exists():
                content = Path(p).read_text(encoding="utf-8", errors="replace")
                parts.append(f"=== {custom['type'].upper()} ===\n{content[:2000]}")
        return "\n\n".join(parts)

    def add_task(self, description: str, priority: str = "medium",
                 dependencies: list[str] | None = None) -> str:
        tasks = self._ctx["log"]["tasks"]
        tid = f"task-{len(tasks)+1:03d}"
        tasks.append({
            "id": tid, "description": description, "status": "pending",
            "priority": priority, "created": _now(),
            "timeline_id": self._ctx["active_timeline"],
            "dependencies": dependencies or [], "notes": [],
        })
        return tid

    def update_task(self, task_id: str, status: str) -> None:
        for t in self._ctx["log"]["tasks"]:
            if t["id"] == task_id:
                t["status"] = status
                if status == "completed":
                    t["completed"] = _now()
                break

    def add_decision(self, decision: str, rationale: str,
                     alternatives: list[dict] | None = None,
                     related_tasks: list[str] | None = None) -> str:
        decisions = self._ctx["log"]["decisions"]
        prev_hash = decisions[-1]["hash"] if decisions else None
        obj: dict[str, Any] = {
            "id": f"dec-{len(decisions)+1:03d}",
            "timestamp": _now(),
            "decision": decision,
            "rationale": rationale,
            "alternatives": alternatives or [],
            "related_tasks": related_tasks or [],
            "timeline_id": self._ctx["active_timeline"],
            "previous_hash": prev_hash,
        }
        obj["hash"] = _sha256(json.dumps(obj, sort_keys=True))
        decisions.append(obj)
        return obj["id"]

    def add_issue(self, description: str, severity: str, location: str = "") -> str:
        issues = self._ctx["log"]["issues"]
        iid = f"issue-{len(issues)+1:03d}"
        issues.append({
            "id": iid, "description": description, "severity": severity,
            "location": location, "discovered": _now(),
            "timeline_id": self._ctx["active_timeline"],
        })
        return iid

    def resolve_issue(self, issue_id: str, resolution: str) -> None:
        for i in self._ctx["log"]["issues"]:
            if i["id"] == issue_id:
                i["resolved"] = _now()
                i["resolution"] = resolution
                break

    def track_file(self, path: str, purpose: str) -> None:
        p = Path(path)
        file_hash = "pending"
        if p.exists():
            try:
                file_hash = _sha256(p.read_bytes().decode("utf-8", errors="replace"))[:12]
            except Exception:
                pass
        key_files = self._ctx["codebase"]["key_files"]
        entry = {"path": str(path), "purpose": purpose, "updated": _now(), "hash": file_hash}
        key_files[:] = [f for f in key_files if f["path"] != str(path)]
        key_files.append(entry)

    def create_timeline(self, name: str, parent: str | None = None) -> str:
        tid = str(uuid4())
        self._ctx["timelines"].append({
            "id": tid, "name": name,
            "parent": parent or self._ctx["active_timeline"],
            "created": _now(), "status": "active",
        })
        return tid

    def switch_timeline(self, tid: str) -> None:
        if any(t["id"] == tid for t in self._ctx["timelines"]):
            self._ctx["active_timeline"] = tid

    # ── Summary ───────────────────────────────────────────────────────

    def summary(self) -> str:
        p = self._ctx["project"]
        log = self._ctx["log"]
        forge = self._ctx["forge"]
        models = self._ctx["models"]
        tasks = log["tasks"]
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        open_issues = sum(1 for i in log["issues"] if "resolved" not in i)
        recent_sessions = forge["sessions"][-5:]
        top_caps = self.top_capsules(5)
        prefs = models["routing_prefs"]

        # CIL memory stats
        epmem_count = len(self._ctx.get("epmem", []))
        smem_stable = sum(
            1 for b in self._ctx.get("smem", [])
            if b.get("status") == EpistemicStatus.STABLE_SEMANTIC.value
        )
        smem_provisional = sum(
            1 for b in self._ctx.get("smem", [])
            if b.get("status") == EpistemicStatus.PROVISIONAL_SEMANTIC.value
        )
        contradiction_count = len(self._ctx.get("contradictions", []))

        lines = [
            f"╔═ Singularity Works — {p['name']} ({'v' + self._ctx['version']})",
            f"║  Root   : {p['root']}",
            f"║  Type   : {p['type']}",
            f"║",
            f"║  TASKS       {completed}/{len(tasks)} completed",
            f"║  DECISIONS   {len(log['decisions'])}",
            f"║  ISSUES      {open_issues} open",
            f"║",
            f"║  ─── CIL Memory ───",
            f"║  SBUF         {self.sbuf.summary()['witness_count']} pending witnesses",
            f"║  EPMEM        {epmem_count} episodic witnesses",
            f"║  SMEM         {smem_stable} stable / {smem_provisional} provisional",
            f"║  CONTRADICTIONS {contradiction_count}",
            f"║",
            f"║  FORGE SESSIONS   {len(forge['sessions'])}",
            f"║  PROVEN AXIOMS    {len(forge['proven_axioms'])}",
            f"║  TOP CAPSULES     {', '.join(top_caps) or 'none yet'}",
            f"║",
            f"║  MODEL ROUTING",
            f"║    Reasoner : {prefs.get('reasoner') or 'auto'}",
            f"║    Coder    : {prefs.get('coder') or 'auto'}",
            f"║    Ghost    : {prefs.get('ghost') or 'auto'}",
        ]
        if recent_sessions:
            lines.append("║")
            lines.append("║  RECENT FORGE SESSIONS")
            for s in recent_sessions:
                status_sym = "✓" if s["status"] == "green" else "✗"
                lines.append(
                    f"║    {status_sym} {s['timestamp'][:16]} | "
                    f"{s['finding_count']} findings | "
                    f"{s['applied']} fixed | "
                    f"{s['dialect_rounds']} rounds"
                )
        lines.append("║")
        lines.append(f"║  INTEGRITY  {'✓ valid' if self.verify() else '✗ MISMATCH'}")
        lines.append("╚" + "═" * 60)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI (backward compat + new commands)
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Singularity Works Context Manager v4.0")
    sub = parser.add_subparsers(dest="cmd")

    for cmd, add_args in [
        ("init",     [("--name", True), ("--root", False, "."), ("--type", False, "unknown"),
                      ("--desc", False, ""), ("--file", False, ".forge-context.json")]),
        ("summary",  [("--file", False, ".forge-context.json")]),
        ("verify",   [("--file", False, ".forge-context.json")]),
        ("context",  [("--file", False, ".forge-context.json"), ("--radical", False, None)]),
        ("task",     [("--file", False, ".forge-context.json"), ("--desc", True), ("--priority", False, "medium")]),
        ("decision", [("--file", False, ".forge-context.json"), ("--text", True), ("--why", True)]),
        ("link-shadow", [("--file", False, ".forge-context.json"), ("--type", True), ("--path", True)]),
    ]:
        p = sub.add_parser(cmd)
        for spec in add_args:
            name, required, *rest = spec
            default = rest[0] if rest else None
            p.add_argument(name, required=required) if required else p.add_argument(name, default=default)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    ctx = ForgeContext(getattr(args, "file", ".forge-context.json"))

    if args.cmd == "init":
        ctx.init(args.name, args.root, args.type, args.desc)
        ctx.save()
        print(f"Initialized: {ctx.path}")
        print(ctx.summary())
    elif args.cmd == "summary":
        ctx.load()
        print(ctx.summary())
    elif args.cmd == "verify":
        ctx.load()
        print("✓ Integrity valid" if ctx.verify() else "✗ Hash mismatch")
    elif args.cmd == "context":
        ctx.load()
        radical = getattr(args, "radical", None)
        hints = [radical] if radical else None
        print(ctx.compile_context(radical_hints=hints))
    elif args.cmd == "task":
        ctx.load()
        tid = ctx.add_task(args.desc, args.priority)
        ctx.save()
        print(f"Task added: {tid}")
    elif args.cmd == "decision":
        ctx.load()
        did = ctx.add_decision(args.text, args.why)
        ctx.save()
        print(f"Decision recorded: {did}")
    elif args.cmd == "link-shadow":
        ctx.load()
        ctx.link_shadow_doc(args.type, args.path)
        ctx.save()
        print(f"Linked {args.type} → {args.path}")


if __name__ == "__main__":
    main()
