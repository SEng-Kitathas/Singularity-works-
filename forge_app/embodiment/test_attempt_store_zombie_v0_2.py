from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from forge_app.recovery import AttemptStore


SOURCE_ROOT = Path(__file__).resolve().parents[2]
CONCURRENCY_WORKER = Path(__file__).with_name("attempt_store_concurrency_worker_v0_2.py")


class AttemptStoreZombieV02Tests(unittest.TestCase):
    def new_store(self, root: Path) -> AttemptStore:
        return AttemptStore(root / "store")

    def test_injected_disk_full_before_commit_rolls_back_everything(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            store = AttemptStore(root)

            def fail_before_commit(phase: str) -> None:
                if phase == "after_rows_before_commit":
                    raise sqlite3.OperationalError("database or disk is full")

            with self.assertRaises(sqlite3.OperationalError):
                store.capture(
                    b"must-not-survive\n",
                    artifact_class="embodiment.disk_full",
                    producer="zombie-v0.2",
                    intent="injected disk-full before commit",
                    attempt_id="attempt-disk-full",
                    phase_hook=fail_before_commit,
                )

            reopened = AttemptStore(root)
            summary = reopened.integrity_summary()
            self.assertTrue(summary["integrity_ok"])
            self.assertEqual(summary["counts"], {"blobs": 0, "attempts": 0, "events": 0})

    def test_concurrent_writers_preserve_every_attempt_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            AttemptStore(root)  # initialize before the start gun
            env = dict(os.environ)
            env["PYTHONPATH"] = str(SOURCE_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
            workers: list[subprocess.Popen[str]] = []
            for ordinal in range(12):
                workers.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(CONCURRENCY_WORKER),
                            "--store",
                            str(root),
                            "--ordinal",
                            str(ordinal),
                        ],
                        cwd=str(SOURCE_ROOT),
                        env=env,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                )

            failures = []
            for ordinal, proc in enumerate(workers):
                out, err = proc.communicate(timeout=30)
                if proc.returncode != 0:
                    failures.append((ordinal, proc.returncode, out, err))
            self.assertEqual(failures, [])

            store = AttemptStore(root)
            summary = store.integrity_summary()
            self.assertTrue(summary["integrity_ok"])
            self.assertEqual(summary["counts"], {"blobs": 12, "attempts": 12, "events": 12})
            for ordinal in range(12):
                attempt_id = f"attempt-concurrent-{ordinal:03d}"
                recovered = store.read_attempt(attempt_id)
                self.assertEqual(
                    recovered["payload"],
                    f"concurrent-attempt-{ordinal:03d}\n".encode("utf-8"),
                )
                self.assertTrue(recovered["verified"])

    def test_retry_after_unknown_commit_outcome_is_idempotent(self) -> None:
        """Desired v0.2 law: same immutable attempt replay returns same receipt.

        The first call commits successfully and then loses its response. A caller that
        repeats the exact operation with the same attempt_id must recover the existing
        committed attempt rather than create a duplicate or fail ambiguously.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            store = AttemptStore(root)
            payload = b"attempt-zero-survives-unknown-outcome\n"

            def lose_receipt(phase: str) -> None:
                if phase == "after_commit_before_readback":
                    raise ConnectionError("simulated caller/transport loss after commit")

            with self.assertRaises(ConnectionError):
                store.capture(
                    payload,
                    artifact_class="code.attempt",
                    producer="zombie-v0.2",
                    intent="unknown commit outcome discriminator",
                    metadata={"ordinal": 0},
                    attempt_id="attempt-unknown-outcome",
                    phase_hook=lose_receipt,
                )

            reopened = AttemptStore(root)
            committed = reopened.read_attempt("attempt-unknown-outcome")
            self.assertEqual(committed["payload"], payload)

            replay = reopened.capture(
                payload,
                artifact_class="code.attempt",
                producer="zombie-v0.2",
                intent="unknown commit outcome discriminator",
                metadata={"ordinal": 0},
                attempt_id="attempt-unknown-outcome",
            )
            self.assertTrue(replay.verified_readback)
            self.assertEqual(replay.attempt_id, "attempt-unknown-outcome")
            self.assertEqual(replay.blob_sha256, committed["blob_sha256"])
            summary = reopened.integrity_summary()
            self.assertEqual(summary["counts"], {"blobs": 1, "attempts": 1, "events": 1})

    def test_same_attempt_id_with_different_content_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = self.new_store(Path(td))
            store.capture(
                b"original\n",
                artifact_class="code.attempt",
                producer="zombie-v0.2",
                intent="identity conflict discriminator",
                metadata={"ordinal": 0},
                attempt_id="attempt-conflict",
            )
            with self.assertRaises(Exception):
                store.capture(
                    b"different\n",
                    artifact_class="code.attempt",
                    producer="zombie-v0.2",
                    intent="identity conflict discriminator",
                    metadata={"ordinal": 0},
                    attempt_id="attempt-conflict",
                )
            summary = store.integrity_summary()
            self.assertEqual(summary["counts"], {"blobs": 1, "attempts": 1, "events": 1})
            self.assertEqual(store.read_attempt("attempt-conflict")["payload"], b"original\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
