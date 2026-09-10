from __future__ import annotations

import unittest
from dataclasses import replace

from forge_app.ergo.recovery_summary import ErgoRecoverySummary, GitSourceSummary
from forge_app.hud.workbench_model import WorkbenchInteractionState, build_workbench_model
from forge_app.shell.githome_model import GitHomeInteractionState, ProjectEntry, ProjectSnapshot, build_githome_model
from forge_app.shell.workspace_model import (
    ForgeShellWorkspaceError,
    ForgeShellWorkspaceState,
    apply_workspace_command,
    build_workspace_model,
    recovery_summary_sha256,
    render_workspace_text,
)
from singularity_works.semantic_field import EvidenceSpan, SemanticFact, SemanticFactBundle, SourceReferent, freeze_bundle


class ForgeShellWorkspaceV01Tests(unittest.TestCase):
    def workbench(self, *, currentness: str = "MATCH", query: str = ""):
        text = "def hello():\n    return 'hi'\n"
        source = SourceReferent.from_text("demo.py", "python", text)
        bundle = SemanticFactBundle(producer="workspace-test")
        bundle.add_source(source)
        evidence = EvidenceSpan.from_lines(source, text, 1, 2)
        bundle.add_evidence(evidence)
        entity = bundle.add_entity(kind="function", name="hello", source_id=source.source_id, evidence_id=evidence.evidence_id)
        bundle.add_fact(
            SemanticFact.create(
                subject_id=entity,
                predicate="returns_literal",
                object_value="hi",
                evidence_ids=[evidence.evidence_id],
                evidence_status="parsed",
                producer="workspace-test",
                assurance_ceiling="FIXTURE_ONLY",
            )
        )
        frozen = freeze_bundle(bundle, {source.path: text})
        return build_workbench_model(
            frozen,
            currentness=currentness,
            state=WorkbenchInteractionState(query=query, selected_entity_id=entity),
        )

    def project_snapshot(self, head: str = "a" * 40) -> ProjectSnapshot:
        entries = (
            ProjectEntry(".", "repo", "directory", True, None, True, False, None, "AGGREGATE", 1, 1, ("CLEAN",)),
            ProjectEntry("demo.py", "demo.py", "file", True, 12, True, False, None, "CLEAN", 0, 0, ()),
        )
        return ProjectSnapshot(
            schema="forge-githome-project-snapshot/0.1",
            root_path="/fixture/repo",
            root_name="repo",
            git_available=True,
            git_error=None,
            head=head,
            branch="main",
            upstream="origin/main",
            ahead=0,
            behind=0,
            dirty=False,
            entries=entries,
            file_count=1,
            directory_count=1,
            ignored_file_count=0,
            untracked_file_count=0,
            changed_tracked_file_count=0,
            scan_errors=(),
        )

    def ergo(self, *, head: str | None = "a" * 40, store_status: str = "READY", recovery_required: bool = False):
        source = GitSourceSummary(
            repo_path="/fixture/repo",
            available=head is not None,
            head=head,
            branch="main" if head is not None else None,
            dirty=False if head is not None else None,
            status_lines=(),
            error=None if head is not None else "unavailable",
        )
        return ErgoRecoverySummary(
            schema="forge-ergo-recovery-summary/0.1",
            store_path="/fixture/attempt_store.sqlite3",
            store_status=store_status,
            integrity_ok=store_status == "READY",
            integrity=("ok",) if store_status == "READY" else (),
            journal_mode="wal" if store_status == "READY" else None,
            schema_version="0.1" if store_status == "READY" else None,
            blob_count=10 if store_status == "READY" else None,
            attempt_count=12 if store_status == "READY" else None,
            event_count=20 if store_status == "READY" else None,
            last_event=None,
            latest_attempts=(),
            source=source,
            normal_mode_allowed=not recovery_required,
            safe_mode_available=True,
            recovery_mode_required=recovery_required,
            reasons=("store unavailable",) if recovery_required else (),
            observer_authority="NONE",
        )

    def composed(self, *, semantic_currentness: str = "MATCH", source_head: str = "a" * 40, ergo_head: str | None = "a" * 40, recovery_required: bool = False):
        workbench = self.workbench(currentness=semantic_currentness)
        githome = build_githome_model(self.project_snapshot(source_head), state=GitHomeInteractionState(selected_path="demo.py"), workbench=workbench)
        ergo = self.ergo(head=ergo_head, store_status="MISSING" if recovery_required else "READY", recovery_required=recovery_required)
        workspace = build_workspace_model(githome, workbench, ergo)
        return githome, workbench, ergo, workspace

    def test_composition_is_deterministic_and_authority_none(self) -> None:
        githome, workbench, ergo, first = self.composed()
        second = build_workspace_model(githome, workbench, ergo)
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertEqual(first.model_sha256, second.model_sha256)
        self.assertEqual(first.projection_authority, "NONE")
        self.assertEqual({panel.authority for panel in first.panels}, {"NONE"})
        self.assertEqual(first.source_alignment, "MATCH")
        self.assertEqual(first.semantic_currentness, "MATCH")
        self.assertEqual(first.policy_mode, "NORMAL")
        self.assertEqual(first.alerts, ())

    def test_githome_workbench_binding_mismatch_fails_closed(self) -> None:
        wb1 = self.workbench(currentness="MATCH", query="")
        wb2 = self.workbench(currentness="MATCH", query="hello")
        githome = build_githome_model(self.project_snapshot(), workbench=wb1)
        with self.assertRaisesRegex(ForgeShellWorkspaceError, "does not match"):
            build_workspace_model(githome, wb2, self.ergo())

    def test_source_alignment_and_semantic_currentness_remain_separate(self) -> None:
        _g, _w, _e, workspace = self.composed(semantic_currentness="MATCH", source_head="a" * 40, ergo_head="b" * 40)
        self.assertEqual(workspace.source_alignment, "MISMATCH")
        self.assertEqual(workspace.semantic_currentness, "MATCH")
        self.assertIn("SOURCE_HEAD_MISMATCH", workspace.alerts)
        self.assertNotIn("SEMANTIC_CURRENTNESS_MISMATCH", workspace.alerts)

        _g, _w, _e, workspace = self.composed(semantic_currentness="MISMATCH")
        self.assertEqual(workspace.source_alignment, "MATCH")
        self.assertEqual(workspace.semantic_currentness, "MISMATCH")
        self.assertIn("SEMANTIC_CURRENTNESS_MISMATCH", workspace.alerts)

    def test_unknown_currentness_is_visible_not_promoted(self) -> None:
        _g, _w, _e, workspace = self.composed(semantic_currentness="UNKNOWN", ergo_head=None)
        self.assertEqual(workspace.source_alignment, "UNKNOWN")
        self.assertEqual(workspace.semantic_currentness, "UNKNOWN")
        self.assertIn("SOURCE_ALIGNMENT_UNKNOWN", workspace.alerts)
        self.assertIn("SEMANTIC_CURRENTNESS_UNKNOWN", workspace.alerts)

    def test_recovery_required_forces_policy_without_authority(self) -> None:
        _g, _w, _e, workspace = self.composed(recovery_required=True)
        self.assertEqual(workspace.policy_mode, "RECOVERY")
        self.assertTrue(workspace.recovery_required)
        self.assertIn("RECOVERY_REQUIRED", workspace.alerts)
        self.assertIn("ATTEMPT_STORE_MISSING", workspace.alerts)
        self.assertEqual(workspace.projection_authority, "NONE")

    def test_focus_and_layout_commands_are_ui_only(self) -> None:
        state = ForgeShellWorkspaceState()
        focused = apply_workspace_command(state, "focus project")
        self.assertTrue(focused.accepted)
        self.assertEqual(focused.state.active_panel, "project")
        self.assertEqual(focused.consequence_scope, "READ_ONLY_UI")
        layout = apply_workspace_command(focused.state, "layout recovery")
        self.assertTrue(layout.accepted)
        self.assertEqual(layout.state.layout, "recovery")
        self.assertEqual(layout.state.active_panel, "recovery")
        denied = apply_workspace_command(layout.state, "git push")
        self.assertFalse(denied.accepted)
        self.assertEqual(denied.ui_intent, "NONE")
        self.assertEqual(denied.state, layout.state)

    def test_render_binding_tamper_fails_closed(self) -> None:
        githome, workbench, ergo, workspace = self.composed()
        bad_panel = replace(workspace.panels[0], model_sha256="0" * 64)
        tampered = replace(workspace, panels=(bad_panel, *workspace.panels[1:]))
        with self.assertRaisesRegex(ForgeShellWorkspaceError, "binding hash mismatch"):
            render_workspace_text(tampered, githome=githome, workbench=workbench, ergo=ergo)

    def test_text_workspace_renders_all_domains_and_boundaries(self) -> None:
        githome, workbench, ergo, workspace = self.composed(semantic_currentness="UNKNOWN")
        text = render_workspace_text(workspace, githome=githome, workbench=workbench, ergo=ergo, width=120)
        self.assertIn("SINGULARITY WORKS // FORGE SHELL", text)
        self.assertIn("SINGULARITY WORKS / GITHOME", text)
        self.assertIn("FORGE // WORKBENCH", text)
        self.assertIn("ERGO / RECOVERY", text)
        self.assertIn("SHELL AUTHORITY NONE", text)
        self.assertIn("SEMANTIC CURRENTNESS UNKNOWN", text)
        self.assertIn("FIELD AUTHORITY NONE", text)
        self.assertIn("AUTHORITY NONE/NONE", text)

    def test_recovery_summary_hash_is_stable(self) -> None:
        summary = self.ergo()
        self.assertEqual(recovery_summary_sha256(summary), recovery_summary_sha256(summary))
        changed = replace(summary, event_count=21)
        self.assertNotEqual(recovery_summary_sha256(summary), recovery_summary_sha256(changed))


if __name__ == "__main__":
    unittest.main()
