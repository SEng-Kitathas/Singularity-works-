# Forge Attempt Store — Zombie v0.2 Qualification — 2026-09-02

Status: **READY_WITH_EVIDENCE for expanded local process-crash / injected-write-failure / concurrent-writer / uncertain-outcome semantics**.
Not power-loss, storage-media, distributed-writer, or aerospace certification.

## Preserved discriminator Attempt 0
Git commit before execution:
`21539f8` — `forge-app: preserve zombie v0.2 discriminator attempt zero`.

Files:
- `forge_app/embodiment/test_attempt_store_zombie_v0_2.py` SHA `44f0338052f9ed5ec7a84c76095fe0b39e62e008bc83a9221a2735a87ff675f3`.
- `forge_app/embodiment/attempt_store_concurrency_worker_v0_2.py` SHA `b2401ea77ab1738db48a6e1ce8c171cf699be5d35aff1cad6798b8ca289d6dfa`.

## First execution scar
Initial v0.2 discriminator result: **3/4 pass, 1 error**.

Passing:
- 12 concurrent writers each committed exactly one distinct attempt/blob/event and exact payload readback succeeded;
- injected `sqlite3.OperationalError("database or disk is full")` before COMMIT rolled the transaction back to 0 blobs / 0 attempts / 0 events with integrity `ok`;
- same `attempt_id` with different content remained rejected and original attempt remained exact.

Failing seam:
- unknown post-COMMIT outcome: the first call committed successfully, then simulated response/transport loss occurred after COMMIT before receipt/readback; repeating the exact immutable operation with the same `attempt_id` failed with `sqlite3.IntegrityError: UNIQUE constraint failed: attempts.attempt_id`.

This was classified as a real architecture gap rather than a harness failure.

## Repair candidate preserved before retest
Git commit:
`a4eb82a85f7f56e25b4feb21ca388e49fb744885` — `forge-app: make attempt replay idempotent after uncertain commit`.

Current `forge_app/recovery/attempt_store.py` SHA:
`1e6d6fad525b6725265be85c96b1342bfdba5d9359485f8ac524dfb3a87a2b09`.

Repair behavior:
- on explicit `attempt_id`, the store first checks for an existing immutable attempt;
- exact replay requires exact payload SHA/bytes, byte length, parent, artifact class, producer, intent and canonical metadata;
- exact replay requires exactly one existing `attempt_captured` event;
- exact replay returns the original attempt/event receipt without inserting a second event/blob/attempt;
- any mismatch under the same `attempt_id` is a hard identity conflict.

No schema migration was required; store schema remains `forge-attempt-store/0.1`.

## Regression + v0.2 execution
Command:
`python -m unittest forge_app.embodiment.test_attempt_store_v0_1 forge_app.embodiment.test_attempt_store_zombie_v0_2 -v`

Result: **9/9 PASS**.

Verified outcomes:
1. original v0.1 hard-kill-before-COMMIT still leaves no phantom state;
2. original v0.1 hard-kill-after-COMMIT still recovers exact attempt;
3. immutable rows remain protected;
4. content deduplication and attempt lineage remain exact;
5. unknown parent still rolls back;
6. 12 concurrent writers succeed exactly once each with integrity `ok`;
7. injected pre-COMMIT disk-full error rolls back every inserted row;
8. unknown post-COMMIT response loss followed by exact retry returns the existing verified attempt and leaves counts at 1 blob / 1 attempt / 1 event;
9. same `attempt_id` with different bytes remains rejected and cannot overwrite the preserved attempt.

## New earned law
**`COMMIT_RECEIPT_LOSS != DUPLICATE_ATTEMPT`**.

More precise form:
An operation with an explicit immutable attempt identity must be safely replayable after an unknown commit outcome. Exact replay recovers the committed occurrence; conflicting replay fails closed.

## Remaining seams
- real filesystem/storage exhaustion rather than injected pre-COMMIT error;
- I/O failure during SQLite/WAL fsync or checkpoint;
- abrupt machine/power loss;
- concurrent writer load above the small 12-process discriminator;
- writer starvation/lock timeout behavior;
- live backup/recovery bundle correctness with WAL present;
- large payload latency/memory behavior;
- schema migration;
- multi-host/distributed writes;
- privacy/encryption/retention.

## Next product implication
Ergo may now safely present an operation as “receipt uncertain, replay by immutable attempt ID” without creating a second attempt. The eventual launcher/recovery UX should surface unknown-outcome recovery explicitly rather than asking the AI/operator to regenerate work.
