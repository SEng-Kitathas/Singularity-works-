# Experiment Report
_Version: 2026-03-31i_

## Purpose
Use this instrument after executing a pressure pass, test, benchmark, probe, or comparison.

## Operator / lab meaning
This file is where reality gets the last word.
Its job is to record what actually happened, what changed, what held up, what broke, and what uncertainty survived contact.

## Model / control obligations
The model SHALL:
- report outcome against the predeclared spec
- preserve both strengthening and weakening evidence
- record deviations from the experiment plan
- distinguish invalid result from negative result
- preserve residual uncertainty and next action

The model SHALL NOT:
- write victory fiction
- hide failed branches if they taught something
- silently upgrade confidence beyond what the evidence supports

## Template
### Experiment
<fill in>

### Date / run context
- <fill in>

### Outcome
- <pass/fail/mixed/inconclusive/invalid>

### Evidence
- <fill in>

### Divergences from spec
- <fill in>

### What strengthened
- <fill in>

### What weakened
- <fill in>

### What surprised us
- <fill in>

### Residual uncertainty
- <fill in>

### Artifact outputs produced
- <fill in>

### Recommendation
- <adopt/iterate/retest/hold/reject>

### Next action
- <fill in>

## Known failure modes this file suppresses
- survivorship-biased reporting
- confidence inflation
- post-hoc rationalization
- loss of useful failure signal

## Update rule
If multiple runs exist, either append a separate report per run or clearly mark run boundaries inside this file. Do not blend incompatible runs into one synthetic result.

## Normative note
Residual uncertainty SHALL survive the report. Do not write victory fiction.

---
## Provenance tail
- Artifact ID: `14 SHALL_RECORD_EXPERIMENT_REPORT_AFTER_EXECUTION.md`
- Artifact class: `experiment_report`
- Authority scope: `post-execution reporting`
- Default read-next file: `15 SHALL_RECORD_MAINTENANCE_NOTE_WHEN_STATE_MUTATES.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `append reports rather than silently rewriting outcomes when possible`
- This artifact SHALL NOT be treated as authoritative in isolation.
