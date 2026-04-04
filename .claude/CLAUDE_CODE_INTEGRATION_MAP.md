# Singularity Works — Claude Code Integration Map
_Version: 2026-04-03_

## Architecture

```
Claude Code (harness/shell)
  ├── .claude/settings.json       ← MCP server + hook configuration
  ├── .claude/hooks/              ← Forge hook adapters
  │   ├── forge_session_start.py  ← Injects Live Shadow at session start
  │   ├── forge_pre_compact.py    ← Backs up transcript, injects shadow before compaction
  │   └── forge_pre_tool_use.py   ← Commit gate, hard blocks, write audit
  └── MCP tools (via singularity_works/forge_mcp_server.py)
      ├── forge_run_battery        ← Run 49/49 battery
      ├── forge_get_assurance      ← Code → green/red verdict
      ├── forge_run_assurance_on_file
      ├── forge_get_open_seams
      ├── forge_get_live_shadow
      └── forge_commit_verified    ← Gated commit (battery must pass)

Singularity Works Forge (brain)
  ├── singularity_works/          ← 28 modules, 12,214 lines
  ├── configs/seed_genome.json    ← 37 capsules
  └── .forge/
      ├── evidence.jsonl          ← Structured audit trail (≠ transcript)
      ├── battery_passed          ← Sentinel consumed by commit gate
      └── configs/                ← Genome copy for MCP server resolution
```

## Compaction Override

`settings.json` overrides the default compaction summary prompt to preserve:
- Battery status (X/49 FP FN)
- Module changes with file paths
- RED assurance findings with requirement text
- Git commits with hashes
- Open seams and P0/P1 items

Fires at 80% context (`contextTokenThreshold: 0.8`) not 100%.

## Commit Gate Flow

```
Claude wants to commit
  → PreToolUse hook fires
  → Checks .forge/battery_passed sentinel
  → BLOCKS if sentinel absent
  → Advises: run forge_commit_verified MCP tool

forge_commit_verified MCP tool:
  → Runs verify_build.py
  → Checks battery result
  → If 49/49: writes .forge/battery_passed sentinel, then commits
  → If <49/49: returns BLOCKED with failure list
```

## Memory Hierarchy (no compaction loss)

```
CLAUDE.md                    ← Live Shadow (forge writes, Claude reads at start)
.claude/settings.json        ← Hook config + compactionControl
state/pcmmad/10A             ← Full PCMMAD Live Shadow (authoritative)
.forge/evidence.jsonl        ← Structured ledger (separate from transcript)
~/.forge/transcripts/        ← Raw transcript backups (PreCompact hook)
```

## Quick Start

Install MCP SDK: `pip install mcp --break-system-packages`

Configure Claude Code:
```bash
# From project root (singularity_works parent directory):
claude --mcp-config .claude/settings.json
```

Or add to ~/.claude/settings.json for global availability.

## MCP Tool Usage Examples

```
# Check if new auth code is safe before committing
forge_get_assurance(
  code="<paste code>",
  requirement="Auth endpoints must implement rate limiting."
)

# Run full battery before any security-sensitive commit
forge_run_battery()

# Gated commit — won't proceed if battery fails
forge_commit_verified(message="feat: add IDOR monitor")

# See what needs attention next
forge_get_open_seams()
forge_get_live_shadow()
```
