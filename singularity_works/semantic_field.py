from __future__ import annotations

"""Singularity Works canonical semantic field.

Promoted from Forge parser-independent semantic fact IR v0.1.

This module is intentionally small. It is not a replacement parser, not a security
ontology, and not a HUD model. It is the durable evidence substrate those layers
may project from.

Core laws embodied here:
- exact source referent before semantic claim;
- parser-native objects never become durable identity;
- fact content and evidence/assurance metadata remain separate;
- UNKNOWN is first-class;
- derived security claims share the same fact field as topology/capability facts;
- projection selects existing fact IDs and has no semantic/authority minting power.
"""

from dataclasses import dataclass, field, asdict
import hashlib
import json
from types import MappingProxyType
from typing import Any, Iterable, Mapping

SCHEMA = "singularity-works.semantic-field/0.1"
PROJECTION_SCHEMA = "singularity-works.semantic-field-projection/0.1"

_ALLOWED_STATUS = {"exact", "parsed", "derived", "inferred_candidate", "unknown", "contradicted"}
_ALLOWED_ENTITY_KINDS = {
    "module", "function", "method", "class", "value", "call", "effect", "capability",
    "composite", "record", "source_span", "external", "unknown", "claim",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (tuple, list)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (set, frozenset)):
        return sorted(_jsonable(v) for v in obj)
    return obj

def _deep_freeze(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return MappingProxyType({str(k): _deep_freeze(v) for k, v in obj.items()})
    if isinstance(obj, (tuple, list)):
        return tuple(_deep_freeze(v) for v in obj)
    if isinstance(obj, (set, frozenset)):
        return frozenset(_deep_freeze(v) for v in obj)
    return obj

def _deep_thaw(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {str(k): _deep_thaw(v) for k, v in obj.items()}
    if isinstance(obj, (tuple, list)):
        return [_deep_thaw(v) for v in obj]
    if isinstance(obj, (set, frozenset)):
        return sorted(_deep_thaw(v) for v in obj)
    return obj

def canonical_json(obj: Any) -> str:
    return json.dumps(_jsonable(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json(payload).encode('utf-8'))[:24]}"


def _line_starts(data: bytes) -> list[int]:
    starts = [0]
    for i, b in enumerate(data):
        if b == 10:
            starts.append(i + 1)
    return starts


def line_range_to_byte_span(data: bytes, start_line: int, end_line: int) -> tuple[int, int]:
    if start_line < 1 or end_line < start_line:
        raise ValueError("invalid line range")
    starts = _line_starts(data)
    if start_line > len(starts):
        raise ValueError("start line beyond source")
    start = starts[start_line - 1]
    end = starts[end_line] if end_line < len(starts) else len(data)
    return start, end


def offset_to_line(data: bytes, offset: int) -> int:
    if offset < 0 or offset > len(data):
        raise ValueError("offset outside source")
    return data.count(b"\n", 0, offset) + 1


@dataclass(frozen=True)
class SourceReferent:
    source_id: str
    path: str
    language: str
    sha256: str
    byte_length: int

    @classmethod
    def from_text(cls, path: str, language: str, text: str, source_id: str | None = None) -> "SourceReferent":
        data = text.encode("utf-8")
        sid = source_id or stable_id("src", {"path": path, "sha256": sha256_bytes(data)})
        return cls(sid, path, language, sha256_bytes(data), len(data))


@dataclass(frozen=True)
class EvidenceSpan:
    evidence_id: str
    source_id: str
    start_byte: int
    end_byte: int
    start_line: int
    end_line: int
    snippet_sha256: str
    role: str = "primary"

    @classmethod
    def from_bytes(
        cls,
        source: SourceReferent,
        source_text: str,
        start_byte: int,
        end_byte: int,
        role: str = "primary",
    ) -> "EvidenceSpan":
        data = source_text.encode("utf-8")
        if sha256_bytes(data) != source.sha256:
            raise ValueError(f"referent drift for {source.path}")
        if start_byte < 0 or end_byte < start_byte or end_byte > len(data):
            raise ValueError("evidence byte span outside source")
        snippet = data[start_byte:end_byte]
        payload = {
            "source_id": source.source_id,
            "start_byte": start_byte,
            "end_byte": end_byte,
            "snippet_sha256": sha256_bytes(snippet),
            "role": role,
        }
        return cls(
            stable_id("ev", payload), source.source_id, start_byte, end_byte,
            offset_to_line(data, start_byte), offset_to_line(data, end_byte),
            sha256_bytes(snippet), role,
        )

    @classmethod
    def from_lines(
        cls,
        source: SourceReferent,
        source_text: str,
        start_line: int,
        end_line: int,
        role: str = "primary",
    ) -> "EvidenceSpan":
        data = source_text.encode("utf-8")
        start, end = line_range_to_byte_span(data, start_line, end_line)
        return cls.from_bytes(source, source_text, start, end, role)


@dataclass(frozen=True)
class SemanticEntity:
    entity_id: str
    kind: str
    name: str
    source_id: str | None = None
    evidence_id: str | None = None
    properties: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SemanticFact:
    fact_id: str
    subject_id: str
    predicate: str
    object_value: Any
    evidence_ids: tuple[str, ...]
    evidence_status: str
    producer: str
    assurance_ceiling: str
    derivation_from: tuple[str, ...] = ()
    properties: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        subject_id: str,
        predicate: str,
        object_value: Any,
        evidence_ids: Iterable[str],
        evidence_status: str,
        producer: str,
        assurance_ceiling: str,
        derivation_from: Iterable[str] = (),
        properties: Mapping[str, Any] | None = None,
    ) -> "SemanticFact":
        if evidence_status not in _ALLOWED_STATUS:
            raise ValueError(f"unsupported evidence status: {evidence_status}")
        base = {
            "subject_id": subject_id,
            "predicate": predicate,
            "object_value": object_value,
            "evidence_ids": sorted(set(evidence_ids)),
            "evidence_status": evidence_status,
            "producer": producer,
            "assurance_ceiling": assurance_ceiling,
            "derivation_from": sorted(set(derivation_from)),
            "properties": dict(properties or {}),
        }
        return cls(
            stable_id("fact", base),
            **{
                **base,
                "evidence_ids": tuple(base["evidence_ids"]),
                "derivation_from": tuple(base["derivation_from"]),
            },
        )


@dataclass(frozen=True)
class UnknownSeam:
    seam_id: str
    subject_id: str | None
    question: str
    reason: str
    evidence_ids: tuple[str, ...]
    producer: str
    assurance_ceiling: str
    blocking: bool = False
    properties: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        subject_id: str | None,
        question: str,
        reason: str,
        evidence_ids: Iterable[str],
        producer: str,
        assurance_ceiling: str,
        blocking: bool = False,
        properties: Mapping[str, Any] | None = None,
    ) -> "UnknownSeam":
        base = {
            "subject_id": subject_id,
            "question": question,
            "reason": reason,
            "evidence_ids": sorted(set(evidence_ids)),
            "producer": producer,
            "assurance_ceiling": assurance_ceiling,
            "blocking": blocking,
            "properties": dict(properties or {}),
        }
        return cls(stable_id("seam", base), **{**base, "evidence_ids": tuple(base["evidence_ids"])})


