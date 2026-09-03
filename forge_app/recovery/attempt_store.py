from __future__ import annotations

"""Crash-oriented content-addressed Attempt Store v0.1.

The authoritative v0.1 unit is one SQLite database (plus WAL/SHM while open).
Artifact bytes, immutable attempt metadata, and the capture journal event commit in
one transaction. Retries create new attempts with parent lineage; they never rewrite
prior attempts.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Callable, Mapping
from uuid import uuid4

SCHEMA_VERSION = "forge-attempt-store/0.1"


class AttemptStoreError(RuntimeError):
    pass


class AttemptVerificationError(AttemptStoreError):
    pass


PhaseHook = Callable[[str], None]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Mapping[str, Any] | None) -> str:
    return json.dumps(value or {}, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


@dataclass(frozen=True)
class CaptureReceipt:
    attempt_id: str
    blob_sha256: str
    byte_length: int
    event_id: str
    parent_attempt_id: str | None
    artifact_class: str
    producer: str
    created_at: str
    verified_readback: bool
    schema: str = SCHEMA_VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventReceipt:
    event_id: str
    event_type: str
    attempt_id: str | None
    blob_sha256: str | None
    payload: dict[str, Any]
    created_at: str
    seq: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AttemptStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "attempt_store.sqlite3"
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=10000")
        mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
        if str(mode).lower() != "wal":
            conn.close()
            raise AttemptStoreError(f"WAL mode unavailable: {mode!r}")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def _initialize(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS store_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS blobs (
                    blob_sha256 TEXT PRIMARY KEY,
                    byte_length INTEGER NOT NULL CHECK(byte_length >= 0),
                    payload BLOB NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id TEXT PRIMARY KEY,
                    blob_sha256 TEXT NOT NULL REFERENCES blobs(blob_sha256),
                    parent_attempt_id TEXT REFERENCES attempts(attempt_id),
                    artifact_class TEXT NOT NULL,
                    producer TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    attempt_id TEXT REFERENCES attempts(attempt_id),
                    blob_sha256 TEXT REFERENCES blobs(blob_sha256),
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_attempts_blob ON attempts(blob_sha256);
                CREATE INDEX IF NOT EXISTS idx_attempts_parent ON attempts(parent_attempt_id);
                CREATE INDEX IF NOT EXISTS idx_events_attempt ON events(attempt_id);

                CREATE TRIGGER IF NOT EXISTS blobs_no_update
                BEFORE UPDATE ON blobs BEGIN
                    SELECT RAISE(ABORT, 'immutable blobs');
                END;
                CREATE TRIGGER IF NOT EXISTS blobs_no_delete
                BEFORE DELETE ON blobs BEGIN
                    SELECT RAISE(ABORT, 'immutable blobs');
                END;
                CREATE TRIGGER IF NOT EXISTS attempts_no_update
                BEFORE UPDATE ON attempts BEGIN
                    SELECT RAISE(ABORT, 'immutable attempts');
                END;
                CREATE TRIGGER IF NOT EXISTS attempts_no_delete
                BEFORE DELETE ON attempts BEGIN
                    SELECT RAISE(ABORT, 'immutable attempts');
                END;
                CREATE TRIGGER IF NOT EXISTS events_no_update
                BEFORE UPDATE ON events BEGIN
                    SELECT RAISE(ABORT, 'immutable events');
                END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete
                BEFORE DELETE ON events BEGIN
                    SELECT RAISE(ABORT, 'immutable events');
                END;
                """
            )
            conn.execute(
                "INSERT OR IGNORE INTO store_meta(key, value) VALUES('schema_version', ?)",
                (SCHEMA_VERSION,),
            )
            current = conn.execute(
                "SELECT value FROM store_meta WHERE key='schema_version'"
            ).fetchone()[0]
            if current != SCHEMA_VERSION:
                raise AttemptStoreError(
                    f"schema mismatch: store={current!r} code={SCHEMA_VERSION!r}"
                )
            conn.commit()
        finally:
            conn.close()

    def capture(
        self,
        payload: bytes,
        *,
        artifact_class: str,
        producer: str,
        intent: str,
        parent_attempt_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        attempt_id: str | None = None,
        phase_hook: PhaseHook | None = None,
    ) -> CaptureReceipt:
        if not isinstance(payload, (bytes, bytearray, memoryview)):
            raise TypeError("payload must be bytes-like")
        payload = bytes(payload)
        if not artifact_class.strip():
            raise ValueError("artifact_class is required")
        if not producer.strip():
            raise ValueError("producer is required")
        if not intent.strip():
            raise ValueError("intent is required")

        blob_sha256 = _sha256(payload)
        attempt_id = attempt_id or f"attempt-{uuid4().hex}"
        event_id = f"event-{uuid4().hex}"
        created_at = _utc_now()
        metadata_json = _canonical_json(metadata)

        conn = self._connect()
        committed = False
        try:
            conn.execute("BEGIN IMMEDIATE")

            # Idempotent replay closes the unknown-outcome gap: if a caller lost
            # the receipt after COMMIT, repeating the exact immutable operation
            # with the same attempt_id returns the already-committed attempt.
            # Any semantic/content mismatch is a hard identity conflict.
            existing_attempt = conn.execute(
                """
                SELECT a.attempt_id, a.blob_sha256, a.parent_attempt_id,
                       a.artifact_class, a.producer, a.intent, a.metadata_json,
                       a.created_at, b.byte_length, b.payload
                FROM attempts a JOIN blobs b ON b.blob_sha256=a.blob_sha256
                WHERE a.attempt_id=?
                """,
                (attempt_id,),
            ).fetchone()
            if existing_attempt is not None:
                existing_payload = bytes(existing_attempt["payload"])
                replay_matches = (
                    existing_attempt["blob_sha256"] == blob_sha256
                    and int(existing_attempt["byte_length"]) == len(payload)
                    and _sha256(existing_payload) == blob_sha256
                    and existing_payload == payload
                    and existing_attempt["parent_attempt_id"] == parent_attempt_id
                    and existing_attempt["artifact_class"] == artifact_class
                    and existing_attempt["producer"] == producer
                    and existing_attempt["intent"] == intent
                    and existing_attempt["metadata_json"] == metadata_json
                )
                if not replay_matches:
                    raise AttemptStoreError(
                        f"attempt_id conflict with different immutable operation: {attempt_id}"
                    )
                capture_events = conn.execute(
                    """
                    SELECT event_id FROM events
                    WHERE attempt_id=? AND event_type='attempt_captured'
                    ORDER BY seq
                    """,
                    (attempt_id,),
                ).fetchall()
                if len(capture_events) != 1:
                    raise AttemptVerificationError(
                        f"attempt capture event cardinality invalid for {attempt_id}: {len(capture_events)}"
                    )
                conn.rollback()
                return CaptureReceipt(
                    attempt_id=attempt_id,
                    blob_sha256=blob_sha256,
                    byte_length=len(payload),
                    event_id=capture_events[0]["event_id"],
                    parent_attempt_id=parent_attempt_id,
                    artifact_class=artifact_class,
                    producer=producer,
                    created_at=existing_attempt["created_at"],
                    verified_readback=True,
                )

            if parent_attempt_id is not None:
                parent = conn.execute(
                    "SELECT attempt_id FROM attempts WHERE attempt_id=?",
                    (parent_attempt_id,),
                ).fetchone()
                if parent is None:
                    raise AttemptStoreError(f"unknown parent attempt: {parent_attempt_id}")

            existing = conn.execute(
                "SELECT byte_length, payload FROM blobs WHERE blob_sha256=?",
                (blob_sha256,),
            ).fetchone()
            if existing is None:
                conn.execute(
                    "INSERT INTO blobs(blob_sha256, byte_length, payload, created_at) VALUES(?,?,?,?)",
                    (blob_sha256, len(payload), sqlite3.Binary(payload), created_at),
                )
            else:
                existing_payload = bytes(existing["payload"])
                if int(existing["byte_length"]) != len(payload) or _sha256(existing_payload) != blob_sha256:
                    raise AttemptVerificationError("content-addressed blob collision or corruption")
                if existing_payload != payload:
                    raise AttemptVerificationError("hash-equivalent blob bytes differ")

            conn.execute(
                """
                INSERT INTO attempts(
                    attempt_id, blob_sha256, parent_attempt_id, artifact_class,
                    producer, intent, metadata_json, created_at
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    attempt_id,
                    blob_sha256,
                    parent_attempt_id,
                    artifact_class,
                    producer,
                    intent,
                    metadata_json,
                    created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO events(
                    event_id, event_type, attempt_id, blob_sha256, payload_json, created_at
                ) VALUES(?,?,?,?,?,?)
                """,
                (
                    event_id,
                    "attempt_captured",
                    attempt_id,
                    blob_sha256,
                    _canonical_json(
                        {
                            "artifact_class": artifact_class,
                            "producer": producer,
                            "parent_attempt_id": parent_attempt_id,
                            "byte_length": len(payload),
                        }
                    ),
                    created_at,
                ),
            )

            if phase_hook is not None:
                phase_hook("after_rows_before_commit")

            conn.commit()
            committed = True

            if phase_hook is not None:
                phase_hook("after_commit_before_readback")

            row = conn.execute(
                """
                SELECT a.attempt_id, a.blob_sha256, a.parent_attempt_id,
                       a.artifact_class, a.producer, a.created_at,
                       b.byte_length, b.payload
                FROM attempts a JOIN blobs b ON b.blob_sha256=a.blob_sha256
                WHERE a.attempt_id=?
                """,
                (attempt_id,),
            ).fetchone()
            event = conn.execute(
                "SELECT event_id FROM events WHERE event_id=? AND attempt_id=?",
                (event_id, attempt_id),
            ).fetchone()
            if row is None or event is None:
                raise AttemptVerificationError("post-commit readback missing attempt or event")
            readback_payload = bytes(row["payload"])
            verified = (
                row["blob_sha256"] == blob_sha256
                and int(row["byte_length"]) == len(payload)
                and _sha256(readback_payload) == blob_sha256
                and readback_payload == payload
            )
            if not verified:
                raise AttemptVerificationError("post-commit payload readback mismatch")

            return CaptureReceipt(
                attempt_id=attempt_id,
                blob_sha256=blob_sha256,
                byte_length=len(payload),
                event_id=event_id,
                parent_attempt_id=parent_attempt_id,
                artifact_class=artifact_class,
                producer=producer,
                created_at=created_at,
                verified_readback=True,
            )
        except BaseException:
            if not committed and conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.close()

    def append_event(
        self,
        event_type: str,
        *,
        attempt_id: str | None = None,
        blob_sha256: str | None = None,
        payload: Mapping[str, Any] | None = None,
        event_id: str | None = None,
    ) -> EventReceipt:
        if not event_type.strip():
            raise ValueError("event_type is required")
        event_id = event_id or f"event-{uuid4().hex}"
        created_at = _utc_now()
        payload_json = _canonical_json(payload)
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            if attempt_id is not None:
                row = conn.execute(
                    "SELECT blob_sha256 FROM attempts WHERE attempt_id=?", (attempt_id,)
                ).fetchone()
                if row is None:
                    raise AttemptStoreError(f"unknown attempt for event: {attempt_id}")
                actual_blob = row["blob_sha256"]
                if blob_sha256 is None:
                    blob_sha256 = actual_blob
                elif blob_sha256 != actual_blob:
                    raise AttemptStoreError("event blob_sha256 does not match attempt")
            existing = conn.execute(
                "SELECT seq,event_id,event_type,attempt_id,blob_sha256,payload_json,created_at FROM events WHERE event_id=?",
                (event_id,),
            ).fetchone()
            if existing is not None:
                matches = (
                    existing["event_type"] == event_type
                    and existing["attempt_id"] == attempt_id
                    and existing["blob_sha256"] == blob_sha256
                    and existing["payload_json"] == payload_json
                )
                if not matches:
                    raise AttemptStoreError(f"event_id conflict with different immutable event: {event_id}")
                conn.rollback()
                return EventReceipt(
                    event_id=existing["event_id"],
                    event_type=existing["event_type"],
                    attempt_id=existing["attempt_id"],
                    blob_sha256=existing["blob_sha256"],
                    payload=json.loads(existing["payload_json"]),
                    created_at=existing["created_at"],
                    seq=int(existing["seq"]),
                )
            cur = conn.execute(
                "INSERT INTO events(event_id,event_type,attempt_id,blob_sha256,payload_json,created_at) VALUES(?,?,?,?,?,?)",
                (event_id,event_type,attempt_id,blob_sha256,payload_json,created_at),
            )
            seq = int(cur.lastrowid)
            conn.commit()
            return EventReceipt(
                event_id=event_id,event_type=event_type,attempt_id=attempt_id,
                blob_sha256=blob_sha256,payload=json.loads(payload_json),
                created_at=created_at,seq=seq,
            )
        except BaseException:
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.close()

    def events_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT seq,event_id,event_type,attempt_id,blob_sha256,payload_json,created_at FROM events WHERE attempt_id=? ORDER BY seq",
                (attempt_id,),
            ).fetchall()
            return [
                {
                    "seq": int(r["seq"]),
                    "event_id": r["event_id"],
                    "event_type": r["event_type"],
                    "attempt_id": r["attempt_id"],
                    "blob_sha256": r["blob_sha256"],
                    "payload": json.loads(r["payload_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        finally:
            conn.close()

    def events_by_type(self, event_type: str, limit: int | None = None) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            sql = "SELECT seq,event_id,event_type,attempt_id,blob_sha256,payload_json,created_at FROM events WHERE event_type=? ORDER BY seq"
            params: tuple[Any, ...]
            if limit is None:
                params = (event_type,)
            else:
                sql += " DESC LIMIT ?"
                params = (event_type, max(0, int(limit)))
            rows = conn.execute(sql, params).fetchall()
            return [
                {
                    "seq": int(r["seq"]),
                    "event_id": r["event_id"],
                    "event_type": r["event_type"],
                    "attempt_id": r["attempt_id"],
                    "blob_sha256": r["blob_sha256"],
                    "payload": json.loads(r["payload_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        finally:
            conn.close()

    def read_attempt(self, attempt_id: str) -> dict[str, Any]:
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT a.*, b.byte_length, b.payload
                FROM attempts a JOIN blobs b ON b.blob_sha256=a.blob_sha256
                WHERE a.attempt_id=?
                """,
                (attempt_id,),
            ).fetchone()
            if row is None:
                raise AttemptStoreError(f"attempt not found: {attempt_id}")
            payload = bytes(row["payload"])
            if len(payload) != int(row["byte_length"]) or _sha256(payload) != row["blob_sha256"]:
                raise AttemptVerificationError(f"payload verification failed: {attempt_id}")
            return {
                "attempt_id": row["attempt_id"],
                "blob_sha256": row["blob_sha256"],
                "parent_attempt_id": row["parent_attempt_id"],
                "artifact_class": row["artifact_class"],
                "producer": row["producer"],
                "intent": row["intent"],
                "metadata": json.loads(row["metadata_json"]),
                "created_at": row["created_at"],
                "byte_length": int(row["byte_length"]),
                "payload": payload,
                "verified": True,
            }
        finally:
            conn.close()

    def lineage(self, attempt_id: str) -> list[str]:
        result: list[str] = []
        current: str | None = attempt_id
        conn = self._connect()
        try:
            seen: set[str] = set()
            while current is not None:
                if current in seen:
                    raise AttemptVerificationError("attempt lineage cycle detected")
                seen.add(current)
                row = conn.execute(
                    "SELECT attempt_id, parent_attempt_id FROM attempts WHERE attempt_id=?",
                    (current,),
                ).fetchone()
                if row is None:
                    raise AttemptStoreError(f"attempt not found in lineage: {current}")
                result.append(row["attempt_id"])
                current = row["parent_attempt_id"]
            return result
        finally:
            conn.close()

    def latest_attempts(self, limit: int = 10) -> list[dict[str, Any]]:
        if limit < 1:
            return []
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT attempt_id, blob_sha256, parent_attempt_id, artifact_class,
                       producer, intent, metadata_json, created_at
                FROM attempts ORDER BY rowid DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [
                {
                    "attempt_id": r["attempt_id"],
                    "blob_sha256": r["blob_sha256"],
                    "parent_attempt_id": r["parent_attempt_id"],
                    "artifact_class": r["artifact_class"],
                    "producer": r["producer"],
                    "intent": r["intent"],
                    "metadata": json.loads(r["metadata_json"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        finally:
            conn.close()

    def integrity_summary(self) -> dict[str, Any]:
        conn = self._connect()
        try:
            integrity_rows = [r[0] for r in conn.execute("PRAGMA integrity_check").fetchall()]
            journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            synchronous = int(conn.execute("PRAGMA synchronous").fetchone()[0])
            counts = {
                table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in ("blobs", "attempts", "events")
            }
            last = conn.execute(
                "SELECT seq, event_id, event_type, attempt_id, created_at FROM events ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            return {
                "schema": SCHEMA_VERSION,
                "db_path": str(self.db_path),
                "integrity": integrity_rows,
                "integrity_ok": integrity_rows == ["ok"],
                "journal_mode": str(journal_mode).lower(),
                "synchronous": synchronous,
                "counts": counts,
                "last_event": dict(last) if last is not None else None,
            }
        finally:
            conn.close()
