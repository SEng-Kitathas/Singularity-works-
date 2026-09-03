from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from forge_app.recovery import AttemptStore
from forge_app.recovery.attempt_store import AttemptStoreError


SOURCE_ROOT = Path(__file__).resolve().parents[2]
WORKER = Path(__file__).with_name("attempt_store_hardkill_worker.py")
HARDKILL_PAYLOAD = b"ATTEMPT-0-HARD-KILL-PAYLOAD\n"


class AttemptStoreV01Tests(unittest.TestCase):
    def new_store(self, root: Path) -> AttemptStore:
        return AttemptStore(root / "store")

    def run_worker(self, store_root: Path, *, attempt_id: str, phase: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SOURCE_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [
                sys.executable,
                str(WORKER),
                "--store",
                str(store_root),
                "--attempt-id",
                attempt_id,
                "--kill-phase",
                phase,
            ],
            cwd=str(SOURCE_ROOT),
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )

    def test_capture_deduplicates_bytes_but_preserves_attempt_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = self.new_store(Path(td))
            root = store.capture(
                b"alpha\n",
                artifact_class="design.attempt",
                producer="test",
                intent="first attempt",
                attempt_id="attempt-root",
                metadata={"ordinal": 0},
            )
            child = store.capture(
                b"alpha\n",
                artifact_class="design.attempt",
                producer="test",
                intent="retry with identical bytes",
                parent_attempt_id=root.attempt_id,
                attempt_id="attempt-child",
                metadata={"ordinal": 1},
            )
            self.assertTrue(root.verified_readback)
            self.assertTrue(child.verified_readback)
            self.assertEqual(root.blob_sha256, child.blob_sha256)
            self.assertEqual(store.lineage(child.attempt_id), ["attempt-child", "attempt-root"])
            self.assertEqual(store.read_attempt("attempt-root")["payload"], b"alpha\n")
            summary = store.integrity_summary()
            self.assertTrue(summary["integrity_ok"])
            self.assertEqual(summary["journal_mode"], "wal")
            self.assertEqual(summary["synchronous"], 2)  # SQLite FULL
            self.assertEqual(summary["counts"], {"blobs": 1, "attempts": 2, "events": 2})

    def test_unknown_parent_rolls_back_capture(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = self.new_store(Path(td))
            with self.assertRaises(AttemptStoreError):
                store.capture(
                    b"orphan retry",
                    artifact_class="code.attempt",
                    producer="test",
                    intent="must not exist",
                    parent_attempt_id="missing-parent",
                    attempt_id="attempt-orphan",
                )
            summary = store.integrity_summary()
            self.assertEqual(summary["counts"], {"blobs": 0, "attempts": 0, "events": 0})
            self.assertTrue(summary["integrity_ok"])

    def test_attempt_blob_and_event_rows_are_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = self.new_store(Path(td))
            receipt = store.capture(
                b"immutable\n",
                artifact_class="code.attempt",
                producer="test",
                intent="immutability probe",
                attempt_id="attempt-immutable",
            )
            conn = sqlite3.connect(store.db_path)
            try:
                for statement, params in [
                    ("UPDATE attempts SET intent='changed' WHERE attempt_id=?", (receipt.attempt_id,)),
                    ("DELETE FROM attempts WHERE attempt_id=?", (receipt.attempt_id,)),
                    ("UPDATE blobs SET byte_length=0 WHERE blob_sha256=?", (receipt.blob_sha256,)),
                    ("DELETE FROM events WHERE attempt_id=?", (receipt.attempt_id,)),
                ]:
                    with self.assertRaises(sqlite3.IntegrityError):
                        conn.execute(statement, params)
                    conn.rollback()
            finally:
                conn.close()
            self.assertTrue(store.integrity_summary()["integrity_ok"])
            self.assertEqual(store.read_attempt(receipt.attempt_id)["payload"], b"immutable\n")

    def test_hard_kill_before_commit_leaves_no_phantom_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store_root = Path(td) / "store"
            result = self.run_worker(
                store_root,
                attempt_id="attempt-kill-before-commit",
                phase="after_rows_before_commit",
            )
            self.assertEqual(result.returncode, 91, msg=result.stderr)
            store = AttemptStore(store_root)
            summary = store.integrity_summary()
            self.assertTrue(summary["integrity_ok"])
            self.assertEqual(summary["counts"], {"blobs": 0, "attempts": 0, "events": 0})
            with self.assertRaises(AttemptStoreError):
                store.read_attempt("attempt-kill-before-commit")

    def test_hard_kill_after_commit_recovers_exact_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store_root = Path(td) / "store"
            result = self.run_worker(
                store_root,
                attempt_id="attempt-kill-after-commit",
                phase="after_commit_before_readback",
            )
            self.assertEqual(result.returncode, 92, msg=result.stderr)
            store = AttemptStore(store_root)
            summary = store.integrity_summary()
            self.assertTrue(summary["integrity_ok"])
            self.assertEqual(summary["counts"], {"blobs": 1, "attempts": 1, "events": 1})
            recovered = store.read_attempt("attempt-kill-after-commit")
            self.assertTrue(recovered["verified"])
            self.assertEqual(recovered["payload"], HARDKILL_PAYLOAD)
            self.assertEqual(recovered["metadata"], {"kill_phase": "after_commit_before_readback"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
