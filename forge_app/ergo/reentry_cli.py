from __future__ import annotations

"""Manual operator surface for checkpoint re-entry v0.1.

The eventual native Ergo UI should call the same CheckpointReentryService. This
CLI exists so the capability is already manually reachable before native UI work.
"""

import argparse
from pathlib import Path

from forge_app.recovery import AttemptStore, ResumeCheckpointManager
from forge_app.recovery.reentry import CheckpointReentryService, OperatorPopup


def render_popup_text(popup: OperatorPopup) -> str:
    lines = [
        f"{popup.title}",
        f"STATUS   {popup.checkpoint_status}",
        f"SEVERITY {popup.severity}",
        f"CHECKPOINT {popup.checkpoint_id}",
        f"GENERATION {popup.generation}",
        f"SOURCE MATCH {popup.source_currentness}",
        f"SOURCE ISOLATION {popup.source_isolation_status}",
        "",
        popup.summary,
        "",
        "ACTIONS",
    ]
    for action in popup.actions:
        state = "AVAILABLE" if action.enabled else "UNAVAILABLE"
        lines.append(f"- {action.action_id}: {action.label} [{state}]")
        lines.append(f"  {action.reason}")
    lines.extend(["", "Quarantine/reputation is unchanged by preparing this re-entry point."])
    return "\n".join(lines) + "\n"


def render_checkpoint_list_text(manager: ResumeCheckpointManager) -> str:
    views = manager.list_checkpoints(limit=500)
    preferred = manager.choose_recovery()
    preferred_id = preferred.checkpoint_id if preferred else None
    lines = ["CHECKPOINTS", "Manual isolated re-entry is available from every listed checkpoint."]
    if not views:
        lines.append("(none)")
    for view in views:
        marker = ">" if view.checkpoint_id == preferred_id else " "
        quarantine = " QUARANTINED" if view.quarantined else ""
        lines.append(
            f"{marker} gen={view.generation:<4} status={view.status:<18} policy={view.resume_policy:<12} {view.checkpoint_id}{quarantine}"
        )
        lines.append(f"  source={view.source_head or 'not recorded'}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare an isolated Forge checkpoint re-entry point")
    parser.add_argument("--store", required=True, help="Attempt Store root")
    parser.add_argument("--reentry-root", required=True, help="Directory for isolated re-entry points")
    parser.add_argument("--checkpoint", default=None, help="Checkpoint ID to prepare")
    parser.add_argument("--list", action="store_true", help="List every checkpoint available for manual re-entry")
    parser.add_argument("--source-repo", default=None, help="Optional active Forge source repository")
    parser.add_argument("--reentry-id", default=None, help="Optional reproducible manual re-entry ID")
    args = parser.parse_args()

    if not args.list and not args.checkpoint:
        parser.error("provide --checkpoint ID or --list")

    store = AttemptStore(Path(args.store))
    manager = ResumeCheckpointManager(store)
    if args.list:
        print(render_checkpoint_list_text(manager), end="")
        if not args.checkpoint:
            return 0

    service = CheckpointReentryService(
        manager,
        reentry_root=Path(args.reentry_root),
        source_repo=Path(args.source_repo) if args.source_repo else None,
    )
    point = service.prepare_manual_reentry(args.checkpoint, reentry_id=args.reentry_id)
    print(render_popup_text(point.popup), end="")
    print(f"REENTRY POINT {point.reentry_dir}")
    print(f"MANIFEST      {point.manifest_path}")
    if point.source_dir:
        print(f"SOURCE         {point.source_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
