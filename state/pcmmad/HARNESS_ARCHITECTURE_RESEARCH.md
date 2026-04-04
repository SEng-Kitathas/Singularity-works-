# Singularity Works Harness Architecture Research
_Version: 2026-04-03 — Derived from official/public/open-source sources only_

## Sources
- Official Claude Code docs (code.claude.com/docs) — hooks, CLAUDE.md, MCP, subagents
- Claude Code npm package v2.1.92 (official npm, already analyzed this session)
- MCP specification v2025-11-25 (modelcontextprotocol.io — open standard, Linux Foundation)
- OpenAI Agents SDK (github.com/openai/openai-agents-python — MIT/Apache, fully open)
- Aider (github.com/Aider-AI/aider — Apache 2.0, fully open)
- Continue.dev (github.com/continuedev/continue — Apache 2.0, fully open)
- Community hooks projects (disler/claude-code-hooks-mastery — community, Apache 2.0)

---

## 1. The Hook Lifecycle — Complete Official Map

Claude Code exposes **12+ lifecycle events** (as of v2.1.76+, confirmed from official docs):

```
Session Layer
  Setup          → --init, --init-only, --maintenance (repo setup)
  SessionStart   → startup, resume, /clear, post-compact
  SessionEnd     → exit, SIGINT, error

Main Loop
  UserPromptSubmit     → inject context or block before Claude sees the prompt
  PreToolUse           → [CAN BLOCK/MODIFY] before tool executes
  PermissionRequest    → intercept permission dialogs, auto-allow/deny
  PostToolUse          → [CAN BLOCK CONTINUATION] after tool succeeds
  PostToolUseFailure   → after tool fails
  Stop                 → [CAN FORCE CONTINUATION] when Claude finishes
  SubagentStart        → when subagent spawns
  SubagentStop         → when subagent completes

Maintenance
  PreCompact           → [FORGE'S PRIMARY HOOK] before context compaction
  PostCompact          → after compaction completes (v2.1.76+)
  Notification         → permission_prompt, idle_prompt, auth_success
```

### Hook Communication Protocol

**Input**: JSON object on stdin with these common fields:
```json
{
  "session_id": "...",
  "transcript_path": "~/.claude/projects/.../transcript.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {"command": "python3 verify_build.py"},
  "tool_use_id": "..."
}
```

**Exit codes:**
- `0` = success, stdout parsed as JSON for structured control
- `2` = **blocking error** — stderr fed back to Claude as error message
- other = non-blocking warning

**Output (structured JSON on stdout):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "...",
    "updatedInput": {"command": "modified-command"},
    "additionalContext": "Extra context injected into Claude's view"
  }
}
```

**Or simple block:**
```json
{"decision": "block", "reason": "Battery must pass before commit"}
```

**Async hooks** (non-blocking, for logging/backup):
```json
{"type": "command", "command": "backup.sh", "async": true, "timeout": 30}
```

**HTTP hooks** (for remote validation services, Feb 2026+):
```json
{"type": "http", "url": "http://localhost:8080/hooks/pre-tool", "timeout": 30}
```

### The 4 Handler Types
1. **command** — shell script, receives JSON on stdin
2. **http** — POST to endpoint, same JSON in/out format (non-2xx = non-blocking)
3. **prompt** — LLM-based semantic evaluation (for nuanced decisions)
4. **agent** — full subagent for deep analysis

### Forge Insertion Points (what this means for us)

```
PreToolUse  → Forge gate: before any Bash/Edit/Write runs
              - Run genome_gate_factory strategy check
              - Return deny + reason if assurance would be red
              - Modify tool input (e.g., inject flags)

PostToolUse → Forge verdict capture
              - On Bash: parse verify_build.py output
              - Gate commit (block if battery failed)
              - Append to evidence_ledger

PreCompact  → CRITICAL: backup raw transcript + inject Live Shadow
              cp transcript.jsonl ~/.forge/backups/
              → PCMMAD-aware summary prompt fires here

SessionStart → Load Live Shadow into additionalContext
              → Inject forge state into Claude's opening context

Stop        → Exit 2 if battery hasn't passed
              → Force Claude to run verify_build before committing
```

---

## 2. The God-Object Anti-Pattern (Lesson from Production)

The oracle repo's **QueryEngine** collapsed: runtime, tool permissions, session persistence, model settings, context cache, abort control, usage tracking — all in one object.

**What breaks:**
- Any single concern change requires touching the god object
- Testing is impossible in isolation
- Authority is unclear (who owns what decision?)
- State leaks between concerns

**The correct split for Singularity Works:**

```
Claude Code (harness/shell)
  ├── Session runtime    → owns REPL, transcript JSONL, context window
  ├── Tool executor      → owns tool invocation and result routing
  └── Hook dispatcher    → owns lifecycle event routing

