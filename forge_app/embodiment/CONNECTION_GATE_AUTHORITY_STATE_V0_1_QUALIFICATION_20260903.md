# Singularity Works Connection Gate Authority State / Receipt v0.1 — Qualification — 2026-09-03

Status: **READY_WITH_EVIDENCE for durable provider/policy/grant/arming/currentness metadata, append-only revocation/disarm/currentness events, persisted authority decisions, pre-operation receipts and readback/reopen behavior on the qualified Attempt Store substrate.**

Not qualified for real OAuth/network transport, token/secret storage, provider revocation feeds, OS/network egress enforcement, or remote-operation commit/reconciliation semantics.

## Governing process
Qualified under RAHL Engineering Canonical SOP R4.1 after R4.1 was linearly inspected/adopted. Relevant base-tier obligations applied: PDVER, hostile engineering, Semantic Helix/next discriminator, Attention Reservoir, OARR/replay, CSC across persistence/authority/execution boundaries, and additive AI contradiction/recomputation support.

## Goal
Make the already-qualified pure Connection Gate authority model durable before any real external connector exists.

## Attempt-0 preservation
Exact candidate was preserved before first execution at:
`4b4d6c5f42a31af2a0547399ffef32802a519e7f`
— `singularity-works: preserve connection gate authority state attempt zero`.

Attempt-0 files/hashes:
- `forge_app/connection_gate/__init__.py`
  SHA `cf9ed239f74a0454bcc4655f7c5cd39489d330a5ed41330ef741391b1587420a`;
- `forge_app/connection_gate/AUTHORITY_STATE_RECEIPT_PROTOCOL_v0_1.md`
  SHA `a39e5189c9ebb0fbaac9aae65d038b2aaf96b5761a4e922ba849144804da5e10`;
- `forge_app/connection_gate/authority_state.py`
  SHA `222dca7e346c291035f740f3decc486c7736104f083b9efd3d4ac28cb0ea6297`;
- `forge_app/embodiment/test_connection_gate_authority_state_v0_1.py`
  SHA `9d346125c8bcfa972e8c046670dff793942a338ba31730920f2aca26448a3d90`.

No repair commit was required after Attempt 0.

## Core laws embodied
- `AUTHORITY_OBJECT != MUTABLE_ACTIVE_POINTER`.
- `AUTHORITY_SCOPE_CHANGE_CREATES_NEW_GENERATION`.
- `REVOCATION_IS_APPEND_ONLY_EVENT_NOT_GRANT_REWRITE`.
- `DISARM_IS_APPEND_ONLY_EVENT_NOT_ARMING_REWRITE`.
- `DECISION_RECEIPT != CAPABILITY_TOKEN`.
- `OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY`.
- `EXECUTION_PREPARATION_REQUIRES_CURRENT_AUTHORITY_REEVALUATION`.
- `AUTHORITY_STATE_FINGERPRINT_BINDS_DECISION_TO_CURRENT_STATE`.
- `NO_SECRET_BYTES_IN_AUTHORITY_STATE_STORE`.

Qualified Connection Gate laws remain active:
- `VERIFIED_PLATFORM != FULL_AUTHORITY`;
- `CONNECTED != ARMED`;
- `AUTHORITY_COMPOSES_BY_INTERSECTION_NOT_UNION`;
- `OPERATOR_INTENT != PLATFORM_APPROVAL_STATE`.

## Persistence model
The layer reuses the already-qualified `AttemptStore` rather than creating a second durability engine.

Immutable objects:
- provider identity metadata;
- credential capability/resource ceiling metadata, never raw secret/token bytes;
- connector policy generation;
- user grant generation;
- session arming generation;
- operation confirmation;
- persisted decision receipt;
- prepared-operation receipt.

Append-only lifecycle events:
- grant revoked;
- arming disarmed;
- currentness changed;
- future operation stages.

There is no mutable global active-grant pointer in v0.1. A changed scope is represented by a new immutable generation ID.

## State fingerprint
Each evaluation materializes exact immutable object identities plus relevant lifecycle events and computes a deterministic authority-state fingerprint.

A persisted ALLOW binds to that fingerprint. `prepare_operation()` materializes authority state again; if revocation/disarm/currentness changed the fingerprint, historical ALLOW remains evidence but cannot authorize a new prepared operation.

