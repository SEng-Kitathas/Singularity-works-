# Evaluation Log — Singularity Works / CIL vNext
_Version: 2026-03-29_
_SOP: §15 — separate scorecards per workstream; null results recorded_

---

## WORKSTREAM: Forge / Detection
DESCRIPTION: Vulnerability detection accuracy across polyglot code samples.
EMPIRICAL FOOTHOLD: YES

### Results Table
| Exp ID | Hypothesis | Mode | Verdict | Confidence | Residuals | Doctrine Effect |
|---|---|---|---|---|---|---|
| Pre-SOP-001 | Forge detects 38/38 known vulns with FP=0 after root cause fixes | EXPLORATORY | SUPPORTED | MEDIUM (no pre-stated kill criterion; exploratory) | Confirmatory replication needed; 4 FN remain (all architectural limits) | P-001, P-002 established |
| Pre-SOP-002 | Self-audit: forge audits own source at same standard | EXPLORATORY | SUPPORTED | MEDIUM | Only law-compliance warns remain | TM-002 established |

### Current Incumbent Baseline
38/38 assault pass, FP=0, FN=0. Core hammer 20/20.
**Status: EXPLORATORY — confirmatory replication pending (EXP-20260329-002)**

### Promoted Findings
- Assault pass 38/38 — PROVISIONAL (P-001)
- Root cause analysis (3 bugs → 7 ambers fixed) — PROVISIONAL (P-002)
- 13 new capsules / 12 new strategies effective — PROVISIONAL (TM-013)

### Provisional Findings (require confirmatory test)
- All above

### Null Results Recorded
- GOROUTINE_LEAK_GO initially failed (routing bug); fixed and included in 38/38.
- SSRF_INDIRECT_RECONSTRUCT initially failed (partial URL validation pattern); fixed.
- OPEN_REDIRECT initially failed (taint tracker nesting bug); fixed.
- GLOBAL_STATE_MUTATION initially failed (dict[param]=value pattern missed); fixed.
- AUTH_BYPASS_ESCALATION was a near-architectural-limit miss; fixed via unsigned JWT strategy.

### Theater Flags
- None confirmed. All conditions were structurally distinct (different code, different detection path).

### Open Questions
- Does 38/38 hold under EXP-20260329-002 (fresh checkout)?
- Do the 4 remaining architectural limit FNs (reflection Java, SSRF chain, etc.) actually represent permanent limits or solvable problems?

---

## WORKSTREAM: Forge / Safety (Substrate-Sovereign)
DESCRIPTION: Protection of the forge's own analysis pipeline against adversarial inputs.
EMPIRICAL FOOTHOLD: YES

### Results Table
| Exp ID | Hypothesis | Mode | Verdict | Confidence | Residuals | Doctrine Effect |
|---|---|---|---|---|---|---|
| Pre-SOP-003 | 5 adversarial tests pass (ReDoS, stack overflow, memory, truncate-not-reject, real vuln preserved) | EXPLORATORY | SUPPORTED | MEDIUM | No testing on intermediate-size inputs (500KB–2MB range) | P-003 established |

### Current Incumbent Baseline
2MB gate at _parse(), build_ir(), Orchestrator.run(). _safe_dotall_finditer() at 500KB chunks.
Truncate-not-reject: real vulns at file top still caught.
**Status: EXPLORATORY — no confirmatory replication**

### Promoted Findings
- Substrate-Sovereign gates — PROVISIONAL (P-003)

### Null Results Recorded
- None (this workstream had no failures in the adversarial test suite)

### Theater Flags
- None. Each adversarial test uses a structurally distinct input class.

---

## WORKSTREAM: CIL Memory (Python)
DESCRIPTION: ForgeContext v4.0 SBUF/EPMEM/SMEM/Contradiction stack, Python side.
EMPIRICAL FOOTHOLD: PARTIAL (smoke tested; not assault-scale tested)

### Results Table
| Exp ID | Hypothesis | Mode | Verdict | Confidence | Residuals | Doctrine Effect |
|---|---|---|---|---|---|---|
| Pre-SOP-004 | ForgeContext v4.0 SBUF→EPMEM consolidation works across 3 sessions | EXPLORATORY | SUPPORTED | LOW (3 sessions only; tiny dataset) | SMEM not yet at ProvisionalSemantic threshold; ContradictionBlock not yet triggered by real contradiction | TM-007; P-004, P-005 established |

### Current Incumbent Baseline
ForgeContext v4.0 wired into Orchestrator. SBUF auto-pushes on gate results. Consolidation after run().
**Status: EXPLORATORY — E2E integration test pending (TM-020)**

### Promoted Findings
- Zep 4-field bi-temporal model adopted — PROVISIONAL (P-004)
- distortion_budget calibration implemented — PROVISIONAL (P-005, E-001)
- smem_get_priors() returns calibrated budgets — PROVISIONAL

### Provisional Findings
- All above

### Null Results Recorded
- SMEM never advanced to StableSemantic in smoke test (only 3 sessions — threshold is 6 witnesses). Expected null, not a failure.

### Theater Flags
- None

### Open Questions
- Does SMEM correctly advance to ProvisionalSemantic after N+ sessions with assault suite?
- Does ContradictionBlock fire when a previously-green capsule produces a red result?

---

