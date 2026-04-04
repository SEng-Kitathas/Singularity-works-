# Maintenance Note
_Version: 2026-03-31i_

## Purpose
Use this instrument whenever a state-bearing, doctrine-bearing, or process-bearing artifact changes in a way that could affect trust, interpretation, or downstream work.

## Operator / lab meaning
This file is the anti-amnesia surface for corpus mutation.
It records what changed, why it changed, what risks it introduced, and what must be revisited because of the change.

## Model / control obligations
The model SHALL:
- record material mutations to state, doctrine, process, or control files
- distinguish correction from refinement, refactor, scope change, and reversal
- note any drift risk created by the mutation
- name downstream artifacts that now need review

The model SHALL NOT:
- silently rewrite sealed state
- present a changed baseline as if it had always existed
- omit follow-up obligations created by the mutation

## Template
### Date / scope
<fill in>

### Artifact(s) changed
- <fill in>

### Mutation type
- <correction/refinement/refactor/promotion/demotion/reversal/scope change/packaging>

### What changed
- <fill in>

### Why it changed
- <fill in>

### What remains stable
- <fill in>

### Risk / drift concerns
- <fill in>

### Downstream artifacts to revisit
- <fill in>

### Follow-up required
- <fill in>

## Known failure modes this file suppresses
- silent rewrite
- hidden baseline movement
- trust erosion from undocumented mutation
- broken lineage between versions

## Update rule
When a sealed state artifact changes, the mutation SHALL be recorded here or in a directly linked successor artifact before the new state is treated as stable.

## Normative note
When a sealed state artifact changes, the mutation SHALL be recorded here or in a directly linked successor artifact.

---
## Provenance tail
- Artifact ID: `15 SHALL_RECORD_MAINTENANCE_NOTE_WHEN_STATE_MUTATES.md`
- Artifact class: `maintenance_log`
- Authority scope: `mutation logging and state continuity`
- Default read-next file: `16 SHALL_REVIEW_PROMOTION_BEFORE_LOAD_BEARING_OR_CANON.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `append new maintenance notes; do not erase prior state history`
- This artifact SHALL NOT be treated as authoritative in isolation.