## Targeted Attempt-0 execution
Command:
`python -W error::ResourceWarning -m unittest forge_app.embodiment.test_connection_gate_authority_state_v0_1 -v`

Result: **11/11 PASS unchanged** in 1.284 seconds.

Verified hostile cases:
1. exact authority-object replay idempotent;
2. same ID/different immutable bytes fails closed;
3. raw secret material rejected by API;
4. revoke is append-only and grant blob remains exact;
5. post-revoke evaluation becomes DENY;
6. old ALLOW cannot prepare after revoke;
7. old ALLOW cannot prepare after disarm;
8. old ALLOW cannot prepare after currentness change;
9. exact unchanged ALLOW can prepare a verified pre-operation receipt;
10. non-ALLOW cannot prepare an operation;
11. exact request-bound confirmation persists and allows preparation;
12. operation-stage replay is idempotent, conflicting same event ID fails, stage regression rejected;
13. reopen reconstructs identical authority state/fingerprint;
14. manual inspection/listing does not mint authority or expose token data.

## Full App regression
After Attempt-0 qualification:
`python -W error::ResourceWarning -m unittest discover -s forge_app/embodiment -p test_*.py -v`

Result: **84/84 PASS** in 10.966 seconds.

## Live real-project durable authority campaign
Source:
`4b4d6c5f42a31af2a0547399ffef32802a519e7f`.

No network I/O performed. No secret material stored.

Actual modeled resource:
`github:SEng-Kitathas/Singularity-works-:branch:forge/app-shell-rd`.

### Generation 1
A broad credential ceiling was durably recorded as metadata while product policy/grant/arming remained narrower.

`live-state-read-before-revoke` -> **ALLOW**.
A pre-operation receipt was successfully created while authority state was unchanged.

Then manual grant revocation was appended.
Verified:
- immutable grant blob before/after revocation remained identical;
- old ALLOW could not prepare a new operation and failed with `OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY`;
- re-evaluation became **DENY**.

### Generation 2
A new grant generation and new arming generation were created rather than widening/reusing the revoked generation.

`live-state-read-generation-2` -> **ALLOW** and a new pre-operation receipt was created.

Manual disarm was appended.
Verified:
- old ALLOW could not prepare afterward;
- re-evaluation became **UNARMED**.

### Generation 3 / currentness
A fresh arming generation restored the narrow read envelope.

`live-state-read-before-stale` -> **ALLOW**.
Then connector-policy currentness was set to STALE through an append-only event.
Verified:
- old ALLOW could not prepare afterward;
- re-evaluation became **STALE**.

### Reopen/readback
The authority state store was reopened over the same real Attempt Store.
Final authority snapshot and fingerprint matched exactly across reopen.

## Live evidence
Packet:
`state/live_connection_gate_authority_state_v0_1.json`
SHA-256:
`c743aaf3bf1f681662637e8d65e6da10881b732772ff9f4991509db3f28ac50b`.

Preserved as Attempt:
`attempt-live-connection-gate-authority-state-v0-1`
with verified readback and the same blob SHA.

Attempt Store after evidence capture:
- integrity `ok`;
- WAL;
- synchronous FULL;
- 81 blobs / 81 attempts / 122 events.

## Bounded claim
On the tested local durable-state boundary, Singularity Works can preserve immutable authority generations and append-only authority lifecycle changes, persist exact authority decisions, bind ALLOW to the exact current authority-state fingerprint, and refuse to prepare new external operations from historical ALLOW after revocation, disarm or currentness change.

This closes a major authority-laundering seam: a previously valid decision does not become ambient or timeless capability.

## Nonclaims / remaining seams
- no OAuth/PKCE flow;
- no raw API token/secret storage;
- no provider-side revocation/currentness feed;
- no OS/network egress enforcement;
- no actual GitHub API call;
- no remote idempotency/unknown-commit-outcome reconciliation;
- no multi-user/delegated organizational authority;
- no formal cryptographic signing of receipts;
- no external tamper-resistant audit log;
- no protection against a process bypassing this gate until the later enforcement boundary exists.

`NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` therefore remains a target enforcement law, not yet a runtime fact.

## Next pressure
Commit/push this qualification report, create a current-source LKG, then pressure the next boundary before any real provider connector: durable operation lifecycle/reconciliation semantics and/or OS/process network egress enforcement. A first real GitHub connector remains branch-scoped read/push only after that enforcement path is earned.
