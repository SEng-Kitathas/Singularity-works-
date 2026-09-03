# Singularity Works / Forge — Cross-Thread Project Control

This directory is the durable Git checkpoint surface for **Main-Dev / Main**.
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
9. `project_control/main/continuity/research_epistemic_shadow.md` when research/frontier meaning matters
10. `project_control/main/continuity/design_thread_stream.md` only as needed for chronology/recovery
11. `project_control/sop/RAHL_ENGINEERING_CANONICAL_SOP_R4_1_2026-09-03/git_safe_active/00_READ_ME_FIRST.md` and `12_COLD_START_PROTOCOL.md` when process re-entry is required.

Then reconcile against live server state and current Git remotes before mutation.

## Current checkpoint facts
- Canonical process SOP: **RAHL Engineering Canonical SOP R4.1**.
- R4.1 carrier SHA-256: `af4364fbcf8e5d33aa2ad06e4da9c4669d4be2ffcbc332e416742bec1543f4d2`.
- Qualified public Main at checkpoint: `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`.
- Main semantic-field candidate: `a7b4511734b1a1e507230308e75b31175aef4c4a`, **LOCAL / UNPROMOTED / pending exact committed-artifact replay**.
- Forge App branch: `forge/app-shell-rd`; live local/remote observation at checkpoint: `328249429cc6e86e15db9797bd58eff5fabc5a2d`, clean. Commit subject: `singularity-works: qualify operation lifecycle reconciliation v0.1`.
- Double-helix model remains: separate pressure, shared identity; independent embodiment, shared canonical truth.

## Git-safe continuity note
The server DTS is the full-fidelity chronological record. The Git copy redacts machine-local drive roots only; its manifest records both source and Git-copy hashes. No credential/token/email findings were present in the control surfaces during the checkpoint scan.

## Core continuity laws
`CHAT_CONTEXT != DURABLE_PROJECT_STATE`

`LIVE_SERVER_STATE != CROSS_THREAD_CHECKPOINT`

`GIT_PUSH_SUCCESS != CONTROL_STATE_COHERENCE`

`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

## Remote establishment
Initial remote establishment was independently verified at commit `8226f2ffb1e9e96bfca7f1ba91b32d47a904388e`; see `PUSH_RECEIPT_20260903.md`. Always resolve current branch HEAD live.
