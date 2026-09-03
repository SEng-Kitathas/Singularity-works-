# Singularity Works / Forge — Cross-Thread Project Control

This directory is the durable Git checkpoint surface for **Singularity Works / Forge across the Main/Core + App double helix**.
It exists because a single project spans multiple chat threads. Chat context is not durable project state.

## Authority boundary
- This branch is a **control/checkpoint branch**, not a public release/promotion branch.
- Qualified public `main` remains separately governed.
- The live PCMMAD server state is the high-fidelity mutable working plane.
- `project_control/.gitattributes` normalizes checkpoint text to LF so Git copies and committed blobs are portable/deterministic across platforms; server-source hashes remain recorded separately.
- This Git tree is a bounded, Git-safe checkpoint of the control state plus a Git-safe derivative of the active RAHL process SOP; canonical source hashes are preserved beside it.
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
15. `project_control/sop/RAHL_ENGINEERING_CANONICAL_SOP_R4_1_2026-09-03/git_safe_active/00_READ_ME_FIRST.md` and `12_COLD_START_PROTOCOL.md` when process re-entry is required.

Then reconcile against live server state and current Git remotes before mutation.

## Current checkpoint facts
- Canonical process SOP: **RAHL Engineering Canonical SOP R4.1**.
- R4.1 carrier SHA-256: `af4364fbcf8e5d33aa2ad06e4da9c4669d4be2ffcbc332e416742bec1543f4d2`.
- Qualified public Main at checkpoint: `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`.
- Main semantic-field candidate: `a7b4511734b1a1e507230308e75b31175aef4c4a`, **LOCAL / UNPROMOTED / pending exact committed-artifact replay**.
- Forge App branch: `forge/app-shell-rd`; live local/remote observation at checkpoint: `328249429cc6e86e15db9797bd58eff5fabc5a2d`, clean. Commit subject: `singularity-works: qualify operation lifecycle reconciliation v0.1`.
- Double-helix model remains: separate pressure, shared identity; independent embodiment, shared canonical truth.
- Main RES SHA-256: `65fad5bae02cb3345b0b22bc9cf0ce2999140a13bd00d7abe0f7091e9cf89120`; authority NONE.
- App RES SHA-256: `1af0ba6e371514645b7bde90425aac5fbbe95eed0c8d0e66d879052fab0bdf45`; authority NONE.

## Git-safe continuity note
The server DTS is the full-fidelity chronological record. The Git derivative redacts machine-local path roots and one email-shaped non-secret identifier found in the App DTS; its manifest records exact server-source hashes, Git-copy hashes, and declared transforms. No credential/token/private-key material is admitted by the checkpoint scan.

## Core continuity laws
`CHAT_CONTEXT != DURABLE_PROJECT_STATE`

`LIVE_SERVER_STATE != CROSS_THREAD_CHECKPOINT`

`GIT_PUSH_SUCCESS != CONTROL_STATE_COHERENCE`

`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

## Remote establishment
Initial remote establishment was independently verified at commit `8226f2ffb1e9e96bfca7f1ba91b32d47a904388e`; see `PUSH_RECEIPT_20260903.md`. Always resolve current branch HEAD live.

## Additive project-local promotion gate
**LINEAR HUMAN READ / SEMANTIC GATE**

If an artifact can be meaningfully read, it SHALL receive a complete linear semantic read before it is promoted, sealed, published, admitted, or treated as load-bearing. Automated checks may precede and support the gate; they SHALL NOT substitute for it.

The exact operator addendum is checkpointed at `project_control/main/maintenance/LINEAR_HUMAN_READ_SEMANTIC_GATE_ADDENDUM_20260903.md`.

## RES ownership
- Main/Core RES owns semantic/Core research continuity.
- App RES owns product/runtime/security research continuity.
- Both are authority NONE. Cross-reference does not transfer authority.
- `RES_CONTENT != GOVERNING_DOCTRINE`.
- `RES_SYNTHESIS != LINEAR_HUMAN_SEMANTIC_READ`.
