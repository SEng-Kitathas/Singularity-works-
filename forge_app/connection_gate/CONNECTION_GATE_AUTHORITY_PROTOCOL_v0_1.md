# Singularity Works Connection Gate Authority Protocol v0.1

Status: **Attempt 0 protocol** — preserve before first execution.

## Goal
Prove the external-authority model before wiring any real provider connector.

The Connection Gate v0.1 is a **pure decision engine**. It performs no network I/O, stores no credential secret, and executes no external consequence.

## Governing laws
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
- `REQUEST_IDENTITY_IS_PART_OF_CONSEQUENCE_AUTHORITY` is an ancestry donor mechanism embodied here through request-bound confirmation.

## Authority layers
Every evaluation supplies independent layers:
1. `ProviderIdentity` — provider + external subject + verification/currentness.
2. `CredentialCeiling` — maximum capabilities/resources technically available to the credential; no secret material.
3. `ConnectorPolicy` — Singularity Works connector capability/resource/consequence ceiling.
4. `UserGrant` — exact principal/provider/connector capability/resource/consequence grant.
5. `SessionArming` — exact principal/provider/connector envelope explicitly armed by the user.
6. `OperationRequest` — exact request ID, principal, provider, connector, capability, resource, consequence, reason and intent source.
7. optional `OperationConfirmation` — exact request/principal-bound confirmation for elevated consequences.

Effective authority is never a merged superset. The requested capability/resource must be accepted by every applicable layer.

## Decisions
The pure evaluator returns one authority-NONE receipt:
- `ALLOW`;
- `REQUIRE_CONFIRMATION`;
- `DENY`;
- `UNARMED`;
- `STALE`;
- `UNKNOWN`.

The receipt is evidence/decision output only. It cannot itself be reused as a capability grant.

## Fail-closed behavior
- unknown provider verification -> UNKNOWN;
- unverified provider -> DENY;
- stale authority layer -> STALE;
- unknown currentness -> UNKNOWN;
- revoked grant -> DENY;
- grant state unknown -> UNKNOWN;
- unarmed or not manually approved session -> UNARMED;
- external-content intent source -> DENY;
- unknown intent source -> UNKNOWN;
- binding mismatch across principal/provider/connector/subject -> DENY;
- capability/resource absent from any authority layer -> DENY;
- consequence above the minimum allowed ceiling -> DENY;
- required confirmation missing -> REQUIRE_CONFIRMATION;
- confirmation for different request/principal -> DENY;
- stale/unknown confirmation -> STALE/UNKNOWN;
- explicit denied confirmation -> DENY.

## Consequence ordering
`READ < WRITE < PUBLISH < ADMIN < DESTRUCTIVE`.

Each policy/grant/arming layer may set its own maximum consequence and confirmation threshold. The effective maximum is the most restrictive maximum. The effective confirmation threshold is the earliest/most restrictive threshold.

## Manual parity
`SessionArming` exists as a first-class input rather than implicit connector state. A user can therefore explicitly arm/disarm the external authority envelope.

The eventual persisted/UI layer must provide manual:
- arm;
- disarm;
- inspect;
- revoke;
- confirm/deny;
- receipt inspection.

## No network claim
Passing this protocol does not mean `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` is enforced yet. That requires a separate process/network enforcement boundary.

## Attempt-0 hostile targets
1. broad token does not widen a narrow grant;
2. wrong resource denied;
3. wrong provider/connector/principal binding denied;
4. unarmed session returns UNARMED;
5. stale grant returns STALE;
6. unknown identity/currentness returns UNKNOWN;
7. external repository/model text cannot mint intent;
8. elevated write requires exact request-bound confirmation;
9. confirmation for another request is denied;
10. revoked grant denied;
11. low-consequence read inside exact armed intersection allowed;
12. armed automation may operate only inside the same effective envelope.
