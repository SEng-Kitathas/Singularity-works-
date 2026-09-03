from __future__ import annotations

"""Read-only Ergo checkpoint/recovery selection summary.

This module reuses the pure checkpoint reputation/selection rules from recovery
without opening an AttemptStore writer or mutating checkpoint lifecycle state.
"""

from dataclasses import dataclass, asdict
import json
from pathlib import Path
import sqlite3
from typing import Any

from forge_app.recovery.resume_checkpoint import (
    ARTIFACT_CLASS,
    CheckpointView,
    choose_recovery_view,
    derive_checkpoint_view,
)


@dataclass(frozen=True)
class ErgoCheckpointSummary:
    schema: str
    store_path: str
    status: str
    checkpoint_count: int
    selected_checkpoint_id: str | None
    selected_generation: int | None
    selected_status: str | None
    selected_resume_policy: str | None
    selected_verified: bool | None
    selected_stable: bool | None
    selected_lkg: bool | None
    selected_quarantined: bool | None
    selected_early_crash_count: int | None
    selected_source_head: str | None
    current_source_head: str | None
    source_currentness: str
    selection_reason: str | None
    selected_semantic_snapshot_id: str | None
    reasons: tuple[str, ...]
    observer_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _event_rows(conn: sqlite3.Connection, checkpoint_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT seq,event_id,event_type,attempt_id,blob_sha256,payload_json,created_at
        FROM events WHERE attempt_id=? ORDER BY seq
        """,
        (checkpoint_id,),
    ).fetchall()
    return [
        {
            "seq": int(row["seq"]),
            "event_id": row["event_id"],
            "event_type": row["event_type"],
            "attempt_id": row["attempt_id"],
            "blob_sha256": row["blob_sha256"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def build_checkpoint_summary(
    store_root: str | Path,
    *,
    limit: int = 500,
    current_source_head: str | None = None,
) -> ErgoCheckpointSummary:
    store_root = Path(store_root)
    db_path = store_root / "attempt_store.sqlite3"
    if not db_path.exists():
        return ErgoCheckpointSummary(
            schema="forge-ergo-checkpoint-summary/0.1",
            store_path=str(db_path),
            status="MISSING",
            checkpoint_count=0,
            selected_checkpoint_id=None,
            selected_generation=None,
            selected_status=None,
            selected_resume_policy=None,
            selected_verified=None,
            selected_stable=None,
            selected_lkg=None,
            selected_quarantined=None,
            selected_early_crash_count=None,
            selected_source_head=None,
            current_source_head=current_source_head,
            source_currentness="UNKNOWN",
            selection_reason=None,
            selected_semantic_snapshot_id=None,
            reasons=("attempt store database is missing",),
            observer_authority="NONE",
        )

    uri = db_path.resolve().as_uri() + "?mode=ro"
    reasons: list[str] = []
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=2.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA query_only=ON")
            rows = conn.execute(
                """
                SELECT a.attempt_id,a.blob_sha256,a.artifact_class,b.payload
                FROM attempts a JOIN blobs b ON b.blob_sha256=a.blob_sha256
                WHERE a.artifact_class=?
                ORDER BY a.rowid DESC LIMIT ?
                """,
                (ARTIFACT_CLASS, max(0, int(limit))),
            ).fetchall()
            views: list[CheckpointView] = []
            for row in rows:
                checkpoint_id = str(row["attempt_id"])
                try:
                    payload = json.loads(bytes(row["payload"]).decode("utf-8"))
                    events = _event_rows(conn, checkpoint_id)
                    views.append(
                        derive_checkpoint_view(
                            checkpoint_id=checkpoint_id,
                            attempt={
                                "blob_sha256": row["blob_sha256"],
                                "artifact_class": row["artifact_class"],
                            },
                            payload=payload,
                            events=events,
                        )
                    )
                except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                    reasons.append(
                        f"checkpoint {checkpoint_id} unreadable: {type(exc).__name__}: {exc}"
                    )
                except Exception as exc:
                    reasons.append(
                        f"checkpoint {checkpoint_id} invalid: {type(exc).__name__}: {exc}"
                    )
            selected = choose_recovery_view(views)
            source_currentness = "UNKNOWN"
            selection_reason: str | None = None
            effective_policy = selected.resume_policy if selected else None
            if selected is not None:
                if selected.source_head and current_source_head:
                    source_currentness = (
                        "MATCH" if selected.source_head == current_source_head else "MISMATCH"
                    )
                if selected.lkg:
                    selection_reason = "latest non-quarantined LKG checkpoint"
                elif selected.stable:
                    selection_reason = "latest non-quarantined STABLE checkpoint"
                elif selected.early_crash_count == 0:
                    selection_reason = "latest non-quarantined VERIFIED checkpoint"
                else:
                    selection_reason = "only non-quarantined crash-associated checkpoint"
                if source_currentness == "MISMATCH" and effective_policy == "NORMAL":
                    effective_policy = "SAFE_ONLY"
                    reasons.append(
                        "selected checkpoint source HEAD differs from current source HEAD; automatic normal resume downgraded"
                    )
            if not rows:
                status = "NONE"
            elif not views:
                status = "DEGRADED"
            elif selected is None:
                status = "RECOVERY_REQUIRED"
            elif source_currentness == "MISMATCH":
                status = "CAUTION"
            elif effective_policy == "NORMAL":
                status = "READY"
            else:
                status = "CAUTION"
            return ErgoCheckpointSummary(
                schema="forge-ergo-checkpoint-summary/0.1",
                store_path=str(db_path),
                status=status,
                checkpoint_count=len(views),
                selected_checkpoint_id=selected.checkpoint_id if selected else None,
                selected_generation=selected.generation if selected else None,
                selected_status=selected.status if selected else None,
                selected_resume_policy=effective_policy,
                selected_verified=selected.verified if selected else None,
                selected_stable=selected.stable if selected else None,
                selected_lkg=selected.lkg if selected else None,
                selected_quarantined=selected.quarantined if selected else None,
                selected_early_crash_count=selected.early_crash_count if selected else None,
                selected_source_head=selected.source_head if selected else None,
                current_source_head=current_source_head,
                source_currentness=source_currentness,
                selection_reason=selection_reason,
                selected_semantic_snapshot_id=selected.semantic_snapshot_id if selected else None,
                reasons=tuple(reasons),
                observer_authority="NONE",
            )
        finally:
            conn.close()
    except (sqlite3.DatabaseError, OSError, ValueError) as exc:
        return ErgoCheckpointSummary(
            schema="forge-ergo-checkpoint-summary/0.1",
            store_path=str(db_path),
            status="UNREADABLE",
            checkpoint_count=0,
            selected_checkpoint_id=None,
            selected_generation=None,
            selected_status=None,
            selected_resume_policy=None,
            selected_verified=None,
            selected_stable=None,
            selected_lkg=None,
            selected_quarantined=None,
            selected_early_crash_count=None,
            selected_source_head=None,
            current_source_head=current_source_head,
            source_currentness="UNKNOWN",
            selection_reason=None,
            selected_semantic_snapshot_id=None,
            reasons=(f"checkpoint store unreadable: {type(exc).__name__}: {exc}",),
            observer_authority="NONE",
        )
