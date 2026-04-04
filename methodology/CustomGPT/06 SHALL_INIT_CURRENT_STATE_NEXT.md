# Current State
_Version: 2026-03-31k_

## Purpose
This file is the live state surface for the current workstream.

It has two simultaneous jobs:
1. give the operator a legible snapshot of what the project currently is
2. force the model to separate verified state from provisional narrative before it starts improvising

## Operator / lab meaning
Use this file to answer:
- what the project is
- what mode it is in
- what baseline is currently load-bearing
- what has actually been verified
- where the work should resume without re-deriving the whole thread

A good current-state file is not a diary.
It is the minimum reliable snapshot needed to restart work cleanly.

## Model / control obligations
When this file is initialized or updated, the model SHALL:
- make the active mode explicit
- distinguish verified state from provisional state
- separate incumbent baseline from open seams
- record the chosen start role and its likely bias when role routing matters
- keep this file short enough to be operational, but concrete enough to survive rehydration
- SHALL NOT fill gaps with vibe, prestige, or conversational momentum

## Minimum fill standard
Do not leave the following structurally unresolved:
- project identity
- mode state
- incumbent baseline
- verified vs provisional split
- resume point

## Template

### Project name
<fill in>

### One-sentence mission
<fill in>

### Current mode state
- <DISCUSSION / BUILD>

### Why this is the current mode
- <trigger language or arbitration result>

### Current corpus / evidence base
- <chat thread / uploaded files / external evidence / mixed>

### Active law stack / doctrine deltas
- <local adaptation, override, or “none”>

### Current incumbent baseline
- <the thing currently treated as the best surviving architecture, method, or conclusion>

### Open seams
- <the highest-friction unresolved questions>

### What is actually verified
- <facts, tests, readings, experiments, or direct evidence already earned>

### What is still provisional
- <hypotheses, extrapolations, pending checks, or unverified claims>

### Current blockers
- <missing evidence, unresolved contradiction, tooling issue, ambiguity, etc.>

### Current risks / technical debt
- <drift risk, stale assumption, untested seam, provenance gap, etc.>

### Active role routing
- Start role: <R1 / R2 / R3 / R4 / R5>
- Why this role is active: <fill in>
- Likely bias / failure mode in this context: <fill in>
- Likely next role handoff: <fill in>

### Resume point
<the exact next load-bearing place to restart work>

### Failure / recovery status
- Last known valid node: <fill in>
- Active failure condition: <none / fill in>
- Recovery mode active: <yes / no>

### Next mutation that would require this file to change
<what event would make this snapshot stale>

## Update trigger
Update this file whenever any of the following materially changes:
- baseline
- mode state
- evidence base
- role routing
- verified/provisional boundary
- resume point

## Completion rule
This file is complete for the pass when a future reader could restart the work without pretending old prose is still current truth.

---
## Provenance tail
- Artifact ID: `06 SHALL_INIT_CURRENT_STATE_NEXT.md`
- Artifact class: `live_state_current`
- Authority scope: `current project state snapshot`
- Default read-next file: `06A SHALL_RUN_FAILURE_RECOVERY_PROTOCOL_NEXT.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `direct update permitted during active pass; record maintenance when semantics materially change`
- This artifact SHALL NOT be treated as authoritative in isolation.
