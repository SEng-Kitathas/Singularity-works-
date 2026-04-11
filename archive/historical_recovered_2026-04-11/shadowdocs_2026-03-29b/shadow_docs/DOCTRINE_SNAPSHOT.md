# Doctrine Snapshot — Singularity Works / CIL vNext
_Date: 2026-03-29_
_Supersedes: (none — initial snapshot)_
_SOP: §5 epistemic vocabulary applies to all entries_

**Note: All entries from pre-SOP work are classified PROVISIONAL, not STABLE.
They were produced exploratorily without pre-stated kill criteria.
Confirmatory replication is required to advance any to STABLE.**

---

## Promoted Beliefs (Stable)
_(survived recursive replay, treated as hard constraints — NONE YET under SOP standard)_

_(All pre-SOP results are PROVISIONAL pending confirmatory replication. Stable column empty by design.)_

---

## Provisional Beliefs
_(integrated but subject to confirmatory replay — produced exploratorily)_

**P-001 — Assault pass: 38/38, FP=0, FN=0 [TM-001]**
The forge correctly flags 38/38 known vulnerability cases with zero false positives and zero false negatives across five wave classes. Core hammer 20/20 never regressed.
Evidence: SW-v1_13.zip; session MHT assault pass logs.
Replay trigger: Any change to genome capsules, strategy dispatch, or IR builder.

**P-002 — Root cause: early-return before IR fallback caused 7 amber regressions [TM-001]**
The three root-cause bugs (hardcoded language, early-return before IR fallback, keyword-only capability inference) were responsible for all 7 original amber cases. Fixing these three was sufficient to achieve 38/38.
Evidence: Session MHT root cause analysis; before/after gate counts.
Replay trigger: Any refactor of _genome_bundle() or _task_capabilities().

**P-003 — Substrate-Sovereign: size gates prevent ReDoS, stack overflow, memory pressure [TM-003]**
2MB content gate in _parse() + build_ir() + Orchestrator.run(). _safe_dotall_finditer() chunks DOTALL patterns at 500KB. Truncate-not-reject preserves real vulnerabilities near file tops.
Evidence: Adversarial test suite (5/5 pass); _parse(), build_ir(), orchestration.py gates.
Replay trigger: Any new regex strategy added; any DOTALL pattern added.

