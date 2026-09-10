from __future__ import annotations

import copy
import unittest

from forge_app.hud.workbench_model import (
    WorkbenchInteractionState,
    WorkbenchModelError,
    apply_readonly_command,
    build_delta_preview,
    build_workbench_model,
    render_workbench_text,
)
from singularity_works.semantic_field import (
    EvidenceSpan,
    SemanticFact,
    SemanticFactBundle,
    SourceReferent,
    UnknownSeam,
    freeze_bundle,
)


class ForgeWorkbenchModelV01Tests(unittest.TestCase):
    def fixture(self):
        text = "def route(request):\n    return request.user.name\n"
        source = SourceReferent.from_text("demo/routes.py", "python", text)
        bundle = SemanticFactBundle(producer="workbench-test")
        bundle.add_source(source)
        evidence = EvidenceSpan.from_lines(source, text, 1, 2)
        bundle.add_evidence(evidence)
        route = bundle.add_entity(
            kind="function",
            name="route",
            source_id=source.source_id,
            evidence_id=evidence.evidence_id,
        )
        capability = bundle.add_entity(
            kind="capability",
            name="render_user_name",
            source_id=source.source_id,
            evidence_id=evidence.evidence_id,
        )
        fact_route = SemanticFact.create(
            subject_id=route,
            predicate="reads_value",
            object_value={"entity_id": capability, "field": "request.user.name"},
            evidence_ids=[evidence.evidence_id],
            evidence_status="parsed",
            producer="workbench-test",
            assurance_ceiling="EXACT_SOURCE_SLICE_ONLY",
        )
        bundle.add_fact(fact_route)
        fact_capability = SemanticFact.create(
            subject_id=capability,
            predicate="implemented_by",
            object_value={"entity_id": route},
            evidence_ids=[evidence.evidence_id],
            evidence_status="derived",
            producer="workbench-test",
            assurance_ceiling="BOUNDED_TEST_FIXTURE",
            derivation_from=[fact_route.fact_id],
        )
        bundle.add_fact(fact_capability)
        seam = UnknownSeam.create(
            subject_id=route,
            question="Does this value cross a trust boundary?",
            reason="The fixture does not model request authentication.",
            evidence_ids=[evidence.evidence_id],
            producer="workbench-test",
            assurance_ceiling="UNKNOWN",
            blocking=True,
        )
        bundle.add_unknown(seam)
        frozen = freeze_bundle(bundle, {source.path: text})
        return frozen, route, capability, evidence.evidence_id, seam.seam_id

    def delta_fixture(self):
        plan = {
            "version": "forge.semantic-delta-replay/0.1.3",
            "plan_id": "sdelta:test-plan",
            "base_bundle_id": "bundle:old",
            "target_bundle_id": "bundle:new",
            "delta_authority": "NONE",
            "operations": [
                {
                    "action": "REMOVE",
                    "collection": "facts",
                    "key": "fact:old",
                    "operation_id": "op:remove-fact",
                    "before_sha256": "a" * 64,
                    "after_sha256": None,
                    "value": None,
                },
                {
                    "action": "UPSERT",
                    "collection": "facts",
                    "key": "fact:new",
                    "operation_id": "op:upsert-fact",
                    "before_sha256": None,
                    "after_sha256": "b" * 64,
                    "value": {"fact_id": "fact:new"},
                },
                {
                    "action": "UPSERT",
                    "collection": "sources",
                    "key": "src:new",
                    "operation_id": "op:upsert-source",
                    "before_sha256": None,
                    "after_sha256": "c" * 64,
                    "value": {"source_id": "src:new", "path": "demo/routes.py"},
                },
            ],
        }
        checks = {
            "authority_none": True,
            "operations_nonempty": True,
            "comment_plan_deterministic": True,
            "comment_replay_exact_bundle_id": True,
            "comment_replay_exact_serialization": True,
            "semantic_removal_replay_exact_bundle_id": True,
            "semantic_removal_replay_exact_serialization": True,
            "reverse_replay_exact_bundle_id": True,
            "reverse_replay_exact_serialization": True,
            "stale_base_rejected": True,
            "tampered_precondition_rejected": True,
            "target_clean_before": True,
            "target_clean_after": True,
            "target_head_unchanged": True,
        }
        summary = {
            "schema": "forge.semantic-delta-replay-pygoat/0.1.3",
            "verdict": "PASS",
            "pass_count": len(checks),
            "check_count": len(checks),
            "checks": checks,
            "claim_ceiling": "EXACT_SEMANTIC_BUNDLE_REPLAY_OVER_QUALIFIED_PYGOAT_SNAPSHOTS_ONLY",
            "plans": {
                "comment": {"plan_id": plan["plan_id"], "operations": len(plan["operations"])},
                "reverse_removed_to_old": {"plan_id": "sdelta:reverse", "operations": 2},
            },
            "not_proven": ["source-code edit materialization"],
        }
        return plan, summary

    def test_model_is_deterministic_authority_none_and_unknown_visible(self) -> None:
        bundle, route, _capability, _evidence, seam = self.fixture()
        state = WorkbenchInteractionState(selected_entity_id=route)
        model1 = build_workbench_model(bundle, currentness="MATCH", state=state)
        model2 = build_workbench_model(bundle, currentness="MATCH", state=state)
        self.assertEqual(model1.canonical_json(), model2.canonical_json())
        self.assertEqual(model1.model_sha256, model2.model_sha256)
        self.assertEqual(model1.source_bundle_id, bundle.bundle_id)
        self.assertEqual(model1.source_authority, "NONE")
        self.assertEqual(model1.projection_authority, "NONE")
        self.assertEqual(model1.currentness, "MATCH")
        self.assertEqual(model1.total_unknown_count, 1)
        self.assertEqual(model1.unknowns[0].seam_id, seam)
        self.assertTrue(model1.unknowns[0].blocking)
        self.assertIsNotNone(model1.inspector)

    def test_inspector_preserves_exact_fact_and_evidence_referents(self) -> None:
        bundle, route, _capability, evidence_id, seam_id = self.fixture()
        model = build_workbench_model(
            bundle,
            currentness="MISMATCH",
            state=WorkbenchInteractionState(selected_entity_id=route),
        )
        inspector = model.inspector
        self.assertIsNotNone(inspector)
        assert inspector is not None
        self.assertEqual(inspector.entity_id, route)
        self.assertEqual(inspector.source_path, "demo/routes.py")
        self.assertEqual(len(inspector.facts), 1)
        self.assertEqual(inspector.facts[0].predicate, "reads_value")
        self.assertEqual(inspector.facts[0].evidence_status, "parsed")
        self.assertEqual(inspector.evidence[0].evidence_id, evidence_id)
        self.assertEqual(inspector.evidence[0].source_path, "demo/routes.py")
        self.assertEqual((inspector.evidence[0].start_line, inspector.evidence[0].end_line), (1, 3))
        self.assertEqual(inspector.unknowns[0].seam_id, seam_id)
        self.assertEqual(model.currentness, "MISMATCH")

    def test_lenses_and_search_only_filter_existing_entities(self) -> None:
        bundle, route, capability, _evidence, _seam = self.fixture()
        all_ids = set(bundle.entities)
        capability_model = build_workbench_model(
            bundle,
            state=WorkbenchInteractionState(lens="capability"),
        )
        self.assertEqual([node.entity_id for node in capability_model.nodes], [capability])
        unknown_model = build_workbench_model(bundle, state=WorkbenchInteractionState(lens="unknown"))
        self.assertEqual([node.entity_id for node in unknown_model.nodes], [route])
        search_model = build_workbench_model(bundle, state=WorkbenchInteractionState(query="request.user.name"))
        self.assertEqual({node.entity_id for node in search_model.nodes}, {route})
        for model in (capability_model, unknown_model, search_model):
            self.assertTrue({node.entity_id for node in model.nodes}.issubset(all_ids))
        self.assertEqual(search_model.total_entity_count, len(all_ids))

    def test_unknown_selection_fails_closed(self) -> None:
        bundle, *_ = self.fixture()
        with self.assertRaisesRegex(WorkbenchModelError, "unknown entity"):
            build_workbench_model(
                bundle,
                state=WorkbenchInteractionState(selected_entity_id="ent:not-real"),
            )

    def test_delta_preview_accepts_bounded_pass_but_materialization_stays_disabled(self) -> None:
        plan, summary = self.delta_fixture()
        preview = build_delta_preview(plan, summary)
        self.assertEqual(preview.qualification_status, "QUALIFIED_BOUNDED")
        self.assertEqual(preview.operation_count, 3)
        self.assertEqual(preview.checks_passed, 14)
        self.assertEqual(preview.checks_total, 14)
        self.assertTrue(preview.reverse_replay_evidence)
        self.assertFalse(preview.materialization_enabled)
        self.assertIn("source edit materialization", preview.materialization_reason)
        counts = {item.collection: item for item in preview.collection_counts}
        self.assertEqual((counts["facts"].remove_count, counts["facts"].upsert_count), (1, 1))
        self.assertEqual((counts["sources"].remove_count, counts["sources"].upsert_count), (0, 1))

    def test_unqualified_or_malformed_delta_does_not_gain_authority(self) -> None:
        plan, summary = self.delta_fixture()
        failed = copy.deepcopy(summary)
        failed["checks"]["tampered_precondition_rejected"] = False
        failed["pass_count"] -= 1
        preview = build_delta_preview(plan, failed)
        self.assertEqual(preview.qualification_status, "UNQUALIFIED")
        self.assertEqual(preview.delta_authority, "NONE")
        self.assertFalse(preview.materialization_enabled)

        elevated = copy.deepcopy(plan)
        elevated["delta_authority"] = "WRITE"
        with self.assertRaisesRegex(WorkbenchModelError, "authority must remain NONE"):
            build_delta_preview(elevated, summary)

        duplicate = copy.deepcopy(plan)
        duplicate["operations"][1]["operation_id"] = duplicate["operations"][0]["operation_id"]
        with self.assertRaisesRegex(WorkbenchModelError, "duplicate semantic delta operation_id"):
            build_delta_preview(duplicate, summary)

    def test_workbench_binds_delta_without_enabling_apply(self) -> None:
        bundle, route, *_ = self.fixture()
        plan, summary = self.delta_fixture()
        model = build_workbench_model(
            bundle,
            currentness="MATCH",
            state=WorkbenchInteractionState(selected_entity_id=route),
            delta_plan=plan,
            delta_qualification_summary=summary,
        )
        self.assertIsNotNone(model.delta_preview)
        assert model.delta_preview is not None
        self.assertEqual(model.delta_preview.qualification_status, "QUALIFIED_BOUNDED")
        materialize = next(item for item in model.commands if item.command_id == "materialize")
        self.assertFalse(materialize.enabled)
        self.assertEqual(materialize.consequence_scope, "DISABLED")
        self.assertTrue(all(item.consequence_scope in {"READ_ONLY_UI", "DISABLED"} for item in model.commands))

    def test_readonly_command_reducer_never_dispatches_consequence(self) -> None:
        bundle, route, capability, *_ = self.fixture()
        state = WorkbenchInteractionState()
        result = apply_readonly_command(state, f"select {route}", bundle=bundle)
        self.assertTrue(result.accepted)
        self.assertEqual(result.state.selected_entity_id, route)
        self.assertEqual(result.consequence_scope, "READ_ONLY_UI")

        result = apply_readonly_command(result.state, "lens capability", bundle=bundle)
        self.assertTrue(result.accepted)
        self.assertEqual(result.state.lens, "capability")

        result = apply_readonly_command(result.state, "find render_user_name", bundle=bundle)
        self.assertTrue(result.accepted)
        model = build_workbench_model(bundle, state=result.state)
        self.assertEqual([node.entity_id for node in model.nodes], [capability])

        denied = apply_readonly_command(result.state, "materialize", bundle=bundle)
        self.assertFalse(denied.accepted)
        self.assertEqual(denied.consequence_scope, "DISABLED")
        self.assertIn("SOURCE_EDIT_MATERIALIZATION", denied.message)

        unknown = apply_readonly_command(result.state, "shell rm -rf anything", bundle=bundle)
        self.assertFalse(unknown.accepted)
        self.assertEqual(unknown.ui_intent, "NONE")

    def test_preview_commands_require_qualified_bound_preview(self) -> None:
        bundle, *_ = self.fixture()
        state = WorkbenchInteractionState()
        denied = apply_readonly_command(state, "preview-delta", bundle=bundle)
        self.assertFalse(denied.accepted)
        plan, summary = self.delta_fixture()
        preview = build_delta_preview(plan, summary)
        allowed = apply_readonly_command(state, "preview-delta", bundle=bundle, delta_preview=preview)
        self.assertTrue(allowed.accepted)
        self.assertEqual(allowed.ui_intent, "SHOW_DELTA_PREVIEW")
        reverse = apply_readonly_command(state, "reverse-preview", bundle=bundle, delta_preview=preview)
        self.assertTrue(reverse.accepted)
        self.assertEqual(reverse.ui_intent, "SHOW_REVERSE_REPLAY_EVIDENCE")

    def test_text_renderer_keeps_truth_and_materialization_boundaries_visible(self) -> None:
        bundle, route, *_ = self.fixture()
        plan, summary = self.delta_fixture()
        model = build_workbench_model(
            bundle,
            currentness="MISMATCH",
            state=WorkbenchInteractionState(selected_entity_id=route),
            delta_plan=plan,
            delta_qualification_summary=summary,
        )
        rendered = render_workbench_text(model, width=100)
        self.assertIn("FORGE // WORKBENCH", rendered)
        self.assertIn("CURRENTNESS MISMATCH", rendered)
        self.assertIn("FIELD AUTHORITY NONE", rendered)
        self.assertIn("PROJECTION AUTHORITY NONE", rendered)
        self.assertIn("DELTA QUALIFIED_BOUNDED", rendered)
        self.assertIn("MATERIALIZE DISABLED", rendered)
        self.assertIn("UNKNOWN BLOCKING", rendered)

    def test_model_rejects_non_frozen_or_authoritative_field(self) -> None:
        bundle, *_ = self.fixture()
        mutable = SemanticFactBundle(producer="mutable")
        with self.assertRaisesRegex(WorkbenchModelError, "FrozenSemanticFactBundle"):
            build_workbench_model(mutable)  # type: ignore[arg-type]

        authoritative = copy.copy(bundle)
        object.__setattr__(authoritative, "authority", "WRITE")
        with self.assertRaisesRegex(WorkbenchModelError, "authority NONE"):
            build_workbench_model(authoritative)


if __name__ == "__main__":
    unittest.main()
