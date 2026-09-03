from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forge_app.recovery import AttemptStore, CheckpointReentryService
from forge_app.recovery.resume_checkpoint import ResumeCheckpointManager, ResumeCheckpointPayload
from forge_app.recovery.session_supervisor import SessionProcessSupervisor, SessionSupervisorError


SOURCE_ROOT = Path(__file__).resolve().parents[2]


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return r.stdout.strip()


def init_repo(root: Path) -> tuple[Path, str]:
    repo = root / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
    git(repo, "config", "user.email", "session-supervisor@test.invalid")
    git(repo, "config", "user.name", "Session Supervisor Test")
    (repo / "work.txt").write_text("stable source\n", encoding="utf-8")
    git(repo, "add", "work.txt")
    git(repo, "commit", "-m", "stable")
    return repo, git(repo, "rev-parse", "HEAD")


def payload(generation: int, source_head: str, *, parent: str | None = None) -> ResumeCheckpointPayload:
    return ResumeCheckpointPayload(
        session_id="supervisor-test",
        generation=generation,
        parent_checkpoint_id=parent,
        project_id="singularity-works-forge-app",
        workspace_id="workspace-supervisor",
        source_branch="test",
        source_head=source_head,
        core_contract_version=None,
        core_currentness_id=None,
        semantic_snapshot_id=None,
        open_referents=("source:work.txt",),
        selected_referents=("entity:work",),
        history_cursor=f"history-{generation}",
        ui_layout_id="layout-test",
        camera_state=None,
        command_cursor=f"command-{generation}",
        active_attempt_ids=(),
        pending_transaction_ids=(),
        counterfactual_branch_id=None,
    )


def worker_command(checkpoint: str, resume: str, ready: Path, *extra: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "forge_app.embodiment.session_coordinator_worker_v0_1",
        "--checkpoint",
        checkpoint,
        "--resume",
        resume,
        "--ready",
        str(ready),
        "--sleep-seconds",
        "60",
        *extra,
    ]


class SessionProcessSupervisorV01Tests(unittest.TestCase):
    def env(self, td: str):
        root = Path(td)
        repo, head = init_repo(root)
        store = AttemptStore(root / "store")
        manager = ResumeCheckpointManager(store)
        reentry = CheckpointReentryService(manager, reentry_root=root / "reentry", source_repo=repo)
        good = manager.capture_checkpoint(payload(1, head), checkpoint_id="checkpoint-good")
        manager.record_resume(good, resume_id="resume-good")
        manager.record_health(good, resume_id="resume-good", healthy_seconds=20, meaningful_operations=5)
        manager.promote_lkg(good, promotion_id="lkg-good")
        risky = manager.capture_checkpoint(payload(2, head, parent=good), checkpoint_id="checkpoint-risky")
        return root, repo, head, store, manager, reentry, good, risky

    def supervisor(self, root: Path, manager: ResumeCheckpointManager, checkpoint: str, resume: str, *extra: str):
        ready = root / "ready" / f"{resume}.json"
        return SessionProcessSupervisor(
            manager,
            checkpoint_id=checkpoint,
            resume_id=resume,
            command=worker_command(checkpoint, resume, ready, *extra),
            ready_path=ready,
            cwd=SOURCE_ROOT,
        )

    def test_external_kill_is_observed_by_supervisor_and_duplicate_observation_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root, _, _, store, manager, _, _, risky = self.env(td)
            sup = self.supervisor(root, manager, risky, "resume-kill-a")
            try:
                sup.start()
                ready = sup.wait_ready()
                self.assertEqual(ready.resume_id, "resume-kill-a")
                receipt, view = sup.kill_and_record()
                self.assertFalse(receipt.expected)
                self.assertEqual(view.early_crash_count, 1)
                self.assertFalse(view.quarantined)
                before = len([e for e in store.events_for_attempt(risky) if e["event_type"] == "checkpoint_crash_associated"])
                receipt2, view2 = sup.record_unexpected_exit()
                after = len([e for e in store.events_for_attempt(risky) if e["event_type"] == "checkpoint_crash_associated"])
                self.assertEqual(receipt.crash_id, receipt2.crash_id)
                self.assertEqual(before, after)
                self.assertEqual(view2.early_crash_count, 1)
            finally:
                sup.close()

    def test_two_distinct_externally_killed_resumes_quarantine_and_auto_prepare_reentry_while_lkg_survives(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root, repo, head, _, manager, reentry, good, risky = self.env(td)
            active_before = (git(repo, "rev-parse", "HEAD"), git(repo, "status", "--porcelain"))
            for resume in ("resume-kill-a", "resume-kill-b"):
                sup = self.supervisor(root, manager, risky, resume)
                try:
                    sup.start()
                    sup.wait_ready()
                    _, view = sup.kill_and_record()
                finally:
                    sup.close()
            self.assertTrue(view.quarantined)
            self.assertEqual(view.status, "QUARANTINED")
            auto = reentry.prepare_quarantined_reentry(risky)
            self.assertEqual(auto.trigger, "quarantine_auto")
            self.assertEqual(auto.source_isolation_status, "EXACT_DETACHED_WORKTREE")
            self.assertEqual(git(Path(auto.source_dir), "rev-parse", "HEAD"), head)
            preferred = manager.choose_recovery()
            self.assertIsNotNone(preferred)
            self.assertEqual(preferred.checkpoint_id, good)
            self.assertEqual((git(repo, "rev-parse", "HEAD"), git(repo, "status", "--porcelain")), active_before)

    def test_expected_shutdown_does_not_create_crash_reputation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root, _, _, store, manager, _, _, risky = self.env(td)
            sup = self.supervisor(root, manager, risky, "resume-expected")
            try:
                sup.start()
                sup.wait_ready()
                receipt = sup.terminate_expected()
                self.assertTrue(receipt.expected)
            finally:
                sup.close()
            events = [e for e in store.events_for_attempt(risky) if e["event_type"] == "checkpoint_crash_associated"]
            self.assertEqual(events, [])
            self.assertEqual(manager.inspect(risky).early_crash_count, 0)

    def test_wrong_ready_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root, _, _, _, manager, _, _, risky = self.env(td)
            sup = self.supervisor(root, manager, risky, "resume-ready", "--ready-resume", "stale-resume")
            try:
                sup.start()
                with self.assertRaisesRegex(SessionSupervisorError, "ready identity mismatch"):
                    sup.wait_ready()
            finally:
                sup.close()

    def test_resume_id_cannot_be_reused_as_second_process_slot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root, _, _, _, manager, _, _, risky = self.env(td)
            sup = self.supervisor(root, manager, risky, "resume-once")
            try:
                sup.start()
                sup.wait_ready()
                sup.terminate_expected()
            finally:
                sup.close()
            second = self.supervisor(root, manager, risky, "resume-once")
            with self.assertRaisesRegex(SessionSupervisorError, "resume_id already used"):
                second.start()


if __name__ == "__main__":
    unittest.main(verbosity=2)
