# Rehydration Note
_Version: 2026-03-31i_

## Why this file exists
This file protects long-running work from one of the most common project-killers in LLM sessions: state drift.
It is both a memory recovery protocol and a reminder that recent chat continuity is not the same thing as reliable project state.

## Load-first rule
Before substantive work, the model SHALL:
1. Read this note.
2. Read the master SOP.
3. Read the model-role routing file.
4. Read the current state / next steps / doctrine snapshot.
5. Read the latest extraction docs, if any exist.
6. Re-state only:
   - incumbent baseline
   - open seams
   - what is actually verified
   - what is still provisional
   - current mode state
   - active role
   - what changed since the last meaningful pass
   - immediate next actions

## Re-entry compression rule
When rehydrating, prefer the compressed ingress grammar from `01 SHALL_READ_BOOTSTRAP_PROMPT_SHIM_NEXT.md` unless the operator explicitly wants a fuller doctrinal recap.

## Restart rule
If context is lost, compaction occurs, or the thread drifts:
- stop widening
- reload the control files
- restate baseline versus open seams
- restate discussion-state versus build-state
- continue only after re-establishing current state

## Memory warning
Never trust recent chat memory alone for a nontrivial project.

## Reality warning
Discourse is not evidence.
Synthesis is not verification.
Model agreement is not truth.

## Anti-ritual warning
Rehydration is not an excuse to burn turns re-explaining the archive to itself.
Re-establish the minimum viable state and continue the work.

## Normative reminder
The model SHALL rehydrate baseline, open seams, verified vs provisional split, current mode state, active role, and current next actions before widening the conversation again.
The model SHALL NOT assume prior summaries remain complete or current.

---
## Provenance tail
- Artifact ID: `02 SHALL_READ_REHYDRATION_NOTE_NEXT.md`
- Artifact class: `rehydration_control`
- Authority scope: `re-entry and state-loss recovery`
- Default read-next file: `03 SHALL_READ_MASTER_SOP_NEXT.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `visible replacement + version bump + provenance regeneration`
- This artifact SHALL NOT be treated as authoritative in isolation.
