# Revisit Ledger
_Version: 2026-03-31i_

## Purpose
This file records claims, seams, and decisions that must return for replay, confirmation, or demotion pressure.

It has two simultaneous jobs:
1. give the operator a visible ledger of what still needs to come back under pressure
2. stop the model from letting unresolved issues disappear into the sediment of a long thread

## Operator / lab meaning
Use this file when something is:
- provisionally accepted but not fully earned
- blocked on new evidence
- likely stale after a new discovery
- worth replaying under stronger method pressure
- vulnerable to demotion or reversal

If it matters enough to revisit, it matters enough to log.

## Model / control obligations
When something is not settled enough to vanish, the model SHALL record it here.
Do not bury revisits inside prose.
Do not let uncertainty evaporate because the thread moved on.

## Template

| Date | Seam / Claim / Decision | Why revisit | What could invalidate it | Evidence or action needed | Priority | Current status | Next action |
|---|---|---|---|---|---|---|---|
| <fill in> | <fill in> | <fill in> | <fill in> | <fill in> | <P0/P1/P2> | <open / blocked / replaying / resolved> | <fill in> |

## Logging rule
Create a revisit entry when any of the following is true:
- confidence is not yet load-bearing
- a claim depends on missing evidence
- a stronger test exists but has not yet been run
- new information may obsolete the current answer
- a promoted conclusion may need demotion

## Completion rule
This file is complete for the pass when every known replay-worthy seam has a visible place to return from.

---
## Provenance tail
- Artifact ID: `09 SHALL_INIT_REVISIT_LEDGER_NEXT.md`
- Artifact class: `live_state_revisit`
- Authority scope: `replay obligations and unresolved seams`
- Default read-next file: `10 SHALL_INIT_TRACE_MATRIX_NEXT.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `direct update permitted during active pass; record maintenance when semantics materially change`
- This artifact SHALL NOT be treated as authoritative in isolation.
