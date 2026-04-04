# Doctrine Snapshot — Singularity Works Forge
_Version: 2026-04-03 · v1.19_

### Active mode-control state
- BUILD
- Why: Active implementation workstream. v1.19 committed, next session continues BUILD on the next seam. No discourse trigger present.

### Current governing laws
- LAW 0: Inactive — build is active
- LAW 1: ACTIVE — no stubs, no TODOs, no fake phasing. Every session produces runnable output verified against the battery.
- LAW 2: BUILD lock active for all forge workstreams until explicit mode change
- LAW 3: If seam is ambiguous (e.g. "should we add IDOR monitor or fix the sections/parts bug first?"), ask explicitly before touching both
- LAW 4: Read full files before editing. Verify line counts match. Do not infer across unread modules.
- LAW 5: Cross-disciplinary grounding required for new strategies — OWASP, CodeQL vocabulary, Semgrep taint model, Linux RV-style monitor synthesis
- LAW Ω: Every artifact at theoretical maximum. Battery must remain 46/46. No new monitor without test case. No new strategy without FP check.
- LAW Σ: Active — surface wrong-path probes, adversarial counterexamples, FP candidates before declaring a new detection done

### Current quality / search posture
- Verification pressure: HIGH — every change must rerun the full battery before commit
- Cross-disciplinary pressure: MEDIUM — new strategies grounded in OWASP/CodeQL/Semgrep vocabulary; new monitors reference Linux RV and OpenRewrite discipline
- Maximum-attainable pressure: HIGH — Law Ω, deletion rule active (kill something per session)
- Divergence / wrong-path pressure: MEDIUM — Law Σ active, FP checks mandatory before any new detection is promoted

### Current incumbent architecture / method
**28-module Python forge over a typed semantic IR + genome-driven gate pipeline + AST-based protocol monitors + evidence ledger + CIL council hook**

Core pipeline:
```
Requirement + Artifact
    → RecoveryEngine.derive()  [recovery.py — generate MonitorSeeds from AST analysis]
    → Orchestrator.run()       [orchestration.py — bundle capsules, run gates + monitors]
    → MonitorEngine.run()      [monitoring.py — 12 AST-based protocol monitors]
    → AssuranceEngine          [assurance.py — rollup to green/red verdict]
    → EvidenceLedger           [evidence_ledger.py — JSONL audit trail]
```

Genome: 37 capsules → RadicalMapGenome.bundle_for_task() → ordered by SMEM budget_weights
Gates: 36 detection strategies in _STRATEGIES (genome_gate_factory.py)
Monitors: 12 runners in _MONITOR_RUNNERS (monitoring.py)
IR: UniversalSemanticIR from language_front_door.py — AST + trust_boundaries + semantic_tokens
Cross-function taint: _propagate_cross_function_taint() — fixed-point 6-hop return-taint

### Active constraints
- No new capabilities until battery holds at 46/46
- No auto-persist of research sandbox outputs into forge continuity
- Behavioral reliability pass (GPT under natural language) deferred until after IDOR + bug fixes
- seed_genome capsule schema: detection_strategy must live inside anti_patterns[0], not top-level
- forge_context.py compile_context() sections/parts bug: known, not yet patched — do not trust contradiction-path outputs until fixed

### What is load-bearing right now
- `singularity_works/` package at v1.19 in `/tmp/sw_v19/` and on GitHub
- `configs/seed_genome.json` — 37 capsules, GenomeCapsule(**kwargs) clean
- Full battery: 38 assault + 8 protocol = 46 cases, all verified this session
- Protocol monitors: 9 auth/session seams + 3 base (must_contain, must_not_contain, must_close_resource)
- Cross-function taint propagation: fixed-point algorithm, WITH-statement client tracking, FP suppression

### What is under challenge
- forge_context.py memory stack: contradiction path runtime behavior unverified
- good_service_issue_only FP: acknowledged, not fixed
- SSRF requirement-selection sensitivity: documented known limit
- genome capsule distribution: 57% trust_boundary_validation — possible under-coverage of other classes

### Active Sigma branches
- **IDOR/ownership gap**: "user can reach the action" vs "user owns this specific object" is a real and common bug class not yet in the monitor set
- **auth_rate_limit gap**: monitor and seeding exist but no empirical battery cases; may produce unexpected FPs or FNs against real code shapes
- **Tree-sitter/SCIP/CPG front door**: ChatGPT and session analysis both converge on this as the right polyglot semantic layer; still doctrinal, not code
- **Forge metadata production for TQ2 (TQ2-11)**: bridge between forge output and TQ2/CIL structured memory; needed for both projects but blocked by TQ2 session depth

### What was recently promoted
- Cross-function SSRF taint propagation (`_propagate_cross_function_taint`) → LOAD-BEARING
- 9 auth/session protocol monitors (v1.18 march, confirmed v1.19) → LOAD-BEARING
- JWT algorithm confusion strategy → WORKING (in battery via upcoming P0 cases)
- HTTP non-TLS strategy → WORKING (same)
- seed_genome.json correct capsule schema → CANON

### What was recently demoted
- forge_sandbox/ (sacrificial Claude's 846-line reconstruction) → TOMBSTONED, replaced
- forge_initial_repo (different unfinished architecture) → ARCHIVED in repo, not current baseline

### Doctrine drift watchlist
- **Mode bleed**: BUILD state can drift into discourse if seam is ambiguous. LAW 3 is the interrupt.
- **Summary substitution**: Do not infer forge module behavior from reading only this file. Read actual source.
- **Mythology accretion**: Deletion rule active. Kill something per session.
- **Behavioral overconfidence**: Self-audit 920/4/0 does not mean the forge is correct under all inputs. It means the test suite passes.
