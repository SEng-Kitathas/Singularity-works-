# Claude Code Integration Map — Singularity Works Forge
_Version: 2026-04-03 · Derived from @anthropic-ai/claude-code v2.1.92 npm package analysis_
_Method: Official npm package inspection only. No leaked/reconstructed source used._

---

## 1. What Claude Code Actually Is (From Our Perspective)

Single minified `cli.js` (13MB), vendored binaries: ripgrep (rg), audio-capture, seccomp.

**The forge's mental model**: Claude Code is a stateful agent loop with a context window, a tool executor, a memory injection system, and a compaction mechanism. The forge is the intelligence that shapes what goes into that context window and what comes out of the tool executor. Claude Code is the hands. The forge is the nervous system.

---

## 2. The Compaction System — The Main Loss Point

### How it actually works

```
contextTokenThreshold (default: sX7 = 1.0, meaning 100% of context window)
    ↓
eX7() fires: counts input_tokens + cache_creation + cache_read + output_tokens
    ↓
if total_tokens < threshold → skip
    ↓
else: POST to /v1/messages with header x-stainless-helper: compaction
      using summaryPrompt (default: tX7) + current message history
    ↓
response.content[0].text → replaces params.messages = [{role:"user", content: summary}]
    ↓
emits compaction_delta stream event
    ↓
compact_boundary system event injected with:
  trigger: "manual" | "auto"
  pre_tokens: number
  preserved_segment?: { head_uuid, anchor_uuid, tail_uuid }
```

### The default summary prompt (tX7) — this is what loses your state:

```
You have been working on the task described above but have not yet completed it.
Write a continuation summary... Include:
1. Task Overview (user's core request, success criteria, clarifications)
2. Current State (completed so far, files created/modified/analyzed, key artifacts)
3. Important Discoveries (technical constraints, decisions, errors, what didn't work)
4. Next Steps (actions needed, blockers, priority order)
5. Context to Preserve (user preferences, domain-specific details, promises made)
Be concise but complete...
Wrap your summary in <summary></summary> tags.
```

**The problem**: This is generic. It compresses your forge session down to "what did we do" without preserving: mode state, verified/provisional split, open seams by name, battery results, capsule state, active law stack. It's the right prompt for a coding task. It's the wrong prompt for a PCMMAD-governed forge session.

### The control surface

`compactionControl` object — OVERRIDABLE:
```javascript
compactionControl: {
  enabled: true,
  contextTokenThreshold: 0.8,  // fire at 80% instead of 100%
  summaryPrompt: YOUR_PCMMAD_SUMMARY_PROMPT,  // ← THE KEY OVERRIDE
  model: "claude-sonnet-4-20250514"
}
```

**This is what we override.** The `summaryPrompt` field is exposed. We replace `tX7` with a PCMMAD-aware compaction prompt that produces a Live Shadow-format output instead of a generic task summary.

### PCMMAD compaction prompt (drop-in replacement for tX7):

```
You are operating under PCMMAD. Compaction is occurring. Your job is to produce a
Live Shadow artifact — NOT a generic task summary. The output MUST preserve:

MODE: [DISCUSSION / BUILD]
ACTIVE ROLE: [R1-R5]
OBJECTIVE: [single concrete deliverable]
AUTHORITY BASE: [exact version/commit]

VERIFIED (evidence-backed, run and confirmed):
- [list each with evidence]

PROVISIONAL (claimed but unverified):
- [list each]

INCUMBENT BASELINE:
- [the thing currently load-bearing]

OPEN SEAMS (unresolved, highest friction first):
- [list each by name]

IMMEDIATE NEXT STEP:
- [exact action, not vague intent]

LAST 10 TURNS (condensed):
1. [turn + state effect]
...

DECISIONS LOCKED IN:
- [irreversible architectural decisions with rationale]

ACTIVE CONSTRAINTS:
- [laws active, deletion rule status, battery requirement]

Wrap output in <live_shadow></live_shadow> tags.
Do NOT produce a narrative summary. Produce operational state.
```

### The preserved_segment hook

When compaction fires with `preserved_segment`, it contains `{head_uuid, anchor_uuid, tail_uuid}` — a splice point. This means some messages are kept verbatim after the summary. The forge can exploit this by ensuring the most recent Live Shadow update is in the kept segment.

---

## 3. Memory Hierarchy — Load Order and Override Points

Loading order (lower = higher override priority):
```
1. Managed   → ~/.claude/managed/ (policy files, cannot be excluded)
2. User      → ~/.claude/CLAUDE.md (global user memory)
3. Project   → <project>/CLAUDE.md + <project>/.claude/CLAUDE.md
4. Local     → <project>/CLAUDE.local.md (gitignored, session-specific)
```

Additional directories:
```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=/path/to/forge/state/pcmmad
```

