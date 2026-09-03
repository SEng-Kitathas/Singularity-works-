from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from forge_app.ergo.reentry_cli import render_checkpoint_list_text, render_popup_text
from forge_app.recovery import AttemptStore, ResumeCheckpointManager, ResumeCheckpointPayload
from forge_app.recovery.reentry import CheckpointReentryService, ReentryPreparationError


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def init_repo(root: Path) -> tuple[Path, str, str]:
    repo = root / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
    git(repo, "config", "user.email", "forge-reentry@test.invalid")
    git(repo, "config", "user.name", "Forge Reentry Test")
    (repo / "work.txt").write_text("generation one\n", encoding="utf-8")
    git(repo, "add", "work.txt")
    git(repo, "commit", "-m", "generation one")
    head1 = git(repo, "rev-parse", "HEAD")
    (repo / "work.txt").write_text("generation two\n", encoding="utf-8")
    git(repo, "add", "work.txt")
    git(repo, "commit", "-m", "generation two")
    head2 = git(repo, "rev-parse", "HEAD")
    return repo, head1, head2


def payload(
    generation: int,
    *,
    source_head: str | None,
    parent: str | None = None,
    active_attempt_ids: tuple[str, ...] = (),
) -> ResumeCheckpointPayload:
    return ResumeCheckpointPayload(
        session_id="reentry-test",
        generation=generation,
        parent_checkpoint_id=parent,
        project_id="singularity-works-forge-app",
        workspace_id="workspace-reentry-test",
        source_branch="test",
        source_head=source_head,
        core_contract_version=None,
        core_currentness_id=None,
        semantic_snapshot_id=None,
        open_referents=("source:work.txt", "entity:test"),
        selected_referents=("entity:test",),
        history_cursor=f"history-{generation}",
        ui_layout_id="layout-test",
        camera_state={"x": generation, "y": 2, "zoom": 1.25},
        command_cursor=f"command-{generation}",
        active_attempt_ids=active_attempt_ids,
        pending_transaction_ids=(f"txn-{generation}",),
        counterfactual_branch_id=f"counterfactual-{generation}",
    )