## WORKSTREAM: CIL Memory (Rust / cil-forge)
DESCRIPTION: Rust ECS substrate — cil.rs SBUF/EPMEM/ContradictionGraph; cil-forge scaffold.
EMPIRICAL FOOTHOLD: YES (unit tests) / NO (integration tests)

### Results Table
| Exp ID | Hypothesis | Mode | Verdict | Confidence | Residuals | Doctrine Effect |
|---|---|---|---|---|---|---|
| Pre-SOP-005 | cil.rs unit tests pass: SBUF invariants, Zep mechanism, epistemic progression, distortion calibration | EXPLORATORY | SUPPORTED | MEDIUM (unit tests are narrow) | No integration test; no Python oracle comparison | TM-004, TM-006; P-007, P-008 |
| Pre-SOP-006 | cil-forge Rust ECS scaffold compiles (cargo check clean) | EXPLORATORY | SUPPORTED | HIGH (compilation is definitive) | Systems are stubs; no gate runner integration | TM-010 |

### Current Incumbent Baseline
cil.rs: SBUF (max 10k, INV-1 through INV-SBUF-5), BiTemporal (4-field), ContradictionGraph (petgraph), distortion calibration.
cil-forge: hecs archetype, 7 system stubs, cargo test 4/4.
**Status: Unit-level EXPLORATORY; integration OPEN**

### Promoted Findings
- ContradictionGraph petgraph implementation — PROVISIONAL (P-008)
- hecs archetype ECS confirmed — PROVISIONAL (P-007)

### Null Results Recorded
- None at unit test level

### Theater Flags
- None

### Open Questions
- Does cil-forge gate_runner produce identical results to Python forge on same content?

---

## WORKSTREAM: Forge / IRIS Escalation
DESCRIPTION: IRIS-mode escalation when IR confidence is low + no static findings.
EMPIRICAL FOOTHOLD: NO (wired but not live-tested)

### Results Table
| Exp ID | Hypothesis | Mode | Verdict | Confidence | Residuals | Doctrine Effect |
|---|---|---|---|---|---|---|
| Pre-SOP-007 | IRIS escalation path wired; offline graceful (no crash when LM unavailable) | EXPLORATORY | SUPPORTED | HIGH (graceful offline is definitive) | Online quality unknown | TM-009; P-006 partial |

### Current Incumbent Baseline
iris_escalate() in genome_gate_factory.py + system_iris_escalation() in cil-forge.
Wired into orchestrator on low-conf IR + no static findings.
**Status: EXPLORATORY — live test required**

### Promoted Findings
- IRIS dual-architecture isomorphism — PROVISIONAL (P-006)

### Null Results Recorded
- None (live test not yet run — not a null, just untested)

### Open Questions
- Does REASONER (35B) produce usable taint specs for Python/Go/Rust code?
- What is the false positive rate of IRIS escalation on non-vulnerable low-conf IR content?

---

## WORKSTREAM: CIL Council
DESCRIPTION: Dialectic REASONER+CODER loop, MAGI replacement.
EMPIRICAL FOOTHOLD: NO (offline path only)

### Results Table
| Exp ID | Hypothesis | Mode | Verdict | Confidence | Residuals | Doctrine Effect |
|---|---|---|---|---|---|---|
| Pre-SOP-008 | cil_council offline graceful (DEADLOCK, no crash when LM unavailable) | EXPLORATORY | SUPPORTED | HIGH (graceful offline definitive) | Online quality, consensus rate, false agree rate all unknown | TM-011; P-010 |

### Current Incumbent Baseline
cil_council.py: 2-role bilateral, max_rounds, Codex Omega audit on output.
**Status: EXPLORATORY — P0 bug (TM-012 self-audit false positive) blocking**

### Promoted Findings
- MAGI dead, bilateral attractor confirmed architecturally — PROVISIONAL (P-010)

### Null Results Recorded
- None (live test not run)

### Theater Flags
- None

### Open Questions
- P0: Fix self-audit false positive before any further development (EXP-20260329-003)
- What is consensus rate on known-correct security claims?

---

## WORKSTREAM: Process
DESCRIPTION: SOP adherence, shadow doc discipline, process debt tracking.
EMPIRICAL FOOTHOLD: YES (this session is the record)

### Results Table
| Exp ID | Hypothesis | Mode | Verdict | Confidence | Residuals | Doctrine Effect |
|---|---|---|---|---|---|---|
| DEV-20260329-001 | Pre-SOP work classified | N/A | DEVIATION | N/A | All pre-SOP work retroactively EXPLORATORY | Shadow doc backfill required |
| DEV-20260329-002 | MHT Loop+ extraction abbreviated | N/A | DEVIATION | N/A | Some orphan signals may be uncaptured | LOW risk assessed |

### Current Incumbent Baseline
SOP adopted at session end. Shadow doc backfill in progress.
**Status: ACTIVE**

### Active Process Debt
- No git tracking on /tmp/sw_v19 (reproducibility failure risk — named)
- No seed/version pinning on Python forge experiments (MLOps standard not met — named)
- cil_council integration tests require live LM Studio (no offline oracle — named)
- Full Loop+ extraction on MHT deferred (DEV-20260329-002 — low risk, deferred)

### Open Questions
- When does git tracking get established? (Target: before next build session)
