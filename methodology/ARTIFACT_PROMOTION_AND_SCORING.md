# ARTIFACT PROMOTION AND SCORING — PCMMAD

## PURPOSE
Define how artifacts advance from working outputs to promoted authority surfaces.

## ELIGIBLE ARTIFACTS
Artifacts MAY include:
- runnable harnesses
- integrated codebases
- authority bundles
- reports
- merge products
- kill verdicts

## SCORING AXES
Each artifact SHALL be scored 0–5 on:

1. REALITY
- Is it runnable, testable, or falsifiable?

2. TARGET FIT
- Does it solve the declared target?

3. COHESION
- Is it internally consistent and architecturally native?

4. DRIFT DISCIPLINE
- Does it surface uncertainty, conflicts, and boundaries clearly?

5. REUSE VALUE
- Can other Labs adopt or build on it cleanly?

## SCORE INTERPRETATION
- 22–25 = PROMOTION CANDIDATE
- 17–21 = HOLD / ITERATE
- 10–16 = PARTIAL / SUPPORTING
- 0–9 = KILL OR ARCHIVE ONLY

## PROMOTION RULES
An artifact MAY be promoted when:
- it is at least RECONCILED and preferably RUNNABLE or better
- it scores high enough
- it does not conflict with current authority
- it is worth protecting from silent drift

Upon promotion:
- assign state label
- declare authority scope
- add or reference in manifest / sealed topology when appropriate
- note superseded artifacts if any

## OUTPUT FORMAT
[PROMOTION REVIEW]
- Artifact:
- State:
- Scores:
  - Reality:
  - Target Fit:
  - Cohesion:
  - Drift Discipline:
  - Reuse Value:
- Total:
- Decision:
- Supersedes:
- Notes:

## RULE
Promotion is earned by artifact strength, not by narrative excitement.

---
## Provenance tail
- Artifact ID: `ARTIFACT_PROMOTION_AND_SCORING.md`
- Artifact class: `artifact_promotion_protocol`
- Authority scope: `artifact scoring and promotion criteria`
- Default read-next file: `CROSS-LAB_MERGE_PROTOCOL.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `visible replacement + version bump + provenance regeneration`
- This artifact SHALL NOT be treated as authoritative in isolation.
