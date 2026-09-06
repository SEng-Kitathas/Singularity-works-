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
- Current public Main branch head is `287c0bad0e9b3fef3002b91702e86b410cada4ce`. Core semantic qualification anchor remains `a7b4511734b1a1e507230308e75b31175aef4c4a` because `287c0bad0e9b3fef3002b91702e86b410cada4ce` is an authority-publication-only child with no Core code changes. `MAIN_BRANCH_HEAD != CORE_QUALIFICATION_ANCHOR`.
- Canonical App-facing bridge: `singularity_works.semantic_field_bridge`, schema `singularity-works.semantic-field-bridge/0.1`.
- Index/projection/delta authority remains NONE unless separately changed by qualified doctrine.
- Evidence identity is not automatically semantic meaning.
- Checkpoint semantic restoration/currentness/snapshot identity remains separate from bridge-source availability.

### Recovery / consequence boundary
- App current source is `forge/app-shell-rd@e9b81750db265a467187c61962ffab3cff98d4fe`, local/remote exact and clean; it is the preserved egress-enforcement Attempt-0 commit and does not by itself qualify the egress primitive.
- Generation 12 `checkpoint-app-live-0012-e9b81750db26` is the current earned LKG for `e9b81750db265a467187c61962ffab3cff98d4fe`: VERIFIED / RESUMED / STABLE / LKG / source MATCH / NORMAL / early crash 0 / not quarantined. Evidence SHA `aeff0db397135d8f227f11e17c1b7b939235b6ae11ee2ae97053246d9d605e0a`.
- Generation 11 `checkpoint-app-live-0011-b674dbaaf428` remains historical LKG evidence for source `b674dba...` but is source-MISMATCH against current App and is not the current recovery ingress.
- `APP_SOURCE_INTEGRATED != NEW_LKG`.
- `BRIDGE_SOURCE_AVAILABLE != CHECKPOINT_SEMANTIC_RESTORATION_QUALIFIED`.
- `OLD_ALLOW_RECEIPT != CURRENT_EXECUTION_AUTHORITY`.
- `UNKNOWN_OUTCOME != SAFE_TO_RETRY`.
- `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` remains unearned as a runtime fact until OS/process enforcement evidence exists.

### Continuity / re-entry
- Git is the durable cross-thread control plane for bounded continuity snapshots.
- Live/server state and Git control state are distinct and must be reconciled.
- Historical handoffs/donors are not current ingress by discoverability alone.
- ICF-CS cold-start order governs fresh-thread re-entry before DTS archaeology.

`DIRECTION != CONSTRAINTS != FRONTIER != HISTORY`

## III. FRONTIER — fast-changing current state
### Earned now
- R4.4 is current canonical process/cold-start SOP; carrier SHA `04f3e94efe8c901cc83a12a9c8531be8a9bb350728b8f9eba53db0fd082b3bbc`.
- Current public Main branch head: `287c0bad0e9b3fef3002b91702e86b410cada4ce`; Core qualification anchor remains `a7b4511734b1a1e507230308e75b31175aef4c4a`.
- App source local/remote exact and clean: `e9b81750db265a467187c61962ffab3cff98d4fe`; this preserves egress Attempt 0 but does not qualify it.
- App generation 12 `checkpoint-app-live-0012-e9b81750db26` is current LKG/source MATCH/NORMAL; Gen11 is historical/source-stale.
- Main->App semantic-field Core integration remains intact; the later Main head is authority-publication-only and the later App head only preserves egress Attempt 0.
- Durable control branch current verified baseline: `pcmmad/project-control@63f7a74f47be4179b5871fd7ff9da819b54e3ab9`, frozen CHECKPOINT SHA `500d7c167ff5d27e6287edf675d7bbc06a91b5a7c169ffa44df753e6af6bb049`, verifier PASS 96, fresh-clone exact/clean. Resolve the branch ref live before mutation; newer verified generations supersede this baseline as currentness evidence.
- ICF-CS v1.1, Main/App source currentness, and Gen12 recovery are server-current but newer than durable control `63f7a74f47be...`; one successor control checkpoint is required before executing egress Attempt 0.

These hashes are **current-ingress pointers**, not perpetual truth. Re-read live Git/recovery state before consequence-bearing mutation.

### Immediate continuity prerequisite
**Publish and fresh-clone verify a successor `pcmmad/project-control` generation from verified predecessor `63f7a74...` containing ICF-CS v1.1 + Main/App source currentness + Gen12 recovery.**

This is continuity durability only; it does not change the product/security frontier below.

### Active immediate frontier
**App OS/process network egress enforcement — Attempt 0.**

Required first pressure:
- inspect actual Windows/process-launch primitives;
- define the protected execution-domain boundary;
- determine where default-deny can actually be enforced;
- attack bypasses through raw sockets, subprocesses, plugins, DNS, and loopback;
- Attempt 0 is already preserved; after successor control readback, execute the exact frozen D0-D3 tests without editing them first;
- do not begin with a real provider connector.

### Open / unearned
- OS/process egress enforcement itself;
- runtime truth of `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`;
- real provider/OAuth/GitHub connector;
- secure Vault token/crypto implementation;
- checkpoint semantic restoration/currentness/snapshot identity;
- supervisor-death / whole-process-tree containment seams;
- inherited package-description/counter metadata repair.

### Deferred / separate
- Main/Core source remains unchanged unless App pressure exposes a genuine semantic/interface requirement.
- Checkpoint restoration identity is a separate cross-arm interface qualification, not a prerequisite for starting egress-enforcement research unless the implementation actually depends on it.
- Packaging-description debt stays separately scoped from semantic/runtime work.

### Immediate next move
First publish/read back the successor control generation from verified predecessor `63f7a74...` containing ICF-CS v1.1, Main/App source currentness and Gen12. After fresh-clone verification, execute the exact already-preserved egress Attempt-0 hostile tests without editing them first.

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
