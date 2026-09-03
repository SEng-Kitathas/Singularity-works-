from __future__ import annotations

"""Renderer-neutral Ergo launch model v0.1.

This module converts read-only recovery facts into a deterministic presentation
contract. It does not execute launch actions, mutate recovery state, or confer
truth/authority from visual status.
"""

from dataclasses import dataclass, asdict
import json
from typing import Any, Iterable

from .checkpoint_summary import ErgoCheckpointSummary
from .recovery_summary import ErgoRecoverySummary


LAUNCH_MODEL_SCHEMA = "forge-ergo-launch-model/0.1"


@dataclass(frozen=True)
class LaunchFact:
    key: str
    label: str
    value: str
    state: str = "NEUTRAL"


@dataclass(frozen=True)
class LaunchMode:
    mode_id: str
    label: str
    enabled: bool
    recommended: bool
    reason: str


@dataclass(frozen=True)
class RecentAttempt:
    attempt_id: str
    artifact_class: str
    intent: str
    blob_sha256: str
    parent_attempt_id: str | None
    created_at: str


@dataclass(frozen=True)
class ErgoLaunchModel:
    schema: str
    title: str
    subtitle: str
    posture: str
    posture_reason: str
    observer_authority: str
    facts: tuple[LaunchFact, ...]
    modes: tuple[LaunchMode, ...]
    recent_attempts: tuple[RecentAttempt, ...]
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )


def _short_hash(value: str | None, length: int = 12) -> str:
    if not value:
        return "—"
    return value[:length]


def _display_count(value: int | None) -> str:
    return "—" if value is None else str(value)


def _source_state(summary: ErgoRecoverySummary) -> tuple[str, str]:
    source = summary.source
    if source is None:
        return "UNKNOWN", "Source repository was not inspected"
    if not source.available:
        return "BLOCKED", "Source repository unavailable"
    if source.dirty:
        return "CAUTION", "Source repository has uncommitted changes"
    return "READY", "Source repository is clean"


def _posture(summary: ErgoRecoverySummary) -> tuple[str, str]:
    if summary.recovery_mode_required:
        return "RECOVERY_REQUIRED", "Durable state requires recovery inspection before normal launch"
    source_state, source_reason = _source_state(summary)
    if source_state in {"BLOCKED", "CAUTION", "UNKNOWN"}:
        return "CAUTION", source_reason
    if summary.store_status == "READY" and summary.integrity_ok is True:
        return "READY", "Durable recovery state and source inspection are ready"
    return "CAUTION", "Launch state contains unresolved evidence"


def _modes(summary: ErgoRecoverySummary) -> tuple[LaunchMode, ...]:
    recovery_required = bool(summary.recovery_mode_required)
    return (
        LaunchMode(
            mode_id="normal",
            label="Normal",
            enabled=bool(summary.normal_mode_allowed),
            recommended=bool(summary.normal_mode_allowed and not recovery_required),
            reason=(
                "Durable state permits normal launch"
                if summary.normal_mode_allowed
                else "Normal launch blocked by recovery state"
            ),
        ),
        LaunchMode(
            mode_id="safe",
            label="Safe",
            enabled=bool(summary.safe_mode_available),
            recommended=False,
            reason=(
                "Reduced-risk launch path remains available"
                if summary.safe_mode_available
                else "Safe launch path unavailable"
            ),
        ),
        LaunchMode(
            mode_id="recovery",
            label="Recovery",
            enabled=True,
            recommended=recovery_required,
            reason=(
                "Recovery inspection is required"
                if recovery_required
                else "Recovery inspection is available but not required"
            ),
        ),
    )


def _checkpoint_state(summary: ErgoCheckpointSummary) -> str:
    if summary.status == "READY":
        return "READY"
    if summary.status in {"CAUTION", "RECOVERY_REQUIRED"}:
        return "CAUTION"
    if summary.status in {"MISSING", "UNREADABLE", "DEGRADED"}:
        return "BLOCKED"
    return "UNKNOWN"


