# Project Commander’s Intent — Singularity Works / Forge — Current

Standard: ICF-CS v1.1
Status: CURRENT PROJECT INTENT / CONSTRAINT / FRONTIER INGRESS
Last updated: 2026-09-06
Authority: project-local continuity/direction surface. Owner intent and stronger project-local doctrine supersede where explicit. Frontier facts still require live readback before mutation.

## I. INTENT — slow-changing project direction
Singularity Works is one software/product whole. Forge Core/Main and Forge App are two development strands of that whole, separated for qualification and pressure—not separate products or competing sources of truth.

The project is trying to become a durable, operator-usable software-production/research platform in which:
- Forge provides canonical semantic/evidence/transformation machinery and shared semantic interfaces;
- App provides recovery, runtime/process embodiment, operator interaction, product/security boundaries, and user-facing execution surfaces;
- canonical truth is not duplicated merely for convenience;
- semantic claims, runtime authority, external consequences, and recovery state remain explicitly separated;
- changes are evidence-bearing, reversible/traceable where practical, and qualified before promotion;
- thread/session churn does not cause direction rollback or historical artifacts to regain current authority.

### Success means
- Main/Core and App converge as one coherent product without silent authority transfer or duplicated canonical subsystems;
- Forge can represent and reason over exact source/evidence/currentness while exposing bounded consumer interfaces;
- App can safely operate/recover against qualified source ancestry and consume canonical Core interfaces without private forks;
- external/consequence-bearing behavior is controlled by explicit product/runtime authority rather than semantic inference;
- current state, doctrine, evidence, recovery, and research frontier remain durable and rehydratable across threads;
- project evolution stays driven by measured reality and hostile qualification rather than stale narratives or aesthetic preference.

`INTENT != TASK_QUEUE`
`INTENT != MUTATION_PERMISSION`

## II. CONSTRAINTS — load-bearing and not casually reopened
### Authority / ownership
- Main/Core owns canonical Forge semantic/currentness/snapshot/bridge implementation.
- App owns product/runtime/recovery/operator/network/external-authority embodiment.
- App consequence mechanisms do not mint Core semantic truth.
- `RES_CONTENT != GOVERNING_DOCTRINE`.
- `FRONTIER != DOCTRINE_AUTHORITY`.

### Cross-arm topology
- `MAIN_DRIFT_SHOULD_BE_INGESTED_EARLY; APP_PROMOTION_SHOULD_BE_INGESTED_LATE`.
- Prefer qualified Main -> App forward sync while drift is small.
- Do not casually rebase/force-rewrite provenance-bearing App history.
- Git mergeability is not architectural/product qualification.
- Bridge first; do not copy canonical Core implementation into App.

### Evidence / promotion
- R4.4 is the current canonical process/cold-start default under `CANONICAL_PROCESS_DEFAULT != UNIVERSAL_DOMAIN_TRUTH`.
- ICF-CS v1.1 is the current binding additive continuity/process doctrine above sealed R4.4: payload `sop/RAHL_ENGINEERING_CANONICAL_SOP_R4_4_ICF_CS_V1_1_ADDENDUM_2026-09-05.zip` SHA `f6f4ab2bafdb0ef2a7db1622a00462990baf980284d5b33827807caea1d41f63`; detached release receipt `sop/ICF_CS_V1_1_DETACHED_RELEASE_RECEIPT_2026-09-05.json` SHA `418346ed6373887b5b924e71ca2bf4b83effad20b7269ab40607f5d2750b970c`; standard SHA `62be845da364ae81f59b6320c9b34b136236bf5be8aa8036018da48efcb754f4`; machine contract SHA `d67726aeb402c280770eeaf314068ed7a1330beb21167d9d6d9b7c4674425bb0`; qualification contract SHA `7d20ed708adb4f7ee147b56da41deac77146b56fc85bd769be3a6d240b3e2029`; mechanized epoch profile SHA `733b799815abdb4b1ff735635f7928953c12944ece579365b5aae138d90f90f8`. v1.0 is demoted historical evidence by demotion receipt SHA `3225fd952d704d31047ffdf01bffbc0968e4428357342ccb8ce5094ae8385057`.
- ICF-CS scope is continuity/rehydration/current-ingress/evaluation-data hygiene only; it does not mint semantic/product/runtime/source/recovery/security authority.
- Readable load-bearing artifacts require complete linear semantic read before promotion/admission.
- `AUTOMATED_CHECKS != LINEAR_HUMAN_SEMANTIC_READ`.
- `GATE_ASSERTED != GATE_WITNESSED`.
- `CONTROL_CHECKPOINT != PRODUCT_PROMOTION`.
- `REMEMBERED_POINTER != CURRENT_STATE_EVIDENCE`.
- Mutation/execution/push claims require consequence-bearing readback.

