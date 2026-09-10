from __future__ import annotations

"""Renderer-neutral Forge Shell Workspace composition v0.1.

The shell binds already-qualified read-only frontend models. It owns focus/layout
state only and deliberately does not mint a combined authority domain.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import shlex
from typing import Any

from forge_app.ergo.recovery_summary import ErgoRecoverySummary
from forge_app.hud.workbench_model import WorkbenchModel, render_workbench_text
from forge_app.shell.githome_model import GitHomeModel, render_githome_text


WORKSPACE_SCHEMA = "forge-shell-workspace/0.1"
WORKSPACE_STATE_SCHEMA = "forge-shell-workspace-state/0.1"
WORKSPACE_PANELS = ("project", "forge", "recovery")
WORKSPACE_LAYOUTS = ("split", "project", "forge", "recovery")


class ForgeShellWorkspaceError(ValueError):
    """Fail-closed invalid workspace composition."""


@dataclass(frozen=True)
class ForgeShellWorkspaceState:
    schema: str = WORKSPACE_STATE_SCHEMA
    active_panel: str = "forge"
    layout: str = "split"

    def __post_init__(self) -> None:
        if self.active_panel not in WORKSPACE_PANELS:
            raise ForgeShellWorkspaceError(f"unsupported active panel: {self.active_panel}")
        if self.layout not in WORKSPACE_LAYOUTS:
            raise ForgeShellWorkspaceError(f"unsupported workspace layout: {self.layout}")


@dataclass(frozen=True)
class WorkspacePanelBinding:
    panel_id: str
    model_sha256: str
    source_identity: str
    currentness: str
    authority: str


@dataclass(frozen=True)
class ForgeShellWorkspaceModel:
    schema: str
    state: ForgeShellWorkspaceState
    policy_mode: str
    source_alignment: str
    semantic_currentness: str
    project_dirty: bool | None
    store_status: str
    recovery_required: bool
    panels: tuple[WorkspacePanelBinding, ...]
    alerts: tuple[str, ...]
    projection_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @property
    def model_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ForgeShellCommandResult:
    accepted: bool
    state: ForgeShellWorkspaceState
    ui_intent: str
    message: str
    consequence_scope: str = "READ_ONLY_UI"


def recovery_summary_sha256(summary: ErgoRecoverySummary) -> str:
    payload = json.dumps(
        summary.as_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_authority(githome: GitHomeModel, workbench: WorkbenchModel, ergo: ErgoRecoverySummary) -> None:
    if githome.project_observer_authority != "NONE" or githome.projection_authority != "NONE":
        raise ForgeShellWorkspaceError("GitHome authority must remain NONE")
    if workbench.source_authority != "NONE" or workbench.projection_authority != "NONE":
        raise ForgeShellWorkspaceError("Workbench authority must remain NONE")
    if ergo.observer_authority != "NONE":
        raise ForgeShellWorkspaceError("Ergo observer authority must remain NONE")


def _validate_githome_workbench_binding(githome: GitHomeModel, workbench: WorkbenchModel) -> None:
    binding = githome.workbench
    if binding is None:
        return
    expected = (
        workbench.model_sha256,
        workbench.source_bundle_id,
        workbench.currentness,
        workbench.projection_authority,
    )
    actual = (
        binding.model_sha256,
        binding.source_bundle_id,
        binding.currentness,
        binding.projection_authority,
    )
    if actual != expected:
        raise ForgeShellWorkspaceError("GitHome Workbench binding does not match supplied Workbench model")


def _source_alignment(githome: GitHomeModel, ergo: ErgoRecoverySummary) -> str:
    source = ergo.source
    if source is None or not source.available or not githome.git_available:
        return "UNKNOWN"
    if source.head is None or githome.head is None:
        return "UNKNOWN"
    return "MATCH" if source.head == githome.head else "MISMATCH"


def build_workspace_model(
    githome: GitHomeModel,
    workbench: WorkbenchModel,
    ergo: ErgoRecoverySummary,
    *,
    state: ForgeShellWorkspaceState | None = None,
) -> ForgeShellWorkspaceModel:
    _validate_authority(githome, workbench, ergo)
    _validate_githome_workbench_binding(githome, workbench)
    state = state or ForgeShellWorkspaceState()
    source_alignment = _source_alignment(githome, ergo)
    policy_mode = "RECOVERY" if ergo.recovery_mode_required else "NORMAL"
    alerts: list[str] = []
    if ergo.recovery_mode_required:
        alerts.append("RECOVERY_REQUIRED")
    if source_alignment == "MISMATCH":
        alerts.append("SOURCE_HEAD_MISMATCH")
    elif source_alignment == "UNKNOWN":
        alerts.append("SOURCE_ALIGNMENT_UNKNOWN")
    if workbench.currentness == "MISMATCH":
        alerts.append("SEMANTIC_CURRENTNESS_MISMATCH")
    elif workbench.currentness == "UNKNOWN":
        alerts.append("SEMANTIC_CURRENTNESS_UNKNOWN")
    if githome.dirty is True:
        alerts.append("PROJECT_DIRTY")
    if githome.scan_errors:
        alerts.append("PROJECT_SCAN_ERRORS")
    if ergo.store_status != "READY":
        alerts.append(f"ATTEMPT_STORE_{ergo.store_status}")

    panels = (
        WorkspacePanelBinding(
            panel_id="project",
            model_sha256=githome.model_sha256,
            source_identity=githome.project_snapshot_sha256,
            currentness=("DIRTY" if githome.dirty else "CLEAN") if githome.dirty is not None else "UNKNOWN",
            authority=githome.projection_authority,
        ),
        WorkspacePanelBinding(
            panel_id="forge",
            model_sha256=workbench.model_sha256,
            source_identity=workbench.source_bundle_id,
            currentness=workbench.currentness,
            authority=workbench.projection_authority,
        ),
        WorkspacePanelBinding(
            panel_id="recovery",
            model_sha256=recovery_summary_sha256(ergo),
            source_identity=ergo.store_path,
            currentness=ergo.store_status,
            authority=ergo.observer_authority,
        ),
    )
    return ForgeShellWorkspaceModel(
        schema=WORKSPACE_SCHEMA,
        state=state,
        policy_mode=policy_mode,
        source_alignment=source_alignment,
        semantic_currentness=workbench.currentness,
        project_dirty=githome.dirty,
        store_status=ergo.store_status,
        recovery_required=ergo.recovery_mode_required,
        panels=panels,
        alerts=tuple(alerts),
    )


def apply_workspace_command(state: ForgeShellWorkspaceState, command: str) -> ForgeShellCommandResult:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        return ForgeShellCommandResult(False, state, "NONE", f"command parse error: {exc}")
    if not tokens:
        return ForgeShellCommandResult(False, state, "NONE", "empty command")
    name = tokens[0].casefold()
    if name == "home" and len(tokens) == 1:
        return ForgeShellCommandResult(True, ForgeShellWorkspaceState(), "RESET_WORKSPACE", "Workspace reset.")
    if name == "focus" and len(tokens) == 2:
        panel = tokens[1].casefold()
        if panel not in WORKSPACE_PANELS:
            return ForgeShellCommandResult(False, state, "NONE", f"unsupported panel: {panel}")
        return ForgeShellCommandResult(
            True,
            ForgeShellWorkspaceState(active_panel=panel, layout=state.layout),
            "FOCUS_PANEL",
            f"Focused {panel}.",
        )
    if name == "layout" and len(tokens) == 2:
        layout = tokens[1].casefold()
        if layout not in WORKSPACE_LAYOUTS:
            return ForgeShellCommandResult(False, state, "NONE", f"unsupported layout: {layout}")
        active = state.active_panel if layout == "split" else layout
        return ForgeShellCommandResult(
            True,
            ForgeShellWorkspaceState(active_panel=active, layout=layout),
            "SET_LAYOUT",
            f"Layout set to {layout}.",
        )
    return ForgeShellCommandResult(False, state, "NONE", f"unsupported read-only workspace command: {name}")


def _binding_map(workspace: ForgeShellWorkspaceModel) -> dict[str, WorkspacePanelBinding]:
    return {panel.panel_id: panel for panel in workspace.panels}


def _validate_render_bindings(
    workspace: ForgeShellWorkspaceModel,
    githome: GitHomeModel,
    workbench: WorkbenchModel,
    ergo: ErgoRecoverySummary,
) -> None:
    bindings = _binding_map(workspace)
    expected = {
        "project": githome.model_sha256,
        "forge": workbench.model_sha256,
        "recovery": recovery_summary_sha256(ergo),
    }
    if set(bindings) != set(expected):
        raise ForgeShellWorkspaceError("workspace panel set does not match required composition")
    for panel_id, model_sha in expected.items():
        if bindings[panel_id].model_sha256 != model_sha:
            raise ForgeShellWorkspaceError(f"workspace {panel_id} binding hash mismatch")


def _recovery_text(ergo: ErgoRecoverySummary, width: int) -> str:
    lines = [
        "ERGO / RECOVERY",
        f"STORE {ergo.store_status}  INTEGRITY {ergo.integrity_ok}  MODE {'RECOVERY' if ergo.recovery_mode_required else 'NORMAL'}",
        f"ATTEMPTS {ergo.attempt_count if ergo.attempt_count is not None else '—'}  BLOBS {ergo.blob_count if ergo.blob_count is not None else '—'}  EVENTS {ergo.event_count if ergo.event_count is not None else '—'}",
    ]
    if ergo.source is not None:
        lines.append(f"SOURCE {ergo.source.branch or '—'}  {(ergo.source.head or '—')[:12]}  DIRTY {ergo.source.dirty}")
    for reason in ergo.reasons:
        lines.append("! " + reason)
    return "\n".join(line if len(line) <= width else line[: max(0, width - 1)] + "…" for line in lines) + "\n"


def render_workspace_text(
    workspace: ForgeShellWorkspaceModel,
    *,
    githome: GitHomeModel,
    workbench: WorkbenchModel,
    ergo: ErgoRecoverySummary,
    width: int = 110,
) -> str:
    _validate_render_bindings(workspace, githome, workbench, ergo)
    width = max(72, min(int(width), 180))
    header = [
        "SINGULARITY WORKS // FORGE SHELL",
        f"LAYOUT {workspace.state.layout}  FOCUS {workspace.state.active_panel}  POLICY {workspace.policy_mode}",
        f"SOURCE ALIGNMENT {workspace.source_alignment}  SEMANTIC CURRENTNESS {workspace.semantic_currentness}",
        f"SHELL AUTHORITY {workspace.projection_authority}",
        "ALERTS " + (" · ".join(workspace.alerts) if workspace.alerts else "none"),
        "═" * width,
    ]
    sections: list[str] = []
    layout = workspace.state.layout
    if layout in {"split", "project"}:
        sections.append(render_githome_text(githome, width=width, row_limit=10).rstrip())
    if layout in {"split", "forge"}:
        sections.append(render_workbench_text(workbench, width=width, node_limit=10).rstrip())
    if layout in {"split", "recovery"}:
        sections.append(_recovery_text(ergo, width).rstrip())
    separator = "\n" + ("═" * width) + "\n"
    return "\n".join(header) + "\n" + separator.join(sections) + "\n"
