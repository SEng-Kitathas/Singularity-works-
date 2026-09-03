from __future__ import annotations

"""Minimal Ergo presentation tier.

This is a reference renderer for the launch model, not the final Forge shell.
It proves that recovery/launch semantics are independent of GPU/UI backend.
"""

import argparse
from pathlib import Path

from .launch_model import build_launch_model, render_minimal_text
from .recovery_summary import build_recovery_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Ergo recovery state in the minimal tier")
    parser.add_argument("--store", required=True, help="Attempt Store root")
    parser.add_argument("--source-repo", default=None, help="Optional Forge source repository")
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--recent", type=int, default=6)
    args = parser.parse_args()

    summary = build_recovery_summary(
        Path(args.store),
        source_repo=Path(args.source_repo) if args.source_repo else None,
        latest_limit=max(0, args.recent),
    )
    model = build_launch_model(summary, recent_limit=max(0, args.recent))
    print(render_minimal_text(model, width=args.width), end="")
    return 2 if model.posture == "RECOVERY_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