@dataclass
class SemanticFactBundle:
    producer: str
    sources: dict[str, SourceReferent] = field(default_factory=dict)
    evidence: dict[str, EvidenceSpan] = field(default_factory=dict)
    entities: dict[str, SemanticEntity] = field(default_factory=dict)
    facts: dict[str, SemanticFact] = field(default_factory=dict)
    unknowns: dict[str, UnknownSeam] = field(default_factory=dict)
    target_execution: bool = False
    authority: str = "NONE"
    schema: str = SCHEMA

    def add_source(self, source: SourceReferent) -> str:
        existing = self.sources.get(source.source_id)
        if existing and existing != source:
            raise ValueError(f"source id collision: {source.source_id}")
        self.sources[source.source_id] = source
        return source.source_id

    def add_evidence(self, span: EvidenceSpan) -> str:
        if span.source_id not in self.sources:
            raise ValueError("evidence references unknown source")
        existing = self.evidence.get(span.evidence_id)
        if existing and existing != span:
            raise ValueError(f"evidence id collision: {span.evidence_id}")
        self.evidence[span.evidence_id] = span
        return span.evidence_id

    def add_entity(
        self,
        *,
        kind: str,
        name: str,
        source_id: str | None = None,
        evidence_id: str | None = None,
        properties: Mapping[str, Any] | None = None,
        entity_id: str | None = None,
    ) -> str:
        if kind not in _ALLOWED_ENTITY_KINDS:
            raise ValueError(f"unsupported entity kind: {kind}")
        if source_id is not None and source_id not in self.sources:
            raise ValueError("entity references unknown source")
        if evidence_id is not None and evidence_id not in self.evidence:
            raise ValueError("entity references unknown evidence")
        payload = {
            "kind": kind,
            "name": name,
            "source_id": source_id,
            "evidence_id": evidence_id,
            "properties": dict(properties or {}),
        }
        eid = entity_id or stable_id("ent", payload)
        entity = SemanticEntity(eid, kind, name, source_id, evidence_id, dict(properties or {}))
        existing = self.entities.get(eid)
        if existing and existing != entity:
            raise ValueError(f"entity id collision: {eid}")
        self.entities[eid] = entity
        return eid

    def add_fact(self, fact: SemanticFact) -> str:
        if fact.subject_id not in self.entities:
            raise ValueError(f"fact subject unknown: {fact.subject_id}")
        for evid in fact.evidence_ids:
            if evid not in self.evidence:
                raise ValueError(f"fact evidence unknown: {evid}")
        for parent in fact.derivation_from:
            if parent not in self.facts:
                raise ValueError(f"fact derivation parent unknown: {parent}")
        existing = self.facts.get(fact.fact_id)
        if existing and existing != fact:
            raise ValueError(f"fact id collision: {fact.fact_id}")
        self.facts[fact.fact_id] = fact
        return fact.fact_id

    def add_unknown(self, seam: UnknownSeam) -> str:
        if seam.subject_id is not None and seam.subject_id not in self.entities:
            raise ValueError("unknown seam subject missing")
        for evid in seam.evidence_ids:
            if evid not in self.evidence:
                raise ValueError("unknown seam evidence missing")
        self.unknowns[seam.seam_id] = seam
        return seam.seam_id

    def merge(self, other: "SemanticFactBundle") -> "SemanticFactBundle":
        if self.schema != other.schema:
            raise ValueError("schema mismatch")
        if self.target_execution or other.target_execution:
            raise ValueError("semantic field merge refuses executed targets")
        # Canonical producer lineage makes merge identity commutative/associative
        # when semantic content is identical. `|` is reserved as the lineage separator.
        producers = sorted(set(self.producer.split("|")) | set(other.producer.split("|")))
        out = SemanticFactBundle(producer="|".join(producers))
        for coll_name in ["sources", "evidence", "entities", "facts", "unknowns"]:
            dst = getattr(out, coll_name)
            for src in [getattr(self, coll_name), getattr(other, coll_name)]:
                for key, value in src.items():
                    if key in dst and dst[key] != value:
                        raise ValueError(f"merge collision in {coll_name}: {key}")
                    dst[key] = value
        return out

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "producer": self.producer,
            "target_execution": self.target_execution,
            "authority": self.authority,
            "sources": [asdict(x) for x in sorted(self.sources.values(), key=lambda x: x.source_id)],
            "evidence": [asdict(x) for x in sorted(self.evidence.values(), key=lambda x: x.evidence_id)],
            "entities": [asdict(x) for x in sorted(self.entities.values(), key=lambda x: x.entity_id)],
            "facts": [asdict(x) for x in sorted(self.facts.values(), key=lambda x: x.fact_id)],
            "unknowns": [asdict(x) for x in sorted(self.unknowns.values(), key=lambda x: x.seam_id)],
        }

    @property
    def bundle_id(self) -> str:
        return stable_id("bundle", self.as_dict())


