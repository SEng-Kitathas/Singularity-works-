# Shadow Pair Maintenance Protocol
_Version: 2026-04-03a_

## Purpose
This protocol defines how the Live Shadow and Design Thread Stream SHALL be maintained together so they act as a genuine anti-drift continuity layer rather than two stale notes.

## Mandatory per-reply loop
Before every reply:
1. Re-read `10A SHALL_INIT_LIVE_SHADOW_NEXT.md`.
2. Re-read the last 10 conversational turns.
3. Reconcile both against the current request.
4. Check whether load-bearing state changed.
5. If yes, update the Live Shadow before or alongside the reply.

After each meaningful exchange:
1. Append the new user turn to the Design Thread Stream.
2. Append the new assistant turn to the Design Thread Stream.
3. Record any material state mutation in the maintenance note if doctrine, state, or next-step semantics changed.

## No-stale rule
The shadow pair SHALL be considered stale if any of the following are true:
- the last 10 turn window no longer reflects the current local thread reality
- the Live Shadow omits a newly locked-in decision
- the Design Thread Stream skipped a state-changing exchange
- the Immediate Next Step no longer matches actual work

If stale, repair the shadow pair before widening the workstream.

## Recovery rule
When continuity appears damaged:
1. Read the Live Shadow.
2. Read the Last 10 Turn Reinforcement Window.
3. Read backward through the Design Thread Stream.
4. Reconstruct authoritative state.
5. Resume only after the shadow pair is current again.

---
## Provenance tail
- Artifact ID: `10C SHALL_MAINTAIN_SHADOW_PAIR_EACH_TURN_NEXT.md`
- Artifact class: `continuity_protocol`
- Authority scope: `bounded shadow maintenance and anti-drift discipline`
- Default read-next file: `11 SHALL_USE_RESEARCH_CROSSWALK_WHEN_NEEDED.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `visible replacement + version bump when protocol changes; otherwise execute as written`
- This artifact SHALL NOT be treated as authoritative in isolation.
