from __future__ import annotations

"""Reference semantic-delta replay algebra for Forge fact bundles v0.1.

This module operates only on already-lowered semantic bundles. It does not edit
source files, infer semantics, or mint authority. A replay plan is an exact,
content-addressed transition between two verified frozen bundles.

Laws:
- exact base bundle identity is a hard precondition;
- operations are typed by canonical bundle collection;
- removals occur in reverse dependency order;
- upserts occur in forward dependency order;
- every changed object carries an exact before/after digest;
- replay must freeze successfully against exact target source texts;
- replay output bundle_id must equal the declared target bundle_id;
- plan authority is always NONE.

SEMANTIC_DELTA_REPLAY != SOURCE_EDIT_MATERIALIZATION
REPLAY_SUCCESS != SEMANTIC_EQUIVALENCE_OF_ARBITRARY_PROGRAMS
DELTA_AUTHORITY = NONE
"""

from dataclasses import asdict, dataclass
import hashlib
from typing import Any, Mapping

from forge_semantic_fact_ir_v0_1_2 import (
    EvidenceSpan,
    FrozenSemanticFactBundle,
    SemanticEntity,
    SemanticFact,
    SemanticFactBundle,
    SourceReferent,
    UnknownSeam,
    canonical_json,
    freeze_bundle,
    stable_id,
)

VERSION = "forge.semantic-delta-replay/0.1"
_COLLECTIONS = ("sources", "evidence", "entities", "facts", "unknowns")
_REMOVE_ORDER = tuple(reversed(_COLLECTIONS))
_UPSERT_ORDER = _COLLECTIONS


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(asdict(value)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DeltaOperation:
    operation_id: str
    action: str
    collection: str
    key: str
    before_sha256: str | None
    after_sha256: str | None
    value: Any | None

    @classmethod
    def create(cls, *, action: str, collection: str, key: str, before: Any | None, after: Any | None) -> "DeltaOperation":
        if action not in {"REMOVE", "UPSERT"}:
            raise ValueError(f"unsupported action: {action}")
        if collection not in _COLLECTIONS:
            raise ValueError(f"unsupported collection: {collection}")
        if action == "REMOVE" and (before is None or after is not None):
            raise ValueError("REMOVE requires before and forbids after")
        if action == "UPSERT" and after is None:
            raise ValueError("UPSERT requires after")
        before_sha = _digest(before) if before is not None else None
        after_sha = _digest(after) if after is not None else None
        payload = {
            "action": action,
            "collection": collection,
            "key": key,
            "before_sha256": before_sha,
            "after_sha256": after_sha,
        }
        return cls(stable_id("op", payload), action, collection, key, before_sha, after_sha, after)

    def descriptor(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "action": self.action,
            "collection": self.collection,
            "key": self.key,
            "before_sha256": self.before_sha256,
            "after_sha256": self.after_sha256,
            "value": asdict(self.value) if self.value is not None else None,
        }


@dataclass(frozen=True)
class SemanticDeltaPlan:
    plan_id: str
    base_bundle_id: str
    target_bundle_id: str
    operations: tuple[DeltaOperation, ...]
    delta_authority: str = "NONE"
    version: str = VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "plan_id": self.plan_id,
            "base_bundle_id": self.base_bundle_id,
            "target_bundle_id": self.target_bundle_id,
            "delta_authority": self.delta_authority,
            "operations": [x.descriptor() for x in self.operations],
        }


def build_plan(base: FrozenSemanticFactBundle, target: FrozenSemanticFactBundle) -> SemanticDeltaPlan:
    if base.authority != "NONE" or target.authority != "NONE":
        raise ValueError("semantic replay refuses authority-bearing bundles")
    removes: list[DeltaOperation] = []
    upserts: list[DeltaOperation] = []
    for coll in _COLLECTIONS:
        a: Mapping[str, Any] = getattr(base, coll)
        b: Mapping[str, Any] = getattr(target, coll)
        for key in sorted(set(a) - set(b)):
            removes.append(DeltaOperation.create(action="REMOVE", collection=coll, key=key, before=a[key], after=None))
        for key in sorted(set(b)):
            if key not in a:
                upserts.append(DeltaOperation.create(action="UPSERT", collection=coll, key=key, before=None, after=b[key]))
            elif a[key] != b[key]:
                # Exact ID collision with differing payload is an invalid semantic state.
                raise ValueError(f"same key has different payload in {coll}: {key}")
    removes.sort(key=lambda x: (_REMOVE_ORDER.index(x.collection), x.key))
    upserts.sort(key=lambda x: (_UPSERT_ORDER.index(x.collection), x.key))
    ops = tuple(removes + upserts)
    payload = {
        "base_bundle_id": base.bundle_id,
        "target_bundle_id": target.bundle_id,
        "delta_authority": "NONE",
        "operations": [x.descriptor() for x in ops],
    }
    return SemanticDeltaPlan(stable_id("sdelta", payload), base.bundle_id, target.bundle_id, ops)


def _copy_bundle(base: FrozenSemanticFactBundle) -> SemanticFactBundle:
    return SemanticFactBundle(
        producer=base.producer,
        sources=dict(base.sources),
        evidence=dict(base.evidence),
        entities=dict(base.entities),
        facts=dict(base.facts),
        unknowns=dict(base.unknowns),
        target_execution=base.target_execution,
        authority=base.authority,
        schema=base.schema,
    )


def replay_plan(
    base: FrozenSemanticFactBundle,
    plan: SemanticDeltaPlan,
    *,
    target_producer: str,
    target_source_texts_by_path: Mapping[str, str],
) -> FrozenSemanticFactBundle:
    if plan.delta_authority != "NONE":
        raise ValueError("delta authority must remain NONE")
    if base.bundle_id != plan.base_bundle_id:
        raise ValueError(f"stale/wrong replay base: {base.bundle_id} != {plan.base_bundle_id}")
    out = _copy_bundle(base)
    out.producer = target_producer

    for op in plan.operations:
        coll = getattr(out, op.collection)
        existing = coll.get(op.key)
        existing_sha = _digest(existing) if existing is not None else None
        if existing_sha != op.before_sha256:
            raise ValueError(f"operation precondition failed: {op.operation_id}")
        if op.action == "REMOVE":
            del coll[op.key]
        elif op.action == "UPSERT":
            if op.value is None or _digest(op.value) != op.after_sha256:
                raise ValueError(f"operation payload digest failed: {op.operation_id}")
            coll[op.key] = op.value
        else:
            raise ValueError(f"unsupported action: {op.action}")

    frozen = freeze_bundle(out, target_source_texts_by_path)
    if frozen.bundle_id != plan.target_bundle_id:
        raise ValueError(f"target bundle mismatch: {frozen.bundle_id} != {plan.target_bundle_id}")
    return frozen
