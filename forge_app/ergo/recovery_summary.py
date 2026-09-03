from __future__ import annotations

"""Read-only Ergo recovery summary over the Forge Attempt Store.

Ergo is an observer here, not persistence authority. Missing/corrupt stores are
reported; this module never creates, repairs, checkpoints, or mutates them.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import sqlite3
import subprocess
from typing import Any


@dataclass(frozen=True)
class GitSourceSummary:
    repo_path: str
    available: bool
    head: str | None
    branch: str | None
    dirty: bool | None
    status_lines: tuple[str, ...]
    error: str | None = None


@dataclass(frozen=True)
class ErgoRecoverySummary:
    schema: str
    store_path: str
    store_status: str
    integrity_ok: bool | None
    integrity: tuple[str, ...]
    journal_mode: str | None
    schema_version: str | None
    blob_count: int | None
    attempt_count: int | None
    event_count: int | None
    last_event: dict[str, Any] | None
    latest_attempts: tuple[dict[str, Any], ...]
    source: GitSourceSummary | None
    normal_mode_allowed: bool
    safe_mode_available: bool
    recovery_mode_required: bool
    reasons: tuple[str, ...]
    observer_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def _git(repo: Path, *args: str) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        timeout=5,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def inspect_git_source(repo_path: str | Path) -> GitSourceSummary:
    repo = Path(repo_path)
    if not repo.exists():
        return GitSourceSummary(str(repo), False, None, None, None, (), "repo path missing")
    rc, head, err = _git(repo, "rev-parse", "HEAD")
    if rc != 0:
        return GitSourceSummary(str(repo), False, None, None, None, (), err or "not a git repository")
    _, branch, _ = _git(repo, "branch", "--show-current")
    rc, status, status_err = _git(repo, "status", "--porcelain=v1")
    lines = tuple(line for line in status.splitlines() if line) if rc == 0 else ()
    return GitSourceSummary(
        repo_path=str(repo),
        available=True,
        head=head,
        branch=branch or None,
        dirty=bool(lines) if rc == 0 else None,
        status_lines=lines,
        error=status_err or None if rc != 0 else None,
    )


def _read_attempt_store(store_root: Path, latest_limit: int) -> dict[str, Any]:
    db_path = store_root / "attempt_store.sqlite3"
    if not db_path.exists():
        return {
            "status": "MISSING",
            "db_path": db_path,
            "integrity_ok": None,
            "integrity": (),
            "journal_mode": None,
            "schema_version": None,
            "counts": None,
            "last_event": None,
            "latest_attempts": (),
            "reason": "attempt store database is missing",
        }

    # mode=ro is load-bearing: Ergo inspection must not create or repair state.
    uri = db_path.resolve().as_uri() + "?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=2.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA query_only=ON")
            integrity = tuple(row[0] for row in conn.execute("PRAGMA integrity_check").fetchall())
            integrity_ok = integrity == ("ok",)
            journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            meta = conn.execute(
                "SELECT value FROM store_meta WHERE key='schema_version'"
            ).fetchone()
            schema_version = meta[0] if meta else None
            counts = {
                table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in ("blobs", "attempts", "events")
            }
            last = conn.execute(
                "SELECT seq, event_id, event_type, attempt_id, created_at FROM events ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            latest = conn.execute(
                """
                SELECT attempt_id, blob_sha256, parent_attempt_id, artifact_class,
                       producer, intent, metadata_json, created_at
                FROM attempts ORDER BY rowid DESC LIMIT ?
                """,
                (max(0, latest_limit),),
            ).fetchall()
            attempts = tuple(
                {
                    "attempt_id": row["attempt_id"],
                    "blob_sha256": row["blob_sha256"],
                    "parent_attempt_id": row["parent_attempt_id"],
                    "artifact_class": row["artifact_class"],
                    "producer": row["producer"],
                    "intent": row["intent"],
                    "metadata": json.loads(row["metadata_json"]),
                    "created_at": row["created_at"],
                }
                for row in latest
            )
            return {
                "status": "READY" if integrity_ok else "DEGRADED",
                "db_path": db_path,
                "integrity_ok": integrity_ok,
                "integrity": integrity,
                "journal_mode": journal_mode,
                "schema_version": schema_version,
                "counts": counts,
                "last_event": dict(last) if last else None,
                "latest_attempts": attempts,
                "reason": None if integrity_ok else "integrity check did not return ok",
            }
        finally:
            conn.close()
    except (sqlite3.DatabaseError, OSError, ValueError) as exc:
        return {
            "status": "UNREADABLE",
            "db_path": db_path,
            "integrity_ok": False,
            "integrity": (),
            "journal_mode": None,
            "schema_version": None,
            "counts": None,
            "last_event": None,
            "latest_attempts": (),
            "reason": f"attempt store unreadable: {type(exc).__name__}: {exc}",
        }


def build_recovery_summary(
    store_root: str | Path,
    *,
    source_repo: str | Path | None = None,
    latest_limit: int = 8,
) -> ErgoRecoverySummary:
    store_root = Path(store_root)
    store = _read_attempt_store(store_root, latest_limit)
    source = inspect_git_source(source_repo) if source_repo is not None else None
    reasons: list[str] = []

    status = store["status"]
    if store.get("reason"):
        reasons.append(str(store["reason"]))
    if source is not None:
        if not source.available:
            reasons.append("source repository unavailable")
        elif source.dirty:
            reasons.append("source repository has uncommitted changes")

    if status == "READY":
        normal = True
        recovery_required = False
    elif status == "MISSING":
        normal = False
        recovery_required = True
    else:
        normal = False
        recovery_required = True

    counts = store["counts"] or {}
    if status == "READY" and int(counts.get("attempts", 0)) == 0:
        reasons.append("attempt store is healthy but contains no preserved attempts")

    return ErgoRecoverySummary(
        schema="forge-ergo-recovery-summary/0.1",
        store_path=str(store["db_path"]),
        store_status=status,
        integrity_ok=store["integrity_ok"],
        integrity=tuple(store["integrity"]),
        journal_mode=store["journal_mode"],
        schema_version=store["schema_version"],
        blob_count=counts.get("blobs"),
        attempt_count=counts.get("attempts"),
        event_count=counts.get("events"),
        last_event=store["last_event"],
        latest_attempts=tuple(store["latest_attempts"]),
        source=source,
        normal_mode_allowed=normal,
        safe_mode_available=True,
        recovery_mode_required=recovery_required,
        reasons=tuple(reasons),
        observer_authority="NONE",
    )