@dataclass(frozen=True)
class FrozenSemanticFactBundle:
    """Verified immutable read snapshot for HUD/query/index consumers.

    Mutation belongs to the build bundle. A frozen snapshot caches canonical identity
    once and exposes recursively immutable fact metadata so stale-read checks are O(1).
    """
    producer: str
    sources: Mapping[str, SourceReferent]
    evidence: Mapping[str, EvidenceSpan]
    entities: Mapping[str, SemanticEntity]
    facts: Mapping[str, SemanticFact]
    unknowns: Mapping[str, UnknownSeam]
    _bundle_id: str
    target_execution: bool = False
    authority: str = "NONE"
    schema: str = SCHEMA

    @property
    def bundle_id(self) -> str:
        return self._bundle_id

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "producer": self.producer,
            "target_execution": self.target_execution,
            "authority": self.authority,
            "sources": [asdict(x) for x in sorted(self.sources.values(), key=lambda x: x.source_id)],
            "evidence": [asdict(x) for x in sorted(self.evidence.values(), key=lambda x: x.evidence_id)],
            "entities": [
                {
                    "entity_id": x.entity_id,
                    "kind": x.kind,
                    "name": x.name,
                    "source_id": x.source_id,
                    "evidence_id": x.evidence_id,
                    "properties": _deep_thaw(x.properties),
                }
                for x in sorted(self.entities.values(), key=lambda x: x.entity_id)
            ],
            "facts": [
                {
                    "fact_id": x.fact_id,
                    "subject_id": x.subject_id,
                    "predicate": x.predicate,
                    "object_value": _deep_thaw(x.object_value),
                 "evidence_ids": list(x.evidence_ids), "evidence_status": x.evidence_status, "producer": x.producer,
                    "assurance_ceiling": x.assurance_ceiling,
                    "derivation_from": list(x.derivation_from),
                    "properties": _deep_thaw(x.properties),
                }
                for x in sorted(self.facts.values(), key=lambda x: x.fact_id)
            ],
            "unknowns": [
                {"seam_id": x.seam_id, "subject_id": x.subject_id, "question": x.question, "reason": x.reason,
                 "evidence_ids": list(x.evidence_ids), "producer": x.producer, "assurance_ceiling": x.assurance_ceiling,
                 "blocking": x.blocking, "properties": _deep_thaw(x.properties)}
                for x in sorted(self.unknowns.values(), key=lambda x: x.seam_id)
            ],
        }


