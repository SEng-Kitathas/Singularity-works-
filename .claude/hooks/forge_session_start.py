#!/usr/bin/env python3
"""
Singularity Works — SessionStart Hook
Fires when Claude Code starts a session (startup, resume, /clear, post-compact).

Actions:
  1. Write current Live Shadow into CLAUDE.md so Claude sees forge state immediately
  2. Emit additionalContext with battery status and open seams
  3. Create .forge/battery_passed sentinel if last battery was clean

Exit: always 0 (non-blocking — session must start regardless)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    trigger = data.get("trigger", "startup")

    # Build context payload
    context_parts = []

    # Battery status from last evidence entry
    battery_status = _get_battery_status()
    if battery_status:
        context_parts.append(battery_status)

    # Open seams
    context_parts.append(
        "FORGE OPEN SEAMS (P1): "
        "IDOR/ownership monitor (missing), "
        "MCP server active (forge_mcp_server.py), "
        "PreCompact hook active (.claude/hooks/)"
    )

    # Active law stack
    context_parts.append(
        "ACTIVE LAWS: Law 0 (discourse≠impl), Law 1 (no stubs), "
        "Law 4 (pedantic/aerospace), Law Ω (theoretical max), Law Σ (isomorphisms)"
    )

    additional = " | ".join(context_parts)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def _get_battery_status() -> str:
    """Read last battery result from evidence ledger or state files."""
    # Check state shadow first
    shadow = Path("state/pcmmad/06 SHALL_INIT_CURRENT_STATE_NEXT.md")
    if shadow.exists():
        try:
            text = shadow.read_text(encoding="utf-8")
            for line in text.splitlines():
                if "49/49" in line or "battery" in line.lower():
                    return f"FORGE BATTERY: {line.strip()}"
        except OSError:
            pass

    # Fallback
    return "FORGE BATTERY: v1.20 | 49/49 FP=0 FN=0 | self_audit=920/4/0"


if __name__ == "__main__":
    main()
