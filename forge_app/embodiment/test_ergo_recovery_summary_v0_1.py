from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from forge_app.ergo import build_recovery_summary
from forge_app.recovery import AttemptStore


class ErgoRecoverySummaryV01Tests(unittest.TestCase):
    def test_missing_store_is_reported_without_creation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "missing-store"
            self.assertFalse(root.exists())
            summary = build_recovery_summary(root)
            self.assertEqual(summary.store_status, "MISSING")
            self.assertFalse(summary.normal_mode_allowed)
            self.assertTrue(summary.recovery_mode_required)
            self.assertEqual(summary.observer_authority, "NONE")
            self.assertFalse(root.exists(), "read-only Ergo inspection created the missing store")

    def test_ready_store_reports_exact_counts_and_latest_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            store = AttemptStore(root)
            receipt = store.capture(
                b"first preserved artifact\n",
                artifact_class="design.attempt",
                producer="ergo-summary-test",
                intent="preserve attempt zero",
                attempt_id="attempt-ergo-ready",
            )
            summary = build_recovery_summary(root)
            self.assertEqual(summary.store_status, "READY")
            self.assertTrue(summary.integrity_ok)
            self.assertEqual(summary.journal_mode, "wal")
            self.assertEqual(summary.schema_version, "forge-attempt-store/0.1")
            self.assertEqual((summary.blob_count, summary.attempt_count, summary.event_count), (1, 1, 1))
            self.assertTrue(summary.normal_mode_allowed)
            self.assertFalse(summary.recovery_mode_required)
            self.assertEqual(summary.latest_attempts[0]["attempt_id"], receipt.attempt_id)
            self.assertEqual(summary.latest_attempts[0]["intent"], "preserve attempt zero")
            self.assertEqual(summary.observer_authority, "NONE")

    def test_ready_inspection_does_not_modify_database_bytes_or_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            store = AttemptStore(root)
            store.capture(
                b"read-only probe\n",
                artifact_class="test.readonly",
                producer="ergo-summary-test",
                intent="prove inspection is non-mutating",
                attempt_id="attempt-readonly",
            )
            db = root / "attempt_store.sqlite3"
            before = (db.read_bytes(), db.stat().st_mtime_ns)
            first = build_recovery_summary(root)
            second = build_recovery_summary(root)
            after = (db.read_bytes(), db.stat().st_mtime_ns)
            self.assertEqual(first.store_status, "READY")
            self.assertEqual(second.store_status, "READY")
            self.assertEqual(before, after)

    def test_corrupt_store_is_reported_not_repaired(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            root.mkdir(parents=True)
            db = root / "attempt_store.sqlite3"
            corrupt = b"not-a-sqlite-database\x00\x01\x02"
            db.write_bytes(corrupt)
            before = db.read_bytes()
            summary = build_recovery_summary(root)
            after = db.read_bytes()
            self.assertEqual(summary.store_status, "UNREADABLE")
            self.assertFalse(summary.normal_mode_allowed)
            self.assertTrue(summary.recovery_mode_required)
            self.assertEqual(summary.observer_authority, "NONE")
            self.assertEqual(before, after, "Ergo attempted to repair/mutate corrupt authoritative state")


if __name__ == "__main__":
    unittest.main(verbosity=2)
