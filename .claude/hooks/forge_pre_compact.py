#!/usr/bin/env python3
"""
Singularity Works — PreCompact Hook
Fires before Claude Code compacts the context window.

Actions:
  1. Backup raw transcript → ~/.forge/transcripts/
  2. Snapshot evidence ledger
  3. Inject Live Shadow as additionalContext so compacted
     summary preserves PCMMAD state, not just chat highlights

Exit codes:
  0 → proceed with compaction (additionalContext injected)
  2 → block compaction (shouldn't normally happen)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # No input — let compaction proceed
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path", "")
    trigger = data.get("trigger", "unknown")

    # ── 1. Backup transcript ──────────────────────────────────────────
    backup_root = Path.home() / ".forge" / "transcripts"
    backup_root.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backed_up = False

    if transcript_path and Path(transcript_path).exists():
        dst = backup_root / f"session_{session_id[:8]}_{ts}.jsonl"
        try:
            import shutil
            shutil.copy2(transcript_path, dst)
            backed_up = True
        except OSError:
            pass  # Non-fatal — proceed anyway

    # ── 2. Snapshot evidence ledger ───────────────────────────────────
    ledger_path = Path(".forge") / "evidence.jsonl"
    if ledger_path.exists():
        ledger_dst = backup_root / f"ledger_{session_id[:8]}_{ts}.jsonl"
        try:
            import shutil
            shutil.copy2(ledger_path, ledger_dst)
        except OSError:
            pass

    # ── 3. Load Live Shadow ───────────────────────────────────────────
    shadow_text = _load_live_shadow()

    # ── 4. Emit output ────────────────────────────────────────────────
    # additionalContext is injected into Claude's compaction summary prompt
    # so the resulting compact preserves forge state, not just chat highlights.
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "additionalContext": shadow_text,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def _load_live_shadow() -> str:
    """Load Live Shadow from PCMMAD state or synthesize fallback."""
    candidates = [
        Path("state/pcmmad/10A SHALL_INIT_LIVE_SHADOW_NEXT.md"),
        Path(".forge/live_shadow.md"),
        Path("CLAUDE.md"),
    ]

    for p in candidates:
        if p.exists():
            try:
                content = p.read_text(encoding="utf-8")
                if len(content.strip()) > 100:
                    return (
                        "=== SINGULARITY WORKS FORGE — LIVE SHADOW ===\n"
                        "PRESERVE THIS STATE IN THE COMPACTED SUMMARY.\n\n"
                        + content[:4000]  # Cap to avoid ballooning the prompt
                    )
            except OSError:
                continue

    # Fallback — synthesize from evidence ledger if it exists
    ledger = Path(".forge") / "evidence.jsonl"
    if ledger.exists():
        try:
            lines = ledger.read_text(encoding="utf-8").strip().splitlines()
            recent = lines[-10:]
            return (
                "=== FORGE EVIDENCE LEDGER (last 10 entries) ===\n"
                "PRESERVE FORGE STATE IN COMPACTED SUMMARY.\n\n"
                + "\n".join(recent)
            )
        except OSError:
            pass

    return (
        "=== SINGULARITY WORKS FORGE ===\n"
        "IMPORTANT: This session uses the Forge security verification system.\n"
        "Preserve: battery status (49/49), active requirements, open seams, "
        "and any verified/red findings in the compacted summary.\n"
        "Do not collapse security evidence into generic 'coding session' summaries."
    )


if __name__ == "__main__":
    main()
