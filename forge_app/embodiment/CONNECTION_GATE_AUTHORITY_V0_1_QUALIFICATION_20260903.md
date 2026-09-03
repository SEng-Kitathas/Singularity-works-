# Singularity Works Connection Gate Authority v0.1 — Qualification — 2026-09-03

Status: **READY_WITH_EVIDENCE for provider-agnostic, pure, fail-closed authority evaluation and explicit decision receipts.**

Not qualified for real OAuth/network transport, credential storage, persisted grant/arming state, process/network enforcement, or external provider security.

## Goal
Prove the authority model before wiring any real external connector.

The v0.1 gate performs **no network I/O**, stores **no credential secret**, and executes **no external consequence**. It only evaluates the exact intersection of independently supplied authority layers and returns an authority-NONE decision receipt.

## Governing laws embodied
- `VERIFIED_IDENTITY != AUTHORIZED_CAPABILITY != EFFECTIVE_AUTHORITY`.
- `VERIFIED_PLATFORM != FULL_AUTHORITY`.
- `CONNECTED != ARMED`.
- `OAUTH_SUCCESS != OPERATION_APPROVAL`.
- `TOKEN_SCOPE != OPERATOR_INTENT`.
- `CAPABILITY_AVAILABLE != CAPABILITY_ACTIVE`.
- `AUTHORITY_COMPOSES_BY_INTERSECTION_NOT_UNION`.
- `OPERATOR_INTENT != PLATFORM_APPROVAL_STATE`.
- `EXTERNAL_CONTENT != OPERATOR_COMMAND`.
- `REMOTE_TEXT != AUTHORITY`.
- `PROMPT_LIKE_CONTENT != INTENT`.
- request-bound confirmation embodies the donor pressure `REQUEST_IDENTITY_IS_PART_OF_CONSEQUENCE_AUTHORITY`.

## Authority layers
The pure evaluator receives:
1. `ProviderIdentity` — provider subject, verification, currentness;
2. `CredentialCeiling` — technical capability/resource ceiling without secret material;
3. `ConnectorPolicy` — Singularity Works connector policy identity and limits;
4. `UserGrant` — exact principal/provider/connector grant;
5. `SessionArming` — exact manually approved active envelope;
6. `OperationRequest` — request/principal/provider/connector/capability/resource/consequence/reason/intent source;
7. optional `OperationConfirmation` — exact request/principal-bound confirmation.

A capability or resource is effective only when **every** relevant layer allows it. Consequence ceiling is the most restrictive maximum. Confirmation threshold is the earliest/most restrictive threshold.

## Attempt-0 preservation
Unexecuted protocol/code/tests were committed and pushed before first evaluation:

`9b65e638729e8ef91c22d02d7c5c1bb942145a99` — `singularity-works: preserve connection gate authority attempt zero`.

Files:
- `forge_app/connection_gate/authority.py`;
- `forge_app/connection_gate/CONNECTION_GATE_AUTHORITY_PROTOCOL_v0_1.md`;
- `forge_app/connection_gate/__init__.py`;
- `forge_app/embodiment/test_connection_gate_authority_v0_1.py`.

## First targeted execution
Command:
`python -W error::ResourceWarning -m unittest forge_app.embodiment.test_connection_gate_authority_v0_1 -v`

Result: **13/13 PASS unchanged**.

Verified hostile cases:
1. exact low-consequence read inside the armed intersection -> ALLOW;
2. credential with admin/force-push scope cannot widen narrower policy/grant/arming;
3. wrong resource denied even with global credential resource ceiling;
4. unarmed or not-manually-approved session -> UNARMED;
5. stale grant -> STALE;
6. unknown provider verification/currentness -> UNKNOWN;
7. external-content intent -> DENY;
8. elevated write -> REQUIRE_CONFIRMATION;
9. exact request/principal-bound confirmation -> ALLOW;
10. confirmation for another request -> DENY;
11. revoked grant -> DENY;
12. principal/provider/connector binding mismatch -> DENY;
13. armed automation remains inside the exact same envelope;
14. decision identity changes when request identity changes.

No repair was required after Attempt 0.

## Full App regression
After adding Connection Gate:
`python -W error::ResourceWarning -m unittest discover -s forge_app/embodiment -p test_*.py -v`

Result: **73/73 PASS** in 9.488 seconds.

## Live non-networking authority discriminator
A live decision packet was generated against the actual Singularity Works GitHub resource identity:

