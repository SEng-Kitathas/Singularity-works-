from __future__ import annotations

"""Exact-evidence source materializer for Singularity Works semantic deltas.

The materializer is intentionally not a semantic authority. It receives an exact
fact/evidence referent plus caller-supplied replacement bytes, verifies preconditions,
and can apply/invert that byte-range edit. Semantic correctness is established only
by re-lowering source and comparing the observed SnapshotDelta.
"""

from dataclasses import dataclass, asdict
import difflib
import hashlib
from typing import Any, Mapping

from .semantic_field import FrozenSemanticFactBundle
from .semantic_field_delta import fact_semantic_key

VERSION = "singularity-works.semantic-materializer/0.1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class SourcePatch:
    patch_id: str
    source_path: str
    expected_source_sha256: str
    expected_snippet_sha256: str
    start_byte: int
    end_byte: int
    old_text: str
    new_text: str
    expected_post_sha256: str
    intended_fact_id: str | None
    intended_semantic_key: str | None
    intended_operation: str
    materializer_authority: str = "NONE"
    explicit_apply_required: bool = True
    version: str = VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def inverse(self) -> "SourcePatch":
        old_bytes = self.old_text.encode("utf-8")
        new_bytes = self.new_text.encode("utf-8")
        payload = {
            "source_path": self.source_path,
            "expected_source_sha256": self.expected_post_sha256,
            "expected_snippet_sha256": sha256_bytes(new_bytes),
            "start_byte": self.start_byte,
            "end_byte": self.start_byte + len(new_bytes),
            "old_text": self.new_text,
            "new_text": self.old_text,
            "expected_post_sha256": self.expected_source_sha256,
            "intended_fact_id": self.intended_fact_id,
            "intended_semantic_key": self.intended_semantic_key,
            "intended_operation": f"inverse:{self.intended_operation}",
        }
        return SourcePatch(
            patch_id=_patch_id(payload),
            materializer_authority="NONE",
            explicit_apply_required=True,
            version=VERSION,
            **payload,
        )


def _patch_id(payload: Mapping[str, Any]) -> str:
    raw = repr(sorted(payload.items())).encode("utf-8")
    return f"patch:{sha256_bytes(raw)[:24]}"


def plan_replace_fact_evidence(
    snapshot: FrozenSemanticFactBundle,
    source_texts_by_path: Mapping[str, str],
    *,
    fact_id: str,
    new_text: str,
    intended_operation: str,
    evidence_index: int = 0,
) -> SourcePatch:
    if fact_id not in snapshot.facts:
        raise ValueError(f"unknown fact: {fact_id}")
    fact = snapshot.facts[fact_id]
    if not fact.evidence_ids:
        raise ValueError("fact has no evidence span to materialize")
    if evidence_index < 0 or evidence_index >= len(fact.evidence_ids):
        raise ValueError("evidence index out of range")
    evidence_id = fact.evidence_ids[evidence_index]
    evidence = snapshot.evidence[evidence_id]
    source = snapshot.sources[evidence.source_id]
    if source.path not in source_texts_by_path:
        raise ValueError(f"missing source text: {source.path}")
    text = source_texts_by_path[source.path]
    data = text.encode("utf-8")
    if sha256_bytes(data) != source.sha256:
        raise ValueError("source referent drift before planning")
    old_bytes = data[evidence.start_byte:evidence.end_byte]
    if sha256_bytes(old_bytes) != evidence.snippet_sha256:
        raise ValueError("evidence snippet drift before planning")
    old_text = old_bytes.decode("utf-8")
    new_bytes = new_text.encode("utf-8")
    post = data[:evidence.start_byte] + new_bytes + data[evidence.end_byte:]
    payload = {
        "source_path": source.path,
        "expected_source_sha256": source.sha256,
        "expected_snippet_sha256": evidence.snippet_sha256,
        "start_byte": evidence.start_byte,
        "end_byte": evidence.end_byte,
        "old_text": old_text,
        "new_text": new_text,
        "expected_post_sha256": sha256_bytes(post),
        "intended_fact_id": fact_id,
        "intended_semantic_key": fact_semantic_key(snapshot, fact),
        "intended_operation": intended_operation,
    }
    return SourcePatch(
        patch_id=_patch_id(payload),
        materializer_authority="NONE",
        explicit_apply_required=True,
        version=VERSION,
        **payload,
    )


def apply_patch_to_text(patch: SourcePatch, source_text: str) -> tuple[str, dict[str, Any]]:
    data = source_text.encode("utf-8")
    actual_pre = sha256_bytes(data)
    if actual_pre != patch.expected_source_sha256:
        raise ValueError(f"source precondition failed: {actual_pre} != {patch.expected_source_sha256}")
    if patch.start_byte < 0 or patch.end_byte < patch.start_byte or patch.end_byte > len(data):
        raise ValueError("patch span outside source")
    current = data[patch.start_byte:patch.end_byte]
    if sha256_bytes(current) != patch.expected_snippet_sha256:
        raise ValueError("snippet precondition failed")
    if current.decode("utf-8") != patch.old_text:
        raise ValueError("old-text precondition failed")
    new_bytes = patch.new_text.encode("utf-8")
    post = data[:patch.start_byte] + new_bytes + data[patch.end_byte:]
    actual_post = sha256_bytes(post)
    if actual_post != patch.expected_post_sha256:
        raise ValueError("postimage hash does not match patch plan")
    return post.decode("utf-8"), {
        "patch_id": patch.patch_id,
        "pre_sha256": actual_pre,
        "post_sha256": actual_post,
        "start_byte": patch.start_byte,
        "old_bytes": len(current),
        "new_bytes": len(new_bytes),
        "materializer_authority": "NONE",
    }


def unified_diff(patch: SourcePatch) -> str:
    old = patch.old_text.splitlines(keepends=True)
    new = patch.new_text.splitlines(keepends=True)
    return "".join(difflib.unified_diff(
        old, new,
        fromfile=f"a/{patch.source_path}",
        tofile=f"b/{patch.source_path}",
        lineterm="\n",
    ))
