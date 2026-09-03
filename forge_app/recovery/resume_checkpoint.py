from __future__ import annotations

"""Append-only resume checkpoint / emulator-like savestate lifecycle v0.1."""

from dataclasses import dataclass, asdict
import json
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from .attempt_store import AttemptStore, AttemptStoreError

CHECKPOINT_SCHEMA = "forge-resume-checkpoint/0.1"
ARTIFACT_CLASS = "recovery.resume_checkpoint"
EARLY_CRASH_SECONDS = 15.0
STABLE_SECONDS = 10.0
STABLE_OPERATIONS = 3


@dataclass(frozen=True)
class ResumeCheckpointPayload:
    session_id: str
    generation: int
    parent_checkpoint_id: str | None
    project_id: str
    workspace_id: str
    source_branch: str | None
    source_head: str | None
    core_contract_version: str | None
    core_currentness_id: str | None
    semantic_snapshot_id: str | None
    open_referents: tuple[str, ...] = ()
    selected_referents: tuple[str, ...] = ()
    history_cursor: str | None = None
    ui_layout_id: str | None = None
    camera_state: Mapping[str, Any] | None = None
    command_cursor: str | None = None
    active_attempt_ids: tuple[str, ...] = ()
    pending_transaction_ids: tuple[str, ...] = ()
    counterfactual_branch_id: str | None = None
    schema: str = CHECKPOINT_SCHEMA

    def canonical_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


@dataclass(frozen=True)
class CheckpointView:
    checkpoint_id: str
    generation: int
    parent_checkpoint_id: str | None
    verified: bool
    resumed: bool
    stable: bool
    lkg: bool
    early_crash_count: int
    quarantined: bool
    status: str
    resume_policy: str
    blob_sha256: str
    source_head: str | None
    semantic_snapshot_id: str | None


def validate_checkpoint_payload(data: dict[str, Any]) -> None:
    if data.get("schema") != CHECKPOINT_SCHEMA:
        raise AttemptStoreError(f"checkpoint schema mismatch: {data.get('schema')!r}")
    if not str(data.get("session_id") or "").strip():
        raise AttemptStoreError("checkpoint session_id missing")
    if not isinstance(data.get("generation"), int) or int(data["generation"]) < 0:
        raise AttemptStoreError("checkpoint generation invalid")
    if not str(data.get("project_id") or "").strip():
        raise AttemptStoreError("checkpoint project_id missing")
    if not str(data.get("workspace_id") or "").strip():
        raise AttemptStoreError("checkpoint workspace_id missing")


def derive_checkpoint_view(
    *,
    checkpoint_id: str,
    attempt: Mapping[str, Any],
    payload: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
) -> CheckpointView:
    validate_checkpoint_payload(dict(payload))
    typed = [(int(e["seq"]), str(e["event_type"]), dict(e["payload"])) for e in events]
    verified = any(t == "checkpoint_verified" for _, t, _ in typed)
    resumed = any(t == "checkpoint_resumed" for _, t, _ in typed)
    quarantine_seq = max((s for s, t, _ in typed if t == "checkpoint_quarantined"), default=-1)
    crash_events = [(s, p) for s, t, p in typed if t == "checkpoint_crash_associated"]
    early_crashes = [(s, p) for s, p in crash_events if bool(p.get("early"))]
    last_crash_seq = max((s for s, _ in crash_events), default=-1)
    last_stable_seq = max((s for s, t, _ in typed if t == "checkpoint_stable"), default=-1)
    last_lkg_seq = max((s for s, t, _ in typed if t == "checkpoint_lkg_promoted"), default=-1)
    quarantined = quarantine_seq >= 0
    stable = last_stable_seq >= 0 and last_stable_seq > last_crash_seq and not quarantined
    lkg = last_lkg_seq >= 0 and last_lkg_seq > last_crash_seq and not quarantined
    if quarantined:
        status = "QUARANTINED"
        policy = "INSPECT_ONLY"
    elif stable:
        status = "LKG" if lkg else "STABLE"
        policy = "NORMAL"
    elif verified and len(early_crashes) == 0:
        status = "VERIFIED"
        policy = "NORMAL"
    elif verified and len(early_crashes) == 1:
        status = "CRASH_ASSOCIATED"
        policy = "SAFE_ONLY"
    elif verified:
        status = "VERIFIED_DEGRADED"
        policy = "SAFE_ONLY"
    else:
        status = "CAPTURED"
        policy = "INSPECT_ONLY"
    return CheckpointView(
        checkpoint_id=checkpoint_id,
        generation=int(payload["generation"]),
        parent_checkpoint_id=payload.get("parent_checkpoint_id"),
        verified=verified,
        resumed=resumed,
        stable=stable,
        lkg=lkg,
        early_crash_count=len(early_crashes),
        quarantined=quarantined,
        status=status,
        resume_policy=policy,
        blob_sha256=str(attempt["blob_sha256"]),
        source_head=payload.get("source_head"),
        semantic_snapshot_id=payload.get("semantic_snapshot_id"),
    )


