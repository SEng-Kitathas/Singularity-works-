from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

from forge_app.ergo.launch_model import build_launch_model, render_minimal_text
from forge_app.ergo.recovery_summary import ErgoRecoverySummary, GitSourceSummary
from forge_app.recovery import AttemptStore
from forge_app.render import render_snapshot_with_fallback


SOURCE_ROOT = Path(__file__).resolve().parents[2]
MINIMAL_RENDERER = [sys.executable, "-m", "forge_app.render.minimal_process_renderer"]
CRASH_RENDERER = [sys.executable, str(Path(__file__).with_name("renderer_crash_worker_v0_1.py"))]


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
        latest_attempts=(
            {
                "attempt_id": "attempt-one",
                "blob_sha256": "a" * 64,
                "parent_attempt_id": None,
                "artifact_class": "design.test",
                "producer": "renderer-protocol-test",
                "intent": "renderer crash-domain discriminator",
                "metadata": {},
                "created_at": "2026-09-03T00:00:00Z",
            },
        ),
        source=GitSourceSummary(
            repo_path="X:/source",
            available=True,
            head="b" * 64,
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


class RendererProcessProtocolV01Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_pythonpath = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = str(SOURCE_ROOT) + os.pathsep + (self.old_pythonpath or "")

    def tearDown(self) -> None:
        if self.old_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = self.old_pythonpath

    def test_out_of_process_minimal_renderer_matches_reference_exactly(self) -> None:
        model = ready_model()
        receipt = render_snapshot_with_fallback(
            model,
            renderer_command=MINIMAL_RENDERER,
            tier="minimal",
            width=72,
        )
        self.assertFalse(receipt.renderer_failed)
        self.assertFalse(receipt.fallback_used)
        self.assertEqual(receipt.authority, "NONE")
        self.assertEqual(receipt.renderer_id, "forge-minimal-process/0.1")
        self.assertEqual(receipt.payload, render_minimal_text(model, width=72))
        expected_hash = hashlib.sha256(model.canonical_json().encode("utf-8")).hexdigest()
        self.assertEqual(receipt.model_sha256, expected_hash)

    def test_renderer_process_death_falls_back_to_same_model(self) -> None:
        model = ready_model()
        receipt = render_snapshot_with_fallback(
            model,
            renderer_command=CRASH_RENDERER,
            tier="accelerated",
            width=72,
        )
        self.assertTrue(receipt.renderer_failed)
        self.assertTrue(receipt.fallback_used)
        self.assertEqual(receipt.authority, "NONE")
        self.assertEqual(receipt.renderer_id, "forge-minimal-inprocess/0.1")
        self.assertIn("renderer exited 93", receipt.failure_reason or "")
        self.assertEqual(receipt.payload, render_minimal_text(model, width=72))

    def test_renderer_death_does_not_mutate_durable_store(self) -> None:
        model = ready_model()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            store = AttemptStore(root)
            store.capture(
                b"durable-before-renderer-crash\n",
                artifact_class="renderer.crash_guard",
                producer="renderer-protocol-test",
                intent="prove renderer crash does not mutate durable state",
                attempt_id="attempt-renderer-guard",
            )
            db = root / "attempt_store.sqlite3"
            before_bytes = db.read_bytes()
            before_mtime = db.stat().st_mtime_ns
            before_summary = store.integrity_summary()

            receipt = render_snapshot_with_fallback(
                model,
                renderer_command=CRASH_RENDERER,
                tier="accelerated",
                width=72,
            )
            self.assertTrue(receipt.fallback_used)

            after_bytes = db.read_bytes()
            after_mtime = db.stat().st_mtime_ns
            reopened = AttemptStore(root)
            after_summary = reopened.integrity_summary()
            self.assertEqual(before_bytes, after_bytes)
            self.assertEqual(before_mtime, after_mtime)
            self.assertEqual(before_summary["counts"], after_summary["counts"])
            self.assertTrue(after_summary["integrity_ok"])
            self.assertEqual(
                reopened.read_attempt("attempt-renderer-guard")["payload"],
                b"durable-before-renderer-crash\n",
            )

    def test_malformed_renderer_response_is_rejected_and_falls_back(self) -> None:
        model = ready_model()
        command = [
            sys.executable,
            "-c",
            "import sys; sys.stdin.read(); sys.stdout.write('not-json')",
        ]
        receipt = render_snapshot_with_fallback(model, renderer_command=command, tier="test", width=72)
        self.assertTrue(receipt.renderer_failed)
        self.assertTrue(receipt.fallback_used)
        self.assertIn("response rejected", receipt.failure_reason or "")
        self.assertEqual(receipt.payload, render_minimal_text(model, width=72))

    def test_wrong_model_hash_response_is_rejected(self) -> None:
        model = ready_model()
        script = (
            "import json,sys; r=json.loads(sys.stdin.read()); "
            "o={'protocol':'forge-render-response/0.1','request_id':r['request_id'],"
            "'model_sha256':'0'*64,'renderer_id':'liar','tier':'test',"
            "'payload_kind':'text/plain','payload':'fake'}; "
            "sys.stdout.write(json.dumps(o))"
        )
        receipt = render_snapshot_with_fallback(
            model,
            renderer_command=[sys.executable, "-c", script],
            tier="test",
            width=72,
        )
        self.assertTrue(receipt.renderer_failed)
        self.assertTrue(receipt.fallback_used)
        self.assertIn("model_sha256 mismatch", receipt.failure_reason or "")
        self.assertEqual(receipt.payload, render_minimal_text(model, width=72))


if __name__ == "__main__":
    unittest.main(verbosity=2)
