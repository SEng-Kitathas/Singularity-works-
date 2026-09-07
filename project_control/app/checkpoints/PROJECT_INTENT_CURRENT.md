# Current Project Ingress Pointer — Singularity Works / Forge

Standard: ICF-CS v1.1
Purpose: bounded discovery pointer only; navigation is not proof.

## Current ingress
1. `state/current/current.md`
2. `state/doctrine_snapshot/PROJECT_COMMANDERS_INTENT_CURRENT.md`
3. `state/doctrine_snapshot/INTENT_CONSTRAINT_FRONTIER_CONTINUITY_STANDARD.md`
4. current canonical process SOP: RAHL Engineering Canonical SOP R4.4
5. `state/next_steps/next_steps.md`
6. `state/doctrine_snapshot/doctrine_snapshot.md`
7. `state/revisit_ledger/revisit_ledger.md`
8. `state/trace_matrix/trace_matrix.md`
9. `continuity/live_shadow/live_shadow.md`
10. `continuity/design_thread_stream/design_thread_stream.md`
11. live Git/recovery/environment readback before mutation

Cold-start grammar:

`CURRENT STATE -> ICF-CS -> CURRENT CANONICAL SOP + NEXT/DOCTRINE/REVISIT/TRACE -> LIVE SHADOW -> DTS -> LIVE READBACK BEFORE MUTATION`

Conflict grammar:

`CONFLICT -> RECOVERY/AUDIT -> LOCALIZE -> REPAIR/SUPERSEDE -> READBACK -> RESUME`

## Current pointer identities
- ICF-CS v1.1 standard SHA: `62be845da364ae81f59b6320c9b34b136236bf5be8aa8036018da48efcb754f4`.
- ICF-CS v1.1 machine contract SHA: `d67726aeb402c280770eeaf314068ed7a1330beb21167d9d6d9b7c4674425bb0`.
- ICF-CS v1.1 qualification contract SHA: `7d20ed708adb4f7ee147b56da41deac77146b56fc85bd769be3a6d240b3e2029`.
- ICF-CS v1.1 mechanized epoch profile SHA: `733b799815abdb4b1ff735635f7928953c12944ece579365b5aae138d90f90f8`.
- ICF-CS v1.1 payload SHA: `f6f4ab2bafdb0ef2a7db1622a00462990baf980284d5b33827807caea1d41f63`.
- Detached release receipt SHA: `418346ed6373887b5b924e71ca2bf4b83effad20b7269ab40607f5d2750b970c`.
- Current project ICF instance SHA: `49972aad08226859105d57a2cc15e1f09d06926263ef8b07beb7ca1526507cf9`.
- R4.4 carrier SHA: `04f3e94efe8c901cc83a12a9c8531be8a9bb350728b8f9eba53db0fd082b3bbc`.
- Current public Main branch head: `6ea95275cdc409ed222e4720b6b04aadaa17e6bf`; authority-publication predecessor `287c0bad0e9b3fef3002b91702e86b410cada4ce`; Core qualification anchor: `a7b4511734b1a1e507230308e75b31175aef4c4a`.
- Governance Contact v1.0 carrier at Main `6ea95275cdc409ed222e4720b6b04aadaa17e6bf` is detached/published but NOT ACTIVE: ZIP `c4ab4a516e088b6c28b5240d6b3877d2e3fb889a8bbbfd406e8e0c73bebdd1ae`, detached receipt `cf2e7bd8e5ed613d3c3a99b7f8645833ddb742ac4939bd1719092b277ef286e6`; `authority/rahl-sop/CURRENT.md` unchanged; authority effect NONE pending target lifecycle.
- Current App source: `43aa7feac7e8a15828116bd700b644560714496d`, local/remote exact, clean, independently fresh-clone verified; bounded protected-process primitive v0.1.2 is qualified under receipt `3d27639447f1d47ac71e892a766444a3e7c8627ff3120b791ecf4470ebeedda6`.
- Current recovery ingress: generation 14 `checkpoint-app-live-0014-43aa7feac7e8`, source MATCH/NORMAL/LKG; Gen13 is historical/source-stale.
- Durable control branch current verified baseline: `pcmmad/project-control@f120ff577cd3a3df438d354ae9cd0662d037663f`, CHECKPOINT SHA `263d3d9aec93c3f3cc037cf34de3d311bd64e0c91d6e36df5b5a68372c675dc4`, verifier PASS 115, fresh-clone exact/clean; it predates App `43aa7fe...` + Gen14 + bounded qualification, which must enter the next normal control checkpoint before materially wider security mutation.

These are remembered/current-ingress pointers, not permission to skip live currentness readback.

`CURRENT_POINTER != CURRENT_FACT_UNTIL_READBACK`
`HISTORICAL_HANDOFF != CURRENT_INGRESS`
`DONOR != AUTHORITY`
