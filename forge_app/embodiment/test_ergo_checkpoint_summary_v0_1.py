from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from forge_app.ergo.checkpoint_summary import build_checkpoint_summary
from forge_app.ergo.launch_model import build_launch_model, render_minimal_text
from forge_app.ergo.recovery_summary import ErgoRecoverySummary, GitSourceSummary
from forge_app.recovery import AttemptStore
from forge_app.recovery.resume_checkpoint import ResumeCheckpointManager, ResumeCheckpointPayload


def payload(generation: int, *, parent: str | None = None) -> ResumeCheckpointPayload:
    return ResumeCheckpointPayload(
        session_id="ergo-checkpoint-summary",
        generation=generation,
        parent_checkpoint_id=parent,
        project_id="singularity-works-forge-app",
        workspace_id="workspace-main",
        source_branch="forge/app-shell-rd",
        source_head=f"head-{generation}",
        core_contract_version=None,
        core_currentness_id=None,
        semantic_snapshot_id=None,
    )


def recovery_summary() -> ErgoRecoverySummary:
    return ErgoRecoverySummary(
        schema="forge-ergo-recovery-summary/0.1",
        store_path="X:/store/attempt_store.sqlite3",
        store_status="READY",
        integrity_ok=True,
        integrity=("ok",),
        journal_mode="wal",
        schema_version="forge-attempt-store/0.1",
        blob_count=1,
        attempt_count=1,
        event_count=1,
        last_event=None,
        latest_attempts=(),
        source=GitSourceSummary(
            repo_path="X:/source",
            available=True,
            head="f" * 64,
            branch="forge/app-shell-rd",
            dirty=False,
            status_lines=(),
            error=None,
        ),
        normal_mode_allowed=True,
        safe_mode_available=True,
        recovery_mode_required=False,
        reasons=(),
        observer_authority="NONE",
    )


class ErgoCheckpointSummaryV01Tests(unittest.TestCase):
    def test_missing_store_is_reported_without_creation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "missing"
            self.assertFalse(root.exists())
            summary = build_checkpoint_summary(root)
            self.assertEqual(summary.status, "MISSING")
            self.assertEqual(summary.checkpoint_count, 0)
            self.assertIsNone(summary.selected_checkpoint_id)
            self.assertEqual(summary.observer_authority, "NONE")
            self.assertFalse(root.exists())

    def test_store_with_no_checkpoints_reports_none(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            AttemptStore(root)
            summary = build_checkpoint_summary(root)
            self.assertEqual(summary.status, "NONE")
            self.assertEqual(summary.checkpoint_count, 0)
            self.assertIsNone(summary.selected_checkpoint_id)

    def test_verified_checkpoint_is_selected_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            store = AttemptStore(root)
            manager = ResumeCheckpointManager(store)
            checkpoint_id = manager.capture_checkpoint(
                payload(1), checkpoint_id="checkpoint-verified"
            )
            db = root / "attempt_store.sqlite3"
            before = (db.read_bytes(), db.stat().st_mtime_ns)
            summary = build_checkpoint_summary(root)
            after = (db.read_bytes(), db.stat().st_mtime_ns)
            self.assertEqual(before, after)
            self.assertEqual(summary.status, "READY")
            self.assertEqual(summary.checkpoint_count, 1)
            self.assertEqual(summary.selected_checkpoint_id, checkpoint_id)
            self.assertEqual(summary.selected_status, "VERIFIED")
            self.assertEqual(summary.selected_resume_policy, "NORMAL")
            self.assertFalse(summary.selected_stable)
            self.assertFalse(summary.selected_lkg)
            self.assertEqual(summary.selected_source_head, "head-1")
            self.assertIsNone(summary.selected_semantic_snapshot_id)

    def test_quarantined_newest_is_not_selected_over_older_lkg(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            store = AttemptStore(root)
            manager = ResumeCheckpointManager(store)
            good = manager.capture_checkpoint(payload(1), checkpoint_id="checkpoint-good")
            manager.record_resume(good, resume_id="resume-good")
            manager.record_health(
                good,
                resume_id="resume-good",
                healthy_seconds=12.0,
                meaningful_operations=4,
            )
            manager.promote_lkg(good, promotion_id="lkg-good")

            risky = manager.capture_checkpoint(
                payload(2, parent=good), checkpoint_id="checkpoint-risky"
            )
            manager.record_resume(risky, resume_id="resume-risky-a")
            manager.record_crash(
                risky,
                resume_id="resume-risky-a",
                crash_id="crash-a",
                seconds_since_resume=2.0,
                failure_domain="session_host",
            )
            manager.record_resume(risky, resume_id="resume-risky-b")
            manager.record_crash(
                risky,
                resume_id="resume-risky-b",
                crash_id="crash-b",
                seconds_since_resume=1.0,
                failure_domain="session_host",
            )

            db = root / "attempt_store.sqlite3"
            before = (db.read_bytes(), db.stat().st_mtime_ns)
            summary = build_checkpoint_summary(root)
            after = (db.read_bytes(), db.stat().st_mtime_ns)
            self.assertEqual(before, after)
            self.assertEqual(summary.checkpoint_count, 2)
            self.assertEqual(summary.selected_checkpoint_id, good)
            self.assertEqual(summary.selected_status, "LKG")
            self.assertTrue(summary.selected_stable)
            self.assertTrue(summary.selected_lkg)
            self.assertEqual(summary.selected_generation, 1)

    def test_launch_model_surfaces_resume_checkpoint_without_minting_core_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            store = AttemptStore(root)
            manager = ResumeCheckpointManager(store)
            manager.capture_checkpoint(payload(1), checkpoint_id="checkpoint-live")
            checkpoint_summary = build_checkpoint_summary(root)
            model = build_launch_model(
                recovery_summary(),
                checkpoint_summary=checkpoint_summary,
            )
            facts = {fact.key: fact for fact in model.facts}
            self.assertEqual(facts["resume_checkpoint"].value, "VERIFIED")
            self.assertEqual(facts["resume_generation"].value, "1")
            self.assertEqual(facts["resume_policy"].value, "NORMAL")
            self.assertEqual(facts["resume_core_snapshot"].value, "not bridged")
            self.assertEqual(facts["resume_core_snapshot"].state, "UNKNOWN")
            rendered = render_minimal_text(model, width=88)
            self.assertIn("Resume checkpoint", rendered)
            self.assertIn("VERIFIED", rendered)
            self.assertIn("Core semantic snapshot", rendered)
            self.assertIn("not bridged", rendered)
            self.assertEqual(model.observer_authority, "NONE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
