# Forge Attempt Store v0.1 — Qualification Checkpoint — 2026-09-02

Status: **READY_WITH_EVIDENCE under the bounded v0.1 process-crash target**.
Not a claim of complete zombie/power-loss/aerospace qualification.

## Preserved implementation under test
Git commit tested unchanged:
`766fe181cf3eeec761e2929d1a42f009f4326194`
(`forge-app: preserve attempt store v0.1 attempt zero`)

Primary artifacts:
- `forge_app/recovery/RECOVERY_ARCHITECTURE_ADR_v0_1.md`.
- `forge_app/recovery/attempt_store.py` — source SHA before execution `d7814b7ad83f89087b95b7c559b21e91563dbd2dff40b368f06194385a1d601d`.
- `forge_app/embodiment/test_attempt_store_v0_1.py` — source SHA before execution `83ed7f2475ac3c1d5c28f45d9e5f9a15a1447ba6d0e00f4c09b21679003da87f`.
- `forge_app/embodiment/attempt_store_hardkill_worker.py` — source SHA `96dedbc625f12e75ab5fcbe7ffbc04c3b1d80cbb36a88cf903b268748952e59a`.

The implementation and tests were committed and pushed **before the first test execution**, intentionally applying `ATTEMPT_0_IS_EVIDENCE_NOT_SCRATCH_SPACE` to Forge's own development process.

## Test command
`python -m unittest forge_app.embodiment.test_attempt_store_v0_1 -v`

Executed from the isolated source tree. Result: return code 0; 5 tests; all PASS.

## Verified discriminators
1. **CAS deduplication without attempt collapse**
   - identical bytes produce one content-addressed blob;
   - distinct attempt records/events remain distinct;
   - child attempt lineage resolves exactly to parent Attempt 0.

2. **Unknown-parent transaction rollback**
   - retry with missing parent is rejected;
   - reopen shows 0 blobs / 0 attempts / 0 events;
   - integrity remains clean.

3. **Append-only immutability**
   - UPDATE/DELETE against attempt/blob/event surfaces rejected by SQLite triggers;
   - original payload remains exact/readable.

4. **Hard kill before COMMIT**
   - actual child process exits via `os._exit(91)` after rows are written inside the active transaction but before COMMIT;
   - reopening the store yields no phantom blob, attempt, or capture event;
   - `PRAGMA integrity_check` reports `ok`.

5. **Hard kill after COMMIT before normal close/readback**
   - actual child process exits via `os._exit(92)` immediately after COMMIT but before graceful close/readback;
   - reopening yields exactly 1 blob / 1 attempt / 1 event;
   - artifact bytes and metadata match exactly;
   - SHA readback verifies;
   - integrity reports `ok`.

## Live bootstrap use
After the test gate passed, a real local store was created at:
`state/attempt_store_v0_1/attempt_store.sqlite3`

It captured six pre-existing significant Attempt-0 artifacts at Git commit `766fe181cf3eeec761e2929d1a42f009f4326194`:

| Artifact class | Blob SHA-256 |
|---|---|
| `design.commander_intent` | `8d0d0422b57a0f285238b20321ca001368f666053c8b2dff069408ac26a3bc5f` |
| `research.local_quarry` | `9c833e6a22a656ceb1c1427603aeaba08ceaccf7a0c8939ad3875e018d9b4238` |
| `research.outside_world` | `b64f83e81e1ab28720fa13e7453c66bf468ae9e8e6eee6b6451cceae6a04f6cf` |
| `design.recovery_architecture` | `da8bf0aab2525b43bb3372bc87895c7967ea6ad11bd4891b82354a8665064275` |
| `code.attempt_store` | `d7814b7ad83f89087b95b7c559b21e91563dbd2dff40b368f06194385a1d601d` |
| `test.attempt_store` | `83ed7f2475ac3c1d5c28f45d9e5f9a15a1447ba6d0e00f4c09b21679003da87f` |

Live integrity readback immediately after capture:
- journal mode: WAL;
- synchronous: SQLite FULL (`2`);
- integrity: `ok`;
- counts: 6 blobs / 6 attempts / 6 capture events.

Derived receipt export:
`state/attempt_store_v0_1/bootstrap_receipts.json`.

## Current architectural claim
For a **single local writer / local filesystem / process-crash** target, the v0.1 SQLite transaction is a qualified improvement over donor direct-JSON persistence:

`artifact bytes + immutable attempt metadata + capture event` either commit together or disappear together.

This is intentionally narrower than “the app can never lose work.”

## Remaining qualification seams
- abrupt machine/power loss rather than process death;
- WAL/database backup/copy behavior while the store is live;
- disk-full / partial-write / I/O error injection;
- filesystem corruption and lost/corrupted WAL;
- concurrent readers/writers and lock starvation;
- large artifact size/latency/memory behavior;
- privacy/encryption/retention policy;
- external immutable CAS mirror/recovery bundle;
- schema migration/version evolution;
- renderer/application crash integration;
- Ergo boot/recovery presentation and selection;
- multi-process writer semantics.

## Demotion trigger
Any later test that yields a committed attempt whose payload cannot be exact-read, a phantom attempt after pre-commit death, mutation of prior attempts, or an unrecoverable internally inconsistent store demotes v0.1 immediately.

## Next cut
Bind a read-only **Ergo Recovery Summary** to the live Attempt Store. Ergo should report real durable state (integrity, latest event/attempts, lineage, recovery posture) without becoming persistence authority. Then expand the Zombie Campaign to disk-full, concurrent-access and recovery-bundle surfaces.
