# Singularity Works Connection Gate Authority State / Receipt Protocol v0.1

Status: **Attempt 0 protocol** — preserve before first execution.

## Goal
Make the already-qualified pure Connection Gate authority model durable and auditable before any real provider/network connector exists.

This protocol deliberately reuses the qualified crash-oriented `AttemptStore` rather than introducing a second persistence engine.

## Core laws
- `AUTHORITY_OBJECT != MUTABLE_ACTIVE_POINTER`.
- `AUTHORITY_SCOPE_CHANGE_CREATES_NEW_GENERATION`.
- `REVOCATION_IS_APPEND_ONLY_EVENT_NOT_GRANT_REWRITE`.
- `DISARM_IS_APPEND_ONLY_EVENT_NOT_ARMING_REWRITE`.
- `DECISION_RECEIPT != CAPABILITY_TOKEN`.
- `OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY`.
- `EXECUTION_PREPARATION_REQUIRES_CURRENT_AUTHORITY_REEVALUATION`.
- `AUTHORITY_STATE_FINGERPRINT_BINDS_DECISION_TO_CURRENT_STATE`.
- `NO_SECRET_BYTES_IN_AUTHORITY_STATE_STORE`.

Existing laws remain:
`VERIFIED_PLATFORM != FULL_AUTHORITY`, `CONNECTED != ARMED`, `AUTHORITY_COMPOSES_BY_INTERSECTION_NOT_UNION`, `OPERATOR_INTENT != PLATFORM_APPROVAL_STATE`.

## Persistence model
Immutable authority objects are stored as Attempt Store artifacts:
- provider identity record;
- credential ceiling metadata (never secret/token bytes);
- connector policy generation;
- user grant generation;
- session arming generation;
- operation confirmation;
- persisted decision receipt;
- prepared operation receipt.

Mutable-looking state is represented only by append-only events against immutable objects:
- grant revoked;
- arming disarmed;
- currentness set CURRENT/STALE/UNKNOWN;
- operation lifecycle stage appended.

## No active pointer
The caller supplies exact IDs for provider/credential/policy/grant/arming/confirmation. There is no mutable global “current grant” pointer that can silently redirect existing requests.

A changed grant scope or policy is a new immutable ID/generation. The older generation remains inspectable and can be revoked/tombstoned by event.

## Authority-state fingerprint
Before evaluation, the state layer materializes each exact authority object plus its relevant lifecycle events. It computes a deterministic fingerprint over:
- exact immutable object blob IDs;
- exact materialized verification/state/currentness fields;
- relevant latest lifecycle event IDs/sequences.

The persisted decision binds to this fingerprint.

Before an operation can be prepared, the exact authority state is materialized again. If the fingerprint differs, the old decision is not executable and the request must be re-evaluated.

## Manual parity
The v0.1 API must expose explicit manual operations:
- register/inspect provider metadata;
- register/inspect credential ceiling metadata;
- register/inspect policy;
- create/inspect/revoke grant;
- create/inspect/disarm arming;
- set/inspect currentness;
- persist/inspect confirmation;
- evaluate/persist decision;
- inspect/list receipts.

No provider connection is required to use these controls.

## Decision persistence
`evaluate_and_persist()`:
1. reads exact authority objects from durable store;
2. materializes lifecycle state;
3. computes authority-state fingerprint;
4. calls the pure v0.1 evaluator;
5. captures an immutable persisted decision artifact containing the pure decision + exact input IDs/fingerprint;
6. readbacks exact bytes.

Decision artifact authority remains NONE.

## Operation preparation
`prepare_operation()` is the future execution boundary precursor.
It requires:
- persisted decision exists;
- decision is ALLOW;
- request ID matches;
- current authority fingerprint exactly equals the decision fingerprint.

It then captures an immutable prepared-operation receipt **before any future external effect**.

If a grant is revoked, arming disarmed, or currentness changes after ALLOW, the old decision cannot prepare a new operation.

## Operation lifecycle
Future connectors may append immutable stages against the prepared operation:
PLANNED / SUBMITTED / STARTED / COMPLETED / REMOTE_OBSERVED / FAILED / UNKNOWN_OUTCOME.

Stage receipts are observations, not proof of remote truth beyond what the stage actually says.

## Attempt-0 hostile targets
1. exact object replay idempotent; same ID/different bytes fail closed;
2. revoke grant does not rewrite grant bytes;
3. disarm does not rewrite arming bytes;
4. stale/currentness event changes materialized evaluation;
5. decision receipt persists exact state fingerprint;
6. old ALLOW cannot prepare operation after revocation;
7. old ALLOW cannot prepare operation after disarm/currentness change;
8. exact unchanged ALLOW can prepare operation;
9. duplicate operation-stage receipt is idempotent; same event ID/different payload fails closed;
10. receipt/inspection paths do not grant capability;
11. no credential secret/token material accepted by API;
12. readback/reopen reconstructs identical authority state and fingerprint.

## Non-claims
This protocol does not yet enforce the OS/network boundary and does not contact GitHub/OAuth/API providers. `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` remains a target until the later enforcement layer proves it.