def build_launch_model(
    summary: ErgoRecoverySummary,
    *,
    recent_limit: int = 6,
    checkpoint_summary: ErgoCheckpointSummary | None = None,
) -> ErgoLaunchModel:
    posture, posture_reason = _posture(summary)
    source = summary.source
    source_state, _ = _source_state(summary)

    source_branch = source.branch if source and source.branch else "—"
    source_head = _short_hash(source.head if source else None)
    source_clean = (
        "yes"
        if source and source.available and source.dirty is False
        else "no"
        if source and source.available and source.dirty is True
        else "unknown"
    )

    facts_list = [
        LaunchFact("store_status", "Recovery store", summary.store_status, "READY" if summary.store_status == "READY" else "BLOCKED"),
        LaunchFact("integrity", "Integrity", "ok" if summary.integrity_ok is True else "unknown" if summary.integrity_ok is None else "failed", "READY" if summary.integrity_ok is True else "BLOCKED"),
        LaunchFact("journal_mode", "Journal", summary.journal_mode or "—", "NEUTRAL"),
        LaunchFact("attempt_count", "Preserved attempts", _display_count(summary.attempt_count), "NEUTRAL"),
        LaunchFact("event_count", "Journal events", _display_count(summary.event_count), "NEUTRAL"),
        LaunchFact("source_branch", "Source branch", source_branch, source_state),
        LaunchFact("source_head", "Source HEAD", source_head, source_state),
        LaunchFact("source_clean", "Source clean", source_clean, source_state),
    ]
    checkpoint_reasons: tuple[str, ...] = ()
    if checkpoint_summary is not None:
        cp_state = _checkpoint_state(checkpoint_summary)
        facts_list.extend(
            [
                LaunchFact(
                    "resume_checkpoint",
                    "Resume checkpoint",
                    checkpoint_summary.selected_status or checkpoint_summary.status,
                    cp_state,
                ),
                LaunchFact(
                    "resume_generation",
                    "Resume generation",
                    _display_count(checkpoint_summary.selected_generation),
                    cp_state,
                ),
                LaunchFact(
                    "resume_policy",
                    "Resume policy",
                    checkpoint_summary.selected_resume_policy or "—",
                    cp_state,
                ),
                LaunchFact(
                    "resume_source_head",
                    "Resume source HEAD",
                    _short_hash(checkpoint_summary.selected_source_head),
                    cp_state,
                ),
                LaunchFact(
                    "resume_core_snapshot",
                    "Core semantic snapshot",
                    _short_hash(checkpoint_summary.selected_semantic_snapshot_id)
                    if checkpoint_summary.selected_semantic_snapshot_id
                    else "not bridged",
                    "READY" if checkpoint_summary.selected_semantic_snapshot_id else "UNKNOWN",
                ),
            ]
        )
        checkpoint_reasons = tuple(checkpoint_summary.reasons)
    facts = tuple(facts_list)

    attempts = tuple(
        RecentAttempt(
            attempt_id=str(item.get("attempt_id", "")),
            artifact_class=str(item.get("artifact_class", "")),
            intent=str(item.get("intent", "")),
            blob_sha256=str(item.get("blob_sha256", "")),
            parent_attempt_id=item.get("parent_attempt_id"),
            created_at=str(item.get("created_at", "")),
        )
        for item in summary.latest_attempts[: max(0, recent_limit)]
    )

    return ErgoLaunchModel(
        schema=LAUNCH_MODEL_SCHEMA,
        title="ERGO // FORGE",
        subtitle="Boot · Integrity · Recovery · Launch",
        posture=posture,
        posture_reason=posture_reason,
        observer_authority=summary.observer_authority,
        facts=facts,
        modes=_modes(summary),
        recent_attempts=attempts,
        reasons=tuple(summary.reasons) + checkpoint_reasons,
    )


def _truncate(value: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(value) <= width:
        return value
    if width == 1:
        return "…"
    return value[: width - 1] + "…"


def _rule(width: int, char: str = "─") -> str:
    return char * max(1, width)


def render_minimal_text(model: ErgoLaunchModel, *, width: int = 80) -> str:
    """Render the first-class minimal tier with no ANSI/GPU assumptions."""
    width = max(48, min(int(width), 160))
    lines: list[str] = []

    def add(value: str = "") -> None:
        lines.append(_truncate(value, width))

    add(model.title)
    add(model.subtitle)
    add(_rule(width))
    add(f"POSTURE  {model.posture}")
    add(model.posture_reason)
    add(f"AUTHORITY {model.observer_authority}")
    add()
    add("SYSTEM")
    for fact in model.facts:
        add(f"[{fact.state:<7}] {fact.label:<20} {fact.value}")

    add()
    add("LAUNCH MODES")
    for mode in model.modes:
        marker = ">" if mode.recommended else " "
        enabled = "AVAILABLE" if mode.enabled else "BLOCKED"
        add(f"{marker} {mode.label:<10} {enabled:<9} {mode.reason}")

    if model.reasons:
        add()
        add("REASONS")
        for reason in model.reasons:
            add(f"- {reason}")

    add()
    add("RECENT PRESERVED WORK")
    if not model.recent_attempts:
        add("(none)")
    else:
        for attempt in model.recent_attempts:
            add(f"{_short_hash(attempt.attempt_id, 18):<18} {attempt.artifact_class}")
            add(f"  {_truncate(attempt.intent, max(8, width - 2))}")

    add(_rule(width))
    add("Ergo is observing durable state.")
    add("Presentation does not create truth.")
    return "\n".join(lines) + "\n"
