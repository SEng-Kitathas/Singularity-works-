# Current State — Singularity Works Forge
_Version: 2026-04-03 · v1.19_

### Project name
Singularity Works

### One-sentence mission
An autonomous, evidence-backed software forge that detects security vulnerabilities, enforces protocol-correctness invariants, and generates controlled remediations — functioning as the control plane between local LLM cognition and Claude Code execution.

### Current mode state
- BUILD

### Why this is the current mode
Active implementation workstream. v1.19 committed and pushed. Next session enters BUILD on the next expansion seam (IDOR/ownership protocol monitor or auth rate-limit seeding, or forge metadata production for TQ2 bridge).

### Current corpus / evidence base
- `/tmp/sw_v19/` — canonical live forge (28 modules, 12,214 lines Python)
- `configs/seed_genome.json` — 37 capsules, all loading clean
- GitHub: `SEng-Kitathas/Singularity-works-` — current authority
- Session context: full build history v1.13 → v1.19
- Uploaded: forge_release_2026-03-30.zip (ChatGPT upstream), forge_current_codebase_2026-03-30.zip, full_forge_messy_dump.zip, geometric_inference.zip

### Active law stack / doctrine deltas
- All Laws 0–5, Ω, Σ active
- FORGE_EXECUTION_SOP_PATCH_v1 active: deletion rule enforced, session footer required
- No overrides or local adaptations

### Current incumbent baseline
**v1.19 forge** — 28 Python modules, 12,214 lines, 37 genome capsules, 36 detection strategies, 12 protocol monitor runners. 46/46 assault+protocol battery, FP=0, FN=0, self_audit=920/4/0.

Stack: local models → Singularity Works (forge/control plane) → Claude Code (harness/front end)

### Open seams
1. **IDOR/ownership protocol monitor** — ChatGPT's recommended next march target: catch "user can reach the action" vs "user is allowed to touch this specific object"
2. **auth_rate_limit seeding** — monitor exists, recovery.py seeding wired, but needs empirical battery cases
3. **forge_context.py `sections`/`parts` bug** — `compile_context()` contradiction branch uses `sections.append()` but accumulator is `parts` → NameError when contradictions exist. Found by ChatGPT live run, not yet verified fixed
4. **SSRF requirement-selection sensitivity** — generic requirement phrasing can produce false green; documented known limit
5. **good_service_issue_only residual FP** — refresh-rotation seam stays red when no request-bound token present; context-breadth mismatch in older rotation monitor
6. **Tree-sitter/SCIP/CPG polyglot front door** — next major architectural seam after protocol monitor saturation
7. **Selective retrieval policy** — Repoformer-style abstention-governed retrieval before neural ranking

### What is actually verified
- 46/46 combined battery (38 assault + 8 protocol), FP=0, FN=0 — confirmed in sandbox 2026-04-03
- self_audit=920 pass / 4 warn / 0 fail — 4 warns are architectural (line length, duplication on large files), zero high/critical
- compile=True, good=green, bad=red, all remediated paths return green
- 9 protocol monitors fire correctly on targeted cases: session-before-redirect, cookie-hardening, logout-clearance, tx-finalization, refresh-rotation, refresh-family, callback-state, recovery-token, rate-limit
- Cross-function SSRF taint: 1-hop getter, 2-hop chain, httpx AsyncClient, urllib.request.urlopen — all confirmed red
- FP suppression confirmed: hardcoded URLs and allowlist-validated callers stay green
- JWT algorithm confusion detection: no-algorithms= catches, algorithms=['none'] catches, verify_signature=False catches
- HTTP non-TLS: hardcoded http:// literal in network call catches
- Callback silent-abstention fix: OAuth callbacks with no state param read now catch
- Goroutine docstring self-scan guard: genome_gate_factory.py no longer false-positives on its own detector docstrings
- 37 capsules load via GenomeCapsule(**kwargs) without TypeError — seed_genome schema fixed

### What is still provisional
- forge_context.py sections/parts bug: identified by ChatGPT, not yet independently verified in current codebase
- auth_rate_limit battery: monitor runner registered, recovery.py seeding added, but no dedicated test cases run yet
- good_service_issue_only FP in refresh-rotation: known, not blocked, low priority
- Behavioral reliability of GPT under natural language / low-supervision use: untested
- TQ2/forge metadata bridge (TQ2-11): planned, not started

### Current blockers
- None blocking v1.19. Next work is greenfield expansion.

### Current risks / technical debt
- 4 warn files (forge_context.py, genome_gate_factory.py, monitoring.py, recovery.py): architectural complexity debt, not security risk
- forge_context.py sections/parts bug: unverified, low probability of causing issues in current test suite but could surface under contradiction path execution
- SSRF requirement-selection sensitivity: known gap, honest limit, not blocking

### Active role routing
- Start role: R5 Reality Pressure Engine
- Why: BUILD state, active implementation, Law 1 active. Every session must produce runnable output.
- Likely bias: expansion before consolidation. Counter with deletion rule.
- Likely next handoff: R1 Conservative Auditor for behavioral reliability pass on GPT

### Resume point
Next BUILD session: pick ONE of (a) IDOR/ownership protocol monitor, (b) auth_rate_limit test battery + empirical verification, (c) forge_context.py sections/parts bug fix + verification. Deliver runnable + tested before widening.

### Failure / recovery status
- Last known valid node: v1.19 @ commit 3305e25, pushed to GitHub
- Active failure condition: none
- Recovery mode active: no

### Next mutation that would require this file to change
Any of: new monitor added, battery case added, new strategy added, verified/provisional boundary shifts, open seam closes or new one opens.
