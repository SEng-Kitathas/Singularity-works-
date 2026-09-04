# RESEARCH EPISTEMIC SHADOW — Singularity Works App

Last updated: 2026-09-04 UTC
Authority: **NONE_BY_CONTENT**
Purpose: zero-authority research continuity for product/runtime/security meaning and frontier.

## 1. Scope / ownership
This RES belongs to the Singularity Works App/product strand.
It tracks what the App has learned, what remains uncertain, and which research questions now carry the highest expected information value.

It does **not** own:
- Forge Core semantic truth;
- product mutation authority;
- external capability authority;
- release/promotion authority;
- security certification.

`RES_CONTENT != GOVERNING_DOCTRINE`
`SYNTHESIS != VERIFICATION`
`ELOQUENT_INFERENCE != LOAD_BEARING_AUTHORITY`

Main/Core retains its separate RES for semantic/Core research. The two RES surfaces may cross-reference each other, but neither silently absorbs the other's authority domain.

## 2. Current verified App research baseline
Qualified clean source:
`328249429cc6e86e15db9797bd58eff5fabc5a2d` on `forge/app-shell-rd`, local/remote exact and clean at generation 10.

Current LKG:
`checkpoint-app-live-0010-328249429cc6`
VERIFIED / RESUMED / STABLE / LKG / source MATCH / NORMAL / early crash 0 / Ergo READY / Normal recommended.

Current Attempt Store readback:
100 blobs / 100 attempts / 163 events, integrity ok, WAL/FULL.

## 3. Research learning — Connection Gate authority
The pure Connection Gate work established that technical provider capability is only a ceiling; Singularity Works effective authority is the intersection of provider identity/currentness, credential ceiling, connector policy, explicit user grant, exact resource scope, session arming, consequence limits and request-bound confirmation.

Key earned distinctions:
- `VERIFIED_PLATFORM != FULL_AUTHORITY`;
- `CONNECTED != ARMED`;
- `OAUTH_SUCCESS != OPERATION_APPROVAL`;
- `TOKEN_SCOPE != OPERATOR_INTENT`;
- `AUTHORITY_COMPOSES_BY_INTERSECTION_NOT_UNION`;
- external content/text cannot mint operator intent.

Research implication: future connector UX should make technical capability visible without visually implying that all technical capability is currently armed or approved.

## 4. Research learning — durable authority state / generation 9
The durable authority-state campaign established:
- immutable provider/policy/grant/arming generations can coexist with append-only revoke/disarm/currentness events;
- scope changes should create new generations rather than mutate old authority objects;
- persisted decisions bind to exact authority-state fingerprints;
- historical ALLOW remains evidence after authority changes but cannot prepare a new consequence;
- no raw token/API secret material belongs in the authority metadata store.

Load-bearing distinctions earned by execution evidence:
- `AUTHORITY_OBJECT != MUTABLE_ACTIVE_POINTER`;
- `AUTHORITY_SCOPE_CHANGE_CREATES_NEW_GENERATION`;
- `REVOCATION_IS_APPEND_ONLY_EVENT_NOT_GRANT_REWRITE`;
- `DISARM_IS_APPEND_ONLY_EVENT_NOT_ARMING_REWRITE`;
- `DECISION_RECEIPT != CAPABILITY_TOKEN`;
- `OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY`;
- `EXECUTION_PREPARATION_REQUIRES_CURRENT_AUTHORITY_REEVALUATION`;
- `AUTHORITY_STATE_FINGERPRINT_BINDS_DECISION_TO_CURRENT_STATE`;
- `NO_SECRET_BYTES_IN_AUTHORITY_STATE_STORE`.

Research implication: authorization is temporal/currentness-sensitive evidence, not a durable transferable object.

