# Experiment Spec
_Version: 2026-03-31i_

## Purpose
Use this instrument before applying pressure to a claim, design, pattern, workflow, or implementation path.

## Operator / lab meaning
This file converts "we should test that" into a falsifiable plan.
It exists to stop vague experimentation, moving goalposts, and post-hoc victory narratives.

## Model / control obligations
The model SHALL:
- state the claim under pressure in testable terms
- define success and failure before execution
- identify the incumbent baseline or comparator
- record assumptions, constraints, and observables
- preserve expected outputs so missing artifacts are visible

The model SHALL NOT:
- backfill criteria after running the test
- hide dependence on unstated assumptions
- run a pressure pass whose outputs cannot be inspected afterward

## Template
### Objective
<fill in>

### Claim / hypothesis under pressure
<fill in>

### Why this matters
- <fill in>

### Baseline / comparator
- <fill in>

### Inputs
- <fill in>

### Constraints / environment
- <fill in>

### Procedure
1. <fill in>

### Observables to capture
- <fill in>

### Success criteria
- <fill in>

### Failure criteria
- <fill in>

### Abort / invalidation conditions
- <fill in>

### Expected artifact outputs
- <logs/reports/patches/metrics/diffs/etc>

### Speculative branches worth probing (Law Sigma)
- <fill in>

## Known failure modes this file suppresses
- test-shaped theater
- moving goalposts
- untracked environmental assumptions
- results that cannot be reproduced or audited

## Update rule
If execution diverges materially from this spec, record the divergence in the experiment report rather than silently editing the spec to match reality.

## Normative note
No experiment SHALL be treated as complete until success criteria, failure criteria, and observables are explicit.

---
## Provenance tail
- Artifact ID: `13 SHALL_DEFINE_EXPERIMENT_SPEC_WHEN_PRESSURE_IS_REQUIRED.md`
- Artifact class: `experiment_spec`
- Authority scope: `test design and pressure setup`
- Default read-next file: `14 SHALL_RECORD_EXPERIMENT_REPORT_AFTER_EXECUTION.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `append reports rather than silently rewriting outcomes when possible`
- This artifact SHALL NOT be treated as authoritative in isolation.