### Semantic-field boundary
- Current public Main branch head is `6ea95275cdc409ed222e4720b6b04aadaa17e6bf`. It is a direct authority-publication-only child of `287c0bad0e9b3fef3002b91702e86b410cada4ce`; Core semantic qualification anchor remains `a7b4511734b1a1e507230308e75b31175aef4c4a` because no Core code changed. `MAIN_BRANCH_HEAD != CORE_QUALIFICATION_ANCHOR`.
- Governance Contact v1.0 pending carrier at Main `6ea95275cdc409ed222e4720b6b04aadaa17e6bf`: ZIP `c4ab4a516e088b6c28b5240d6b3877d2e3fb889a8bbbfd406e8e0c73bebdd1ae`, detached receipt `cf2e7bd8e5ed613d3c3a99b7f8645833ddb742ac4939bd1719092b277ef286e6`, exact payload semantic stream `ae5e645ffaab627ae0959bf6780591bd0dae622a91cad265b39c1885b7ac75ff` (2,357 lines). `authority/rahl-sop/CURRENT.md` remains unchanged; target lifecycle is incomplete; authority effect remains NONE. `DETACHED_RELEASED != TARGET_PUBLISHED`; `POST_PUBLICATION_READBACK != ACTIVE`; `CARRIER_PRESENT != PROJECT_SPECIFIC_AUTHORITY_REWRITE`.
- Canonical App-facing bridge: `singularity_works.semantic_field_bridge`, schema `singularity-works.semantic-field-bridge/0.1`.
- Index/projection/delta authority remains NONE unless separately changed by qualified doctrine.
- Evidence identity is not automatically semantic meaning.
- Checkpoint semantic restoration/currentness/snapshot identity remains separate from bridge-source availability.

### Recovery / consequence boundary
- App current source is `forge/app-shell-rd@43aa7feac7e8a15828116bd700b644560714496d`, local/remote exact, clean, and independently fresh-clone verified. It descends from preserved Attempt 0 through D2 v0.1.1/v0.1.2 repair lineage.
- Generation 14 `checkpoint-app-live-0014-43aa7feac7e8` is the current earned LKG for `43aa7feac7e8a15828116bd700b644560714496d`: VERIFIED / RESUMED / STABLE / LKG / source MATCH / NORMAL / early crash 0 / not quarantined. Blob `4efabde670986f65fc3e1736452300b299f79045e5b537ea46425e1dbbbd2136`; evidence SHA `bc4bbddd0addc9be743ca01d7f022b2d2b1228373e1eac7d181937a008a32c50`.
- Generation 13 remains historical LKG evidence for `9bc35af...` and is source-stale against current App.
- Protected-process primitive v0.1.2 is **BOUNDED QUALIFIED** for the exact tested Windows host/source/test boundary. Qualification receipt SHA `3d27639447f1d47ac71e892a766444a3e7c8627ff3120b791ecf4470ebeedda6`, preserved as `attempt-egress-process-primitive-v0-1-2-bounded-qualification`; first committed D2 PASS `5919cdc7af94d0e34d5884366eb3f328762422c03f2346afd332690820863b68`; same-commit D0-D3 4/4 regression PASS `1a571cae54279aa4b79646b87dfb254701957088d481bc7b0de7c832935055fa`.
- Qualified bounded claims cover the exact zero-capability AppContainer + immediate Job root, tested root loopback denial, validated PowerShell/Process.Start descendant loopback denial, and bounded Job-close timeout teardown.
- `LOCAL_LOOPBACK_PROCESS_CONTAINMENT != GENERAL_EXTERNAL_EGRESS_CONTAINMENT`.
- `BOUNDED_PRIMITIVE_QUALIFIED != PRODUCTION_ENFORCEMENT_INTEGRATED`.
- `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` remains unearned as a runtime law.
- `APP_SOURCE_INTEGRATED != NEW_LKG`.
- `BRIDGE_SOURCE_AVAILABLE != CHECKPOINT_SEMANTIC_RESTORATION_QUALIFIED`.
- `OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY`.
- `UNKNOWN_OUTCOME != SAFE_TO_RETRY`.

### Continuity / re-entry
- Git is the durable cross-thread control plane for bounded continuity snapshots.
- Live/server state and Git control state are distinct and must be reconciled.
- Historical handoffs/donors are not current ingress by discoverability alone.
- ICF-CS cold-start order governs fresh-thread re-entry before DTS archaeology.

`DIRECTION != CONSTRAINTS != FRONTIER != HISTORY`

