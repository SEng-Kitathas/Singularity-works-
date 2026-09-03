from __future__ import annotations

"""Checkpoint re-entry preparation v0.1.

One preparation primitive serves both automatic quarantine handling and explicit
manual operator recovery. It materializes an isolated, inspectable recovery lane
without clearing quarantine or mutating the active source checkout.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Literal
from uuid import uuid4

from .attempt_store import AttemptStoreError
from .resume_checkpoint import ResumeCheckpointManager

REENTRY_SCHEMA = "forge-checkpoint-reentry/0.1"
POPUP_SCHEMA = "forge-reentry-popup/0.1"
TRIGGERS = {"manual", "quarantine_auto"}


class ReentryPreparationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PopupAction:
    action_id: str
    label: str
    enabled: bool
    reason: str


@dataclass(frozen=True)
class OperatorPopup:
    schema: str
    severity: str
    title: str
    summary: str
    checkpoint_id: str
    checkpoint_status: str
    generation: int
    source_head: str | None
    current_source_head: str | None
    source_currentness: str
    source_isolation_status: str
    actions: tuple[PopupAction, ...]
    authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReentryPoint:
    schema: str
    reentry_id: str
    trigger: str
    checkpoint_id: str
    checkpoint_generation: int
    checkpoint_status: str
    checkpoint_quarantined: bool
    checkpoint_blob_sha256: str
    checkpoint_payload_sha256: str
    source_head: str | None
    current_source_head: str | None
    source_currentness: str
    source_isolation_status: str
    reentry_dir: str
    source_dir: str | None
    checkpoint_payload_path: str
    attempt_index_path: str
    popup_path: str
    manifest_path: str
    manifest_attempt_id: str
    prepared_at: str
    popup: OperatorPopup
    authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return cleaned[:180] or "reentry"


def _run_git(repo: Path, *args: str) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        timeout=20,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class CheckpointReentryService:
    def __init__(
        self,
        manager: ResumeCheckpointManager,
        *,
        reentry_root: str | Path,
        source_repo: str | Path | None = None,
    ) -> None:
        self.manager = manager
        self.store = manager.store
        self.reentry_root = Path(reentry_root)
        self.source_repo = Path(source_repo) if source_repo is not None else None
        self.manager.register_quarantine_handler(self.prepare_quarantined_reentry)

    def _current_source_head(self) -> str | None:
        if self.source_repo is None or not self.source_repo.exists():
            return None
        rc, out, _ = _run_git(self.source_repo, "rev-parse", "HEAD")
        return out if rc == 0 and out else None

    def _read_checkpoint_payload(self, checkpoint_id: str) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
        attempt = self.store.read_attempt(checkpoint_id)
        try:
            raw = bytes(attempt["payload"])
            payload = json.loads(raw.decode("utf-8"))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            raise ReentryPreparationError(
                f"checkpoint payload unreadable: {checkpoint_id}: {type(exc).__name__}: {exc}"
            ) from exc
        return payload, raw, attempt

    def _attempt_index(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        index: list[dict[str, Any]] = []
        for attempt_id in payload.get("active_attempt_ids") or ():
            item: dict[str, Any] = {"attempt_id": str(attempt_id), "found": False}
            try:
                attempt = self.store.read_attempt(str(attempt_id))
                item.update(
                    {
                        "found": True,
                        "blob_sha256": attempt.get("blob_sha256"),
                        "artifact_class": attempt.get("artifact_class"),
                        "intent": attempt.get("intent"),
                        "parent_attempt_id": attempt.get("parent_attempt_id"),
                        "created_at": attempt.get("created_at"),
                    }
                )
            except Exception as exc:
                item["error"] = f"{type(exc).__name__}: {exc}"
            index.append(item)
        return index

    def _materialize_source(self, final_dir: Path, source_head: str | None) -> tuple[str, str | None]:
        if not source_head:
            return "SOURCE_NOT_RECORDED", None
        if self.source_repo is None or not self.source_repo.exists():
            return "SOURCE_REPO_UNAVAILABLE", None
        rc, _, _ = _run_git(self.source_repo, "cat-file", "-e", f"{source_head}^{{commit}}")
        if rc != 0:
            return "SOURCE_COMMIT_UNAVAILABLE", None

        source_dir = final_dir / "source"
        if source_dir.exists():
            rc, existing_head, err = _run_git(source_dir, "rev-parse", "HEAD")
            if rc != 0 or existing_head != source_head:
                raise ReentryPreparationError(
                    f"existing re-entry source worktree identity mismatch: expected={source_head} actual={existing_head or err}"
                )
            return "EXACT_DETACHED_WORKTREE", str(source_dir)

        result = subprocess.run(
            [
                "git",
                "-C",
                str(self.source_repo),
                "worktree",
                "add",
                "--detach",
                str(source_dir),
                source_head,
            ],
            text=True,
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"WORKTREE_FAILED:{result.returncode}", None
        rc, exact_head, err = _run_git(source_dir, "rev-parse", "HEAD")
        if rc != 0 or exact_head != source_head:
            raise ReentryPreparationError(
                f"materialized source readback mismatch: expected={source_head} actual={exact_head or err}"
            )
        return "EXACT_DETACHED_WORKTREE", str(source_dir)

    def _popup(
        self,
        *,
        checkpoint_id: str,
        trigger: str,
        view: Any,
        source_isolation_status: str,
        current_source_head: str | None,
    ) -> OperatorPopup:
        source_currentness = "UNKNOWN"
        if view.source_head and current_source_head:
            source_currentness = "MATCH" if view.source_head == current_source_head else "MISMATCH"
        preferred = self.manager.choose_recovery()
        return_available = bool(preferred and preferred.checkpoint_id != checkpoint_id)
        compare_available = bool(view.source_head and current_source_head)
        source_exact = source_isolation_status == "EXACT_DETACHED_WORKTREE"

        if view.quarantined:
            severity = "RECOVERY_ISOLATED"
            title = "Quarantined checkpoint isolated"
            summary = (
                "Forge preserved the checkpoint exactly and prepared an isolated re-entry lane. "
                "Quarantine remains active; inspect or recover work without returning it to normal auto-resume."
            )
        elif trigger == "manual":
            severity = "MANUAL_REENTRY"
            title = "Manual checkpoint re-entry prepared"
            summary = (
                "Forge prepared this checkpoint in an isolated lane without changing its reputation or the active checkout."
            )
        else:
            severity = "RECOVERY"
            title = "Checkpoint re-entry prepared"
            summary = "Forge prepared an isolated checkpoint re-entry lane."

        actions = (
            PopupAction(
                "open_isolated_reentry",
                "Open isolated re-entry",
                True,
                "Checkpoint work-state payload is materialized; exact source worktree available"
                if source_exact
                else "Checkpoint work-state payload is materialized; source is state-only/unavailable",
            ),
            PopupAction(
                "inspect_checkpoint",
                "Inspect checkpoint",
                True,
                "Inspection is always available and does not clear quarantine",
            ),
            PopupAction(
                "compare_to_current",
                "Compare to current",
                compare_available,
                "Checkpoint and current source identities are available"
                if compare_available
                else "Both checkpoint and current source identities are required",
            ),
            PopupAction(
                "return_to_lkg",
                "Return to known-good checkpoint",
                return_available,
                f"Preferred checkpoint: {preferred.checkpoint_id}"
                if return_available and preferred is not None
                else "No different preferred checkpoint is currently available",
            ),
            PopupAction(
                "dismiss",
                "Dismiss",
                True,
                "Leave the prepared isolated re-entry point intact for later manual use",
            ),
        )
        return OperatorPopup(
            schema=POPUP_SCHEMA,
            severity=severity,
            title=title,
            summary=summary,
            checkpoint_id=checkpoint_id,
            checkpoint_status=view.status,
            generation=view.generation,
            source_head=view.source_head,
            current_source_head=current_source_head,
            source_currentness=source_currentness,
            source_isolation_status=source_isolation_status,
            actions=actions,
            authority="NONE",
        )

    def _from_existing_manifest(self, manifest_path: Path) -> ReentryPoint:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        popup_data = manifest.pop("popup")
        popup = OperatorPopup(
            actions=tuple(PopupAction(**item) for item in popup_data["actions"]),
            **{k: v for k, v in popup_data.items() if k != "actions"},
        )
        return ReentryPoint(popup=popup, **manifest)

    def _seal_manifest(
        self,
        *,
        checkpoint_id: str,
        trigger: str,
        manifest_path: Path,
    ) -> ReentryPoint:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        manifest_sha = _sha256_bytes(manifest_bytes)
        manifest_attempt_id = str(manifest["manifest_attempt_id"])
        safe_id = str(manifest["reentry_id"])
        source_status = str(manifest["source_isolation_status"])
        self.store.capture(
            manifest_bytes,
            artifact_class="recovery.checkpoint_reentry_manifest",
            producer="forge-app:checkpoint-reentry-v0.1",
            intent=f"prepare {trigger} isolated re-entry for {checkpoint_id}",
            parent_attempt_id=checkpoint_id,
            metadata={
                "schema": REENTRY_SCHEMA,
                "reentry_id": safe_id,
                "trigger": trigger,
                "checkpoint_id": checkpoint_id,
                "manifest_sha256": manifest_sha,
                "source_isolation_status": source_status,
            },
            attempt_id=manifest_attempt_id,
        )
        self.store.append_event(
            "checkpoint_reentry_prepared",
            attempt_id=checkpoint_id,
            payload={
                "reentry_id": safe_id,
                "trigger": trigger,
                "manifest_attempt_id": manifest_attempt_id,
                "manifest_sha256": manifest_sha,
                "source_isolation_status": source_status,
            },
            event_id=f"checkpoint-reentry:{checkpoint_id}:{safe_id}",
        )
        return self._from_existing_manifest(manifest_path)

    def prepare_reentry(
        self,
        checkpoint_id: str,
        *,
        trigger: Literal["manual", "quarantine_auto"] = "manual",
        reentry_id: str | None = None,
    ) -> ReentryPoint:
        if trigger not in TRIGGERS:
            raise ValueError(f"unsupported re-entry trigger: {trigger}")
        view = self.manager.inspect(checkpoint_id)
        if trigger == "quarantine_auto" and not view.quarantined:
            raise ReentryPreparationError(
                f"automatic quarantine re-entry requires quarantined checkpoint: {checkpoint_id} status={view.status}"
            )

        if reentry_id is None:
            reentry_id = (
                f"reentry-quarantine-{_safe_component(checkpoint_id)}"
                if trigger == "quarantine_auto"
                else f"reentry-manual-{_safe_component(checkpoint_id)}-{uuid4().hex}"
            )
        safe_id = _safe_component(reentry_id)
        final_dir = self.reentry_root / safe_id
        manifest_path = final_dir / "reentry_manifest.json"

        payload, raw_payload, attempt = self._read_checkpoint_payload(checkpoint_id)
        payload_sha = _sha256_bytes(raw_payload)

        if manifest_path.exists():
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected = {
                "schema": REENTRY_SCHEMA,
                "reentry_id": safe_id,
                "trigger": trigger,
                "checkpoint_id": checkpoint_id,
                "checkpoint_payload_sha256": payload_sha,
            }
            for key, value in expected.items():
                if existing.get(key) != value:
                    raise ReentryPreparationError(
                        f"existing re-entry manifest conflicts on {key}: expected={value!r} actual={existing.get(key)!r}"
                    )
            return self._seal_manifest(
                checkpoint_id=checkpoint_id,
                trigger=trigger,
                manifest_path=manifest_path,
            )

        final_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_payload_path = final_dir / "checkpoint_payload.json"
        attempt_index_path = final_dir / "attempt_index.json"
        popup_path = final_dir / "operator_popup.json"

        checkpoint_payload_path.write_bytes(raw_payload)
        attempt_index = self._attempt_index(payload)
        attempt_index_path.write_text(
            _canonical_json(
                {
                    "schema": "forge-reentry-attempt-index/0.1",
                    "checkpoint_id": checkpoint_id,
                    "active_attempts": attempt_index,
                    "pending_transaction_ids": list(payload.get("pending_transaction_ids") or ()),
                }
            )
            + "\n",
            encoding="utf-8",
        )

        current_source_head = self._current_source_head()
        source_status, source_dir = self._materialize_source(final_dir, view.source_head)
        popup = self._popup(
            checkpoint_id=checkpoint_id,
            trigger=trigger,
            view=view,
            source_isolation_status=source_status,
            current_source_head=current_source_head,
        )
        popup_path.write_text(_canonical_json(popup.as_dict()) + "\n", encoding="utf-8")

        manifest_attempt_id = f"reentry-manifest-{safe_id}"
        manifest = {
            "schema": REENTRY_SCHEMA,
            "reentry_id": safe_id,
            "trigger": trigger,
            "checkpoint_id": checkpoint_id,
            "checkpoint_generation": view.generation,
            "checkpoint_status": view.status,
            "checkpoint_quarantined": view.quarantined,
            "checkpoint_blob_sha256": str(attempt["blob_sha256"]),
            "checkpoint_payload_sha256": payload_sha,
            "source_head": view.source_head,
            "current_source_head": current_source_head,
            "source_currentness": popup.source_currentness,
            "source_isolation_status": source_status,
            "reentry_dir": str(final_dir),
            "source_dir": source_dir,
            "checkpoint_payload_path": str(checkpoint_payload_path),
            "attempt_index_path": str(attempt_index_path),
            "popup_path": str(popup_path),
            "manifest_path": str(manifest_path),
            "manifest_attempt_id": manifest_attempt_id,
            "popup": popup.as_dict(),
            "authority": "NONE",
            "prepared_at": _utc_now(),
        }
        manifest_bytes = (_canonical_json(manifest) + "\n").encode("utf-8")
        manifest_path.write_bytes(manifest_bytes)
        manifest_sha = _sha256_bytes(manifest_bytes)

        return self._seal_manifest(
            checkpoint_id=checkpoint_id,
            trigger=trigger,
            manifest_path=manifest_path,
        )

    def prepare_manual_reentry(
        self, checkpoint_id: str, *, reentry_id: str | None = None
    ) -> ReentryPoint:
        return self.prepare_reentry(
            checkpoint_id, trigger="manual", reentry_id=reentry_id
        )

    def prepare_quarantined_reentry(self, checkpoint_id: str) -> ReentryPoint:
        return self.prepare_reentry(checkpoint_id, trigger="quarantine_auto")
