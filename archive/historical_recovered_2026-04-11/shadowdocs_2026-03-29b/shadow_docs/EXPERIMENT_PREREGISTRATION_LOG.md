# Experiment Pre-Registration Log — Singularity Works / CIL vNext
_Version: 2026-03-29_
_SOP: R-16, R-17 — mode declared before execution; kill criteria mandatory for confirmatory_

---

```
EXPERIMENT ID:           EXP-20260329-001
DATE PRE-REGISTERED:     2026-03-29
MODE:                    CONFIRMATORY
WORKSTREAM:              CIL Memory / Genome Selection
HYPOTHESIS:              Calibrated distortion_budget from smem_get_priors() produces
                         measurably different genome capsule selection vs. fixed budget=0.20,
                         and this difference results in >= 1 additional true positive or
                         >= 1 fewer false positive in the assault pass.
WHAT WOULD FALSIFY:      Calibrated and uncalibrated budgets produce identical capsule
                         selection across all 38 assault cases (zero delta in hit pattern).
                         OR: calibrated selection produces MORE false positives than uncalibrated.
SUCCESS THRESHOLD:       >= 1 true positive gained OR >= 1 false positive eliminated
                         that is directly attributable to the calibrated budget.
ANALYSIS PLAN:           1. Run assault pass with fixed distortion_budget=0.20 (control)
                         2. Run forge_context through 3 sessions to build SMEM state
                         3. Run assault pass again with calibrated budget active
                         4. Compare per-case results: any delta in hit/miss/FP pattern?
                         5. If delta: verify causally linked to budget change, not other variance
BASELINES:
  Internal:  38/38, FP=0 with fixed budget (current incumbent)
  External:  no external baseline available for this specific integration test
             (flag: process debt — add an external static analysis tool comparison)
VARIANTS:    fixed budget=0.20 vs. calibrated budget from smem_get_priors()
STRUCTURAL DISTINCTNESS: The two conditions differ in exactly one variable: whether
                         distortion_budget is fixed or SMEM-calibrated. All else equal.
                         If identical results: calibration has no effect — record as NULL.
SAMPLE/SEED PLAN:
  N:       38 assault cases (deterministic — no sampling)
  Seeds:   N/A (deterministic pipeline)
  Splits:  N/A
DEVIATION POLICY:        Any deviation from above logged in Deviation Log before analysis.
NEARBY VARIABLES STILL OPEN:
  - Does calibration affect performance on novel (unseen) vulnerability classes?
  - Does calibration degrade over time if SMEM accumulates incorrect beliefs?
WHAT RECURSIVE REPLAY IS TRIGGERED BY A POSITIVE RESULT:
  - RC-001 (temperature↔distortion) promoted from EXPLORATORY to CONFIRMATORY signal
  - smem_get_priors() design confirmed — extend to semantic_vq.rs in CRHQ
WHAT RECURSIVE REPLAY IS TRIGGERED BY A NULL RESULT:
  - TM-008 status → COLLAPSED for this specific integration
  - Re-examine whether smem_get_priors() is the right integration point
  - Consider whether distortion_budget should feed into genome scoring, not bundle selection
STATUS:                  REGISTERED — not yet executed
```

---

```
EXPERIMENT ID:           EXP-20260329-002
DATE PRE-REGISTERED:     2026-03-29
MODE:                    CONFIRMATORY
WORKSTREAM:              Forge / Detection
HYPOTHESIS:              The assault pass (38/38, FP=0, FN=0) is reproducible from
                         the current codebase (SW-v1_13.zip) with a fresh execution
                         on a clean tmp directory.
WHAT WOULD FALSIFY:      Any score < 38/38, or any FP > 0, on the 38-case assault
                         suite with an unmodified checkout of SW-v1_13.zip.
SUCCESS THRESHOLD:       38/38, FP=0, FN=0 (exact match — no tolerance).
ANALYSIS PLAN:           1. Extract SW-v1_13.zip to a fresh /tmp directory
                         2. Run examples/verify_build.py — confirm baseline (good/bad/bad_rem)
                         3. Run the 38-case assault script from scratch
                         4. Compare results against DEV-20260329-001's exploratory result
BASELINES:
  Internal:  Prior exploratory run: 38/38, FP=0, FN=0 (session MHT)
  External:  None (no external comparable benchmark)
VARIANTS:                Fresh directory extraction vs. in-session state
STRUCTURAL DISTINCTNESS: The key distinction is filesystem state — fresh extract vs.
                         accumulated session state. If results differ: session state contamination.
SAMPLE/SEED PLAN:        N=38 (deterministic), no seeds, no splits.
DEVIATION POLICY:        Any deviation logged before analysis.
NEARBY VARIABLES STILL OPEN:
  - Are results stable across Python versions (3.10 vs 3.12)?
  - Are results stable if configs/ directory is regenerated vs. extracted from zip?
WHAT RECURSIVE REPLAY IS TRIGGERED BY A POSITIVE RESULT:
  - P-001 can be advanced toward STABLE (one confirmatory replication done)
  - Confidence in "assault pass is the foundational result" increases significantly
WHAT RECURSIVE REPLAY IS TRIGGERED BY A NULL RESULT:
  - P-001 demoted to QUARANTINED pending investigation
  - Root cause: session state contamination? Nondeterminism in detection? Filesystem?
  - Pause all other build work — this is the foundation
STATUS:                  REGISTERED — not yet executed
```

---

```
EXPERIMENT ID:           EXP-20260329-003
DATE PRE-REGISTERED:     2026-03-29
MODE:                    EXPLORATORY
WORKSTREAM:              Forge / Safety (cil_council.py)
GOAL:                    Fix the cil_council.py self-audit false positive (P0 blocker).
                         Identify encoding approach that passes forge self-audit without
                         degrading the council's own Law 1 detection capability.
SCOPE:                   cil_council.py token_placeholder_check false positive.
                         singularity_works/genome_gate_factory.py token_placeholder_check strategy.
WHAT WOULD BE INTERESTING:
                         An encoding (e.g., join-based string construction, Unicode lookalike,
                         comment guard, or strategy exemption) that:
                         (a) passes verify_build.py with 0 failures
                         (b) preserves the council's ability to detect actual Law 1 violations
WHAT WOULD NOT:          A brute-force suppression that disables the strategy globally.
                         That would be a Law 1 violation in the detection system itself.
NOTE:                    Results from this experiment are TENTATIVE.
                         A confirmatory experiment verifying (a) and (b) independently
                         is required before promoting the fix.
STATUS:                  PLANNED — next immediate action
```

---

_Log is append-only. Future experiments added below._
