from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from forge_app.recovery import AttemptStore
from forge_app.recovery.attempt_store import AttemptStoreError
from forge_app.recovery.resume_checkpoint import (
    ARTIFACT_CLASS,
    CHECKPOINT_SCHEMA,
    ResumeCheckpointManager,
    ResumeCheckpointPayload,
)


def payload(
    generation: int,
    *,
    parent: str | None = None,
    source_head: str | None = None,
    semantic_snapshot_id: str | None = None,
) -> ResumeCheckpointPayload:
    return ResumeCheckpointPayload(
        session_id="session-alpha",
        generation=generation,
        parent_checkpoint_id=parent,
        project_id="singularity-works-forge-app",
        workspace_id="workspace-main",
        source_branch="forge/app-shell-rd",
        source_head=source_head or f"head-{generation}",
        core_contract_version="forge-core-interface/0.1",
        core_currentness_id=f"core-current-{generation}",
        semantic_snapshot_id=semantic_snapshot_id or f"semantic-snapshot-{generation}",
        open_referents=("source:alpha",),
        selected_referents=("entity:alpha",),
        history_cursor=f"history-{generation}",
        ui_layout_id="layout-ergo-a",
        camera_state={"x": generation, "y": 0, "zoom": 1.0},
        command_cursor=f"command-{generation}",
        active_attempt_ids=(f"attempt-work-{generation}",),
        pending_transaction_ids=(),
        counterfactual_branch_id=None,
    )