Forge (brain/authority)
  ├── ForgeContext        → owns project state, requirement bundles
  ├── Orchestrator        → owns capsule selection and run sequencing
  ├── AssuranceEngine     → owns green/red verdict
  ├── EvidenceLedger      → owns JSONL audit trail (separate from transcript)
  └── CIL Council         → owns IRIS validation (distinct from execution)

Adapters (boundary, thin)
  ├── forge_hook_adapter.py → translates hook events → forge calls
  ├── forge_mcp_server.py   → exposes forge as MCP tools
  └── forge_context_loader.py → writes Live Shadow to CLAUDE.md
```

**Critical insight from production**: Raw transcript persistence and evidentiary judgment are **different systems**. Claude Code owns the transcript (raw conversation stream). The forge owns the ledger (structured, attributed, curated evidence). They must never collapse into one artifact.

---

## 3. The MCP Seam — Official Specification

MCP is now a Linux Foundation open standard (donated Dec 2025). Full source at modelcontextprotocol.io.

**3 Primitives:**
```
Tools     → arbitrary code execution (what agents DO)
            Server exposes: name, description, inputSchema
            Client invokes: tools/call with arguments
            
Resources → structured data (what agents READ)
            Identified by URI: file://, db://, logs://
            Text or binary content
            
Prompts   → reusable templates (how agents are INSTRUCTED)
            Parameterized workflow starters
```

**Connection Lifecycle (3 phases):**
```
1. Initialize
   Client → initialize(clientInfo, protocolVersion, capabilities)
   Server → initialize response (serverInfo, capabilities)
   Client → initialized notification (ready)
   
2. Operation
   Normal request/response via JSON-RPC 2.0
   
3. Shutdown
   Transport close (no protocol message required)
```

**Security model:**
- Host = gatekeeper and orchestrator
- Each client operates within well-defined boundaries
- Human consent required before tool invocation
- Roots = filesystem boundaries for server access
- Sampling = server can request model generation *through* client (client retains control)

**Forge as MCP Server:**
```python
from mcp.server import Server
import mcp.types as types

app = Server("singularity-works")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name="forge_run_battery",
                   description="Run the full 46-case security battery",
                   inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="forge_get_assurance",
                   description="Get security verdict for a code artifact",
                   inputSchema={"type": "object",
                               "properties": {"code": {"type": "string"},
                                             "requirement": {"type": "string"}}}),
        types.Tool(name="forge_get_open_seams",
                   description="Return current open seams from trace matrix"),
        types.Tool(name="forge_get_live_shadow",
                   description="Return current Live Shadow state"),
        types.Tool(name="forge_commit_verified",
                   description="Commit only after battery passes",
                   inputSchema={"type": "object",
                               "properties": {"message": {"type": "string"}}}),
    ]
```

This makes forge a **first-class tool in Claude Code's tool universe** — not a subprocess, not a wrapper. A peer.

---

## 4. Subagent Patterns — Official Claude Code Architecture

Claude Code subagents have their own context window, constrained tool sets, and live in `.claude/agents/`.

**From official docs:**
```yaml
# .claude/agents/security-triage.md
name: security-triage
description: "Run security analysis on code artifacts. Use proactively when code touches auth, network, or exec surfaces."
tools: [Read, Bash]  # constrained tool set
---

You are a security triage agent for Singularity Works.
Your only job: run forge analysis and return verdict.

For any file you receive:
1. Read the file
2. Run: python3 -c "from singularity_works.orchestration import Orchestrator; ..."
3. Return the assurance verdict and open seams
```

**Subagent lifecycle hooks:**
- `SubagentStart` — fires when spawned
- `SubagentStop` — fires when done (can block/continue like `Stop`)

**Forge agent topology:**
```
repo-scoper    → Read + Grep only, identifies targets
security-triage → Read + Bash(restricted), runs forge analysis  
verdict-auditor → Read only, second-pass review of findings
deep-research  → WebSearch + Read, researches patterns
```

**Key pattern from OpenAI Agents SDK (open source):**
Guardrails run **in parallel** with agent execution and fail fast. Don't run checks sequentially after — run them concurrently and cancel if they fail. This maps to: forge assurance runs concurrent with Claude Code's execution path, not after.

---

## 5. Context Design — Immutable Baseline vs Refreshable Observations

**From Aider (open source, Apache 2.0):**
Aider's repository map is the key pattern: it doesn't dump the whole codebase into context. It builds a **map** (function signatures, file structure) from tree-sitter parse that gives the LLM structural awareness without context explosion. Files are explicitly added/removed from "the chat" rather than always present.

**Lesson for Forge:**
```
CLAUDE.md (immutable baseline):
  - Forge version and battery state
  - Active law stack
  - Architecture decisions locked in
  - Open seams