**Injection format**: Loaded as a user-role message:
```
"The following is the user's CLAUDE.md configuration. These are instructions 
the user provided to the agent and should be treated as part of the user's 
intent when evaluating actions."
```

### Forge → Claude Code mapping:

```
FORGE ARTIFACT              CLAUDE CODE SURFACE
──────────────────────────────────────────────────────
Live Shadow (10A)       →   CLAUDE.md (Project layer)
                            Re-read before every reply via PCMMAD protocol
                            
Design Thread Stream    →   CLAUDE.local.md (gitignored, session-specific)
(10B)                       Raw chronological — too long for CLAUDE.md

Seed genome summary     →   CLAUDE.md section: "Active detection capabilities"

Battery state           →   CLAUDE.md section: "Verified baseline: 46/46"

Open seams              →   CLAUDE.md section: "Open seams" (from trace matrix)

Law stack               →   CLAUDE.md section: "Active constraints"
```

**The practical implementation**: Forge writes a structured CLAUDE.md on session open. Claude Code picks it up as context. The forge's Live Shadow IS the CLAUDE.md. They are the same artifact, different names.

---

## 4. Tool Protocol — The Real Integration Surface

### Tools available to Claude Code agent:
From sdk-tools.d.ts (official type definitions):
- `Bash` — execute bash commands
- `Edit` → `FileEditInput/FileEditOutput` — edit files
- `Read` → `FileReadInput/FileReadOutput` — read files (text, image, notebook, PDF)
- `FileWrite` → `FileWriteInput/FileWriteOutput` — write files  
- `Glob` — file pattern matching
- `Grep` — content search (via bundled ripgrep)
- `Agent` → `AgentInput/AgentOutput` — spawn sub-agents
- `WebFetch`, `WebSearch`
- `TodoWrite` — task tracking
- `ListMcpResources`, `McpInput` — MCP tool calls
- `Network Access` — network operations
- `AskUserQuestion` — pause for human input

### Tool result format:
```json
{
  "type": "tool_result",
  "tool_use_id": "<id>",
  "content": "<string or array>",
  "is_error": false
}
```

### Tool hooks (pre/post execution):
```
PreToolCall  → can modify input, block execution
PostToolCall → can see result, trigger side effects
```

**Forge integration point**: `PostToolCall` on `Bash` is where forge results get picked up. When Claude Code runs `python3 examples/verify_build.py`, the forge's assurance verdict comes back through this channel.

### Tool filtering:
```javascript
allowedTools: ["Bash", "Read", "FileWrite", "Grep"]
disallowedTools: ["WebSearch", "WebFetch"]
```

The forge can constrain Claude Code to only the tools needed for a given task.

---

## 5. Programmatic Interface — How Forge Controls Claude Code

### --print mode (non-interactive pipe):
```bash
echo "task description" | claude --print --output-format=stream-json --verbose
```

Stream-json event types:
```
system      → session start, compact_boundary, hook events
message     → assistant turns
user        → user turns  
text        → text deltas
content_block_start/delta/stop
message_start/delta/stop
task_completed
error, authentication_error
idle, keep_alive
```

### Session persistence:
```bash
claude --print --resume <session_id>  # resume a specific session
```

### appendSystemPrompt:
The forge can inject additional system context beyond CLAUDE.md:
```javascript
appendSystemPrompt: `
FORGE MODE ACTIVE
Battery state: 46/46 verified
Active law: LAW 1 (no stubs, no TODOs)
Deletion rule: active
`
```

### allowedTools + hooks:
Claude Code respects tool restrictions at the session level. The forge can lock it to:
- `Bash` only (for execution tasks)
- `Bash` + `FileWrite` (for patching tasks)
- `Read` + `Grep` (for audit tasks)

---

## 6. MCP Integration — The Power Surface

MCP servers are the forge's natural extension mechanism:

```javascript
mcpServers: {
  "singularity-works": {
    type: "url",
    url: "http://localhost:PORT/mcp"
  }
}
```

This gives Claude Code access to forge tools as MCP tools:
- `forge_run_battery()` — run the 46-case battery and return verdicts
- `forge_get_assurance(artifact)` — get assurance verdict for a code snippet
- `forge_get_open_seams()` — return current revisit ledger
- `forge_get_state()` — return Live Shadow
- `forge_commit_verified(message)` — commit only after battery pass

The forge becomes a first-class tool in Claude Code's tool universe. Not a wrapper. A peer.

---

## 7. The Compaction Override — Concrete Implementation

### Step 1: Write a forge-aware CLAUDE.md

