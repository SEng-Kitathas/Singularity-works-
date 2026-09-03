from __future__ import annotations

"""Non-authoritative query accelerator for Singularity Works semantic field.

The index is disposable/rebuildable projection machinery. It is deliberately not
part of bundle identity and cannot add facts, entities, evidence, unknowns, or
authority. Indexed queries must be observationally identical to canonical scans.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .semantic_field import (
    FactProjection,
    FrozenSemanticFactBundle,
    canonical_json,
    stable_id,
)

VERSION = "singularity-works.semantic-field-index/0.1"


@dataclass
class SemanticFactIndex:
    source_bundle_id: str
    all_fact_ids: frozenset[str]
    by_predicate: dict[str, frozenset[str]]
    by_subject_kind: dict[str, frozenset[str]]
    by_property: dict[tuple[str, str], frozenset[str]]
    unknown_ids: tuple[str, ...]
    projection_authority: str = "NONE"
    version: str = VERSION

    @classmethod
    def build(cls, bundle: FrozenSemanticFactBundle) -> "SemanticFactIndex":
        pred: dict[str, set[str]] = defaultdict(set)
        kinds: dict[str, set[str]] = defaultdict(set)
        props: dict[tuple[str, str], set[str]] = defaultdict(set)
        for fid, fact in bundle.facts.items():
            pred[fact.predicate].add(fid)
            subject = bundle.entities[fact.subject_id]
            kinds[subject.kind].add(fid)
            for key, value in fact.properties.items():
                props[(key, canonical_json(value))].add(fid)
        return cls(
            source_bundle_id=bundle.bundle_id,
            all_fact_ids=frozenset(bundle.facts),
            by_predicate={k: frozenset(v) for k, v in pred.items()},
            by_subject_kind={k: frozenset(v) for k, v in kinds.items()},
            by_property={k: frozenset(v) for k, v in props.items()},
            unknown_ids=tuple(sorted(bundle.unknowns)),
        )

    def query(
        self,
        bundle: FrozenSemanticFactBundle,
        *,
        predicates: Iterable[str] | None = None,
        subject_kinds: Iterable[str] | None = None,
        property_filters: Mapping[str, Any] | None = None,
        include_unknowns: bool = False,
    ) -> FactProjection:
        if not isinstance(bundle, FrozenSemanticFactBundle):
            raise TypeError("semantic fact index requires a verified FrozenSemanticFactBundle snapshot")
        if bundle.bundle_id != self.source_bundle_id:
            raise ValueError("stale semantic fact index: bundle snapshot identity changed")
        pred = set(predicates or [])
        skinds = set(subject_kinds or [])
        pfilters = dict(property_filters or {})

        candidates: set[str] | None = None

        def intersect(ids: Iterable[str]) -> None:
            nonlocal candidates
            s = set(ids)
            candidates = s if candidates is None else candidates & s

        if pred:
            union: set[str] = set()
            for p in pred:
                union.update(self.by_predicate.get(p, ()))
            intersect(union)
        if skinds:
            union = set()
            for kind in skinds:
                union.update(self.by_subject_kind.get(kind, ()))
            intersect(union)
        for key, value in pfilters.items():
            intersect(self.by_property.get((key, canonical_json(value)), ()))
        if candidates is None:
            candidates = set(self.all_fact_ids)

        selected = tuple(sorted(candidates))
        entities: set[str] = set()
        for fid in selected:
            fact = bundle.facts[fid]
            entities.add(fact.subject_id)
            if isinstance(fact.object_value, Mapping) and "entity_id" in fact.object_value:
                oid = fact.object_value["entity_id"]
                if oid in bundle.entities:
                    entities.add(oid)

        unknown_ids = self.unknown_ids if include_unknowns else ()
        for uid in unknown_ids:
            sid = bundle.unknowns[uid].subject_id
            if sid:
                entities.add(sid)

        query = {
            "predicates": sorted(pred),
            "subject_kinds": sorted(skinds),
            "property_filters": pfilters,
            "include_unknowns": include_unknowns,
        }
        payload = {
            "source_bundle_id": bundle.bundle_id,
            "query": query,
            "selected_fact_ids": list(selected),
            "selected_entity_ids": sorted(entities),
            "selected_unknown_ids": list(unknown_ids),
            "projection_authority": "NONE",
        }
        return FactProjection(
            stable_id("proj", payload),
            bundle.bundle_id,
            query,
            selected,
            tuple(sorted(entities)),
            tuple(unknown_ids),
            projection_authority="NONE",
        )
