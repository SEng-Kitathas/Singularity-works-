from __future__ import annotations

from pathlib import Path
import hashlib
import sys
import tempfile
import unittest

from forge_app.ergo.launch_model import build_launch_model, render_minimal_text
from forge_app.ergo.recovery_summary import ErgoRecoverySummary, GitSourceSummary
from forge_app.render.persistent_host import PersistentRendererError, PersistentRendererHost


SOURCE_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_RENDERER = [sys.executable, "-m", "forge_app.render.persistent_process_renderer"]
HOSTILE_WORKER = Path(__file__).with_name("persistent_renderer_test_worker_v0_1.py")


def ready_model():
    summary = ErgoRecoverySummary(
        schema="forge-ergo-recovery-summary/0.1",
        store_path="X:/attempt_store.sqlite3",
        store_status="READY",
        integrity_ok=True,
        integrity=("ok",),
        journal_mode="wal",
        schema_version="forge-attempt-store/0.1",
        blob_count=1,
        attempt_count=1,
        event_count=1,
        last_event={"seq": 1, "event_type": "attempt_captured", "attempt_id": "attempt-one"},
        latest_attempts=(),
        source=GitSourceSummary(
            repo_path="X:/source",
            available=True,
            head="a" * 64,
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
    return build_launch_model(summary)


class PersistentRendererHostV01Tests(unittest.TestCase):
    def test_handshake_and_heartbeat_bind_generation(self) -> None:
        host = PersistentRendererHost(REFERENCE_RENDERER, timeout_seconds=2.0)
        try:
            first = host.heartbeat()
            second = host.heartbeat()
            self.assertEqual(first.generation_id, second.generation_id)
            self.assertEqual(first.heartbeat_seq, 1)
            self.assertEqual(second.heartbeat_seq, 2)
            self.assertEqual(first.renderer_id, "forge-persistent-minimal/0.1")
            self.assertEqual(first.authority, "NONE")
        finally:
            host.close()

    def test_persistent_frame_matches_minimal_reference_exactly(self) -> None:
        model = ready_model()
        host = PersistentRendererHost(REFERENCE_RENDERER, timeout_seconds=2.0, fallback_width=72)
        try:
            receipt = host.render_frame(model, tier="minimal", width=72)
            self.assertFalse(receipt.renderer_failed)
            self.assertFalse(receipt.fallback_used)
            self.assertEqual(receipt.payload, render_minimal_text(model, width=72))
            self.assertEqual(receipt.renderer_id, "forge-persistent-minimal/0.1")
            self.assertEqual(receipt.frame_seq, 1)
            expected = hashlib.sha256(model.canonical_json().encode("utf-8")).hexdigest()
            self.assertEqual(receipt.model_sha256, expected)
            self.assertEqual(receipt.authority, "NONE")
        finally:
            host.close()

    def test_first_generation_crash_falls_back_then_next_frame_restarts_new_generation(self) -> None:
        model = ready_model()
        with tempfile.TemporaryDirectory() as td:
            sentinel = Path(td) / "crashed-once.txt"
            command = [
                sys.executable,
                str(HOSTILE_WORKER),
                "--crash-first-frame-sentinel",
                str(sentinel),
            ]
            host = PersistentRendererHost(command, timeout_seconds=2.0, fallback_width=72)
            try:
                first = host.render_frame(model, tier="accelerated", width=72)
                self.assertTrue(first.renderer_failed)
                self.assertTrue(first.fallback_used)
                self.assertEqual(first.payload, render_minimal_text(model, width=72))
                first_generation = first.generation_id

                second = host.render_frame(model, tier="accelerated", width=72)
                self.assertFalse(second.renderer_failed)
                self.assertFalse(second.fallback_used)
                self.assertEqual(second.payload, "HOSTILE-TEST-RENDERED\n")
                self.assertNotEqual(second.generation_id, first_generation)
                self.assertEqual(second.frame_seq, 2)
            finally:
                host.close()

    def test_wrong_generation_handshake_is_rejected_to_fallback(self) -> None:
        model = ready_model()
        command = [sys.executable, str(HOSTILE_WORKER), "--wrong-generation"]
        host = PersistentRendererHost(command, timeout_seconds=2.0, fallback_width=72)
        try:
            receipt = host.render_frame(model, tier="test", width=72)
            self.assertTrue(receipt.renderer_failed)
            self.assertTrue(receipt.fallback_used)
            self.assertIn("generation mismatch", receipt.failure_reason or "")
            self.assertEqual(receipt.payload, render_minimal_text(model, width=72))
            self.assertIsNone(host.generation_id)
        finally:
            host.close()

    def test_frame_sequence_is_monotonic_across_renderer_restart(self) -> None:
        model = ready_model()
        with tempfile.TemporaryDirectory() as td:
            sentinel = Path(td) / "crash.txt"
            host = PersistentRendererHost(
                [sys.executable, str(HOSTILE_WORKER), "--crash-first-frame-sentinel", str(sentinel)],
                timeout_seconds=2.0,
            )
            try:
                receipts = [host.render_frame(model) for _ in range(3)]
                self.assertEqual([r.frame_seq for r in receipts], [1, 2, 3])
                self.assertTrue(receipts[0].fallback_used)
                self.assertFalse(receipts[1].fallback_used)
                self.assertFalse(receipts[2].fallback_used)
                self.assertEqual(receipts[1].generation_id, receipts[2].generation_id)
                self.assertNotEqual(receipts[0].generation_id, receipts[1].generation_id)
            finally:
                host.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
