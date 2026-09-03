# Singularity Works External Operation Lifecycle / Reconciliation Protocol v0.1

Status: **Attempt 0 protocol** — preserve before first execution.

## Goal
Close the last local semantic/durability seam before real network enforcement: distinguish authority to attempt an external consequence from what actually happened after preparation/submission, and prevent uncertain outcomes from creating duplicate consequences.

This protocol performs no real network I/O. A simulated remote ledger is used only to pressure local lifecycle and reconciliation semantics.

## Governing laws
- `PREPARED != SUBMITTED != STARTED != COMPLETED != REMOTE_OBSERVED`.
- `LOCAL_SUCCESS != REMOTE_COMMIT_PROVEN`.
- `UNKNOWN_OUTCOME != SAFE_TO_RETRY`.
- `RETRY_AFTER_UNKNOWN_REQUIRES_RECONCILIATION`.
- `IDEMPOTENCY_KEY != AUTHORITY`.
- `DECISION_RECEIPT != CAPABILITY_TOKEN`.
- `OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY`.
- `REMOTE_OBSERVATION != LOCAL_COMPLETION_ASSUMPTION`.
- `SAME_OPERATION_IDENTITY != NEW_CONSEQUENCE_IDENTITY`.
- `ABSENT_AFTER_RECONCILIATION != NEVER_SUBMITTED_WITHOUT_EVIDENCE`.

## Identity model
A prepared external operation receives an immutable **external operation identity** before any submission:
- operation ID;
- stable idempotency key;
- request ID;
- persisted ALLOW decision ID/attempt;
- exact authority-state fingerprint;
- provider/connector/resource/capability identity;
- payload/effect fingerprint if supplied.

The idempotency key is stable for the operation identity and is never regenerated merely because a caller lost a receipt.

## Legal lifecycle graph
Base state: `PREPARED`.

Legal transitions:
- PREPARED -> SUBMITTED
- PREPARED -> FAILED_LOCAL
- SUBMITTED -> STARTED
- SUBMITTED -> COMPLETED_LOCAL
- SUBMITTED -> UNKNOWN_OUTCOME
- SUBMITTED -> FAILED_LOCAL
- STARTED -> COMPLETED_LOCAL
- STARTED -> UNKNOWN_OUTCOME
- STARTED -> FAILED_LOCAL
- COMPLETED_LOCAL -> REMOTE_OBSERVED_COMMITTED
- COMPLETED_LOCAL -> UNKNOWN_OUTCOME
- UNKNOWN_OUTCOME -> REMOTE_OBSERVED_COMMITTED
- UNKNOWN_OUTCOME -> REMOTE_OBSERVED_ABSENT
- REMOTE_OBSERVED_ABSENT -> SUBMITTED only through explicit same-identity replay authorization

Terminal-for-this-operation states:
- REMOTE_OBSERVED_COMMITTED
- FAILED_LOCAL

`REMOTE_OBSERVED_ABSENT` is a reconciled absence state, not automatic permission to retry. A separate replay authorization event must bind the same operation/idempotency identity and current authority.

## Submission gate
Immediately before SUBMITTED, the lifecycle layer SHALL:
1. reload the persisted ALLOW decision;
2. re-materialize current authority state;
3. require the decision fingerprint still matches;
4. require operation identity/request match;
5. require no prior committed/unknown lifecycle state that makes a new submission unsafe.

Authority revocation/disarm/currentness drift between PREPARED and SUBMITTED therefore blocks submission.

## Unknown outcome
If caller/process loses the consequence receipt after submission or cannot determine remote result:
- append UNKNOWN_OUTCOME for the existing operation identity;
- do not create a new operation ID;
- do not mint a fresh idempotency key;
- block blind resubmission.

Reconciliation must query/inspect a provider-specific remote identity through a future connector. In v0.1 this is represented by an injected zero-authority observation, not a network call.

Possible reconciliation results:
- COMMITTED -> `REMOTE_OBSERVED_COMMITTED`; no retry;
- ABSENT -> `REMOTE_OBSERVED_ABSENT`; replay remains blocked until explicitly authorized under current authority;
- UNKNOWN -> remain UNKNOWN_OUTCOME.

## Replay after reconciled absence
A replay authorization:
- applies only to the same immutable operation ID/idempotency key;
- requires current authority fingerprint to remain valid or a fresh persisted ALLOW decision for the same request/effect;
- is append-only and idempotent;
- permits transition `REMOTE_OBSERVED_ABSENT -> SUBMITTED` for the same consequence identity.

It does not create a new consequence identity.

## Remote observation
Remote observations carry authority NONE. They report evidence about a provider-side consequence; they do not grant permission.

Observation must bind:
- operation ID;
- idempotency key;
- provider/connector/resource;
- observation ID/source;
- outcome COMMITTED/ABSENT/UNKNOWN;
- optional remote object/version/hash identity.

## Attempt-0 hostile targets
1. exact lifecycle event replay idempotent;
2. same lifecycle event ID with different payload fails closed;
3. illegal branch switch/regression rejected;
4. authority revoke after PREPARED blocks SUBMITTED;
5. UNKNOWN_OUTCOME blocks blind resubmission;
6. UNKNOWN + COMMITTED reconciliation reaches REMOTE_OBSERVED_COMMITTED and remains non-retriable;
7. UNKNOWN + ABSENT reconciliation still blocks retry until explicit replay authorization;
8. authorized replay preserves same operation ID/idempotency key;
9. stale authority blocks replay authorization;
10. exact duplicate replay authorization idempotent;
11. remote observation for wrong operation/idempotency key rejected;
12. reopen reconstructs identical lifecycle state;
13. decision/prepared/lifecycle/observation receipts remain authority NONE;
14. no network I/O and no credential secret material.

## Nonclaims
This protocol does not yet prove real provider idempotency support, real remote observability, OAuth, token security or OS/network enforcement. It establishes the local consequence/reconciliation semantics those later integrations must obey.
