from __future__ import annotations

"""Stable read/materialization facade for the canonical semantic field.

This module is intentionally thin. Forge App and other consumers should depend on
this surface rather than on lab adapters or parser-specific lowerings. It does not
own extraction semantics and cannot mint authority.
"""

from typing import Any, Iterable, Mapping

from .semantic_field import (
    FactProjection, FrozenSemanticFactBundle, SemanticFactBundle,
    freeze_bundle, project, verify_bundle,
)
from .semantic_field_delta import SnapshotDelta, diff_snapshots
from .semantic_field_index import SemanticFactIndex
from .semantic_materializer import SourcePatch, apply_patch_to_text, plan_replace_fact_evidence

BRIDGE_SCHEMA = "singularity-works.semantic-field-bridge/0.1"

def describe_snapshot(snapshot: FrozenSemanticFactBundle) -> dict[str, Any]:
    return {
        "schema": BRIDGE_SCHEMA,
        "bundle_id": snapshot.bundle_id,
        "source_count": len(snapshot.sources),
        "evidence_count": len(snapshot.evidence),
        "entity_count": len(snapshot.entities),
        "fact_count": len(snapshot.facts),
        "unknown_count": len(snapshot.unknowns),
        "authority": snapshot.authority,
        "target_execution": snapshot.target_execution,
    }

def build_read_index(snapshot: FrozenSemanticFactBundle) -> SemanticFactIndex:
    return SemanticFactIndex.build(snapshot)

def select_facts(
    snapshot: FrozenSemanticFactBundle,
    *,
    predicates: Iterable[str] | None = None,
    subject_kinds: Iterable[str] | None = None,
    property_filters: Mapping[str, Any] | None = None,
    include_unknowns: bool = False,
    index: SemanticFactIndex | None = None,
) -> FactProjection:
    if index is not None:
        return index.query(
            snapshot, predicates=predicates, subject_kinds=subject_kinds,
            property_filters=property_filters, include_unknowns=include_unknowns,
        )
    return project(
        snapshot, predicates=predicates, subject_kinds=subject_kinds,
        property_filters=property_filters, include_unknowns=include_unknowns,
    )

def compare_snapshots(old: FrozenSemanticFactBundle, new: FrozenSemanticFactBundle) -> SnapshotDelta:
    return diff_snapshots(old, new)

__all__ = [
    "BRIDGE_SCHEMA", "FactProjection", "FrozenSemanticFactBundle",
    "SemanticFactBundle", "SemanticFactIndex", "SnapshotDelta", "SourcePatch",
    "apply_patch_to_text", "build_read_index", "compare_snapshots",
    "describe_snapshot", "freeze_bundle", "plan_replace_fact_evidence",
    "select_facts", "verify_bundle",
]
