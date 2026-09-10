# Forge Delta -> Patch Bridge v0.1 — Interface Version Mismatch

Date: 2026-09-09 UTC
Status: **FIRST ATTEMPT IMMUTABLE / 27 OF 28 CHECKS PASS / NOT ADMITTED AS BRIDGE QUALIFICATION**
Control: `4783bf040546d0ba331879a104006540030d51fc` / CHECKPOINT `a537abe0c6b98ef5393b5fd0a8ea14cd5c7e270da1f3d8f46155419f189b0a26`, fresh-clone verifier PASS 253.
Bridge module `fd478615088a3dde2b052aea41e747a00b8647700c650f8c4a1e477cdaf008c2`; harness `7b2c2adb8e92049645248cd8f253b89b7e697bfdffadaf02cbf1d1d261ed2858`; exact first summary/stdout `dd93df1d6ec662763ac5d20a9ed25ace4f514a43d706e1294683d0a73d6efce5`; stderr empty.

## Verified result
The run materially succeeded end-to-end except for one interface identity assertion:
- semantic replay target exact: PASS;
- isolated source materialization exact target bytes: PASS;
- re-lowered materialized bundle exactly equals replay target: PASS;
- observed removed/added semantic-key sets exactly equal bridge sets: PASS;
- rollback source and bundle exact: PASS;
- stale patch rejected; target Git clean/unchanged; all authorities NONE: PASS;
- sole failure: `anchor_semantic_key_matches_patch`.

Bridge/replay semantic key under snapshot-delta v0.4: `sem:cbcebb9cb857a8d6962fe58f`.
Incumbent materializer v0.1 intended semantic key under snapshot-delta v0.3: `sem:eead6942606ea7baa9605bd2`.

## Root cause
`forge_semantic_materializer_v0_1.py` imports `fact_semantic_key` from snapshot-delta v0.3. v0.3 includes evidence snippet fingerprints in semantic continuity identity. The current qualified snapshot-delta v0.4 intentionally excludes generic evidence text from semantic meaning and uses occurrence matching separately. The bridge correctly uses v0.4, producing a different semantic key for the same fact.

Classification: **INTERFACE_VERSION_MISMATCH_SEMANTIC_KEY_V0_3_VS_V0_4**. This is not a source materialization failure and not a replay failure. No v0.1 bridge admission is granted because its semantic identity contract is internally inconsistent. Same bridge Attempt SHALL NOT be rerun.

## Repair boundary
After checkpoint, NEW materializer v0.1.1 may change only its semantic-key dependency from snapshot-delta v0.3 to v0.4 plus version label. It must first regress the incumbent PyGoat materialization contract (26/26) before a NEW bridge v0.1.1 attempt may run. No automatic lowering/generalization is added.

`SEMANTIC_KEY_VERSION_MISMATCH != MATERIALIZATION_FAILURE`
`MATERIALIZED_TARGET_EXACT != BRIDGE_CONTRACT_QUALIFIED_WHILE_IDS_DISAGREE`
`V0_3_CONTINUITY_KEY != V0_4_CONTINUITY_KEY`