`github:SEng-Kitathas/Singularity-works-:branch:forge/app-shell-rd`

Source HEAD:
`9b65e638729e8ef91c22d02d7c5c1bb942145a99`.

No network I/O was performed.

Technical credential ceiling intentionally included:
- `repo.read`;
- `repo.push`;
- `repo.admin`;
- `repo.force_push`;
- global resource ceiling `*`.

Singularity Works policy/user/session envelopes allowed only:
- `repo.read`;
- `repo.push`;
- exact `forge/app-shell-rd` branch resource;
- maximum WRITE consequence;
- confirmation from WRITE upward.

### Live decisions
1. `live-read` -> **ALLOW**.
2. `live-push` without confirmation -> **REQUIRE_CONFIRMATION**.
3. same exact `live-push` with exact request/principal confirmation -> **ALLOW**.
4. `live-main-push` -> **DENY** because `main` is outside policy/grant/arming resource intersection.
5. `live-force-push` -> **DENY** because DESTRUCTIVE exceeds the effective consequence envelope.
6. `live-external-text` -> **DENY** because external content cannot mint operator intent.
7. `live-unarmed` -> **UNARMED**.
8. `live-stale` -> **STALE**.
9. `live-unknown` -> **UNKNOWN**.

This demonstrates the core user requirement: a connected/verified provider and technically powerful credential do not imply admin/destructive authority inside Singularity Works.

## Decision receipts
Every result carries:
- deterministic decision ID bound to request and authority inputs;
- decision and reasons;
- request/principal/provider/connector identity;
- capability/resource/consequence/intent source;
- provider subject;
- credential/policy/grant/arming IDs;
- exact confirmation ID when supplied;
- computed effective capability/resource intersection;
- `receipt_authority = NONE`.

The receipt is evidence, not a reusable capability token.

## Live evidence preservation
Packet:
`state/live_connection_gate_authority_v0_1.json`
SHA-256:
`97e403c2211da3a2b0b05b807b5d64081de9febae3e0ad386a1333aa9ecb038e`.

Attempt Store:
`attempt-live-connection-gate-authority-v0-1`
with exact verified readback and the same blob SHA.

Store after capture:
- integrity `ok`;
- WAL;
- synchronous FULL;
- 62 blobs / 62 attempts / 96 events.

## Source hashes at Attempt-0 qualification
At `9b65e638729e8ef91c22d02d7c5c1bb942145a99`:
- `forge_app/connection_gate/authority.py`
  SHA `2745e3fc7c4a4814a9d04eeb50accb22c1b74715e8cb58fad8a970ac0b19cdc8`;
- `forge_app/connection_gate/CONNECTION_GATE_AUTHORITY_PROTOCOL_v0_1.md`
  SHA `7a444c6f8db0198a3d47cbea64674298cc65b3a89345478ce0f24bfd2de85525`;
- `forge_app/connection_gate/__init__.py`
  SHA `18b725b679bf7b85c38d038a86e578876fad6c5abac52ef72d43f6cdf5b05ea1`;
- `forge_app/embodiment/test_connection_gate_authority_v0_1.py`
  SHA `dddb5cc55017518f004517272c2d2f1c94a85fe8870dd63765e4e4b48a4ef825`.

## Bounded claim
Singularity Works now has a provider-agnostic authority evaluator that can distinguish verified identity, technical credential scope, product connector policy, explicit user grant, active manual session arming, exact resource scope, consequence class, intent source and request-bound confirmation.

On the tested pure-decision boundary, authority narrows by intersection and fails closed on unverified, stale, unknown, revoked, unarmed, mismatched, out-of-scope and externally-minted-intent conditions.

A powerful credential cannot silently promote itself into broader Singularity Works authority.

## Not yet qualified
- actual OAuth authorization-code/PKCE flow;
- secure token/secret storage;
- persisted grant/session-arming ledger;
- revocation propagation from provider;
- provider metadata/currentness acquisition;
- actual GitHub API calls;
- process/network enforcement proving all egress must traverse the Gate;
- receipt persistence/append-only audit integration for every real external call;
- rate limit/retry/unknown commit outcome for external operations;
- multi-user/delegated organizational authority;
- connector compromise;
- remote service compromise;
- formal security certification.

## Next pressure
Commit this qualification report and create a current-source LKG. Then build the first **persisted/manual authority-state + receipt ledger** or the process/network enforcement boundary before connecting a real provider. The first real provider should remain branch-scoped GitHub read/push with admin/delete/force-push unavailable by policy.
