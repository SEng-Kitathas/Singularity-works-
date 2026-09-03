from __future__ import annotations

import hashlib
import unittest

from singularity_works.facts import Fact as LegacyFact
from singularity_works.semantic_ir import UniversalSemanticIR
from singularity_works.semantic_field import (
    EvidenceSpan,
    SemanticFact,
    SemanticFactBundle,
    SourceReferent,
    UnknownSeam,
    entity_ref,
    freeze_bundle,
    project,
    verify_bundle,
)
from singularity_works.semantic_field_bridge import (
    build_read_index,
    describe_snapshot,
    select_facts,
)
from singularity_works.semantic_field_delta import diff_snapshots
from singularity_works.semantic_materializer import (
    apply_patch_to_text,
    plan_replace_fact_evidence,
)


def make_snapshot(
    text: str,
    *,
    path: str = "fixture/sample.py",
    predicate: str = "calls",
    fact_properties: dict | None = None,
    unknown: bool = False,
):
    bundle = SemanticFactBundle(producer="tests.semantic-field")
    src = SourceReferent.from_text(path, "python", text)
    bundle.add_source(src)
    ev = EvidenceSpan.from_bytes(src, text, 0, len(text.encode("utf-8")))
    bundle.add_evidence(ev)
    subject = bundle.add_entity(
        kind="function",
        name="fixture.main",
        source_id=src.source_id,
        properties={"module": "fixture"},
    )
    target = bundle.add_entity(kind="external", name="fixture.target")
    fact = SemanticFact.create(
        subject_id=subject,
        predicate=predicate,
        object_value=entity_ref(target),
        evidence_ids=[ev.evidence_id],
        evidence_status="parsed",
        producer="tests.semantic-field",
        assurance_ceiling="TEST_ONLY",
        properties=fact_properties or {"source_surface": "test"},
    )
    bundle.add_fact(fact)
    if unknown:
        bundle.add_unknown(UnknownSeam.create(
            subject_id=subject,
            question="unresolved behavior",
            reason="test seam",
            evidence_ids=[ev.evidence_id],
            producer="tests.semantic-field",
            assurance_ceiling="TEST_ONLY",
        ))
    return freeze_bundle(bundle, {path: text}), fact.fact_id


class SemanticFieldCoreTests(unittest.TestCase):
    def test_coexists_with_legacy_fact_and_semantic_ir(self):
        snap, fid = make_snapshot("target()\n")
        self.assertIn(fid, snap.facts)
        self.assertIsNot(LegacyFact, SemanticFact)
        legacy_ir = UniversalSemanticIR(artifact_id="a", language="python", content="x=1")
        self.assertEqual(legacy_ir.artifact_id, "a")
        self.assertEqual(snap.authority, "NONE")

    def test_frozen_index_projection_equals_scan_and_has_no_authority(self):
        snap, fid = make_snapshot("target()\n", unknown=True)
        idx = build_read_index(snap)
        slow = project(snap, predicates=["calls"], include_unknowns=True)
        fast = select_facts(snap, predicates=["calls"], include_unknowns=True, index=idx)
        self.assertEqual(slow, fast)
        self.assertEqual(slow.selected_fact_ids, (fid,))
        self.assertEqual(slow.projection_authority, "NONE")
        self.assertEqual(idx.projection_authority, "NONE")
        self.assertEqual(len(slow.selected_unknown_ids), 1)

    def test_source_drift_rejected(self):
        text = "target()\n"
        snap, _ = make_snapshot(text)
        report = verify_bundle(snap, {"fixture/sample.py": text + "# drift\n"})
        self.assertFalse(report["pass"])
        self.assertTrue(any("source referent drift" in e for e in report["errors"]))

    def test_evidence_text_change_is_revision_refresh_not_meaning_change(self):
        old, _ = make_snapshot("target(a)\n")
        new, _ = make_snapshot("target(b)\n")
        delta = diff_snapshots(old, new)
        self.assertEqual(delta.added_semantic_keys, ())
        self.assertEqual(delta.removed_semantic_keys, ())
        self.assertEqual(len(delta.refreshed_facts), 1)
        self.assertEqual(delta.delta_authority, "NONE")

    def test_explicit_provider_implementation_identity_is_semantic(self):
        old_text = "lambda x: x + 1"
        new_text = "lambda x: 1 + x"
        old_sha = hashlib.sha256(old_text.encode()).hexdigest()
        new_sha = hashlib.sha256(new_text.encode()).hexdigest()
        old, _ = make_snapshot(old_text, predicate="provides_capability", fact_properties={
            "capability_id": "LOCAL",
            "provider_implementation_sha256": old_sha,
        })
        new, _ = make_snapshot(new_text, predicate="provides_capability", fact_properties={
            "capability_id": "LOCAL",
            "provider_implementation_sha256": new_sha,
        })
        delta = diff_snapshots(old, new)
        self.assertEqual(len(delta.removed_semantic_keys), 1)
        self.assertEqual(len(delta.added_semantic_keys), 1)
        self.assertEqual(len(delta.refreshed_facts), 0)

    def test_materializer_apply_inverse_exact_and_drift_rejected(self):
        text = "target(a)\n"
        snap, fid = make_snapshot(text)
        patch = plan_replace_fact_evidence(
            snap, {"fixture/sample.py": text},
            fact_id=fid, new_text="target(b)\n", intended_operation="replace-call",
        )
        post, receipt = apply_patch_to_text(patch, text)
        self.assertEqual(post, "target(b)\n")
        self.assertEqual(receipt["materializer_authority"], "NONE")
        inverse = patch.inverse()
        restored, _ = apply_patch_to_text(inverse, post)
        self.assertEqual(restored, text)
        with self.assertRaises(ValueError):
            apply_patch_to_text(patch, text + "# stale\n")

    def test_index_rejects_stale_snapshot(self):
        old, _ = make_snapshot("target(a)\n")
        new, _ = make_snapshot("target(b)\n")
        idx = build_read_index(old)
        with self.assertRaises(ValueError):
            idx.query(new, predicates=["calls"])

    def test_bridge_descriptor_is_bounded_read_surface(self):
        snap, _ = make_snapshot("target()\n", unknown=True)
        desc = describe_snapshot(snap)
        self.assertEqual(desc["bundle_id"], snap.bundle_id)
        self.assertEqual(desc["fact_count"], 1)
        self.assertEqual(desc["unknown_count"], 1)
        self.assertEqual(desc["authority"], "NONE")
        self.assertFalse(desc["target_execution"])


if __name__ == "__main__":
    unittest.main()
