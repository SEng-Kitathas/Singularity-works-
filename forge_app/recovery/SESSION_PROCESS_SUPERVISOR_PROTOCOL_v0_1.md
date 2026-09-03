# Singularity Works Session Process Supervisor Protocol v0.1

Status: **Attempt 0 protocol** — preserve before first execution.

## Goal
Prove that checkpoint crash association survives the death of the resumed session coordinator because a separate surviving supervisor—not the dying process—owns crash observation and durable reputation mutation.

## Boundary
The supervisor is App-owned recovery infrastructure. The supervised child is a replaceable runtime process and receives **no Attempt Store path/capability** from this protocol.

Locked laws:
- `SESSION_PROCESS_DEATH != CHECKPOINT_DATA_DEATH`.
- `DYING_PROCESS != CRASH_REPUTATION_AUTHORITY`.
- `SUPERVISOR_OBSERVATION != CHILD_SELF_REPORT`.
- `RESUME_ID != REUSABLE_PROCESS_SLOT`.
- `CHILD_READY_ACK != SESSION_STABILITY`.
- `CRASH_ID_REPLAY_USES_ORIGINAL_OBSERVATION`.
- existing `CRASH_ASSOCIATION_CAUSES_QUARANTINE_NOT_DELETION` remains governing.

## Start ordering
For each supervised resume generation:
1. choose a unique immutable `resume_id`;
2. append/verify `checkpoint_resumed` for that exact checkpoint/resume identity;
3. capture supervisor monotonic start time;
4. spawn the child with checkpoint/resume identity and a unique transient ready-receipt path;
5. verify the child's ready receipt exactly matches checkpoint ID, resume ID and spawned PID before treating it as READY.

The checkpoint/resume generation therefore exists durably before the child can begin meaningful session work.

## Ready receipt
The child may create one transient JSON ready receipt:
- protocol `singularity-session-child-ready/0.1`;
- checkpoint ID;
- resume ID;
- child PID.

This receipt is identity/liveness evidence only.
It is not checkpoint reputation, session stability, semantic truth or authority.

## Crash observation
An unexpected child exit is associated by the surviving supervisor using:
- exact checkpoint ID;
- exact resume ID;
- deterministic crash ID bound to that resume generation unless explicitly supplied;
- supervisor-measured seconds since resume start;
- failure domain;
- child PID / exit code in detail.

The supervisor calls the existing `ResumeCheckpointManager.record_crash()` path. Existing duplicate-event idempotence and quarantine handler semantics therefore remain canonical.

Two distinct early process deaths on two distinct resume IDs of the same checkpoint should produce:
`VERIFIED -> CRASH_ASSOCIATED -> QUARANTINED`
and automatically prepare the existing deterministic isolated re-entry lane when a `CheckpointReentryService` is registered.

## Expected shutdown
A deliberately expected shutdown must not be recorded as crash association merely because the process exits. The caller must explicitly choose the expected-shutdown path.

## Failure handling
- wrong/malformed/stale ready identity: fail closed and do not accept READY;
- child exits before ready: supervisor may record the observed unexpected exit against the already-durable resume generation;
- duplicate observation of the same deterministic crash ID: read/reuse the original durable crash observation; do not recompute elapsed time or create a different immutable event;
- supervisor crash after child death but before crash receipt is outside v0.1 and remains a later recovery seam.

## Qualification target
Attempt 0 should prove:
1. one actual externally killed child creates one early crash association;
2. second distinct externally killed resume generation quarantines the disposable checkpoint;
3. quarantine invokes the existing auto re-entry service and creates the exact isolated lane/popup;
4. known-good LKG remains selected;
5. duplicate crash observation is idempotent;
6. active source and durable checkpoint bytes remain unchanged by child death;
7. expected shutdown does not create crash reputation;
8. wrong ready identity is rejected.
