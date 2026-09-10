from __future__ import annotations

"""Bridge exact semantic replay intent to evidence-anchored source materialization.

The bridge is deliberately *not* a source lowerer. A semantic delta can say what
semantic relation disappeared or appeared; it does not uniquely determine source
syntax. This module therefore resolves removed semantic keys to exact base facts and
evidence spans suitable for the incumbent SourcePatch materializer. Replacement
bytes remain an explicit caller/lowering-policy input, and correctness is established
only after materialization, re-lowering, and exact target comparison.

SEMANTIC_INTENT != UNIQUE_SOURCE_SYNTAX
DELTA_TO_PATCH_BRIDGE != SOURCE_LOWERER
BRIDGE_AUTHORITY = NONE
"""

from dataclasses import dataclass, asdict
import hashlib
from typing import Any

from forge_semantic_delta_replay_v0_1_3 import SemanticDeltaPlan
from forge_semantic_fact_ir_v0_1_2 import FrozenSemanticFactBundle, canonical_json, stable_id
from forge_semantic_snapshot_delta_v0_4 import diff_snapshots, fact_semantic_key

VERSION = "forge.semantic-delta-materialization-bridge/0.1"


@dataclass(frozen=True)
class RemovedSemanticAnchor:
    anchor_id: str
    semantic_key: str
    fact_id: str
    source_path: str
    source_sha256: str
    evidence_id: str
    evidence_start_byte: int
    evidence_end_byte: int
    evidence_snippet_sha256: str
    bridge_authority: str = "NONE"
    version: str = VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MaterializationBridgePlan:
    bridge_plan_id: str
    semantic_plan_id: str
    base_bundle_id: str
    target_bundle_id: str
    removed_semantic_keys: tuple[str, ...]
    added_semantic_keys: tuple[str, ...]
    ambiguous_semantic_keys: tuple[str, ...]
    multiplicity_change_count: int
    removed_anchors: tuple[RemovedSemanticAnchor, ...]
    bridge_authority: str = "NONE"
    version: str = VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "bridge_plan_id": self.bridge_plan_id,
            "semantic_plan_id": self.semantic_plan_id,
            "base_bundle_id": self.base_bundle_id,
            "target_bundle_id": self.target_bundle_id,
            "removed_semantic_keys": list(self.removed_semantic_keys),
            "added_semantic_keys": list(self.added_semantic_keys),
            "ambiguous_semantic_keys": list(self.ambiguous_semantic_keys),
            "multiplicity_change_count": self.multiplicity_change_count,
            "removed_anchors": [x.as_dict() for x in self.removed_anchors],
            "bridge_authority": self.bridge_authority,
        }


def build_materialization_bridge(
    base: FrozenSemanticFactBundle,
    target: FrozenSemanticFactBundle,
    semantic_plan: SemanticDeltaPlan,
) -> MaterializationBridgePlan:
    if semantic_plan.delta_authority != "NONE":
        raise ValueError("semantic plan authority must remain NONE")
    if base.bundle_id != semantic_plan.base_bundle_id:
        raise ValueError("bridge base does not match semantic plan base")
    if target.bundle_id != semantic_plan.target_bundle_id:
        raise ValueError("bridge target does not match semantic plan target")

    observed = diff_snapshots(base, target)
    if observed.delta_authority != "NONE":
        raise ValueError("snapshot delta authority must remain NONE")

    by_key: dict[str, list[str]] = {}
    for fid, fact in base.facts.items():
        by_key.setdefault(fact_semantic_key(base, fact), []).append(fid)

    anchors: list[RemovedSemanticAnchor] = []
    for semantic_key in observed.removed_semantic_keys:
        fact_ids = sorted(by_key.get(semantic_key, []))
        if len(fact_ids) != 1:
            raise ValueError(f"removed semantic key is not uniquely materializable: {semantic_key} -> {len(fact_ids)} facts")
        fact = base.facts[fact_ids[0]]
        if len(fact.evidence_ids) != 1:
            raise ValueError(f"removed semantic fact does not have exactly one evidence span: {fact.fact_id}")
        evidence = base.evidence[fact.evidence_ids[0]]
        source = base.sources[evidence.source_id]
        payload = {
            "semantic_key": semantic_key,
            "fact_id": fact.fact_id,
            "source_path": source.path,
            "source_sha256": source.sha256,
            "evidence_id": evidence.evidence_id,
            "evidence_start_byte": evidence.start_byte,
            "evidence_end_byte": evidence.end_byte,
            "evidence_snippet_sha256": evidence.snippet_sha256,
        }
        anchors.append(RemovedSemanticAnchor(
            anchor_id=stable_id("matanchor", payload),
            bridge_authority="NONE",
            version=VERSION,
            **payload,
        ))

    descriptor = {
        "semantic_plan_id": semantic_plan.plan_id,
        "base_bundle_id": base.bundle_id,
        "target_bundle_id": target.bundle_id,
        "removed_semantic_keys": list(observed.removed_semantic_keys),
        "added_semantic_keys": list(observed.added_semantic_keys),
        "ambiguous_semantic_keys": list(observed.ambiguous_semantic_keys),
        "multiplicity_change_count": len(observed.multiplicity_changes),
        "removed_anchors": [x.as_dict() for x in anchors],
        "bridge_authority": "NONE",
    }
    return MaterializationBridgePlan(
        bridge_plan_id=stable_id("matbridge", descriptor),
        semantic_plan_id=semantic_plan.plan_id,
        base_bundle_id=base.bundle_id,
        target_bundle_id=target.bundle_id,
        removed_semantic_keys=tuple(observed.removed_semantic_keys),
        added_semantic_keys=tuple(observed.added_semantic_keys),
        ambiguous_semantic_keys=tuple(observed.ambiguous_semantic_keys),
        multiplicity_change_count=len(observed.multiplicity_changes),
        removed_anchors=tuple(anchors),
        bridge_authority="NONE",
        version=VERSION,
    )


def bridge_fingerprint(plan: MaterializationBridgePlan) -> str:
    return hashlib.sha256(canonical_json(plan.as_dict()).encode("utf-8")).hexdigest()
