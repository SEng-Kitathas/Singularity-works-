"""Forge native-shell, GitHome, and workspace renderer-neutral frontend contracts."""

from .githome_model import (
    GitHomeCommandResult,
    GitHomeInteractionState,
    GitHomeModel,
    GitHomeModelError,
    GitHomeWorkbenchBinding,
    ProjectEntry,
    ProjectSnapshot,
    apply_githome_command,
    build_githome_model,
    inspect_project,
    render_githome_text,
)
from .workspace_model import (
    ForgeShellCommandResult,
    ForgeShellWorkspaceError,
    ForgeShellWorkspaceModel,
    ForgeShellWorkspaceState,
    WorkspacePanelBinding,
    apply_workspace_command,
    build_workspace_model,
    recovery_summary_sha256,
    render_workspace_text,
)

__all__ = [
    "ForgeShellCommandResult",
    "ForgeShellWorkspaceError",
    "ForgeShellWorkspaceModel",
    "ForgeShellWorkspaceState",
    "GitHomeCommandResult",
    "GitHomeInteractionState",
    "GitHomeModel",
    "GitHomeModelError",
    "GitHomeWorkbenchBinding",
    "ProjectEntry",
    "ProjectSnapshot",
    "WorkspacePanelBinding",
    "apply_githome_command",
    "apply_workspace_command",
    "build_githome_model",
    "build_workspace_model",
    "inspect_project",
    "recovery_summary_sha256",
    "render_githome_text",
    "render_workspace_text",
]
