#!/usr/bin/env python3
"""
Singularity Works — PreToolUse Hook
Fires before every Claude Code tool execution.

Rules:
  - Bash: block dangerous patterns (rm -rf on project root, DROP TABLE, etc.)
  - git commit: block unless .forge/battery_passed sentinel exists
  - Write/Edit: log to evidence ledger for audit trail

Exit codes:
  0 → allow (with optional additionalContext)
  2 → BLOCK — stderr fed back to Claude as error message
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Patterns that always block regardless of context
_HARD_BLOCK_BASH = [
    (r"\brm\s+-rf\s+/\b",          "rm -rf on root filesystem blocked"),
    (r"\bDROP\s+TABLE\b",           "DROP TABLE blocked — use migrations"),
    (r"\btruncate\s+/dev/",         "truncate on device blocked"),
    (r">\s*/etc/passwd",            "write to /etc/passwd blocked"),
    (r"\bchmod\s+777\s+/",          "chmod 777 on root blocked"),
]

# Warn but don't block (additionalContext injected)
_SOFT_WARN_BASH = [
    (r"\bgit\s+push\s+.*--force\b", "force push detected — verify intentional"),
    (r"\bpip\s+install\b",           "pip install — ensure --break-system-packages if needed"),
]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name == "Bash":
        _handle_bash(tool_input.get("command", ""))
    elif tool_name in ("Write", "Edit", "MultiEdit"):
        _handle_write(tool_input, tool_name)
    else:
        sys.exit(0)


def _handle_bash(command: str) -> None:
    # Hard blocks
    for pattern, reason in _HARD_BLOCK_BASH:
        if re.search(pattern, command, re.IGNORECASE):
            print(reason, file=sys.stderr)
            sys.exit(2)

    # git commit gate — require battery_passed sentinel
    if re.search(r"\bgit\s+commit\b", command):
        sentinel = Path(".forge") / "battery_passed"
        if not sentinel.exists():
            msg = (
                "FORGE GATE: git commit blocked.\n"
                "Run forge_commit_verified (MCP) or verify_build.py first.\n"
                "Battery must pass (49/49) before committing."
            )
            print(msg, file=sys.stderr)
            sys.exit(2)
        # Consume sentinel — one commit per pass
        sentinel.unlink(missing_ok=True)
        sys.exit(0)

    # Soft warns
    warnings = []
    for pattern, warn in _SOFT_WARN_BASH:
        if re.search(pattern, command, re.IGNORECASE):
            warnings.append(warn)

    if warnings:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": "FORGE WARNING: " + "; ".join(warnings),
            }
        }
        print(json.dumps(output))

    sys.exit(0)


def _handle_write(tool_input: dict, tool_name: str) -> None:
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    # Block writes to critical files
    blocked = [".forge/evidence.jsonl", "configs/seed_genome.json"]
    for b in blocked:
        if file_path.endswith(b):
            print(f"FORGE GATE: direct write to {b} blocked — use forge tools", file=sys.stderr)
            sys.exit(2)

    # Log write to forge audit trail (best-effort, non-blocking)
    _log_write(file_path, tool_name)
    sys.exit(0)


def _log_write(file_path: str, tool_name: str) -> None:
    try:
        import time
        ledger = Path(".forge") / "write_audit.jsonl"
        ledger.parent.mkdir(exist_ok=True)
        entry = json.dumps({
            "ts": time.time(),
            "tool": tool_name,
            "file": file_path,
        })
        with ledger.open("a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    main()
