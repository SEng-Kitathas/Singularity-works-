# Forge Resume Checkpoint / Savestate v0.1 — Qualification — 2026-09-03

Status: **READY_WITH_EVIDENCE for bounded local checkpoint lifecycle / crash-loop avoidance semantics**.
Not yet a complete persistent-session, power-loss, or source-transaction recovery qualification.

## Commander intent
Provide emulator-like save-state/resume behavior without repeatedly restoring the newest state if that state is associated with a crash.

## Attempt-0 preservation
Initial protocol, checkpoint manager, generalized lifecycle-event support, hostile test suite, and Main development-division evaluation were committed and pushed **before first execution**:

`d06bf16` — `forge-app: preserve resume checkpoint savestate attempt zero`.

Key Attempt-0 sources:
- `forge_app/recovery/RESUME_CHECKPOINT_PROTOCOL_v0_1.md` SHA `2020183abec627cf11fe701025c242a6a2fca2d6a302f840b832582b614dc4aa`.
- `forge_app/embodiment/test_resume_checkpoint_v0_1.py` SHA `d243f73900c60655442bba2d032eedef15d4267030de10ad7916edde38fac7b8`.
- Main division evaluation verbatim SHA `ed0b2385dd7f56a295db8980e85025a5316b457182258b613894fa4b486cd9e3`.

## Lifecycle model
Checkpoint bytes are immutable Attempt Store artifacts. Lifecycle/reputation is append-only event history.

Nominal:
`CAPTURED -> VERIFIED -> RESUMED -> STABLE -> LKG`

Failure:
`VERIFIED/RESUMED -> CRASH_ASSOCIATED -> QUARANTINED`

Locked semantics:
- `LATEST_CHECKPOINT != BEST_RECOVERY_POINT`.
- `PERSISTENCE_VALID != RUNTIME_STABLE`.
- `CRASH_ASSOCIATION_CAUSES_QUARANTINE_NOT_DELETION`.
- `CHECKPOINT_BYTES != PROCESS_IMAGE`.
- `CHECKPOINT_REPUTATION_IS_EVENT_DERIVED`.
- App checkpoints reference Core contract/currentness/snapshot IDs; they do not reimplement Core semantics.

v0.1 policy thresholds:
- STABLE lease: >=10 seconds healthy runtime + >=3 meaningful operations after resume;
- early crash window: <=15 seconds after resume;
- two distinct early crashes -> QUARANTINED;
- duplicate crash receipt with same immutable crash ID must be idempotent.

## First execution scar
Initial checkpoint test execution from preserved commit `d06bf16`:
**4/8 PASS; 1 assertion failure; 3 errors**.

Failures exposed a real generation-identity gap:
- `record_crash` had no `resume_id` binding;
- late health evidence from an older resumed generation could incorrectly promote a checkpoint after a newer resume had already started.

This was classified as an architecture defect, not a harness failure.

## First repair
Descendant repair preserved before retest:

`34d9859` — `forge-app: bind checkpoint health and crash evidence to latest resume`.

Repair:
- derive the latest `checkpoint_resumed` event;
- health evidence must match the latest immutable `resume_id`;
- crash evidence must match the latest immutable `resume_id`;
- stale generation evidence fails closed.

Retest result: **7/8 PASS**.

Remaining failure exposed a generalized event-journal replay bug: lifecycle-event replay compared the stored resolved blob SHA against caller `blob_sha256=None` before resolving the event's attempt identity. Exact duplicate crash receipt was therefore misclassified as conflicting immutable event data.

## Second repair
Descendant repair preserved before retest:

`02a0a9b5bbb33b16dd9ba6e7f393b6994557c12d` — `forge-app: make lifecycle event replay resolve attempt identity first`.

Current source hashes:
- `forge_app/recovery/attempt_store.py` SHA `819ea3b55b7e2141f8f1079f1fb7d21b400f73334ad25c9c335558b5ec428192`.
- `forge_app/recovery/resume_checkpoint.py` SHA `172f66ecf0c9076ab610e47870d527754338df340f5d7f9e248c85b98a9b8046`.

Repair:
- resolve/verify event attempt -> blob identity before idempotent replay comparison;
- exact lifecycle-event replay now returns the existing immutable event receipt;
- conflicting event ID reuse still fails closed.

Checkpoint retest: **8/8 PASS**.

## Verified checkpoint behaviors
1. checkpoint capture creates immutable checkpoint bytes + `checkpoint_verified` event;
2. captured-but-unverified artifact is never automatically selected for resume;
3. stable lease requires configured healthy duration and meaningful operations;
4. only stable non-quarantined checkpoint may be promoted LKG;
5. two distinct early crashes quarantine the checkpoint;
6. quarantine leaves checkpoint bytes exact and available for forensic inspection;
7. duplicate crash receipt is idempotent and does not increment crash count;
8. stale health evidence from an older resume generation is rejected;
9. stale crash evidence from an older resume generation is rejected;
10. older STABLE/LKG checkpoint outranks newer merely-VERIFIED checkpoint for automatic recovery.

## Full stack regression
After the generalized journal repair, the complete existing recovery/Ergo/renderer/checkpoint regression was executed:

- Attempt Store v0.1: 5 tests;
- Zombie v0.2: 4 tests;
- Ergo Recovery Observer v0.1: 4 tests;
- Ergo Launch Model v0.1: 6 tests;
- Renderer Process Protocol v0.1: 5 tests;
- Resume Checkpoint v0.1: 8 tests.

Result: **32/32 PASS** in 1.759 seconds.

## Current bounded claim
For the tested local append-only recovery model, Forge can preserve multiple immutable resume generations and rank recovery by runtime evidence rather than recency alone.

A newer crash-associated state can be quarantined without deletion while an older STABLE/LKG checkpoint remains the preferred automatic recovery point.

This directly prevents the naive emulator/autosave failure mode where “latest” repeatedly restores the program to the edge of the same crash.

## Cross-strand boundary
Main/Core owns canonical semantics, contracts, evidence/currentness, LBE substrate, materialization rules, capability logic, and shared interfaces.

App owns the checkpoint/session/recovery embodiment. Checkpoints may carry exact Core contract/currentness/snapshot identity references but may not silently encode substitute semantic meaning.

If App needs private semantic reconstruction to resume, that is a cross-strand interface defect to send upstream.

## Remaining seams
- persistent session host/heartbeat must produce the real STABLE lease evidence;
- renderer/session generation identity must be tied to checkpoint resume IDs;
- active-session host crash must append crash association automatically;
- source/editor pending-transaction resume semantics remain open;
- checkpoint payload migration/versioning;
- recovery selection surfaced through Ergo UI;
- real machine/power loss and storage failure;
- recovery-bundle/backup behavior;
- long-lived checkpoint retention/GC policy;
- actual semantic snapshot restoration through a qualified Core interface.

## Next cut
Build the persistent session/renderer host so real heartbeat + meaningful-operation evidence can promote `VERIFIED -> STABLE -> LKG`, and deliberate early host death can automatically drive `CRASH_ASSOCIATED -> QUARANTINED` while preserving an older known-good checkpoint.