**P-004 — Zep 4-field bi-temporal model is the correct timestamp architecture for CIL [TM-005]**
Four fields (t_created, t_expired ∈ T'; valid_from, valid_until ∈ T) cleanly separates when CIL ingested a fact from when the fact held in the world. The prior tri-temporal design (superseded_at) is retired.
Evidence: arXiv 2501.13956; BiTemporal in forge_context.py + cil.rs.
Replay trigger: Any change to memory layer persistence format.

**P-005 — Temperature ↔ Distortion budget: single degree of freedom [TM-008, RC-001]**
arXiv 2509.24431 proves temperature parameter controls centroid tightness in contrastive training. In CIL/CRHQ, distortion_budget controls the same property. They are coordinate transformations of one variable.
Evidence: arXiv 2509.24431; calibrate_distortion_budget() in Rust + Python; unit test confirms tight < loose.
Replay trigger: Any redesign of CRHQ quantization or Radical family budgets.

**P-006 — IRIS (LLM→formal→LLM) and Forge (heuristic→gate→LLM) are dual architectures [TM-009, RC-003]**
IRIS and the forge both arrive at the same convergence structure from different directions. Their synthesis is the IRIS escalation path: when forge IR confidence is low, escalate to REASONER for taint spec inference.
Evidence: arXiv 2405.17238; iris_escalate() implementation; architectural analysis.
Replay trigger: When IRIS escalation is tested with live LM results.

**P-007 — hecs archetype ECS is the correct cil-forge substrate [TM-010, RC-004]**
Archetype ECS provides SoA memory layout with L1 cache locality across gate iterations. hecs chosen over Bevy (no render stack needed) and shipyard (archetype model preferred). Systems are stateless functions.
Evidence: ECS literature; cil-forge scaffold compiles; cargo test 4/4; architectural analysis.
Replay trigger: When actual system performance is measured vs. Python oracle.

**P-008 — ContradictionGraph: petgraph DiGraph with Zep invalidation is correct CIL-015 implementation [TM-006]**
Directed graph: A→B means "B contradicts A." Zep mechanism: contradict() sets valid_until of A = valid_from of B. EpistemicStatus progression thresholds (3 for ProvisionalSemantic, 6 for StableSemantic) are functionally appropriate.
Evidence: cil.rs unit tests (4/4 pass): Zep mechanism, epistemic progression, distortion calibration, SBUF invariants.
Replay trigger: When ContradictionGraph is integrated into Python forge and tested E2E.

**P-009 — CIL is architecturally ahead of Zep/MemVerse on epistemic layer [RC-006]**
Zep tracks temporal ranges but not epistemic confidence states. MemVerse uses three tiers but no contradiction graph. CIL has all four: SBUF (hippocampal fast-write) + EPMEM (bi-temporal ledger) + SMEM (epistemic state machine) + ContradictionGraph.
Evidence: arXiv 2501.13956, 2512.03627, 2602.05665; architectural comparison.
Replay trigger: When another agent memory system implements epistemic state tracking.

**P-010 — MAGI multi-model council is dead; cil_council bilateral attractor is the replacement [TM-011]**
MONOSPEC_v2.0_OMEGA.md declared MAGI dead. Axiom 4 (Weights ARE Memory) rules out multi-model architectures. Two-role bilateral debate (REASONER + CODER) converges faster than trilateral consensus.
Evidence: MONOSPEC_v2.0_OMEGA.md; cil_council.py; offline graceful test.
Replay trigger: When cil_council is tested with live LM Studio.

---

## Exploratory Signals
_(tentative; require confirmatory test before promotion)_

**E-001 — Distortion budget calibration changes genome bundle selection hit rates [EXPLORATORY]**
The calibrated budget math is sound and unit-tested. Whether it actually produces different capsule selection — and whether that improves assault pass performance — is untested.
Next: EXP-20260329-001 (confirmatory pre-registration required).

**E-002 — IRIS escalation correctly identifies taint flows that static analysis misses [EXPLORATORY]**
The escalation path is wired. No live test has been run. Whether the REASONER produces high-quality taint specs for non-Java code is unknown.
Next: Test with live LM Studio on intentionally low-confidence IR content.

**E-003 — cil-forge Rust gate runner is faster than Python equivalent [EXPLORATORY]**
No benchmark run. Architectural reasoning supports the hypothesis (L1 cache locality, zero GC, SoA layout).
Next: Benchmark experiment with identical content sample set.

**E-004 — cil_council online mode produces useful synthesis for novel vulnerability class identification [EXPLORATORY]**
Offline path graceful. Online path untested. synthesize_novel_class() is implemented but never run.
Next: Test with LM Studio when available.

---

## Quarantined Claims
_(overclaiming, theater, or single-pass validation)_

_(None yet. If any assertion above cannot meet its replay trigger, it will be moved here.)_

---

## Collapsed Paths
_(fully exhausted under closure standard — five conditions met)_

**C-001 — MAGI multi-model council as viable architecture**
Closed by Axiom 4 (Weights ARE Memory) + bilateral attractor analysis. Not a failed implementation — wrong architectural class. Replaced by cil_council bilateral design.
Evidence: MONOSPEC_v2.0_OMEGA.md; architectural analysis.

**C-002 — Hardcoded language="python" in _genome_bundle()**
Root cause bug, now fixed. All non-Python vulnerabilities were silently falling through. Fix verified: 38/38 assault pass. Path closed.
Evidence: Root cause analysis in session MHT; post-fix assault pass.

---

## Open Tensions
_(contradictions not yet resolved)_

**T-001 — cil_council.py self-audit false positive vs. Law 1 enforcement**
The forge's Law 1 detection (token_placeholder_check) fires on cil_council.py's own Codex audit code — which contains the strings "TODO", "FIXME" etc. as detection targets. The forge is correct to flag these patterns. The council code is correct to check for them. The tension: how to encode detection strings in the council so the forge's scanner doesn't fire on them without making the council's audit code unreadable.
Resolution path: Encode detection strings in the council; or add an explicit exemption for "detection pattern strings" to token_placeholder_check.
Priority: P0 — blocking verify_build.

**T-002 — Confirmatory replication of 38/38 not yet scheduled**
The assault pass is the foundational result. Under the SOP it is EXPLORATORY (no pre-stated kill criterion). Promoting to STABLE requires a confirmatory run with pre-stated hypothesis and kill criterion. This is a process tension, not a technical one.
Resolution path: EXP-20260329-002 (confirmatory assault pass replication).
Priority: P1.