class ResumeCheckpointV01Tests(unittest.TestCase):
    def new_manager(self, td: str) -> tuple[AttemptStore, ResumeCheckpointManager]:
        store = AttemptStore(Path(td) / "store")
        return store, ResumeCheckpointManager(store)

    def test_capture_is_immutable_verified_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, manager = self.new_manager(td)
            checkpoint_id = manager.capture_checkpoint(
                payload(1), checkpoint_id="checkpoint-001"
            )
            self.assertEqual(checkpoint_id, "checkpoint-001")
            view = manager.inspect(checkpoint_id)
            self.assertEqual(view.status, "VERIFIED")
            self.assertTrue(view.verified)
            self.assertFalse(view.stable)
            self.assertFalse(view.quarantined)
            self.assertEqual(view.resume_policy, "NORMAL")

            attempt = store.read_attempt(checkpoint_id)
            decoded = json.loads(attempt["payload"].decode("utf-8"))
            self.assertEqual(decoded["schema"], CHECKPOINT_SCHEMA)
            self.assertEqual(decoded["generation"], 1)
            self.assertEqual(attempt["artifact_class"], ARTIFACT_CLASS)
            events = store.events_for_attempt(checkpoint_id)
            self.assertEqual(
                [event["event_type"] for event in events],
                ["attempt_captured", "checkpoint_verified"],
            )

    def test_stability_lease_then_lkg_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager = self.new_manager(td)
            checkpoint_id = manager.capture_checkpoint(
                payload(1), checkpoint_id="checkpoint-stable"
            )
            manager.record_resume(checkpoint_id, resume_id="resume-a")
            self.assertFalse(
                manager.record_health(
                    checkpoint_id,
                    resume_id="resume-a",
                    healthy_seconds=9.9,
                    meaningful_operations=100,
                )
            )
            self.assertFalse(manager.inspect(checkpoint_id).stable)
            self.assertTrue(
                manager.record_health(
                    checkpoint_id,
                    resume_id="resume-a",
                    healthy_seconds=10.0,
                    meaningful_operations=3,
                )
            )
            self.assertEqual(manager.inspect(checkpoint_id).status, "STABLE")
            manager.promote_lkg(checkpoint_id, promotion_id="lkg-001")
            view = manager.inspect(checkpoint_id)
            self.assertTrue(view.stable)
            self.assertTrue(view.lkg)
            self.assertEqual(view.status, "LKG")
            self.assertEqual(view.resume_policy, "NORMAL")

    def test_two_distinct_early_crashes_quarantine_new_state_and_preserve_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, manager = self.new_manager(td)
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
            risky_before = store.read_attempt(risky)["payload"]
            manager.record_resume(risky, resume_id="resume-risky-1")
            first = manager.record_crash(
                risky,
                resume_id="resume-risky-1",
                crash_id="crash-001",
                seconds_since_resume=2.0,
                failure_domain="session_host",
                detail="first early crash",
            )
            self.assertEqual(first.early_crash_count, 1)
            self.assertFalse(first.quarantined)
            self.assertEqual(first.status, "CRASH_ASSOCIATED")
            self.assertEqual(first.resume_policy, "SAFE_ONLY")

            manager.record_resume(risky, resume_id="resume-risky-2")
            second = manager.record_crash(
                risky,
                resume_id="resume-risky-2",
                crash_id="crash-002",
                seconds_since_resume=1.0,
                failure_domain="session_host",
                detail="second early crash",
            )
            self.assertEqual(second.early_crash_count, 2)
            self.assertTrue(second.quarantined)
            self.assertEqual(second.status, "QUARANTINED")
            self.assertEqual(second.resume_policy, "INSPECT_ONLY")
            self.assertEqual(store.read_attempt(risky)["payload"], risky_before)

            selected = manager.choose_recovery()
            self.assertIsNotNone(selected)
            assert selected is not None
            self.assertEqual(selected.checkpoint_id, good)
            self.assertTrue(selected.lkg)

    def test_duplicate_crash_receipt_is_idempotent_not_second_crash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager = self.new_manager(td)
            checkpoint_id = manager.capture_checkpoint(
                payload(1), checkpoint_id="checkpoint-crash-idempotent"
            )
            manager.record_resume(checkpoint_id, resume_id="resume-a")
            first = manager.record_crash(
                checkpoint_id,
                resume_id="resume-a",
                crash_id="crash-same",
                seconds_since_resume=3.0,
                failure_domain="session_host",
            )
            second = manager.record_crash(
                checkpoint_id,
                resume_id="resume-a",
                crash_id="crash-same",
                seconds_since_resume=3.0,
                failure_domain="session_host",
            )
            self.assertEqual(first.early_crash_count, 1)
            self.assertEqual(second.early_crash_count, 1)
            self.assertFalse(second.quarantined)

    def test_latest_checkpoint_is_not_preferred_over_older_stable_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager = self.new_manager(td)
            older = manager.capture_checkpoint(payload(10), checkpoint_id="checkpoint-010")
            manager.record_resume(older, resume_id="resume-older")
            manager.record_health(
                older,
                resume_id="resume-older",
                healthy_seconds=20.0,
                meaningful_operations=8,
            )
            manager.promote_lkg(older, promotion_id="lkg-older")
            manager.capture_checkpoint(
                payload(11, parent=older), checkpoint_id="checkpoint-011"
            )
            selected = manager.choose_recovery()
            self.assertIsNotNone(selected)
            assert selected is not None
            self.assertEqual(selected.checkpoint_id, older)
            self.assertEqual(selected.status, "LKG")

    def test_captured_but_unverified_checkpoint_is_never_automatic_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, manager = self.new_manager(td)
            raw = payload(1).canonical_json().encode("utf-8")
            store.capture(
                raw,
                artifact_class=ARTIFACT_CLASS,
                producer="test-interrupted-checkpoint",
                intent="simulate crash after capture before verification event",
                metadata={"schema": CHECKPOINT_SCHEMA, "generation": 1},
                attempt_id="checkpoint-captured-only",
            )
            view = manager.inspect("checkpoint-captured-only")
            self.assertEqual(view.status, "CAPTURED")
            self.assertEqual(view.resume_policy, "INSPECT_ONLY")
            self.assertIsNone(manager.choose_recovery())

    def test_stale_resume_health_cannot_promote_newer_runtime_generation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager = self.new_manager(td)
            checkpoint_id = manager.capture_checkpoint(
                payload(1), checkpoint_id="checkpoint-stale-health"
            )
            manager.record_resume(checkpoint_id, resume_id="resume-generation-a")
            manager.record_resume(checkpoint_id, resume_id="resume-generation-b")
            with self.assertRaises(AttemptStoreError):
                manager.record_health(
                    checkpoint_id,
                    resume_id="resume-generation-a",
                    healthy_seconds=30.0,
                    meaningful_operations=20,
                )
            view = manager.inspect(checkpoint_id)
            self.assertFalse(view.stable)
            self.assertEqual(view.status, "VERIFIED")

    def test_crash_receipt_must_match_latest_resume_generation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager = self.new_manager(td)
            checkpoint_id = manager.capture_checkpoint(
                payload(1), checkpoint_id="checkpoint-stale-crash"
            )
            manager.record_resume(checkpoint_id, resume_id="resume-a")
            manager.record_resume(checkpoint_id, resume_id="resume-b")
            with self.assertRaises(AttemptStoreError):
                manager.record_crash(
                    checkpoint_id,
                    resume_id="resume-a",
                    crash_id="crash-stale",
                    seconds_since_resume=1.0,
                    failure_domain="session_host",
                )
            view = manager.inspect(checkpoint_id)
            self.assertEqual(view.early_crash_count, 0)
            self.assertFalse(view.quarantined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
