# Failure And Recovery Protocol
_Version: 2026-03-31k_

## Purpose
This file defines how the archive responds when execution breaks, contradicts itself, deadlocks, or loses a clean continuation path.

Its operator role is to make recovery explicit.
Its control role is to stop silent drift, hand-waving, and fake continuity after a break.

## Core rule
Failure is not terminal by default.
Failure is a signal that the current state surface is no longer safe to trust without correction.

## Failure conditions
A failure condition exists when any of the following occurs:
- contradiction in logic or state
- chain break or missing required file
- missing required evidence for a claimed step
- execution deadlock or empty loop
- invalid output structure
- role mismatch that is now degrading the work
- verification failure against the package integrity surfaces

## On failure detection
When a failure condition is detected, the model SHALL:
1. halt forward narration
2. enter Diagnostic Mode
3. name the failure condition directly
4. identify the last known valid node
5. separate verified state from provisional salvage

## Recovery procedure
After diagnosis, the model SHALL:
1. backtrack to the last verified node
2. re-evaluate the assumption that caused the break
3. apply the minimum correction needed to restore progress
4. re-enter execution from the nearest still-valid point
5. update state surfaces if the correction changes the live project picture

## Escalation rule
If the failure survives two clean recovery attempts, the model SHALL:
- activate Adaptive Interpretation Mode
- preserve the highest-order archive intent still available
- continue with the best valid approximation
- log the persistent failure rather than hiding it

## Logging requirement
All material failures SHALL be recorded in the appropriate live-state surfaces, especially:
- `09 SHALL_INIT_REVISIT_LEDGER_NEXT.md`
- `10 SHALL_INIT_TRACE_MATRIX_NEXT.md`
- `15 SHALL_RECORD_MAINTENANCE_NOTE_WHEN_STATE_MUTATES.md` when state semantics materially change

## SHALL NOT rules
- SHALL NOT fake continuity after a known break
- SHALL NOT treat contradiction as acceptable merely because prose still sounds smooth
- SHALL NOT keep executing from a state already shown to be invalid
- SHALL NOT hide repeated failure behind vague optimism

## Completion rule
This file has done its job for the pass when the work either:
- returns to a valid execution path
- or records an honestly bounded best-valid approximation

---
## Provenance tail
- Artifact ID: `06A SHALL_RUN_FAILURE_RECOVERY_PROTOCOL_NEXT.md`
- Artifact class: `failure_recovery_protocol`
- Authority scope: `failure detection, backtracking, and recovery discipline`
- Default read-next file: `07 SHALL_INIT_NEXT_STEPS_NEXT.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `visible replacement + version bump + provenance regeneration`
- This artifact SHALL NOT be treated as authoritative in isolation.
