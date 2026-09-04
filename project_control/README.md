# Singularity Works / Forge — Cross-Thread Project Control

This directory is the durable Git checkpoint surface for **Singularity Works / Forge across the Main/Core + App double helix**.
It exists because a single project spans multiple chat threads. Chat context is not durable project state.

## Authority boundary
- This branch is a **control/checkpoint branch**, not a public release/promotion branch.
- Qualified public `main` remains separately governed.
- The live PCMMAD server state is the high-fidelity mutable working plane.
- `project_control/.gitattributes` normalizes checkpoint text to LF so Git copies and committed blobs are portable/deterministic across platforms; server-source hashes remain recorded separately.
- This Git tree is a bounded, Git-safe checkpoint of control state. The current RAHL R4.2 SOP is carried as exact binary copies under the Main/App control slices; the retained R4.1 Git-safe derivative is ancestry/history only. Canonical server-source hashes remain recorded separately.
- `GIT_PUSH_SUCCESS != CONTROL_STATE_COHERENCE`: always read the branch HEAD and checkpoint manifest before trusting it.

## Re-entry read order
For a fresh thread/session:
1. `project_control/README.md`
2. `project_control/CHECKPOINT.json`
3. `project_control/main/continuity/live_shadow.md`
4. `project_control/main/state/current.md`
5. `project_control/main/state/doctrine_snapshot.md`
6. `project_control/main/state/next_steps.md`
7. `project_control/main/state/trace_matrix.md`
8. `project_control/main/state/revisit_ledger.md`
9. `project_control/main/continuity/research_epistemic_shadow.md` when Core research/frontier meaning matters
10. `project_control/app/continuity/live_shadow.md`
11. `project_control/app/state/current.md`
12. `project_control/app/state/doctrine_snapshot.md`
13. `project_control/app/continuity/research_epistemic_shadow.md` when product/security research/frontier meaning matters
14. Main/App Design Thread Streams only as needed for chronology/recovery
15. `project_control/main/sop/RAHL_ENGINEERING_CANONICAL_SOP_R4_2_2026-09-03.zip` or the byte-identical App copy when process re-entry is required; extract/read the active R4.2 package under its own cold-start protocol. The retained R4.1 Git-safe derivative is ancestry/history, not the current SOP.

Then reconcile against live server state and current Git remotes before mutation.

## Current checkpoint facts
- Canonical process SOP: **RAHL Engineering Canonical SOP R4.2**.
- R4.2 carrier SHA-256: `eb167543e9ceb2ae01449f421d2916e61b7dd924270ea2e83e3364c9d808ce9a`.
- Exact carrier copies: `project_control/main/sop/RAHL_ENGINEERING_CANONICAL_SOP_R4_2_2026-09-03.zip` and `project_control/app/sop/RAHL_ENGINEERING_CANONICAL_SOP_R4_2_2026-09-03.zip`.
- R4.2 admission: 35/35 current readable members; deterministic semantic-read stream 3,175/3,175 lines, SHA `f6997264acb625d54d3924d2c25dc0689dfe1bbf65eb64eaa52c2afd61e68c3a`; primary verifier PASS; hostile suite 26/26 rejected; exact R4.1/R4.0/R3.1 ancestry reuse verified.
- Qualified public Main at checkpoint: `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`.
- Main semantic-field candidate: `a7b4511734b1a1e507230308e75b31175aef4c4a`, **LOCAL / UNPROMOTED / pending exact committed-artifact replay**.
- Forge App branch: `forge/app-shell-rd`; live local/remote observation at checkpoint: `328249429cc6e86e15db9797bd58eff5fabc5a2d`, clean. Commit subject: `singularity-works: qualify operation lifecycle reconciliation v0.1`.
- Double-helix model remains: separate pressure, shared identity; independent embodiment, shared canonical truth.
- Main RES SHA-256: `a232664ad90dada57ccbc2ca085f11a6e0ee159a5c434f528943ad729033979f`; authority NONE.
- App RES SHA-256: `519722deee61e3fa436418fb71848609c6d670876de6618e1755a1702d8536e5`; authority NONE.

## Git-safe continuity note
The server DTS is the full-fidelity chronological record. The Git derivative redacts machine-local path roots and one email-shaped non-secret identifier found in the App DTS; its manifest records exact server-source hashes, Git-copy hashes, and declared transforms. No credential/token/private-key material is admitted by the checkpoint scan.

## Core continuity laws
`CHAT_CONTEXT != DURABLE_PROJECT_STATE`

`LIVE_SERVER_STATE != CROSS_THREAD_CHECKPOINT`

`GIT_PUSH_SUCCESS != CONTROL_STATE_COHERENCE`

`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

## Remote establishment
Initial remote establishment was independently verified at commit `8226f2ffb1e9e96bfca7f1ba91b32d47a904388e`; see `PUSH_RECEIPT_20260903.md`. Always resolve current branch HEAD live.

## Canonical R4.2 semantic-admission gate
**LINEAR HUMAN READ / SEMANTIC GATE**

If an artifact can be meaningfully read, it SHALL receive a complete linear semantic read before it is promoted, sealed, published, admitted, or treated as load-bearing. Automated checks may precede and support the gate; they SHALL NOT substitute for it.

The exact operator addendum remains checkpointed at `project_control/main/maintenance/LINEAR_HUMAN_READ_SEMANTIC_GATE_ADDENDUM_20260903.md` as provenance/history; R4.2 now carries the active rule canonically.

## RES ownership
- Main/Core RES owns semantic/Core research continuity.
- App RES owns product/runtime/security research continuity.
- Both are authority NONE. Cross-reference does not transfer authority.
- `RES_CONTENT != GOVERNING_DOCTRINE`.
- `RES_SYNTHESIS != LINEAR_HUMAN_SEMANTIC_READ`.

## Current SOP carrier copies
- Main control copy: `project_control/main/sop/RAHL_ENGINEERING_CANONICAL_SOP_R4_2_2026-09-03.zip`.
- App control copy: `project_control/app/sop/RAHL_ENGINEERING_CANONICAL_SOP_R4_2_2026-09-03.zip`.
- Both are 625,556 bytes and exact SHA-256 `eb167543e9ceb2ae01449f421d2916e61b7dd924270ea2e83e3364c9d808ce9a`.
- The two control copies are exact binaries, not rewritten Git-safe derivatives.
## R4.2 full-adherence revalidation — 2026-09-04
- Server carrier re-read: 35/35 active/current readable members, 3,070 source lines, 0 unread.
- Fresh exact-carrier verifier PASS; hostile suite 26/26 rejected.
- Bilateral Main/App continuity audit found and repaired R4.2 currentness drift before this control refresh.
- Pre-publication audit: `project_control/main/maintenance/RAHL_R4_2_FULL_ADHERENCE_AUDIT_20260904.md`, source SHA `f63c31e79674837ee823037edbf344e333b0e6861aa479da3c108f786dacc76c`.
- Pre-refresh control tip observed live: `efd86410359946de1c514cc098ef0df8583a9bb9`.
- Current Git snapshot must pass its own semantic/readback gates before this audit can close.