@dataclass(frozen=True)
class FactProjection:
    projection_id: str
    source_bundle_id: str
    query: Mapping[str, Any]
    selected_fact_ids: tuple[str, ...]
    selected_entity_ids: tuple[str, ...]
    selected_unknown_ids: tuple[str, ...]
    projection_authority: str = "NONE"
    schema: str = PROJECTION_SCHEMA


def project(
    bundle: SemanticFactBundle,
    *,
    predicates: Iterable[str] | None = None,
    subject_kinds: Iterable[str] | None = None,
    property_filters: Mapping[str, Any] | None = None,
    include_unknowns: bool = False,
) -> FactProjection:
    pred = set(predicates or [])
    skinds = set(subject_kinds or [])
    pfilters = dict(property_filters or {})
    selected: list[str] = []
    entities: set[str] = set()
    evidence_entities: set[str] = set()
    for fact in bundle.facts.values():
        subject = bundle.entities[fact.subject_id]
        if pred and fact.predicate not in pred:
            continue
        if skinds and subject.kind not in skinds:
            continue
        if any(fact.properties.get(k) != v for k, v in pfilters.items()):
            continue
        selected.append(fact.fact_id)
        entities.add(fact.subject_id)
        if isinstance(fact.object_value, Mapping) and "entity_id" in fact.object_value:
            oid = fact.object_value["entity_id"]
            if oid in bundle.entities:
                entities.add(oid)
    unknown_ids = tuple(sorted(bundle.unknowns)) if include_unknowns else ()
    for uid in unknown_ids:
        sid = bundle.unknowns[uid].subject_id
        if sid:
            evidence_entities.add(sid)
    query = {
        "predicates": sorted(pred),
        "subject_kinds": sorted(skinds),
        "property_filters": pfilters,
        "include_unknowns": include_unknowns,
    }
    payload = {
        "source_bundle_id": bundle.bundle_id,
        "query": query,
        "selected_fact_ids": sorted(selected),
        "selected_entity_ids": sorted(entities | evidence_entities),
        "selected_unknown_ids": list(unknown_ids),
        "projection_authority": "NONE",
    }
    return FactProjection(
        stable_id("proj", payload), bundle.bundle_id, query,
        tuple(sorted(selected)), tuple(sorted(entities | evidence_entities)), unknown_ids,
    )


