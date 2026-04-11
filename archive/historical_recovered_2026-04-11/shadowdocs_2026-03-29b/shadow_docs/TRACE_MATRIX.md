# Trace Matrix — Singularity Works / CIL vNext
_Version: 2026-03-29 (initial backfill from session MHT)_
_SOP: UNIVERSAL_LAB_SOP_2026-03-29.md_

**Update rule:** Update by delta, never by replacement. Append new rows. Annotate status changes inline.

---

| ID | Requirement / Seam | Status | Mode | Evidence | Workstream | Notes |
|---|---|---|---|---|---|---|
| TM-001 | Forge gate pipeline: 38/38 assault pass, FP=0, FN=0 | Stable | Exploratory (pre-SOP) | SW-v1_13.zip; session MHT §assault | Forge / Detection | Zero false positives. Retroactively: EXPLORATORY — no pre-stated kill criterion. Confirmatory rerun needed to promote to Stable under SOP. |
| TM-002 | Self-audit: forge audits its own source with same standard | Stable | Exploratory (pre-SOP) | verify_build.py; 804/0/0 pass/warn/fail | Forge / Detection | Self-audit clean. Law-compliance / security verdict separation applied. |
| TM-003 | Substrate-Sovereign gates: ReDoS, stack overflow, memory pressure mitigations | Stable | Exploratory (pre-SOP) | Adversarial test suite (5 tests); session MHT | Forge / Safety | 3MB input→2ms, 10k nesting caught, ReDoS <0.1ms, truncate-not-reject confirmed. |
| TM-004 | CIL-013 SBUF formal spec (invariants INV-1 through INV-SBUF-5) | Provisional | Exploratory (pre-SOP) | cil.rs unit tests (4/4 pass); cil_forge v0.1.0.zip | CIL Memory (Rust) | Rust unit tests pass. Not yet integrated end-to-end. |
| TM-005 | CIL-014 Zep 4-field bi-temporal model (t_created/t_expired ∈ T', valid_from/valid_until ∈ T) | Provisional | Exploratory (pre-SOP) | forge_context.py v4.0; cil.rs BiTemporal; session MHT | CIL Memory | Python + Rust implementations. Smoke tested. Confirmatory E2E not yet run. |
| TM-006 | CIL-015 Contradiction Graph: petgraph DiGraph, Zep invalidation mechanism | Provisional | Exploratory (pre-SOP) | cil.rs ContradictionGraph; 4 unit tests | CIL Memory (Rust) | Unit tests pass: Zep mechanism, epistemic progression, distortion calibration. Not integrated into Python forge. |
| TM-007 | ForgeContext v4.0 SBUF→EPMEM consolidation + Orchestrator wiring | Provisional | Exploratory (pre-SOP) | forge_context.py; orchestration.py; smoke test 3-session | CIL Memory (Python) | Wired and smoke tested. VERIFY gate not yet run. Integration test with assault cases pending. |
| TM-008 | Temperature ↔ Distortion budget self-calibration | Provisional | Exploratory (pre-SOP) | smem_get_priors() in forge_context.py; cil.rs calibrate_distortion_budget(); unit test | CIL Memory | Math verified. Not yet integrated into genome bundle selection loop. Confirmatory experiment pending (EXP-20260329-001). |
| TM-009 | IRIS-mode escalation: low-conf IR → REASONER taint spec inference → DynamicCapsule | Provisional | Exploratory (pre-SOP) | genome_gate_factory.py iris_escalate(); orchestration.py IRIS block | Forge / IRIS | Wired. Best-effort offline path. Not tested with live LM Studio. |
| TM-010 | cil-forge Rust ECS scaffold: hecs archetype, 7 systems, cargo check clean | Active | Exploratory (pre-SOP) | cil-forge v0.1.0.zip; cargo test 4/4 | cil-forge Rust | Compiles. Systems are functional stubs. No integration test vs Python oracle. |
| TM-011 | cil_council v2.0: dialectic REASONER+CODER loop | Provisional | Exploratory (pre-SOP) | cil_council.py; offline graceful test | CIL Council | MAGI dead, bilateral attractor confirmed. Offline graceful. Online not tested. Self-audit false positive (P0 bug). |
| TM-012 | cil_council.py self-audit false positive: Law 1 string triggers token_placeholder_check | Active | Confirmatory (P0) | verify_build.py fail on cil_council.py | Forge / Safety | BLOCKING. Detection strings in Codex audit code match forge's own pattern scanner. Fix = encode detection strings. |
| TM-013 | Genome capsule expansion: 23→35 capsules, 22→34 strategies | Stable | Exploratory (pre-SOP) | seed_genome.json; genome_gate_factory.py | Forge / Detection | New capsules: XPATH/XXE/LDAP, goroutine leak, format string C, integer overflow alloc, prototype constructor, reflection injection, unsigned JWT, open redirect, mass assignment, global state mutation, TLS default, template injection, getattr injection. |
| TM-014 | Language front door: polyglot IR (Python full AST, others heuristic) | Stable | Exploratory (pre-SOP) | language_front_door.py; IR confidence field | Forge / IR | IR confidence field drives IRIS escalation. Language detection commits — "unknown" is architectural failure per L-02. |
| TM-015 | Loop+ Meta Control Layer adoption | Active | Doc update | LOOP_PLUS_AGNOSTIC_GUIDE_META_CONTROL_2026-03-29bc-1.md | Process | Folded into SOP §12. Active going forward. This session is first application. |
| TM-016 | SOP adoption and shadow doc backfill | Active | Doc update | UNIVERSAL_LAB_SOP_2026-03-29.md; DEV-20260329-001 | Process | SOP loaded at session end. All pre-SOP work retroactively EXPLORATORY. Backfill in progress. |
| TM-017 | cil-forge system implementations (real capsule dispatch in Rust) | Open | Exploratory | Pending | cil-forge Rust | Current gate_runner calls heuristic inline functions. Must dispatch to Python oracle or replicate all strategies in Rust. |
| TM-018 | Distortion budget → genome bundle selection integration | Open | Confirmatory (planned) | Pending EXP-20260329-001 | CIL Memory | Does calibrated distortion_budget actually change capsule selection and hit rate? Pre-stated kill criterion required. |
| TM-019 | CIL-council integration with forge orchestrator (IRIS validation path) | Open | Exploratory | Pending | CIL Council | wire quick_validate() into orchestrator IRIS escalation. Requires live LM. |
| TM-020 | ForgeContext v4.0 E2E integration test (assault + CIL state verification) | Open | Confirmatory (planned) | Pending | CIL Memory | Run assault suite with forge_context_path active. Verify EPMEM grows, SMEM promotes, contradiction resolves correctly. |
| TM-021 | Git version control for /tmp/sw_v19 | Open | Process debt | Named debt | Process | No git tracking. Reproducibility failure risk. Must be closed before any build is called "production-ready." |
| TM-022 | KarnOS/SYNAPSE: Laws 7-14 (GODSPEC v4.0.0), TQ2 quaternion weights | Open | Deferred | Background | KarnOS/SYNAPSE | Out of scope this session. TQ2 (OD-49 resolved), Tesseract quaternion encoding confirmed as normative. Deferred. |
| TM-023 | NEXUS browser shell: nexus-storage and nexus-memory before browser shell | Open | Deferred | Background | NEXUS | Roadmap reordered: cognitive substrate is the product. Deferred. |
| TM-024 | CIL2 workspace retargeting: cil-council → dialectic loop, cil-taint → contradiction graph | Open | Exploratory | Pending | CIL2 (Rust) | cil-council target confirmed. cil-taint maps to ContradictionGraph foundation. Not yet acted on. |