## III. FRONTIER — fast-changing current state
### Earned now
- R4.4 is current canonical process/cold-start SOP; carrier SHA `04f3e94efe8c901cc83a12a9c8531be8a9bb350728b8f9eba53db0fd082b3bbc`.
- Current public Main branch head: `6ea95275cdc409ed222e4720b6b04aadaa17e6bf`; immediate authority-publication predecessor `287c0bad0e9b3fef3002b91702e86b410cada4ce`; Core qualification anchor remains `a7b4511734b1a1e507230308e75b31175aef4c4a`.
- App source local/remote exact, clean and independently fresh-clone verified: `43aa7feac7e8a15828116bd700b644560714496d`.
- App Gen14 `checkpoint-app-live-0014-43aa7feac7e8` is current LKG/source MATCH/NORMAL; Gen13 is historical/source-stale.
- Protected-process primitive v0.1.2 is bounded QUALIFIED under receipt `3d27639447f1d47ac71e892a766444a3e7c8627ff3120b791ecf4470ebeedda6`. First committed D2 v0.1.2 PASS `5919cdc7af94d0e34d5884366eb3f328762422c03f2346afd332690820863b68`; same-commit D0-D3 4/4 regression PASS `1a571cae54279aa4b79646b87dfb254701957088d481bc7b0de7c832935055fa`.
- Main->App semantic-field Core integration remains intact; App D2 repair changes no protected-process implementation or Core semantics.
- Latest independently verified durable control is `pcmmad/project-control@f120ff577cd3a3df438d354ae9cd0662d037663f`, CHECKPOINT `263d3d9aec93c3f3cc037cf34de3d311bd64e0c91d6e36df5b5a68372c675dc4`, verifier PASS 115, fresh-clone exact/clean.
- App `43aa7feac7e8a15828116bd700b644560714496d` + Gen14 + bounded qualification are newer than that control generation and must enter the next normal control checkpoint before new consequence-bearing bypass attempts.

These hashes are **current-ingress pointers**, not perpetual truth. Re-read live Git/recovery state before consequence-bearing mutation.

### Immediate continuity prerequisite
**Publish and fresh-clone verify the next normal `pcmmad/project-control` generation from verified predecessor `f120ff577cd3a3df438d354ae9cd0662d037663f` carrying App `43aa7feac7e8a15828116bd700b644560714496d`, Gen14, the bounded v0.1.2 qualification receipt/evidence, and the repaired current-ingress surfaces.**

This is continuity durability only; it does not widen the qualification claim.

### Active product/security frontier after that checkpoint
**Wider egress-bypass pressure + production launch-site integration.**

Next attempts require separate preservation/qualification for materially new claims. Pressure targets include:
- DNS resolution/transport behavior;
- UDP/QUIC and non-TCP egress;
- proxy/environment-mediated egress;
- helper/browser/plugin/imported-code launch paths;
- COM/RPC/service/WSL or equivalent local escape surfaces;
- Job breakaway/process-tree semantics beyond the exact tested path;
- actual protected launch-site wiring and broker/Gate allow-path integration.

Do not promote child-process/AppContainer evidence into machine-wide firewall control. Do not start with a real provider connector.

### Open / unearned
- general external egress containment;
- production launch-site enforcement integration;
- runtime truth of `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`;
- real provider/OAuth/GitHub connector;
- secure Vault token/crypto implementation;
- checkpoint semantic restoration/currentness/snapshot identity;
- broader bypass classes listed above;
- inherited package-description/counter metadata repair.

### Deferred / separate
- Main/Core source remains unchanged unless App pressure exposes a genuine semantic/interface requirement.
- Checkpoint restoration identity is separate from the egress primitive.
- Packaging-description debt stays separately scoped.

### Immediate next move
Publish/read back the next normal control checkpoint from `f120ff577cd3a3df438d354ae9cd0662d037663f` containing App `43aa7feac7e8a15828116bd700b644560714496d`, Gen14 and the bounded protected-process qualification. After fresh-clone verification, preserve a **new** Attempt for the next wider bypass/production-integration discriminator; do not reuse or rewrite Attempt-0/v0.1.1/v0.1.2 evidence.

## IV. HISTORY BOUNDARY
The following categories are useful but are not current ingress by default:
- old handoffs;
- prior R4.x adoption generations;
- superseded Main/App SHAs;
- Gen10 and earlier recovery generations;
- donor-project artifacts;
- historical audit campaigns;
- old green test reports whose source/environment identity no longer matches.

Use them as lineage/evidence/donor surfaces only after current ingress is established.

`HISTORICAL_HANDOFF != CURRENT_INGRESS`
`DONOR != AUTHORITY`
`RECENT_TIMESTAMP != CURRENT_AUTHORITY`
`STALE_GREEN != CURRENT_EVIDENCE`

## V. RE-ENTRY CONTRACT
Read in this order for a fresh thread/project re-entry:

`CURRENT STATE -> ICF-CS -> CURRENT CANONICAL SOP + NEXT/DOCTRINE/REVISIT/TRACE -> LIVE SHADOW -> DTS -> LIVE READBACK BEFORE MUTATION`

If material conflict exists:

`CONFLICT -> RECOVERY/AUDIT -> LOCALIZE -> REPAIR/SUPERSEDE -> READBACK -> RESUME`

The discoverable pointer is `checkpoints/PROJECT_INTENT_CURRENT.md`.
