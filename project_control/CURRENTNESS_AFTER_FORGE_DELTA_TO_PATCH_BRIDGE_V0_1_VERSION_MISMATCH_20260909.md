# Control Currentness — Forge Delta->Patch Bridge v0.1 Interface Version Mismatch — 2026-09-09

Status: **FORGE CORE INTERFACE MISMATCH / 27 OF 28 CHECKS PASS / NOT ADMITTED AS BRIDGE QUALIFICATION**
Predecessor control `4783bf040546d0ba331879a104006540030d51fc` / CHECKPOINT `a537abe0c6b98ef5393b5fd0a8ea14cd5c7e270da1f3d8f46155419f189b0a26`, fresh-clone verifier PASS 253.

Bridge module `fd478615088a3dde2b052aea41e747a00b8647700c650f8c4a1e477cdaf008c2` + harness `7b2c2adb8e92049645248cd8f253b89b7e697bfdffadaf02cbf1d1d261ed2858` executed once. Exact summary/stdout `dd93df1d6ec662763ac5d20a9ed25ace4f514a43d706e1294683d0a73d6efce5` reports 27/28 pass.

End-to-end effect was exact: materialized source equals replay target, re-lowered materialized bundle equals replay target, reverse rollback exact, real PyGoat clean/unchanged. Sole failed check: semantic key identity. Replay/bridge current snapshot-delta v0.4 key `sem:cbcebb9cb857a8d6962fe58f`; incumbent materializer v0.1 snapshot-delta v0.3 key `sem:eead6942606ea7baa9605bd2`.

Verified root cause: v0.3 includes evidence snippet fingerprints in semantic continuity key; v0.4 deliberately excludes generic evidence text from semantic meaning and handles occurrence identity separately.

No bridge qualification is admitted while semantic identity versions disagree. Same v0.1 bridge attempt is non-replayable. Next allowed repair: materializer v0.1.1 key-version-only dependency v0.3 -> v0.4, then re-run the incumbent PyGoat 26/26 materialization contract as a NEW regression attempt before NEW bridge v0.1.1.

`SEMANTIC_KEY_VERSION_MISMATCH != MATERIALIZATION_FAILURE`
`EXACT_EFFECT != CONTRACT_COHERENCE`
`V0_3_CONTINUITY_KEY != V0_4_CONTINUITY_KEY`
