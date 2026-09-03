from __future__ import annotations

"""Semantic snapshot delta for the Singularity Works semantic field.

Exact fact IDs are revision identities because they include evidence/currentness.
This module adds a *derived* continuity key that normalizes entity meaning and
excludes revision-only evidence IDs. It never rewrites fact truth or authority.

A delta can therefore distinguish:
- RETAINED_REVISION: exact fact revision survived unchanged;
- REFRESHED_EVIDENCE: same semantic claim, new exact evidence/currentness;
- ADDED_SEMANTIC / REMOVED_SEMANTIC;
- AMBIGUOUS_MATCH: continuity key is non-unique and must remain unresolved.
"""

from dataclasses import dataclass, asdict
from typing import Any, Mapping

from .semantic_field import (
    FrozenSemanticFactBundle,
    SemanticEntity,
    SemanticFact,
    canonical_json,
    stable_id,
)

VERSION = "singularity-works.semantic-field-delta/0.1"

_VOLATILE_PROPERTY_KEYS = {
    "origin_edge_id", "origin_finding_id", "source_id", "source_surface",
}


def _source_path(bundle: FrozenSemanticFactBundle, source_id: str | None) -> str | None:
    if source_id and source_id in bundle.sources:
        return bundle.sources[source_id].path
    return None


def entity_semantic_descriptor(bundle: FrozenSemanticFactBundle, entity: SemanticEntity) -> dict[str, Any]:
    props = {k: v for k, v in entity.properties.items() if k not in _VOLATILE_PROPERTY_KEYS}
    return {
        "kind": entity.kind,
        "name": entity.name,
        "source_path": _source_path(bundle, entity.source_id),
        "properties": props,
    }


def _normalize_object(bundle: FrozenSemanticFactBundle, value: Any) -> Any:
    if isinstance(value, Mapping) and "entity_id" in value and value["entity_id"] in bundle.entities:
        return {"entity": entity_semantic_descriptor(bundle, bundle.entities[value["entity_id"]])}
    if isinstance(value, Mapping):
        return {k: _normalize_object(bundle, v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_normalize_object(bundle, x) for x in value]
    return value


def fact_semantic_key(bundle: FrozenSemanticFactBundle, fact: SemanticFact) -> str:
    """Semantic continuity key, intentionally excluding generic evidence text.

    Evidence proves a claim and distinguishes occurrences; it does not automatically
    define the meaning of every claim. If implementation identity is semantic (for
    example a provider implementation), the lowering must state that explicitly in
    fact/entity properties rather than relying on a coarse evidence snippet hash.
    """
    props = {k: v for k, v in fact.properties.items() if k not in _VOLATILE_PROPERTY_KEYS}
    payload = {
        "subject": entity_semantic_descriptor(bundle, bundle.entities[fact.subject_id]),
        "predicate": fact.predicate,
        "object": _normalize_object(bundle, fact.object_value),
        "properties": props,
        "producer_family": fact.producer.split(":", 2)[-1] if ":" in fact.producer else fact.producer,
        "assurance_ceiling": fact.assurance_ceiling,
    }
    return stable_id("sem", payload)


def fact_occurrence_key(bundle: FrozenSemanticFactBundle, fact: SemanticFact) -> str:
    """Derived occurrence matcher used only when a semantic key has multiplicity."""
    evidence_fingerprints = sorted(
        {
            (
                bundle.sources[bundle.evidence[e].source_id].path
                if bundle.evidence[e].source_id in bundle.sources else None,
                bundle.evidence[e].snippet_sha256,
                bundle.evidence[e].role,
            )
            for e in fact.evidence_ids
            if e in bundle.evidence
        }
    )
    return stable_id("occ", {
        "semantic_key": fact_semantic_key(bundle, fact),
        "evidence_fingerprints": evidence_fingerprints,
    })


def _fact_source_paths(bundle: FrozenSemanticFactBundle, fact: SemanticFact) -> list[str]:
    paths = set()
    for eid in fact.evidence_ids:
        ev = bundle.evidence.get(eid)
        if ev and ev.source_id in bundle.sources:
            paths.add(bundle.sources[ev.source_id].path)
    return sorted(paths)


@dataclass(frozen=True)
class RefreshedFact:
    semantic_key: str
    old_fact_id: str
    new_fact_id: str
    old_source_paths: tuple[str, ...]
    new_source_paths: tuple[str, ...]


@dataclass(frozen=True)
class MultiplicityChange:
    semantic_key: str
    old_count: int
    new_count: int
    retained_exact_count: int
    unmatched_old_fact_ids: tuple[str, ...]
    unmatched_new_fact_ids: tuple[str, ...]


@dataclass(frozen=True)
class SnapshotDelta:
    delta_id: str
    old_bundle_id: str
    new_bundle_id: str
    changed_sources: tuple[dict[str, Any], ...]
    added_sources: tuple[str, ...]
    removed_sources: tuple[str, ...]
    retained_revision_fact_ids: tuple[str, ...]
    refreshed_facts: tuple[RefreshedFact, ...]
    added_semantic_keys: tuple[str, ...]
    removed_semantic_keys: tuple[str, ...]
    ambiguous_semantic_keys: tuple[str, ...]
    multiplicity_changes: tuple[MultiplicityChange, ...]
    old_invalidated_fact_ids: tuple[str, ...]
    new_fact_ids_on_changed_sources: tuple[str, ...]
    delta_authority: str = "NONE"
    version: str = VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "delta_id": self.delta_id,
            "old_bundle_id": self.old_bundle_id,
            "new_bundle_id": self.new_bundle_id,
            "changed_sources": list(self.changed_sources),
            "added_sources": list(self.added_sources),
            "removed_sources": list(self.removed_sources),
            "retained_revision_fact_ids": list(self.retained_revision_fact_ids),
            "refreshed_facts": [asdict(x) for x in self.refreshed_facts],
            "added_semantic_keys": list(self.added_semantic_keys),
            "removed_semantic_keys": list(self.removed_semantic_keys),
            "ambiguous_semantic_keys": list(self.ambiguous_semantic_keys),
            "multiplicity_changes": [asdict(x) for x in self.multiplicity_changes],
            "old_invalidated_fact_ids": list(self.old_invalidated_fact_ids),
            "new_fact_ids_on_changed_sources": list(self.new_fact_ids_on_changed_sources),
            "delta_authority": self.delta_authority,
        }


