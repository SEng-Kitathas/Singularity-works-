# Singularity Works — Claude Code Directive

This project uses the **Singularity Works Forge** as its validation substrate.
All code produced, modified, or reviewed in this session is subject to forge
gate validation before being considered complete.

---

## The Three Systems You Are Operating Within

```
YOU (Claude Code — orchestration, file access, planning)
     ↕
LM Studio (local models — synthesis, fix generation)
     ↕
Singularity Works Forge (formal invariant validation)
```

The forge is the ground truth for code correctness in this project.
A gate result of `red` means the artifact is not done, regardless of
whether the code looks correct. `green` is done. Nothing else is done.

---

## Available Forge Tools

Run these via bash in any project directory that has `lcc.bat` on PATH,
or invoke directly via `python path/to/forge_bridge.py`:

```bash
# Validate a file — returns JSON gate results
python forge_bridge.py validate <file> "<requirement>"

# Run dialectic fix loop — forge → coder → forge → reasoner → coder → forge
python forge_bridge.py fix <file> "<requirement>"

# Check LM Studio status and model roles
python forge_bridge.py status

# See project context and forge session history
python forge_context.py summary
```

### Forge output schema

```json
{
  "status": "red|amber|green",
  "findings": [
    {
      "gate": "genome:logic.second_order_injection:interprocedural_sqli",
      "code": "interprocedural_sqli",
      "message": "Taint from request.args reaches SQL sink via get_users_by_role",
      "severity": "critical",
      "rewrite_candidate": "Validate fields against allowlist before interpolation",
      "transformation_axiom": "prefer_parameter_binding_to_string_interpolation",
      "linked_laws": ["LAW_4", "LAW_OMEGA"]
    }
  ],
  "transformation_candidates": [...],
  "derived_facts": ["sql_injection_confirmed", "trust_sensitive_sink_hazard"]
}
```

---

## Workflow — What You Must Do

### Before marking any task complete:

1. **Validate** every file you modified:
   ```bash
   python forge_bridge.py validate <modified_file> "<requirement from task>"
   ```

2. **If red**: Do not mark the task done. Use transformation candidates
   to understand what must change. Apply fixes.

3. **If still red after your fix**: Run the dialectic loop:
   ```bash
   python forge_bridge.py fix <file> "<requirement>"
   ```
   The dialectic loop engages the local LLM models (7B coder → 35B
   reasoner if needed) to generate fixes, then re-validates automatically.

4. **Record the decision** when a fix produces green:
   ```bash
   python forge_context.py decision \
     --text "Fixed interprocedural SQLi in get_users_by_role" \
     --why "fields param from request.args flowed into f-string SQL; now validated against allowlist"
   ```

5. **Only then**: Mark the task complete.

---

## Forge Gate Severity Reference

| Severity | Meaning | Action |
|---|---|---|
| `critical` | Architectural invariant violated — security, memory safety, atomicity | Must fix before done |
| `high` | Significant correctness/security issue | Must fix before done |
| `warn` | Law compliance advisory | Review, justify or fix |
| `pass` | Gate discharged — claim verified | No action needed |

---

## Model Roles (LM Studio)

| Role | Model | Use For |
|---|---|---|
| REASONER | qwen3.5-35b (Claude 4.6 Opus distilled) | Deep analysis, architecture, compound failures |
| CODER | qwen2.5-coder-7b | Synthesis, applying fixes, iteration |
| GHOST | qwen3.5-0.8b | Quick checks, spec summaries, pre-screening |

The forge bridge auto-detects these from LM Studio. You do not need to
specify model names manually — `forge_bridge.py status` shows current roles.

---

## The Immutable Laws (Always Active)

These govern all work in this session:

- **Law 0**: Discourse ≠ Implementation. Exploring ideas freely is fine.
  Touching files invokes Law 1.
- **Law 1**: `0-Day not Someday` — when building: no stubs, no TODOs,
  no MVPs, no phases. Full production-grade only.
- **Law 4**: Pedantic execution. VERIFY, DON'T INFER. Aerospace-grade minimum.
- **Law Ω**: Every artifact at theoretical maximum quality. Not "good enough."
- **Law Σ**: Voice speculative ideas. Map isomorphisms. Challenge assumptions.

When a forge gate says `red`, that is Law 1 speaking. The code is not done.

---

## Project Context

Context is stored in `.forge-context.json` in the project root.
It tracks: tasks, decisions, issues, forge session history, genome priors,
and model routing preferences learned from this project's history.

```bash
# View full context summary
python forge_context.py summary

# Add a task
python forge_context.py task --desc "Fix SSRF in webhook handler"

# Link a shadow document / trace matrix
python forge_context.py link-shadow --type trace_matrix --path docs/trace.md
```

---

## Bug Bounty Mode

When analyzing external code for vulnerabilities:

1. Run `python forge_bridge.py validate <target_file> "No vulnerabilities"` first.
   The forge will identify what it can formally detect.

2. Use the interprocedural analysis output — `derived_facts` especially —
   to understand compound vulnerability chains.

3. The `SECOND_ORDER_SQLI`, `TIMING_ATTACK`, `REDOS`, `CIRCULAR_DEP`,
   `INCOMPLETE_SANITIZATION` detectors are the highest-value catches
   because they require interprocedural reasoning that standard scanners miss.

4. All analysis stays local. No code leaves the machine.

---

## Shadow Docs and Project Knowledge

If this project has a trace matrix or research crosswalk document,
link it at session start:

```bash
python forge_context.py link-shadow --type trace_matrix --path docs/TRACE.md
python forge_context.py link-shadow --type research_crosswalk --path docs/CROSSWALK.md
```

Linked documents are injected into the LLM context during dialectic
fix rounds, giving the models project-specific architectural knowledge.