def verify_bundle(bundle: SemanticFactBundle, source_texts_by_path: Mapping[str, str]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if bundle.target_execution:
        errors.append("target_execution must be false for canonical static semantic fields")
    if bundle.authority != "NONE":
        errors.append("bundle authority must remain NONE")

    source_by_id = bundle.sources
    for source in source_by_id.values():
        if source.path not in source_texts_by_path:
            errors.append(f"missing source text: {source.path}")
            continue
        data = source_texts_by_path[source.path].encode("utf-8")
        if sha256_bytes(data) != source.sha256:
            errors.append(f"source referent drift: {source.path}")
        if len(data) != source.byte_length:
            errors.append(f"source length drift: {source.path}")

    for ev in bundle.evidence.values():
        source = source_by_id.get(ev.source_id)
        if not source:
            errors.append(f"evidence {ev.evidence_id} missing source")
            continue
        text = source_texts_by_path.get(source.path)
        if text is None:
            continue
        data = text.encode("utf-8")
        if ev.start_byte < 0 or ev.end_byte < ev.start_byte or ev.end_byte > len(data):
            errors.append(f"evidence span out of range: {ev.evidence_id}")
            continue
        if sha256_bytes(data[ev.start_byte:ev.end_byte]) != ev.snippet_sha256:
            errors.append(f"evidence snippet drift: {ev.evidence_id}")
        if offset_to_line(data, ev.start_byte) != ev.start_line:
            errors.append(f"evidence start line mismatch: {ev.evidence_id}")

    for ent in bundle.entities.values():
        if ent.kind not in _ALLOWED_ENTITY_KINDS:
            errors.append(f"entity kind invalid: {ent.entity_id}")
        if ent.source_id and ent.source_id not in bundle.sources:
            errors.append(f"entity source missing: {ent.entity_id}")
        if ent.evidence_id and ent.evidence_id not in bundle.evidence:
            errors.append(f"entity evidence missing: {ent.entity_id}")

    for fact in bundle.facts.values():
        if fact.subject_id not in bundle.entities:
            errors.append(f"fact subject missing: {fact.fact_id}")
        if fact.evidence_status not in _ALLOWED_STATUS:
            errors.append(f"fact evidence status invalid: {fact.fact_id}")
        if any(e not in bundle.evidence for e in fact.evidence_ids):
            errors.append(f"fact evidence missing: {fact.fact_id}")
        if any(p not in bundle.facts for p in fact.derivation_from):
            errors.append(f"fact derivation parent missing: {fact.fact_id}")
        recomputed = SemanticFact.create(
            subject_id=fact.subject_id, predicate=fact.predicate, object_value=fact.object_value,
            evidence_ids=fact.evidence_ids, evidence_status=fact.evidence_status,
            producer=fact.producer, assurance_ceiling=fact.assurance_ceiling,
            derivation_from=fact.derivation_from, properties=fact.properties,
        ).fact_id
        if recomputed != fact.fact_id:
            errors.append(f"fact identity drift: {fact.fact_id}")

    for seam in bundle.unknowns.values():
        if seam.subject_id and seam.subject_id not in bundle.entities:
            errors.append(f"unknown seam subject missing: {seam.seam_id}")
        if any(e not in bundle.evidence for e in seam.evidence_ids):
            errors.append(f"unknown seam evidence missing: {seam.seam_id}")

    return {
        "schema": "singularity-works.semantic-field-verification/0.1",
        "bundle_id": bundle.bundle_id,
        "source_count": len(bundle.sources),
        "evidence_count": len(bundle.evidence),
        "entity_count": len(bundle.entities),
        "fact_count": len(bundle.facts),
        "unknown_count": len(bundle.unknowns),
        "errors": errors,
        "warnings": warnings,
        "pass": not errors,
    }


def freeze_bundle(bundle: SemanticFactBundle, source_texts_by_path: Mapping[str, str]) -> FrozenSemanticFactBundle:
    """Verify once, then create a recursively immutable read snapshot with cached ID."""
    report = verify_bundle(bundle, source_texts_by_path)
    if not report["pass"]:
        raise ValueError(f"cannot freeze invalid semantic bundle: {report['errors']}")
    bid = bundle.bundle_id
    sources = MappingProxyType(dict(bundle.sources))
    evidence = MappingProxyType(dict(bundle.evidence))
    entities = MappingProxyType({
        k: SemanticEntity(v.entity_id, v.kind, v.name, v.source_id, v.evidence_id, _deep_freeze(v.properties))
        for k, v in bundle.entities.items()
    })
    facts = MappingProxyType({
        k: SemanticFact(
            v.fact_id,
            v.subject_id,
            v.predicate,
            _deep_freeze(v.object_value),
            tuple(v.evidence_ids),
            v.evidence_status,
            v.producer,
            v.assurance_ceiling,
            tuple(v.derivation_from),
            _deep_freeze(v.properties),
        )
        for k, v in bundle.facts.items()
    })
    unknowns = MappingProxyType({
        k: UnknownSeam(v.seam_id, v.subject_id, v.question, v.reason, tuple(v.evidence_ids), v.producer,
                       v.assurance_ceiling, v.blocking, _deep_freeze(v.properties))
        for k, v in bundle.unknowns.items()
    })
    frozen = FrozenSemanticFactBundle(
        bundle.producer,
        sources,
        evidence,
        entities,
        facts,
        unknowns,
        bid,
        bundle.target_execution,
        bundle.authority,
        bundle.schema,
    )
    # Snapshot serialization must remain canonically identical to the verified build bundle.
    if canonical_json(frozen.as_dict()) != canonical_json(bundle.as_dict()):
        raise ValueError("freeze serialization drift")
    return frozen


def entity_ref(entity_id: str) -> dict[str, str]:
    return {"entity_id": entity_id}
