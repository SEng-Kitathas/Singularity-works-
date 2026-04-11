# Revisit Ledger — Singularity Works / CIL vNext
_Version: 2026-03-29_
_SOP: §4 R-09 — no closure by one failed framing; RECURSE is mandatory_

---

```
REVISIT ID:         RV-20260329-001
DATE TRIGGERED:     2026-03-29
TRIGGER:            EXP-20260329-002 (confirmatory assault replication) — if POSITIVE result:
                    38/38 holds on fresh checkout → P-001 advances toward STABLE
SEAMS AFFECTED:     TM-001, P-001, P-002
WHAT MUST BE DONE:  Run 38-case assault suite from clean SW-v1_13.zip extraction.
                    Record per-case results. Compare against exploratory baseline.
PRIORITY:           P1 (high — foundational result)
STATUS:             OPEN
RESOLVED DATE:      —
RESOLUTION:         —
```

---

```
REVISIT ID:         RV-20260329-002
DATE TRIGGERED:     2026-03-29
TRIGGER:            EXP-20260329-002 — if NULL RESULT (score < 38/38 or FP > 0):
                    Fresh checkout fails → P-001 demoted to QUARANTINED
SEAMS AFFECTED:     TM-001, P-001, P-002, TM-002, ALL downstream build work
WHAT MUST BE DONE:  Pause all other development.
                    Root cause: session state contamination? Nondeterminism? Filesystem?
                    Run forensics before any other experiment.
PRIORITY:           P0 if triggered (blocking)
STATUS:             OPEN (contingent on EXP-20260329-002)
RESOLVED DATE:      —
RESOLUTION:         —
```

---

```
REVISIT ID:         RV-20260329-003
DATE TRIGGERED:     2026-03-29
TRIGGER:            EXP-20260329-001 — if POSITIVE (calibrated budget changes hit pattern):
                    distortion_budget calibration is load-bearing → extend to semantic_vq.rs
SEAMS AFFECTED:     RC-001, TM-008, E-001
WHAT MUST BE DONE:  Extend self-calibrating budget to CRHQ semantic_vq.rs codebook training.
                    Promote RC-001 temperature↔distortion isomorphism from EXPLORATORY to
                    CONFIRMATORY signal.
PRIORITY:           P2 (medium)
STATUS:             OPEN (contingent on EXP-20260329-001)
RESOLVED DATE:      —
RESOLUTION:         —
```

---

```
REVISIT ID:         RV-20260329-004
DATE TRIGGERED:     2026-03-29
TRIGGER:            EXP-20260329-001 — if NULL (calibrated budget has no effect):
                    Integration point is wrong → revisit whether distortion_budget
                    should feed into genome scoring or capsule ordering, not selection
SEAMS AFFECTED:     TM-008, RC-001, E-001, smem_get_priors() design
WHAT MUST BE DONE:  Examine alternative integration points:
                    (a) distortion_budget as tiebreaker in capsule scoring
                    (b) distortion_budget as threshold for IRIS escalation trigger
                    (c) distortion_budget as CRHQ parameter only (not forge routing)
PRIORITY:           P2 (medium)
STATUS:             OPEN (contingent on EXP-20260329-001)
RESOLVED DATE:      —
RESOLUTION:         —
```

---

```
REVISIT ID:         RV-20260329-005
DATE TRIGGERED:     2026-03-29
TRIGGER:            When ContradictionGraph is integrated into Python forge (TM-006):
                    Earlier Python ContradictionBlock list → needs upgrade to proper graph
SEAMS AFFECTED:     TM-006, TM-007, P-008
WHAT MUST BE DONE:  Port ContradictionGraph Rust implementation back to Python forge_context.py.
                    Or: use the Rust graph via PyO3 bridge.
                    Verify: contradiction detection in SMEM produces same behavior as Rust unit tests.
PRIORITY:           P2 (medium)
STATUS:             OPEN
RESOLVED DATE:      —
RESOLUTION:         —
```

---

```
REVISIT ID:         RV-20260329-006
DATE TRIGGERED:     2026-03-29
TRIGGER:            When cil-forge system implementations replace stubs (TM-017):
                    Earlier "architecture confirmed" claim → needs empirical validation
                    Does Rust gate runner actually match Python oracle on same inputs?
SEAMS AFFECTED:     TM-017, P-007, RC-004, E-003
WHAT MUST BE DONE:  Run benchmark: identical 38 assault cases through both Python forge
                    and Rust cil-forge. Compare per-case verdicts.
                    Any divergence is a correctness bug, not a performance issue.
PRIORITY:           P1 (high — cil-forge migration path depends on oracle match)
STATUS:             OPEN
RESOLVED DATE:      —
RESOLUTION:         —
```

---

```
REVISIT ID:         RV-20260329-007
DATE TRIGGERED:     2026-03-29
TRIGGER:            When cil_council online mode is tested with live LM Studio:
                    Earlier P-010 (MAGI dead, bilateral attractor confirmed) → needs empirical test
                    Does the bilateral loop actually converge? What is consensus rate?
SEAMS AFFECTED:     TM-011, P-010, E-004
WHAT MUST BE DONE:  Run cil_council.debate() on 10+ known-correct security claims.
                    Record: consensus rate, round distribution, Codex audit results.
                    Record: any case where council produces false consensus.
PRIORITY:           P2 (medium — blocked by LM availability)
STATUS:             OPEN
RESOLVED DATE:      —
RESOLUTION:         —
```
