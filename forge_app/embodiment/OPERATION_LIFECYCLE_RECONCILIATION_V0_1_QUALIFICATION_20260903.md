# Singularity Works External Operation Lifecycle / Reconciliation v0.1 — Qualification — 2026-09-03

Status: **READY_WITH_EVIDENCE for local durable external-operation identity, legal lifecycle transitions, uncertain-outcome blocking, zero-authority reconciliation observations, same-identity replay after proven absence, and authority-currentness gating before submission.**

Not qualified for real network/provider transport, provider-native idempotency guarantees, OAuth/token security or OS/process egress enforcement.

## Process
Qualified under adopted RAHL Engineering Canonical SOP R4.1.

## Attempt 0
Preserved before first execution at:
`7db4f518e42998246d4043fdc63c22a1c35aa71f`
— `singularity-works: preserve operation lifecycle reconciliation attempt zero`.

Attempt-0 source hashes:
- `forge_app/connection_gate/__init__.py` SHA `efb50e737f61fde83ae4bd5f9f9e2c0c7690d11dd9cede1e4c62b07bf3e3e2dc`;
- `forge_app/connection_gate/OPERATION_LIFECYCLE_RECONCILIATION_PROTOCOL_v0_1.md` SHA `4d9389704ca3a1ed3435f3711598c1a9253b2189acb80c32e691c6fa97c53ccc`;
- `forge_app/connection_gate/operation_lifecycle.py` SHA `946d29fcc98cbf6050f8118135e08a1c6df70477b220dc7a657b40821812f8e1`;
- `forge_app/embodiment/test_operation_lifecycle_reconciliation_v0_1.py` SHA `ff331e238106ebffd61b0f23878d59d374d1d53302ed1bc8f19b8b6da8cf7edc`.

No repair commit was required after first execution.

## Earned laws
- `PREPARED != SUBMITTED != STARTED != COMPLETED != REMOTE_OBSERVED`.
- `LOCAL_SUCCESS != REMOTE_COMMIT_PROVEN`.
- `UNKNOWN_OUTCOME != SAFE_TO_RETRY`.
- `RETRY_AFTER_UNKNOWN_REQUIRES_RECONCILIATION`.
- `IDEMPOTENCY_KEY != AUTHORITY`.
- `REMOTE_OBSERVATION != LOCAL_COMPLETION_ASSUMPTION`.
- `SAME_OPERATION_IDENTITY != NEW_CONSEQUENCE_IDENTITY`.
- `ABSENT_AFTER_RECONCILIATION != AUTOMATIC_RETRY_AUTHORITY`.
- existing `OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY` remains active at submission/replay boundaries.

## Lifecycle model
Immutable external-operation identity is established before submission and binds:
operation ID, stable idempotency key, request/decision identity, authority-state fingerprint, provider/connector/resource/capability, and effect fingerprint.

Legal transition graph distinguishes PREPARED, SUBMITTED, STARTED, COMPLETED_LOCAL, UNKNOWN_OUTCOME, REMOTE_OBSERVED_COMMITTED, REMOTE_OBSERVED_ABSENT and FAILED_LOCAL. Terminal/uncertain branches are explicit rather than represented by a simple numeric rank.

Exact transition receipt replay resolves the original durable observation before current-state checks; same transition ID with changed semantics fails closed.

## Targeted execution
Command:
`python -W error::ResourceWarning -m unittest forge_app.embodiment.test_operation_lifecycle_reconciliation_v0_1 -v`

Result: **10/10 PASS unchanged**.

Verified:
- exact transition replay idempotent;
- transition-ID semantic conflict rejected;
- illegal terminal branch switch rejected;
- revoke after PREPARED blocks SUBMITTED;
- UNKNOWN_OUTCOME blocks blind resubmission;
- COMMITTED reconciliation closes operation without retry;
- ABSENT reconciliation still requires explicit replay authorization;
- replay preserves same operation/idempotency identity;
- stale/revoked authority blocks replay authorization;
- wrong remote idempotency identity rejected;
- reopen reconstructs lifecycle exactly;
- receipts/remote observations authority NONE and no network I/O.

## Full App regression
After lifecycle addition:
**94/94 PASS** with ResourceWarning-as-error in 13.110 seconds.

## Live real-project simulated-remote campaign
Source:
`7db4f518e42998246d4043fdc63c22a1c35aa71f`.

No network I/O. No secret material stored.

### Operation A — uncertain then committed
Operation `live-lifecycle-committed` used idempotency key:
`sw-op-4337c8b08e3f6ae25e6de66cf6bdae71`.

SUBMITTED -> UNKNOWN_OUTCOME.
Blind resubmission rejected: `blind resubmission rejected from UNKNOWN_OUTCOME`.
Injected zero-authority remote observation reported COMMITTED.
Final state: `REMOTE_OBSERVED_COMMITTED`.
No retry permitted.

### Operation B — uncertain, absent, same-identity replay
Operation `live-lifecycle-absent-replay` used idempotency key:
`sw-op-9c9832a15b8288617086f8e3384f80a1`.

SUBMITTED -> UNKNOWN_OUTCOME -> remote ABSENT.
Blind retry remained rejected with `RETRY_AFTER_UNKNOWN_REQUIRES_RECONCILIATION_AND_REPLAY_AUTHORIZATION`.
Explicit replay authorization was appended.
Replay used the **same operation ID and same idempotency key**, then reached COMPLETED_LOCAL and zero-authority remote COMMITTED observation.
Final state: `REMOTE_OBSERVED_COMMITTED`.

### Operation C — authority drift before submission
Operation `live-lifecycle-revoked-before-submit` was PREPARED.
Grant was revoked before SUBMITTED.
Submission failed with:
`OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY: authority changed before consequence`.
Final state remained PREPARED.

### Reopen
All three lifecycle views reconstructed exactly after reopening the real Attempt Store.

## Evidence
Packet:
`state/live_operation_lifecycle_reconciliation_v0_1.json`
SHA `00a7cc4744c7985f2117ebfeae0cf9bbc29751c89265a5286f3d69b228f08dc9`.

Attempt:
`attempt-live-operation-lifecycle-v0-1`
with verified readback and the same blob SHA.

Attempt Store after evidence capture:
98 blobs / 98 attempts / 157 events, integrity ok, WAL/FULL.

## Bounded claim
On the tested local durable boundary, Singularity Works can prevent a lost/ambiguous external-operation receipt from becoming an accidental duplicate consequence. An uncertain outcome blocks blind retry; reconciliation may close committed state or prove absence; absence alone still does not authorize retry; explicit replay uses the same consequence identity and current authority must still hold.

## Remaining seams
- actual provider idempotency/reconciliation APIs;
- process/network enforcement proving all egress traverses the Gate;
- unknown outcome when provider cannot expose reliable reconciliation identity;
- connector crash/restart during transport;
- provider-side race between reconciliation and replay;
- OAuth/PKCE and secret storage;
- signed/tamper-resistant external audit receipts.

## Next pressure
Create a current-source LKG, then move to **OS/process network egress enforcement**. Do not implement a real GitHub connector before proving protected execution domains cannot bypass the Connection Gate.