```markdown
# FORGE SESSION — PCMMAD ACTIVE

## Mode
BUILD — Law 1 active. No stubs. No TODOs. Battery must pass before commit.

## Authority Base
v1.19 @ commit 3305e25 | 46/46 FP=0 FN=0 | self_audit=920/4/0

## Active Law Stack
Laws 0-5, Ω, Σ active. FORGE_EXECUTION_SOP_PATCH_v1 active.
Deletion rule: kill something per session.

## Verified Baseline
- 28 modules, 12,214 lines, 37 capsules, 36 strategies, 12 monitors
- 46/46 battery: FP=0 FN=0 at 1.2s
- seed_genome.json: all 37 capsules load without TypeError

## Open Seams (P0 first)
1. forge_context.py sections/parts NameError — contradiction path bug, unpatched
2. auth_rate_limit: 3 battery cases needed
3. IDOR/ownership monitor: next march target

## Immediate Next Step
Fix forge_context.py sections/parts, run 49/49, commit v1.20.
```

### Step 2: Override the compaction prompt

Write a `.claude/compaction.md` or pass via `compactionControl.summaryPrompt`:

```
You are in a PCMMAD-governed forge session. Compaction is occurring.
Do NOT produce a generic task summary.
Produce a Live Shadow artifact with these exact sections:
[FORGE LIVE SHADOW]
MODE: BUILD
VERIFIED: [list with evidence]
PROVISIONAL: [list]
BASELINE: [module count, line count, battery state]
OPEN SEAMS: [P0 first, by name]
NEXT STEP: [exact]
LAST 10 TURNS: [condensed, with state effects]
LOCKED DECISIONS: [irreversible]
[/FORGE LIVE SHADOW]
```

### Step 3: Set threshold lower

Fire compaction at 80% instead of at overflow:
```
contextTokenThreshold: 0.8
```

This means you get a clean compaction BEFORE the context degrades, not after it's already saturated and lossy.

---

## 8. The Full Integration Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Singularity Works Forge              │
│                                                      │
│  genome + strategies + monitors + taint engine       │
│  → assurance verdicts (green/red)                    │
│  → evidence.jsonl (audit trail)                      │
│  → PCMMAD state surfaces (Live Shadow, DTS)          │
└──────────────────┬──────────────────────────────────┘
                   │  MCP server (localhost)
                   │  forge_run(), forge_get_state(), etc.
                   ↓
┌─────────────────────────────────────────────────────┐
│               Claude Code (claude CLI)               │
│                                                      │
│  CLAUDE.md ← forge Live Shadow (injected per session)│
│  compactionControl.summaryPrompt ← PCMMAD prompt    │
│  allowedTools ← forge-constrained per task          │
│  hooks.preToolCall ← forge gate check               │
│  hooks.postToolCall ← forge verdict capture         │
│                                                      │
│  Tools: Bash, Read, FileWrite, Grep, Agent, MCP      │
└──────────────────┬──────────────────────────────────┘
                   │  stream-json events
                   ↓
┌─────────────────────────────────────────────────────┐
│           Forge Orchestration Layer                  │
│                                                      │
│  Parse stream-json → route verdicts → update state  │
│  On task_completed → run battery → gate commit      │
│  On compaction_delta → verify Live Shadow preserved  │
└─────────────────────────────────────────────────────┘
```

---

## 9. What We Own vs What Claude Code Owns

| Concern | Owner | Notes |
|---|---|---|
| Vulnerability detection logic | Forge | genome_gate_factory.py, strategies |
| Protocol monitor semantics | Forge | monitoring.py, 12 runners |
| Assurance verdicts | Forge | assurance.py |
| Evidence audit trail | Forge | evidence_ledger.py (JSONL) |
| Session memory / Live Shadow | Forge | CLAUDE.md injection |
| Compaction behavior | Forge (via override) | summaryPrompt override |
| Tool execution | Claude Code | Bash, Read, Write, Grep |
| Context window management | Claude Code (configured by forge) | threshold setting |
| File I/O in project | Claude Code | via tool calls |
| Commit/push operations | Claude Code | via Bash tool |
| MCP tool dispatch | Claude Code | forge registers as MCP server |

---

## 10. Immediate Next Steps for Integration

**Session-start script** (`forge_session_open.py`):
1. Read state/pcmmad/10A LIVE_SHADOW
2. Write to `CLAUDE.md` in project root
3. Start Claude Code with:
   - `--output-format=stream-json`
   - `compactionControl.summaryPrompt` = PCMMAD prompt
   - `contextTokenThreshold` = 0.8
   - MCP server pointing at forge

**On compaction_delta event**:
1. Parse the summary from `<live_shadow>` tags
2. Verify it contains VERIFIED/PROVISIONAL/OPEN_SEAMS sections
3. Update state/pcmmad/10A with the new shadow
4. Append to state/pcmmad/10B Design Thread Stream

**On task_completed**:
1. Run `python3 examples/verify_build.py`
2. If battery fails → block commit, surface seam
3. If battery passes → gate commit, update trace matrix

This is the forge-as-control-plane architecture. Claude Code becomes the execution layer. The forge is the authority layer.