class CheckpointReentryV01Tests(unittest.TestCase):
    def env(self, td: str):
        root = Path(td)
        repo, head1, head2 = init_repo(root)
        store = AttemptStore(root / "store")
        work = store.capture(
            b"exact preserved AI/operator work\n",
            artifact_class="work.test",
            producer="checkpoint-reentry-test",
            intent="preserved work referenced by checkpoint",
            attempt_id="attempt-work-one",
        )
        manager = ResumeCheckpointManager(store)
        service = CheckpointReentryService(
            manager,
            reentry_root=root / "reentry",
            source_repo=repo,
        )
        return root, repo, head1, head2, store, manager, service, work

    def make_lkg(self, manager: ResumeCheckpointManager, checkpoint_id: str) -> None:
        manager.record_resume(checkpoint_id, resume_id=f"resume-{checkpoint_id}")
        manager.record_health(
            checkpoint_id,
            resume_id=f"resume-{checkpoint_id}",
            healthy_seconds=20.0,
            meaningful_operations=5,
        )
        manager.promote_lkg(checkpoint_id, promotion_id=f"lkg-{checkpoint_id}")

    def test_manual_reentry_from_old_checkpoint_materializes_exact_detached_source_and_work_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root, repo, head1, head2, store, manager, service, work = self.env(td)
            checkpoint_id = manager.capture_checkpoint(
                payload(
                    1,
                    source_head=head1,
                    active_attempt_ids=(work.attempt_id,),
                ),
                checkpoint_id="checkpoint-old",
            )
            self.make_lkg(manager, checkpoint_id)
            active_before = (git(repo, "rev-parse", "HEAD"), git(repo, "status", "--porcelain"))

            point = service.prepare_manual_reentry(
                checkpoint_id, reentry_id="manual-old-checkpoint"
            )

            self.assertEqual(point.trigger, "manual")
            self.assertEqual(point.checkpoint_id, checkpoint_id)
            self.assertEqual(point.source_isolation_status, "EXACT_DETACHED_WORKTREE")
            self.assertEqual(point.source_currentness, "MISMATCH")
            self.assertIsNotNone(point.source_dir)
            assert point.source_dir is not None
            isolated = Path(point.source_dir)
            self.assertEqual(git(isolated, "rev-parse", "HEAD"), head1)
            self.assertEqual((isolated / "work.txt").read_text(encoding="utf-8"), "generation one\n")
            self.assertEqual((git(repo, "rev-parse", "HEAD"), git(repo, "status", "--porcelain")), active_before)
            self.assertEqual(active_before[0], head2)

            saved_payload = json.loads(Path(point.checkpoint_payload_path).read_text(encoding="utf-8"))
            self.assertEqual(saved_payload["camera_state"], {"x": 1, "y": 2, "zoom": 1.25})
            self.assertEqual(saved_payload["pending_transaction_ids"], ["txn-1"])
            attempt_index = json.loads(Path(point.attempt_index_path).read_text(encoding="utf-8"))
            self.assertTrue(attempt_index["active_attempts"][0]["found"])
            self.assertEqual(attempt_index["active_attempts"][0]["blob_sha256"], work.blob_sha256)

            self.assertEqual(point.popup.severity, "MANUAL_REENTRY")
            actions = {a.action_id: a for a in point.popup.actions}
            self.assertTrue(actions["open_isolated_reentry"].enabled)
            self.assertTrue(actions["compare_to_current"].enabled)
            self.assertIn("Manual checkpoint re-entry prepared", render_popup_text(point.popup))

            events = [e for e in store.events_for_attempt(checkpoint_id) if e["event_type"] == "checkpoint_reentry_prepared"]
            self.assertEqual(len(events), 1)
            manifest_attempt = store.read_attempt(point.manifest_attempt_id)
            self.assertEqual(manifest_attempt["parent_attempt_id"], checkpoint_id)

    def test_quarantine_automatically_prepares_isolated_reentry_and_keeps_older_lkg(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root, repo, head1, head2, store, manager, service, _ = self.env(td)
            good = manager.capture_checkpoint(
                payload(1, source_head=head1), checkpoint_id="checkpoint-good"
            )
            self.make_lkg(manager, good)
            risky = manager.capture_checkpoint(
                payload(2, source_head=head2, parent=good), checkpoint_id="checkpoint-risky"
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
            view = manager.record_crash(
                risky,
                resume_id="resume-risky-b",
                crash_id="crash-b",
                seconds_since_resume=1.0,
                failure_domain="session_host",
            )
            self.assertTrue(view.quarantined)
            self.assertEqual(view.status, "QUARANTINED")

            auto = service.prepare_quarantined_reentry(risky)
            self.assertEqual(auto.trigger, "quarantine_auto")
            self.assertEqual(auto.popup.severity, "RECOVERY_ISOLATED")
            self.assertEqual(auto.source_isolation_status, "EXACT_DETACHED_WORKTREE")
            self.assertTrue(Path(auto.manifest_path).exists())
            self.assertTrue(Path(auto.popup_path).exists())
            self.assertTrue(manager.inspect(risky).quarantined)

            preferred = manager.choose_recovery()
            self.assertIsNotNone(preferred)
            assert preferred is not None
            self.assertEqual(preferred.checkpoint_id, good)
            actions = {a.action_id: a for a in auto.popup.actions}
            self.assertTrue(actions["return_to_lkg"].enabled)
            self.assertIn(good, actions["return_to_lkg"].reason)

            auto_events = [
                e
                for e in store.events_for_attempt(risky)
                if e["event_type"] == "checkpoint_reentry_prepared"
                and e["payload"]["trigger"] == "quarantine_auto"
            ]
            self.assertEqual(len(auto_events), 1)

    def test_manual_path_remains_available_for_quarantined_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, _, _, head2, _, manager, service, _ = self.env(td)
            risky = manager.capture_checkpoint(
                payload(2, source_head=head2), checkpoint_id="checkpoint-manual-quarantine"
            )
            manager.record_resume(risky, resume_id="resume-a")
            manager.record_crash(
                risky,
                resume_id="resume-a",
                crash_id="crash-a",
                seconds_since_resume=1.0,
                failure_domain="session_host",
            )
            manager.record_resume(risky, resume_id="resume-b")
            manager.record_crash(
                risky,
                resume_id="resume-b",
                crash_id="crash-b",
                seconds_since_resume=1.0,
                failure_domain="session_host",
            )
            manual = service.prepare_manual_reentry(
                risky, reentry_id="manual-quarantined-inspection"
            )
            self.assertEqual(manual.trigger, "manual")
            self.assertTrue(manual.checkpoint_quarantined)
            self.assertEqual(manual.checkpoint_status, "QUARANTINED")
            self.assertTrue(manager.inspect(risky).quarantined)
            self.assertNotEqual(
                manual.reentry_id,
                service.prepare_quarantined_reentry(risky).reentry_id,
            )

    def test_quarantine_commit_then_manifest_seal_failure_is_repaired_by_duplicate_crash_replay(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root, _, _, head2, store, manager, service, _ = self.env(td)
            risky = manager.capture_checkpoint(
                payload(2, source_head=head2), checkpoint_id="checkpoint-repair-auto"
            )
            manager.record_resume(risky, resume_id="resume-a")
            manager.record_crash(
                risky,
                resume_id="resume-a",
                crash_id="crash-a",
                seconds_since_resume=1.0,
                failure_domain="session_host",
            )
            manager.record_resume(risky, resume_id="resume-b")

            original_capture = store.capture
            injected = {"done": False}

            def failing_capture(*args, **kwargs):
                if kwargs.get("artifact_class") == "recovery.checkpoint_reentry_manifest" and not injected["done"]:
                    injected["done"] = True
                    raise RuntimeError("injected manifest receipt loss")
                return original_capture(*args, **kwargs)

            store.capture = failing_capture  # type: ignore[method-assign]
            try:
                with self.assertRaisesRegex(RuntimeError, "injected manifest receipt loss"):
                    manager.record_crash(
                        risky,
                        resume_id="resume-b",
                        crash_id="crash-b",
                        seconds_since_resume=1.0,
                        failure_domain="session_host",
                    )
            finally:
                store.capture = original_capture  # type: ignore[method-assign]

            self.assertTrue(manager.inspect(risky).quarantined)
            auto_dir = root / "reentry" / "reentry-quarantine-checkpoint-repair-auto"
            self.assertTrue((auto_dir / "reentry_manifest.json").exists())

            replay = manager.record_crash(
                risky,
                resume_id="resume-b",
                crash_id="crash-b",
                seconds_since_resume=1.0,
                failure_domain="session_host",
            )
            self.assertTrue(replay.quarantined)
            point = service.prepare_quarantined_reentry(risky)
            store.read_attempt(point.manifest_attempt_id)
            events = [
                e
                for e in store.events_for_attempt(risky)
                if e["event_type"] == "checkpoint_reentry_prepared"
            ]
            self.assertEqual(len(events), 1)

    def test_same_reentry_id_cannot_be_reused_for_different_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, _, head1, head2, _, manager, service, _ = self.env(td)
            first = manager.capture_checkpoint(
                payload(1, source_head=head1), checkpoint_id="checkpoint-first"
            )
            second = manager.capture_checkpoint(
                payload(2, source_head=head2), checkpoint_id="checkpoint-second"
            )
            service.prepare_manual_reentry(first, reentry_id="shared-reentry-id")
            with self.assertRaisesRegex(ReentryPreparationError, "conflicts on checkpoint_id"):
                service.prepare_manual_reentry(second, reentry_id="shared-reentry-id")

    def test_manual_reentry_without_source_repo_still_materializes_state_and_popup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = AttemptStore(root / "store")
            manager = ResumeCheckpointManager(store)
            service = CheckpointReentryService(manager, reentry_root=root / "reentry")
            checkpoint_id = manager.capture_checkpoint(
                payload(1, source_head="f" * 40), checkpoint_id="checkpoint-state-only"
            )
            point = service.prepare_manual_reentry(
                checkpoint_id, reentry_id="manual-state-only"
            )
            self.assertEqual(point.source_isolation_status, "SOURCE_REPO_UNAVAILABLE")
            self.assertIsNone(point.source_dir)
            self.assertTrue(Path(point.checkpoint_payload_path).exists())
            actions = {a.action_id: a for a in point.popup.actions}
            self.assertTrue(actions["open_isolated_reentry"].enabled)
            self.assertIn("state-only", actions["open_isolated_reentry"].reason)

    def test_manual_checkpoint_browser_lists_every_checkpoint_and_marks_preferred(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            _, _, head1, head2, _, manager, service, _ = self.env(td)
            good = manager.capture_checkpoint(
                payload(1, source_head=head1), checkpoint_id="checkpoint-browser-good"
            )
            self.make_lkg(manager, good)
            risky = manager.capture_checkpoint(
                payload(2, source_head=head2, parent=good), checkpoint_id="checkpoint-browser-risky"
            )
            manager.record_resume(risky, resume_id="resume-browser-a")
            manager.record_crash(
                risky,
                resume_id="resume-browser-a",
                crash_id="crash-browser-a",
                seconds_since_resume=1.0,
                failure_domain="session_host",
            )
            manager.record_resume(risky, resume_id="resume-browser-b")
            manager.record_crash(
                risky,
                resume_id="resume-browser-b",
                crash_id="crash-browser-b",
                seconds_since_resume=1.0,
                failure_domain="session_host",
            )
            rendered = render_checkpoint_list_text(manager)
            self.assertIn("Manual isolated re-entry is available from every listed checkpoint.", rendered)
            self.assertIn("checkpoint-browser-good", rendered)
            self.assertIn("checkpoint-browser-risky", rendered)
            self.assertIn("QUARANTINED", rendered)
            preferred_line = next(line for line in rendered.splitlines() if "checkpoint-browser-good" in line)
            self.assertTrue(preferred_line.startswith(">"))



if __name__ == "__main__":
    unittest.main(verbosity=2)
