"""Forge native-shell and GitHome renderer-neutral frontend contracts."""

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

__all__ = [
    "GitHomeCommandResult",
    "GitHomeInteractionState",
    "GitHomeModel",
    "GitHomeModelError",
    "GitHomeWorkbenchBinding",
    "ProjectEntry",
    "ProjectSnapshot",
    "apply_githome_command",
    "build_githome_model",
    "inspect_project",
    "render_githome_text",
]
