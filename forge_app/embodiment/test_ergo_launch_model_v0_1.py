from __future__ import annotations

import json
import unittest

from forge_app.ergo.launch_model import build_launch_model, render_minimal_text
from forge_app.ergo.recovery_summary import ErgoRecoverySummary, GitSourceSummary


def ready_summary(*, dirty: bool = False) -> ErgoRecoverySummary:
    return ErgoRecoverySummary(
        schema="forge-ergo-recovery-summary/0.1",
        store_path="X:/forge/attempt_store.sqlite3",
        store_status="READY",
        integrity_ok=True,
        integrity=("ok",),
        journal_mode="wal",
        schema_version="forge-attempt-store/0.1",
        blob_count=4,
        attempt_count=5,
        event_count=5,
        last_event={"seq": 5, "event_type": "attempt_captured", "attempt_id": "attempt-005"},
        latest_attempts=(
            {
                "attempt_id": "attempt-005",
                "blob_sha256": "a" * 64,
                "parent_attempt_id": "attempt-004",
                "artifact_class": "design.ui",
                "producer": "test",
                "intent": "Preserve the first Ergo launch model before renderer work",
                "metadata": {},
                "created_at": "2026-09-03T00:00:00Z",
            },
        ),
        source=GitSourceSummary(
            repo_path="X:/forge/source",
            available=True,
            head="1234567890abcdef" * 4,
            branch="forge/app-shell-rd",
            dirty=dirty,
            status_lines=(" M forge_app/example",) if dirty else (),
            error=None,
        ),
        normal_mode_allowed=True,
        safe_mode_available=True,
        recovery_mode_required=False,
        reasons=("source repository has uncommitted changes",) if dirty else (),
        observer_authority="NONE",
    )


def recovery_summary() -> ErgoRecoverySummary:
    return ErgoRecoverySummary(
        schema="forge-ergo-recovery-summary/0.1",
        store_path="X:/forge/attempt_store.sqlite3",
        store_status="UNREADABLE",
        integrity_ok=False,
        integrity=(),
        journal_mode=None,
        schema_version=None,
        blob_count=None,
        attempt_count=None,
        event_count=None,
        last_event=None,
        latest_attempts=(),
        source=GitSourceSummary(
            repo_path="X:/forge/source",
            available=True,
            head="f" * 64,
            branch="forge/app-shell-rd",
            dirty=False,
            status_lines=(),
            error=None,
        ),
        normal_mode_allowed=False,
        safe_mode_available=True,
        recovery_mode_required=True,
        reasons=("attempt store unreadable",),
        observer_authority="NONE",
    )


class ErgoLaunchModelV01Tests(unittest.TestCase):
    def test_ready_model_recommends_normal_without_minting_authority(self) -> None:
        model = build_launch_model(ready_summary())
        self.assertEqual(model.posture, "READY")
        self.assertEqual(model.observer_authority, "NONE")
        modes = {mode.mode_id: mode for mode in model.modes}
        self.assertTrue(modes["normal"].enabled)
        self.assertTrue(modes["normal"].recommended)
        self.assertTrue(modes["safe"].enabled)
        self.assertTrue(modes["recovery"].enabled)
        self.assertFalse(modes["recovery"].recommended)
        self.assertEqual(model.recent_attempts[0].attempt_id, "attempt-005")

    def test_recovery_required_model_blocks_normal_and_recommends_recovery(self) -> None:
        model = build_launch_model(recovery_summary())
        self.assertEqual(model.posture, "RECOVERY_REQUIRED")
        modes = {mode.mode_id: mode for mode in model.modes}
        self.assertFalse(modes["normal"].enabled)
        self.assertTrue(modes["recovery"].enabled)
        self.assertTrue(modes["recovery"].recommended)
        self.assertEqual(model.observer_authority, "NONE")

    def test_dirty_source_is_caution_not_false_recovery(self) -> None:
        model = build_launch_model(ready_summary(dirty=True))
        self.assertEqual(model.posture, "CAUTION")
        modes = {mode.mode_id: mode for mode in model.modes}
        self.assertTrue(modes["normal"].enabled)
        self.assertTrue(modes["normal"].recommended)
        self.assertFalse(modes["recovery"].recommended)
        self.assertIn("source repository has uncommitted changes", model.reasons)

    def test_canonical_json_is_deterministic_and_complete(self) -> None:
        first = build_launch_model(ready_summary()).canonical_json()
        second = build_launch_model(ready_summary()).canonical_json()
        self.assertEqual(first, second)
        decoded = json.loads(first)
        self.assertEqual(decoded["schema"], "forge-ergo-launch-model/0.1")
        self.assertEqual(decoded["observer_authority"], "NONE")
        self.assertEqual(decoded["facts"][0]["key"], "store_status")

    def test_minimal_renderer_is_bounded_plain_text(self) -> None:
        model = build_launch_model(ready_summary())
        rendered = render_minimal_text(model, width=64)
        self.assertTrue(rendered.endswith("\n"))
        self.assertNotIn("\x1b", rendered)
        self.assertIn("ERGO // FORGE", rendered)
        self.assertIn("POSTURE  READY", rendered)
        self.assertIn("RECENT PRESERVED WORK", rendered)
        self.assertIn("Presentation does not create truth.", rendered)
        for line in rendered.splitlines():
            self.assertLessEqual(len(line), 64)

    def test_minimal_renderer_clamps_tiny_width_to_operable_floor(self) -> None:
        model = build_launch_model(recovery_summary())
        rendered = render_minimal_text(model, width=10)
        for line in rendered.splitlines():
            self.assertLessEqual(len(line), 48)
        self.assertIn("RECOVERY_REQUIRED", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
