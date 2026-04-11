# Singularity Works — Integration Layer

**Forge + LM Studio + Claude Code = one cohesive force multiplier.**

This package wires three systems that were built for each other:

| System | Role |
|---|---|
| **Claude Code** | Orchestration harness. File access, planning, tool calling. |
| **LM Studio** (local models) | Synthesis engine. Generates code, applies fixes. |
| **Singularity Works Forge** | Validation engine. Formal invariant checking. Nothing is done until the forge says green. |

---

## Files in This Package

| File | Purpose |
|---|---|
| `lcc.bat` | Windows launcher. One command to start everything. |
| `forge_bridge.py` | Model routing + dialectic loop. The connective tissue. |
| `forge_context.py` | Project context v3.0. Upgrades old v2.0 context system. |
| `CLAUDE.md` | Claude Code directive. Drop in any project root. |
| `setup.bat` | Windows installer. Run once, configures PATH and env. |
| `sw_env.bat` | Auto-generated environment config. Source to activate. |

---

## Quick Start

**One-time setup:**
```bat
cd path\to\this\package
setup.bat
```

**Per project (run in your project directory):**
```bat
:: Initialize forge context for this project
python forge_context.py init --name "MyProject"

:: Copy Claude Code directive
copy CLAUDE.md CLAUDE.md

:: Launch
lcc --auto
```

**During a session:**
```bat
:: Validate a file through the forge
lcc --validate src\auth.py

:: Run full dialectic fix loop (forge → coder → reasoner → forge)
lcc --fix src\database.py

:: See forge session history and project genome priors
python forge_context.py summary
```

---

## Model Roles

Your three LM Studio models are auto-detected and assigned roles:

| Model | Role | Used For |
|---|---|---|
| `qwen3.5-35b-a3b-claude-4.6-opus-reasoning-distilled` | **REASONER** | Deep analysis when fixes fail, architectural review, complex multi-vector findings |
| `qwen2.5-coder-7b-instruct-abliterated` | **CODER** | Fast code synthesis, applying forge transformation candidates |
| `qwen3.5-0.8b-unredacted-max` | **GHOST** | Quick pre-screening, spec summarization, rapid iteration |

Detection is automatic — model names are matched by heuristic patterns.
If the wrong model gets a role, set it via environment:
```bat
set LM_REASONER=qwen3.5-35b-a3b-claude-4.6-opus-reasoning-distilled
set LM_CODER=qwen2.5-coder-7b-instruct-abliterated
set LM_GHOST=qwen3.5-0.8b-unredacted-max
```

---

## The Dialectic Loop

When you run `lcc --fix file.py`, this happens:

```
1. Forge analyzes file → produces structured findings
   {gate, severity, message, rewrite_candidate, transformation_axiom}

2. If green → done. Return fixed file.

3. CODER (7B) receives findings as structured constraints
   → generates corrected code
   → forge re-validates

4. If still failing after round 1:
   REASONER (35B) analyzes why fixes aren't working
   → produces repair plan
   → CODER implements plan
   → forge re-validates

5. Loop until green or budget exhausted (default 3 rounds)
```

The forge determines when something is fixed. The LLM can't declare victory.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Project Directory                    │
│  CLAUDE.md  (forge directive — Claude Code reads at startup) │
│  .forge-context.json  (project context, genome priors)       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code (harness)                     │
│  • Reads CLAUDE.md to understand forge workflow              │
│  • Calls forge_bridge.py validate before marking tasks done  │
│  • Calls forge_bridge.py fix when validation fails           │
│  • Pointed at LM Studio via ANTHROPIC_BASE_URL               │
└──────────────┬─────────────────────┬────────────────────────┘
               │                     │
               ▼                     ▼
┌─────────────────────┐   ┌──────────────────────────────────┐
│  LM Studio           │   │  Singularity Works Forge         │
│  ─────────────────  │   │  ────────────────────────────── │
│  REASONER: 35B MoE  │   │  23 genome capsules              │
│  CODER:    7B       │◄──►│  22 detection strategies         │
│  GHOST:    0.8B     │   │  Interprocedural call graph      │
│                     │   │  Universal Semantic IR           │
│  LM Studio API:     │   │  Switchboard derivation engine   │
│  localhost:1234     │   │  Evidence-bearing assurance      │
└─────────────────────┘   └──────────────────────────────────┘
```

---

## Bug Bounty Workflow

All analysis stays on your machine. Nothing leaves the network.

```bat
:: Point forge at target code
lcc --validate target\vulnerable_app.py "No security vulnerabilities"

:: The forge returns structured findings:
:: - interprocedural_sqli, timing_attack, redos, ssrf, pickle_rce, etc.
:: - derived compound facts: trust_sensitive_sink_hazard, sql_injection_confirmed
:: - Full call chain for each finding: where taint enters, where it reaches the sink

:: Get the 35B reasoner to analyze compound findings
lcc --reasoner
:: Then in Claude Code: use forge findings as the vulnerability report base
```

The forge catches what standard scanners miss:
- **SECOND_ORDER_SQLI** — taint through function call chains
- **TIMING_ATTACK** — non-constant-time comparison in security functions
- **PATH_TRAVERSAL_BYPASS** — naive check bypassed by URL encoding
- **REDOS** — nested quantifiers causing exponential backtracking
- **CIRCULAR_DEP** — classes that deadlock each other during initialization

---

## Per-Project Configuration

### Shadow docs and trace matrix

Link your project's design documents so the LLM models get architectural
context during dialectic fix rounds:

```bat
python forge_context.py link-shadow --type trace_matrix --path docs\TRACE.md
python forge_context.py link-shadow --type research_crosswalk --path docs\RESEARCH.md
```

### Genome priors

After a few forge sessions, the context tracks which genome capsules fire
most in your project. This feeds back into genome bundle selection —
the forge prioritizes capsules that matter for your codebase.

```bat
python forge_context.py summary
:: Shows: top capsules, proven axioms, session history
```

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `LM_HOST` | `127.0.0.1` | LM Studio host |
| `LM_PORT` | `1234` | LM Studio port |
| `FORGE_DIR` | auto-detected | Path to `sw_v19` directory |
| `CONTEXT_FILE` | `.forge-context.json` | Project context file name |

Override in terminal or add to your shell profile.

---

## Upgrading from v2.0 Context System

The v3.0 context manager reads v2.0 files automatically and migrates them.
Run in a directory with an old `.claude-context.json`:

```bat
python forge_context.py init --name "MyProject" --file .forge-context.json
:: Then manually copy tasks/decisions from the old file if needed
```

v3.0 adds: forge gate history, genome priors, model routing preferences,
shadow doc wiring, project-specific proven axioms.
