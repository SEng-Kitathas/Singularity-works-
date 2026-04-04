# Live Shadow
_Version: 2026-04-03a_

## Purpose
This file SHALL hold the minimum high-fidelity active state of the current conversation.
It is the bounded reinforcing sub-context window used to resist compaction drift and stale continuity.

## Operating rule
Before every reply:
1. Re-read this file.
2. Re-read the last 10 conversational turns.
3. Reconcile both against the current user request.
4. Update this file if load-bearing state changed.

## Required sections
- Thread identity
- Active user intent
- Current authoritative state
- Active constraints
- Decisions locked in
- Open loops
- Immediate next step
- Last 10 turn reinforcement window
- Delta since previous shadow

## Template
```md
# LIVE SHADOW

## Thread Identity
- Thread:
- Last Updated:
- Mode:
- Dominant Objective:

## Active User Intent
- 

## Current Authoritative State
- 

## Active Constraints
- 

## Decisions Locked In
- 

## Open Loops
- 

## Immediate Next Step
- 

## Last 10 Turn Reinforcement Window
1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 

## Delta Since Previous Shadow
- 
```

---
## Provenance tail
- Artifact ID: `10A SHALL_INIT_LIVE_SHADOW_NEXT.md`
- Artifact class: `live_shadow`
- Authority scope: `minimum high-fidelity active conversation state`
- Default read-next file: `10B SHALL_INIT_DESIGN_THREAD_STREAM_NEXT.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `direct update permitted each turn; preserve bounded size and explicit deltas`
- This artifact SHALL NOT be treated as authoritative in isolation.