def diff_snapshots(old: FrozenSemanticFactBundle, new: FrozenSemanticFactBundle) -> SnapshotDelta:
    old_by_path = {s.path: s for s in old.sources.values()}
    new_by_path = {s.path: s for s in new.sources.values()}
    changed_sources = []
    for path in sorted(set(old_by_path) & set(new_by_path)):
        a, b = old_by_path[path], new_by_path[path]
        if a.sha256 != b.sha256 or a.byte_length != b.byte_length:
            changed_sources.append({
                "path": path,
                "old_source_id": a.source_id,
                "new_source_id": b.source_id,
                "old_sha256": a.sha256,
                "new_sha256": b.sha256,
                "old_bytes": a.byte_length,
                "new_bytes": b.byte_length,
            })
    added_sources = sorted(set(new_by_path) - set(old_by_path))
    removed_sources = sorted(set(old_by_path) - set(new_by_path))

    old_groups: dict[str, list[str]] = {}
    new_groups: dict[str, list[str]] = {}
    for fid, fact in old.facts.items():
        old_groups.setdefault(fact_semantic_key(old, fact), []).append(fid)
    for fid, fact in new.facts.items():
        new_groups.setdefault(fact_semantic_key(new, fact), []).append(fid)

    retained: list[str] = []
    refreshed: list[RefreshedFact] = []
    added: list[str] = []
    removed: list[str] = []
    ambiguous: list[str] = []
    multiplicity: list[MultiplicityChange] = []

    for key in sorted(set(old_groups) | set(new_groups)):
        olds_all = sorted(old_groups.get(key, []))
        news_all = sorted(new_groups.get(key, []))

        # Exact fact revisions survive first; never throw away exact continuity merely
        # because a semantic key has multiple occurrences.
        common = sorted(set(olds_all) & set(news_all))
        retained.extend(common)
        olds = sorted(set(olds_all) - set(common))
        news = sorted(set(news_all) - set(common))

        if not olds and not news:
            continue
        if not olds_all and news_all:
            added.append(key)
            continue
        if olds_all and not news_all:
            removed.append(key)
            continue

        # A unique semantic claim on each side is the same meaning with refreshed
        # evidence/currentness, even if its evidence snippet text changed.
        if len(olds) == 1 and len(news) == 1:
            refreshed.append(RefreshedFact(
                key, olds[0], news[0],
                tuple(_fact_source_paths(old, old.facts[olds[0]])),
                tuple(_fact_source_paths(new, new.facts[news[0]])),
            ))
            continue

        # For repeated semantic claims, use evidence fingerprints only as a derived
        # occurrence disambiguator. They are not part of semantic meaning itself.
        old_occ: dict[str, list[str]] = {}
        new_occ: dict[str, list[str]] = {}
        for fid in olds:
            old_occ.setdefault(fact_occurrence_key(old, old.facts[fid]), []).append(fid)
        for fid in news:
            new_occ.setdefault(fact_occurrence_key(new, new.facts[fid]), []).append(fid)

        paired_old: set[str] = set()
        paired_new: set[str] = set()
        for occ in sorted(set(old_occ) & set(new_occ)):
            oo = sorted(old_occ[occ])
            nn = sorted(new_occ[occ])
            if len(oo) == 1 and len(nn) == 1:
                refreshed.append(RefreshedFact(
                    key, oo[0], nn[0],
                    tuple(_fact_source_paths(old, old.facts[oo[0]])),
                    tuple(_fact_source_paths(new, new.facts[nn[0]])),
                ))
                paired_old.add(oo[0]); paired_new.add(nn[0])

        olds_left = sorted(set(olds) - paired_old)
        news_left = sorted(set(news) - paired_new)
        if not olds_left and not news_left:
            continue
        if len(olds_left) == 1 and len(news_left) == 1:
            # After occurrence-stable duplicates have been paired, one residual pair is
            # unambiguous and represents refreshed evidence for the same semantic claim.
            refreshed.append(RefreshedFact(
                key, olds_left[0], news_left[0],
                tuple(_fact_source_paths(old, old.facts[olds_left[0]])),
                tuple(_fact_source_paths(new, new.facts[news_left[0]])),
            ))
            continue

        multiplicity.append(MultiplicityChange(
            key, len(olds_all), len(news_all), len(common), tuple(olds_left), tuple(news_left)
        ))
        if olds_left and news_left:
            ambiguous.append(key)

    changed_old_source_ids = (
        {x["old_source_id"] for x in changed_sources}
        | {old_by_path[p].source_id for p in removed_sources}
    )
    changed_new_source_ids = (
        {x["new_source_id"] for x in changed_sources}
        | {new_by_path[p].source_id for p in added_sources}
    )

    old_invalidated = []
    for fid, fact in old.facts.items():
        if any(old.evidence[e].source_id in changed_old_source_ids for e in fact.evidence_ids if e in old.evidence):
            old_invalidated.append(fid)
    new_changed = []
    for fid, fact in new.facts.items():
        if any(new.evidence[e].source_id in changed_new_source_ids for e in fact.evidence_ids if e in new.evidence):
            new_changed.append(fid)

    payload = {
        "old_bundle_id": old.bundle_id,
        "new_bundle_id": new.bundle_id,
        "changed_sources": changed_sources,
        "added_sources": added_sources,
        "removed_sources": removed_sources,
        "retained_revision_fact_ids": sorted(retained),
        "refreshed": [asdict(x) for x in refreshed],
        "added_semantic_keys": sorted(added),
        "removed_semantic_keys": sorted(removed),
        "ambiguous_semantic_keys": sorted(ambiguous),
        "multiplicity_changes": [asdict(x) for x in sorted(multiplicity, key=lambda x: x.semantic_key)],
        "old_invalidated_fact_ids": sorted(old_invalidated),
        "new_fact_ids_on_changed_sources": sorted(new_changed),
        "delta_authority": "NONE",
    }
    return SnapshotDelta(
        stable_id("delta", payload), old.bundle_id, new.bundle_id,
        tuple(changed_sources), tuple(added_sources), tuple(removed_sources),
        tuple(sorted(retained)), tuple(sorted(refreshed, key=lambda x: x.semantic_key)),
        tuple(sorted(added)), tuple(sorted(removed)), tuple(sorted(ambiguous)),
        tuple(sorted(multiplicity, key=lambda x: x.semantic_key)),
        tuple(sorted(old_invalidated)), tuple(sorted(new_changed)), "NONE",
    )