## 5. Research learning — operation lifecycle / generation 10
The local consequence/reconciliation campaign established:
- PREPARED/SUBMITTED/STARTED/COMPLETED_LOCAL/REMOTE_OBSERVED are distinct evidence states;
- local completion does not prove remote commit;
- UNKNOWN_OUTCOME blocks blind retry;
- remote reconciliation is zero-authority evidence about consequence state;
- remote ABSENT does not automatically authorize retry;
- explicit replay after proven absence preserves the same operation/idempotency identity and still requires current authority;
- authority drift after PREPARED blocks SUBMITTED.

Earned distinctions:
- `PREPARED != SUBMITTED != STARTED != COMPLETED != REMOTE_OBSERVED`;
- `LOCAL_SUCCESS != REMOTE_COMMIT_PROVEN`;
- `UNKNOWN_OUTCOME != SAFE_TO_RETRY`;
- `RETRY_AFTER_UNKNOWN_REQUIRES_RECONCILIATION`;
- `IDEMPOTENCY_KEY != AUTHORITY`;
- `REMOTE_OBSERVATION != LOCAL_COMPLETION_ASSUMPTION`;
- `SAME_OPERATION_IDENTITY != NEW_CONSEQUENCE_IDENTITY`;
- `ABSENT_AFTER_RECONCILIATION != AUTOMATIC_RETRY_AUTHORITY`.

Research implication: future provider adapters must conform to this consequence ontology rather than collapsing provider SDK return values into product truth.

## 6. Current frontier — OS/process egress enforcement
The dominant unresolved security question is now whether protected Singularity Works execution domains can be technically prevented from bypassing Connection Gate.

Target law remains **not yet earned**:
`NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`.

Highest-value discriminators:
1. define the exact protected execution-domain boundary;
2. identify Windows primitives capable of default-deny child-process networking without overstating machine-wide control;
3. pressure raw socket access;
4. pressure subprocess/helper-binary escape;
5. pressure plugin/imported-code escape;
6. pressure DNS, loopback and local-service paths;
7. pressure inherited handles/proxies/environment-mediated egress;
8. prove a broker-only allow path can bind transport to a current prepared operation/lifecycle identity;
9. fail closed when enforcement status/currentness is UNKNOWN;
10. preserve manual operator inspection and revocation paths.

## 7. Active Sigma branches / competing enforcement frames
These are research branches, not decisions:
- per-child-process Windows firewall/WFP containment;
- AppContainer or restricted-token style execution domains;
- isolated broker process with protected children denied ambient network;
- job/process-tree containment combined with network controls;
- local proxy-only architecture with OS deny for direct egress;
- disposable sandbox/container/VM boundary for untrusted plugins/imported code;
- capability-token/broker handles that never expose ambient socket authority.

Each branch must be evaluated for actual enforceability on the current Windows runtime, failure behavior, child-process inheritance, operator recoverability, and compatibility with Singularity Works UX.

## 8. Attention Reservoir
Keep visible until resolved:
- whether Windows child-process network denial can be proven without admin/machine-global policy;
- DNS and loopback bypass behavior;
- subprocess trees and inherited capabilities;
- connector/broker crash between local submission and transport observation;
- provider-specific reconciliation limits;
- eventual Vault secret boundary for OAuth/API credentials;
- distinction between protected-domain enforcement and whole-machine firewall claims;
- Core semantic bridge remains UNKNOWN and Main-owned.

## 9. Linear Human Read / Semantic Gate
R4.2-canonical process law; originally introduced as operator-bound additive doctrine and retained in that history:

**LINEAR HUMAN READ / SEMANTIC GATE**

If an artifact can be meaningfully read, it SHALL receive a complete linear semantic read before it is promoted, sealed, published, admitted, or treated as load-bearing. Automated checks may precede and support the gate; they SHALL NOT substitute for it.

RES consequence:
- RES may summarize, rank, hypothesize or point to an artifact before promotion;
- RES synthesis does not satisfy the semantic gate;
- automated verification does not satisfy the semantic gate;
- unread readable artifacts remain ineligible for load-bearing promotion.