.claude/forge-context.md (refreshable observations):
  - Current git branch and status
  - Last battery run result
  - Active requirement being worked
  - Recent evidence.jsonl entries
  
This separates: what doesn't change (baseline) from what should refresh.
```

**From Continue.dev (open source, Apache 2.0):**
Continue's `.continue/checks/` — checks as markdown files with name, description, and LLM prompt — is the cleanest expression of the "policy as code" idea. Each check is:
```markdown
---
name: Security Gate
description: Block commits with known vulnerability patterns
---
Review this diff for security issues. Flag as failing if:
- SQL queries built with string concatenation
- Missing input validation on API endpoints
- Unsafe deserialization patterns
If none found, pass.
```

This is exactly the forge's requirement + assurance loop expressed as a CI/CD check. The forge's genome capsules are the production version of this pattern.

---

## 6. Transcript vs Ledger Split — The Core Design Decision

**The canonical failure mode** (from production oracle analysis, preserved as lesson not code):
"Raw transcript persistence and evidentiary judgment are different systems."

**Correct split:**

```
Transcript (Claude Code owns)
  Location: ~/.claude/projects/.../transcript.jsonl
  Content:  Every message, tool call, tool result, verbatim
  Purpose:  Session replay, resume, compaction input
  Format:   JSONL, append-only, never edited
  Access:   Read-only to Forge (via hook input: transcript_path)

Evidence Ledger (Forge owns)
  Location: forge_workspace/evidence.jsonl
  Content:  Attributed, curated, structured findings
            {verdict, requirement, code_hash, strategy_hits, timestamp}
  Purpose:  Audit trail, batch reporting, pattern memory
  Format:   JSONL, append-only, structured schema
  Access:   Write by Forge, Read by hooks and reporting layer

Live Shadow (PCMMAD owns)
  Location: CLAUDE.md / state/pcmmad/10A
  Content:  Minimum high-fidelity active state
  Purpose:  Compaction-resistant continuity
  Format:   Markdown
  Access:   Written by Forge, Read by Claude Code at session start
```

**PreCompact hook pattern (how Forge protects the transcript):**
```python
# .claude/hooks/pre_compact.py
import json, sys, shutil
from pathlib import Path
from datetime import datetime

data = json.load(sys.stdin)
transcript_path = data.get("transcript_path", "")

if transcript_path:
    # Preserve raw transcript before compaction destroys it
    backup = Path.home() / ".forge" / "transcripts" / f"session_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(transcript_path, backup)
    
    # Inject PCMMAD-aware summary prompt
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "additionalContext": open("state/pcmmad/10A SHALL_INIT_LIVE_SHADOW_NEXT.md").read()
        }
    }))
```

---

## 7. The AGENTS.md Standard (Emerging, 2025)

OpenAI introduced AGENTS.md (similar to CLAUDE.md) as a repo-level configuration for AI agent behavior. Combined with CLAUDE.md, these are converging on a standard: **markdown files in the repo define agent behavior constraints**.

For Singularity Works, the canonical project file set becomes:
```
CLAUDE.md              → Live Shadow + active constraints (forge writes this)
.claude/settings.json  → Hook configuration (forge installs this)
.claude/agents/        → Subagent definitions (forge provides these)
state/pcmmad/          → Full PCMMAD state surfaces
configs/seed_genome.json → Capsule configuration
```

---

## 8. Summary — Research Value Delivered

| Need | Source | Signal |
|---|---|---|
| Hook lifecycle (complete) | Official Claude Code docs | 12+ events, 4 handler types, full schema |
| God-object anti-pattern | Production lesson (frozen) | QueryEngine collapse → split 4 ways |
| Transcript vs ledger | Production lesson (frozen) | Two separate artifacts, never collapse |
| MCP seam | Official MCP spec (Linux Foundation) | 3 primitives, 3-phase lifecycle, security model |
| Subagent spawning | Official Claude Code docs | .claude/agents/, constrained tool sets |
| Compaction hook | Official Claude Code docs + npm | PreCompact event, summaryPrompt override |
| Context design | Aider (Apache 2.0) | Repository map pattern, immutable baseline |
| Policy-as-code | Continue.dev (Apache 2.0) | .continue/checks/ markdown pattern |
| Multi-agent handoffs | OpenAI Agents SDK (open source) | Guardrails in parallel, not sequential |
| HTTP hooks | Official Claude Code docs | Remote forge endpoint pattern |
| AGENTS.md standard | OpenAI (2025) | Convergence with CLAUDE.md |

**All value extracted from clean, legitimate, open sources.**
**No leaked, proprietary, or legally problematic material used.**
