# Revisit Ledger — Singularity Works Forge
_Version: 2026-04-03 · v1.19_

| ID | Item | Reason for revisit | Trigger condition | Status |
|---|---|---|---|---|
| RL-001 | forge_context.py sections/parts bug | NameError on contradiction path identified by ChatGPT live run on v1.17; not patched in current codebase | P0 fix session | OPEN |
| RL-002 | good_service_issue_only refresh FP | Refresh-rotation monitor fires when no request-bound token present; context-breadth mismatch in older rotation seam | If FP causes battery regression or user reports | OPEN / low priority |
| RL-003 | SSRF requirement-selection sensitivity | Generic requirement phrasing produces false green; routing vs detection root cause unclear | Deep-dive into bundle selection + requirement flag logic | OPEN |
| RL-004 | auth_rate_limit monitor empirical battery | Monitor registered, seeding wired, zero test cases run | P0 next session | OPEN |
| RL-005 | Tree-sitter/SCIP/CPG polyglot front door | ChatGPT + session analysis convergent recommendation; currently doctrinal only | After IDOR + behavioral reliability pass | DEFERRED |
| RL-006 | Behavioral reliability of GPT under natural language | Identified as the hardest remaining risk; skipped shadow updates, wrong artifact class, false confidence | After v1.20 clean | DEFERRED |
| RL-007 | EXP-20260329-001 null result root cause | budget_weights calculated but not consumed — fixed in v1.15, but experiment was not replicated with tight-weights condition | Next experiment slot | DEFERRED |
| RL-008 | cil-forge Rust ECS integration | Real Rust crates exist in AI-Research repo; Python oracle bridge in place but Rust build fractured | After TQ2 focus period | DEFERRED |
| RL-009 | forge_context.py memory stack full audit | sections/parts bug found by external run; may have sibling runtime-only bugs in other branches | After P0 contradiction path fix | OPEN |
| RL-010 | forge capsule distribution skew | 21/37 capsules are trust_boundary_validation; may under-cover other attack classes | When adding next capsule set | ACTIVE AWARENESS |
| RL-011 | IRIS escalation live quality | CIL council IRIS path wired and offline-graceful, but live quality against actual LM Studio endpoint not tested | When LM Studio endpoint accessible | DEFERRED |
| RL-012 | Distillation budget_weights effect on non-trivial cases | Known: budget_weights changes capsule ordering. Unknown: measurable effect on real-world bug detection | Long-form experiment after behavioral pass | DEFERRED |