`RES_SYNTHESIS != LINEAR_HUMAN_SEMANTIC_READ`
`MACHINE_PASS != HUMAN_SEMANTIC_GATE_PASS`
`SUMMARY != LINEAR_READ`

## 10. Revisit triggers
Update this RES when any of the following materially changes the meaning/frontier:
- OS/process egress enforcement Attempt 0 is designed or executed;
- a bypass is discovered;
- a Windows enforcement primitive is proven impractical or sufficient;
- real provider transport begins;
- OAuth/secret-storage architecture changes;
- GitHome/Vault architecture gains consequence-bearing implementation;
- Main publishes a qualified Core restoration/currentness bridge;
- a security assumption is promoted, demoted or contradicted.

## 11. Current research-to-do
1. Linearly read any meaningfully readable enforcement artifact before load-bearing promotion.
2. Inspect current Windows/process-launch topology and available enforcement primitives.
3. Build the smallest discriminator that can falsify ambient-network denial.
4. Preserve Attempt 0 before first execution.
5. Attack raw socket/subprocess/plugin/DNS/loopback paths.
6. Keep `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` UNKNOWN/not-earned until runtime enforcement evidence exists.


## 12. Semantic gate — first verified publication-boundary learning
Truth status: VERIFIED cross-project process embodiment; authority NONE for App security claims.

The Linear Human Read / Semantic Gate has now been exercised on the durable Main Git control publication boundary. Complete readable set: 55 files / 5,481 lines / 349,333 bytes; semantic-read stream SHA `8661b5fb6b3e6a9dd6814f625eea456ffe25b28f980db0033c8f0d69a228260f`.

The linear read found two semantic representation ambiguities not resolved by machine integrity/privacy checks. Both were corrected and reread before publication. Machine verification and remote/fresh-clone readback then passed.

App research implication for upcoming egress-enforcement work:
- passing tests/hashes/static checks cannot be used as a proxy for semantic clarity of enforcement scope;
- the read must specifically pressure whether claims like “network denied,” “protected child,” “broker-only,” or “machine-wide” actually mean what the implementation proves;
- human-semantic ambiguity is itself a security risk when enforcement scope is consequence-bearing.

`MACHINE_INTEGRITY_PASS != SEMANTIC_UNAMBIGUITY`
`ENFORCEMENT_TEST_PASS != ENFORCEMENT_SCOPE_SEMANTICALLY_UNAMBIGUOUS`
`SEMANTIC_READ_FINDING != MACHINE_VALIDATION_FINDING`

This strengthens the semantic gate as a required App promotion precondition while preserving `RES_CONTENT != GOVERNING_DOCTRINE`.

## R4.2 full-adherence synchronization — 2026-09-04
Truth status: VERIFIED process-ingestion/currentness evidence; RES authority remains NONE_BY_CONTENT.

R4.2 is the active universal engineering/research process and cold-start default for this arm. Fresh 2026-09-04 source contact re-read all 35 active/current readable members (3,070 source lines, 0 unread) from exact carrier SHA `eb167543e9ceb2ae01449f421d2916e61b7dd924270ea2e83e3364c9d808ce9a`; fresh verifier PASS and hostile campaign 26/26 rejected.

Operational meaning retained from R4.2:
- semantic admission requires complete linear reading before load-bearing authority transitions; automation supports but does not substitute;
- substantial finite deterministic work defaults to the strongest sufficient operator/local/server plane;
- response loss requires consequence-bearing readback before rerun;
- after the first deterministic bridge/transport failure, repeating the same architecture without rerouting is presumptively a process error;
- continuity remains navigation/research state rather than truth authority.

`AUTOMATED_CHECKS != LINEAR_SEMANTIC_READ`
`CONTROL_PLANE_RESPONSE_FAILURE != LOCAL_EXECUTION_FAILURE`
`STRONGEST_SURVIVING_PLANE != PRETTIEST_PLANE`
`RES_CONTENT != GOVERNING_DOCTRINE`