def choose_recovery_view(views: Sequence[CheckpointView]) -> CheckpointView | None:
    candidates = [v for v in views if v.verified and not v.quarantined]
    stable = [v for v in candidates if v.stable]
    if stable:
        return max(stable, key=lambda v: (v.generation, v.checkpoint_id))
    clean_verified = [v for v in candidates if v.early_crash_count == 0]
    if clean_verified:
        return max(clean_verified, key=lambda v: (v.generation, v.checkpoint_id))
    single_crash = [v for v in candidates if v.early_crash_count == 1]
    if single_crash:
        return max(single_crash, key=lambda v: (v.generation, v.checkpoint_id))
    return None


class ResumeCheckpointManager:
    def __init__(self, store: AttemptStore) -> None:
        self.store = store
        self._quarantine_handler: Callable[[str], Any] | None = None

    def register_quarantine_handler(self, handler: Callable[[str], Any]) -> None:
        if self._quarantine_handler is not None and self._quarantine_handler is not handler:
            raise AttemptStoreError("quarantine handler already registered")
        self._quarantine_handler = handler

    @staticmethod
    def _validate_payload_dict(data: dict[str, Any]) -> None:
        validate_checkpoint_payload(data)

    def capture_checkpoint(self, payload: ResumeCheckpointPayload, *, checkpoint_id: str | None = None) -> str:
        checkpoint_id = checkpoint_id or f"checkpoint-{uuid4().hex}"
        raw = payload.canonical_json().encode("utf-8")
        receipt = self.store.capture(
            raw,
            artifact_class=ARTIFACT_CLASS,
            producer="forge-app:resume-checkpoint-v0.1",
            intent=f"resume checkpoint generation {payload.generation}",
            parent_attempt_id=payload.parent_checkpoint_id,
            metadata={
                "schema": CHECKPOINT_SCHEMA,
                "session_id": payload.session_id,
                "generation": payload.generation,
                "parent_checkpoint_id": payload.parent_checkpoint_id,
                "source_head": payload.source_head,
                "core_contract_version": payload.core_contract_version,
                "core_currentness_id": payload.core_currentness_id,
                "semantic_snapshot_id": payload.semantic_snapshot_id,
            },
            attempt_id=checkpoint_id,
        )
        readback = self.store.read_attempt(checkpoint_id)
        data = json.loads(readback["payload"].decode("utf-8"))
        self._validate_payload_dict(data)
        self.store.append_event(
            "checkpoint_verified",
            attempt_id=checkpoint_id,
            payload={"schema": CHECKPOINT_SCHEMA, "generation": payload.generation, "blob_sha256": receipt.blob_sha256},
            event_id=f"checkpoint-verified:{checkpoint_id}",
        )
        return checkpoint_id

    def record_resume(self, checkpoint_id: str, *, resume_id: str) -> None:
        self.store.append_event(
            "checkpoint_resumed",
            attempt_id=checkpoint_id,
            payload={"resume_id": resume_id},
            event_id=f"checkpoint-resumed:{checkpoint_id}:{resume_id}",
        )

    def _latest_resume(self, checkpoint_id: str) -> tuple[int, str] | None:
        events = self.store.events_for_attempt(checkpoint_id)
        resumes = [
            (int(event["seq"]), str(event["payload"].get("resume_id") or ""))
            for event in events
            if event["event_type"] == "checkpoint_resumed"
        ]
        if not resumes:
            return None
        seq, resume_id = max(resumes, key=lambda item: item[0])
        if not resume_id:
            raise AttemptStoreError(f"checkpoint resume event missing resume_id: {checkpoint_id}")
        return seq, resume_id

    def _require_latest_resume(self, checkpoint_id: str, resume_id: str) -> int:
        latest = self._latest_resume(checkpoint_id)
        if latest is None:
            raise AttemptStoreError(f"checkpoint has not been resumed: {checkpoint_id}")
        seq, latest_resume_id = latest
        if latest_resume_id != resume_id:
            raise AttemptStoreError(
                f"stale resume generation for {checkpoint_id}: supplied={resume_id} latest={latest_resume_id}"
            )
        return seq

    def record_health(self, checkpoint_id: str, *, resume_id: str, healthy_seconds: float, meaningful_operations: int) -> bool:
        self._require_latest_resume(checkpoint_id, resume_id)
        if healthy_seconds < STABLE_SECONDS or meaningful_operations < STABLE_OPERATIONS:
            return False
        self.store.append_event(
            "checkpoint_stable",
            attempt_id=checkpoint_id,
            payload={
                "resume_id": resume_id,
                "healthy_seconds": float(healthy_seconds),
                "meaningful_operations": int(meaningful_operations),
                "threshold_seconds": STABLE_SECONDS,
                "threshold_operations": STABLE_OPERATIONS,
            },
            event_id=f"checkpoint-stable:{checkpoint_id}:{resume_id}",
        )
        return True

    def promote_lkg(self, checkpoint_id: str, *, promotion_id: str) -> None:
        view = self.inspect(checkpoint_id)
        if not view.stable or view.quarantined:
            raise AttemptStoreError("only stable non-quarantined checkpoints may become LKG")
        self.store.append_event(
            "checkpoint_lkg_promoted",
            attempt_id=checkpoint_id,
            payload={"promotion_id": promotion_id},
            event_id=f"checkpoint-lkg:{checkpoint_id}:{promotion_id}",
        )

    def record_crash(self, checkpoint_id: str, *, resume_id: str, crash_id: str, seconds_since_resume: float, failure_domain: str, detail: str = "") -> CheckpointView:
        self._require_latest_resume(checkpoint_id, resume_id)
        early = float(seconds_since_resume) <= EARLY_CRASH_SECONDS
        self.store.append_event(
            "checkpoint_crash_associated",
            attempt_id=checkpoint_id,
            payload={
                "resume_id": resume_id,
                "crash_id": crash_id,
                "seconds_since_resume": float(seconds_since_resume),
                "early": early,
                "failure_domain": failure_domain,
                "detail": detail,
            },
            event_id=f"checkpoint-crash:{checkpoint_id}:{crash_id}",
        )
        view = self.inspect(checkpoint_id)
        if view.early_crash_count >= 2 and not view.quarantined:
            self.store.append_event(
                "checkpoint_quarantined",
                attempt_id=checkpoint_id,
                payload={"reason": "two_distinct_early_crashes", "early_crash_count": view.early_crash_count},
                event_id=f"checkpoint-quarantine:{checkpoint_id}",
            )
            view = self.inspect(checkpoint_id)
        if view.quarantined and self._quarantine_handler is not None:
            # Replay is intentional: the handler is required to be idempotent so
            # a lost response after the quarantine commit can repair/return the
            # already prepared isolation lane.
            self._quarantine_handler(checkpoint_id)
        return view

    def inspect(self, checkpoint_id: str) -> CheckpointView:
        attempt = self.store.read_attempt(checkpoint_id)
        if attempt["artifact_class"] != ARTIFACT_CLASS:
            raise AttemptStoreError(f"not a resume checkpoint: {checkpoint_id}")
        payload = json.loads(attempt["payload"].decode("utf-8"))
        events = self.store.events_for_attempt(checkpoint_id)
        return derive_checkpoint_view(
            checkpoint_id=checkpoint_id,
            attempt=attempt,
            payload=payload,
            events=events,
        )

    def list_checkpoints(self, *, limit: int = 200) -> list[CheckpointView]:
        attempts = [a for a in self.store.latest_attempts(limit=max(1, limit * 4)) if a["artifact_class"] == ARTIFACT_CLASS]
        views = [self.inspect(a["attempt_id"]) for a in attempts[:limit]]
        return sorted(views, key=lambda v: (v.generation, v.checkpoint_id), reverse=True)

    def choose_recovery(self) -> CheckpointView | None:
        return choose_recovery_view(self.list_checkpoints(limit=500))
