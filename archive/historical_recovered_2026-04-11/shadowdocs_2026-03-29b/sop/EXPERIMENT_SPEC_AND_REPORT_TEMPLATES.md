# Experiment Spec Template
_Version: 2026-03-29_

Complete this before running. For confirmatory experiments, also file in the Pre-Registration Log.

---

```
EXPERIMENT ID:           [EXP-YYYYMMDD-NNN]
TITLE:                   [descriptive — not "test 3"]
MODE:                    CONFIRMATORY / EXPLORATORY
WORKSTREAM:              [which scorecard line this feeds]

GOAL:
  [one sentence — what question this answers]

HYPOTHESIS (confirmatory only):
  [exactly one falsifiable claim]

KILL CRITERION (confirmatory only):
  [exactly what result would falsify the hypothesis — specific and measurable]
  [if you cannot state this, reclassify as exploratory]

SUCCESS THRESHOLD (confirmatory only):
  [minimum result to consider hypothesis supported]

BASELINES:
  Internal:  [current incumbent or simpler version]
  External:  [mandatory — a minimal comparator outside the project]
  [if no external baseline, state why and flag for addition]

VARIANTS:
  [what changes between conditions]

STRUCTURAL DISTINCTNESS CHECK:
  [explicit statement that conditions are genuinely different]
  [identical results from these conditions = implementation error, not data]

SAMPLE / SEED PLAN:
  N:       [number of samples/runs]
  Seeds:   [explicit seeds — reproducibility requirement]
  Splits:  [train/val/test or equivalent]

ANALYSIS PLAN:
  [exactly how results will be analyzed — metric, aggregation, comparison]
  [do not change after data are observed]

NEARBY VARIABLES STILL OPEN:
  [what this experiment does NOT close — mandatory]

WHAT RECURSIVE REPLAY IS TRIGGERED BY A POSITIVE RESULT:
  [which earlier seams must be revisited if hypothesis is supported]

WHAT RECURSIVE REPLAY IS TRIGGERED BY A NULL RESULT:
  [which earlier seams must be revisited if hypothesis is not supported]
```

---

# Experiment Report Template
_Version: 2026-03-29_

Complete after execution. Update the Evaluation Log, Deviation Log (if any), and Revisit Ledger.

---

```
EXPERIMENT ID:           [matches spec]
DATE COMPLETED:          [timestamp]
MODE:                    CONFIRMATORY / EXPLORATORY
WORKSTREAM:              [scorecard line]

HYPOTHESIS TESTED:
  [exact claim from spec]

RESULT SUMMARY:
  [what actually happened — specific numbers/outcomes]

VERDICT:
  SUPPORTED / NOT SUPPORTED / INCONCLUSIVE / NULL
  [null results must still be recorded — they are data]

WHAT CHANGED (vs. baseline):
  [specific deltas]

WHAT DID NOT CHANGE:
  [what remained stable]

EXTERNAL BASELINE COMPARISON:
  [how result compares to external comparator — mandatory]

DEVIATIONS FROM PLAN:
  [any — list deviation IDs; if none, state "none"]

EVALUATION THEATER CHECK:
  [were conditions structurally distinct? evidence?]
  [if identical results: flag as theater, audit before accepting]

RESIDUALS (what this experiment does NOT resolve):
  [mandatory — no experiment resolves everything]

NEARBY VARIABLES STILL OPEN:
  [what the spec listed — update if changed]

CONFIDENCE:
  HIGH / MEDIUM / LOW
  [reasoning: sample size, seed coverage, baseline quality, deviation count]

DOCTRINE EFFECT:
  [what this changes in the belief system — or "none" if truly nothing changed]

RECURSIVE REPLAY OBLIGATIONS:
  [what earlier seams must now be revisited — specific]

NULL RESULT RECORDED IN EVALUATION LOG:
  YES / N/A

NEXT ACTION:
  [specific, ordered — not "continue exploring"]
```
