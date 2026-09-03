from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
import unittest

from forge_app.recovery import AttemptStore
from forge_app.recovery.attempt_store import AttemptStoreError
from forge_app.recovery.resume_checkpoint import ResumeCheckpointManager, ResumeCheckpointPayload
from forge_app.recovery.session_health import SessionHealthLease


@dataclass
class FakeClock:
    now: float = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def checkpoint_payload(generation: int, *, parent: str | None = None) -> ResumeCheckpointPayload:
    return ResumeCheckpointPayload(
        session_id="session-health",
        generation=generation,
        parent_checkpoint_id=parent,
        project_id="singularity-works-forge-app",
        workspace_id="workspace-main",
        source_branch="forge/app-shell-rd",
        source_head=f"head-{generation}",
        core_contract_version="forge-core-interface/0.1",
        core_currentness_id=f"core-current-{generation}",
        semantic_snapshot_id=f"semantic-snapshot-{generation}",
    )


class SessionHealthV01Tests(unittest.TestCase):
    def new_env(self, td: str):
        store = AttemptStore(Path(td) / "store")
        manager = ResumeCheckpointManager(store)
        clock = FakeClock()
        return store, manager, clock

    def test_runtime_health_plus_meaningful_operations_promotes_stable_then_lkg(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager, clock = self.new_env(td)
            checkpoint_id = manager.capture_checkpoint(
                checkpoint_payload(1), checkpoint_id="checkpoint-health"
            )
            lease = SessionHealthLease.begin(
                manager,
                checkpoint_id,
                resume_id="resume-health",
                clock=clock,
            )
            self.assertFalse(lease.note_meaningful_operation())
            self.assertFalse(lease.note_meaningful_operation())
            self.assertFalse(lease.note_meaningful_operation())
            self.assertFalse(manager.inspect(checkpoint_id).stable)
            clock.advance(10.0)
            self.assertTrue(lease.heartbeat())
            self.assertTrue(manager.inspect(checkpoint_id).stable)
            view = lease.promote_lkg(promotion_id="lkg-health")
            self.assertTrue(view.lkg)
            self.assertEqual(view.status, "LKG")

    def test_renderer_heartbeats_alone_cannot_promote_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager, clock = self.new_env(td)
            checkpoint_id = manager.capture_checkpoint(
                checkpoint_payload(1), checkpoint_id="checkpoint-no-ops"
            )
            lease = SessionHealthLease.begin(
                manager,
                checkpoint_id,
                resume_id="resume-no-ops",
                clock=clock,
            )
            for _ in range(5):
                clock.advance(5.0)
                self.assertFalse(lease.heartbeat())
            view = manager.inspect(checkpoint_id)
            self.assertFalse(view.stable)
            self.assertEqual(view.status, "VERIFIED")

    def test_early_session_crash_associates_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager, clock = self.new_env(td)
            checkpoint_id = manager.capture_checkpoint(
                checkpoint_payload(1), checkpoint_id="checkpoint-early-crash"
            )
            lease = SessionHealthLease.begin(
                manager,
                checkpoint_id,
                resume_id="resume-early-crash",
                clock=clock,
            )
            clock.advance(4.0)
            view = lease.record_session_crash(
                crash_id="session-crash-001",
                failure_domain="session_host",
                detail="deliberate early session crash",
            )
            self.assertEqual(view.status, "CRASH_ASSOCIATED")
            self.assertEqual(view.early_crash_count, 1)
            self.assertFalse(view.quarantined)

    def test_two_early_session_crashes_quarantine_latest_and_recovery_selects_older_lkg(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager, clock = self.new_env(td)
            older = manager.capture_checkpoint(
                checkpoint_payload(1), checkpoint_id="checkpoint-older"
            )
            old_lease = SessionHealthLease.begin(
                manager, older, resume_id="resume-older", clock=clock
            )
            old_lease.note_meaningful_operation(3)
            clock.advance(10.0)
            self.assertTrue(old_lease.heartbeat())
            old_lease.promote_lkg(promotion_id="lkg-older")

            risky = manager.capture_checkpoint(
                checkpoint_payload(2, parent=older), checkpoint_id="checkpoint-risky"
            )
            first = SessionHealthLease.begin(
                manager, risky, resume_id="resume-risky-a", clock=clock
            )
            clock.advance(2.0)
            first.record_session_crash(
                crash_id="session-crash-a", failure_domain="session_host"
            )

            second = SessionHealthLease.begin(
                manager, risky, resume_id="resume-risky-b", clock=clock
            )
            clock.advance(1.0)
            view = second.record_session_crash(
                crash_id="session-crash-b", failure_domain="session_host"
            )
            self.assertTrue(view.quarantined)
            self.assertEqual(view.status, "QUARANTINED")

            selected = manager.choose_recovery()
            self.assertIsNotNone(selected)
            assert selected is not None
            self.assertEqual(selected.checkpoint_id, older)
            self.assertTrue(selected.lkg)

    def test_stale_session_lease_cannot_promote_after_new_resume_generation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, manager, clock = self.new_env(td)
            checkpoint_id = manager.capture_checkpoint(
                checkpoint_payload(1), checkpoint_id="checkpoint-stale-lease"
            )
            stale = SessionHealthLease.begin(
                manager, checkpoint_id, resume_id="resume-a", clock=clock
            )
            stale.note_meaningful_operation(3)
            SessionHealthLease.begin(
                manager, checkpoint_id, resume_id="resume-b", clock=clock
            )
            clock.advance(20.0)
            with self.assertRaises(AttemptStoreError):
                stale.heartbeat()
            self.assertFalse(manager.inspect(checkpoint_id).stable)


if __name__ == "__main__":
    unittest.main(verbosity=2)
