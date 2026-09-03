# Git Cross-Thread Project Control Checkpoint — 2026-09-03

Mode: BUILD-COMMIT -> CHECKPOINT
Role: R4 Convergence Refiner / R5 Reality Pressure Engine

## Operator requirement
The same Forge project must survive repeated chat-thread switches caused by conversation limits. Git therefore becomes a required durable cross-thread control/checkpoint plane in addition to the live PCMMAD server state.

`CHAT_CONTEXT != DURABLE_PROJECT_STATE`
`LIVE_SERVER_STATE != CROSS_THREAD_CHECKPOINT`
`GIT_PUSH_SUCCESS != CONTROL_STATE_COHERENCE`
`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

## Continuity-first ordering executed
Before any Git mutation, Main directly updated and read back:
- Live Shadow;
- Design Thread Stream;
- Research Epistemic Shadow;
- Current State;
- Doctrine Snapshot;
- Next Steps;
- Trace Matrix;
- Revisit Ledger.

The pre-Git continuity/state readback was coherent across all eight required surfaces.

## Git control branch
Repository: `https://github.com/SEng-Kitathas/Singularity-works-`
Branch: `pcmmad/project-control`
Branch base: exact qualified public Main `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`.

The branch is intentionally separate from public `main` and from the unpromoted semantic-field candidate.

### Initial control checkpoint
Commit: `8226f2ffb1e9e96bfca7f1ba91b32d47a904388e`
Message: `control: establish R4.1 cross-thread project checkpoint`
- 52 files created;
- 4,947 inserted lines;
- local checkpoint verifier PASS;
- staged Git blob hashes matched the checkpoint manifest;
- `git diff --cached --check` PASS after Git-safe normalization;
- working tree clean.

Initial remote readback:
- GitHub `pcmmad/project-control` = `8226f2ffb1e9e96bfca7f1ba91b32d47a904388e`;
- GitHub `main` = `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`;
- GitHub `forge/app-shell-rd` = `328249429cc6e86e15db9797bd58eff5fabc5a2d`.

Fresh single-branch clone from GitHub at that commit ran `python project_control/VERIFY_CHECKPOINT.py` and returned PASS with 51 manifested files.

### Establishment receipt commit
Commit: `174ba730f691a50f332b77bb8803370ed642cae4`
Message: `control: record remote checkpoint establishment`

This commit adds `project_control/PUSH_RECEIPT_20260903.md` and updates README/CHECKPOINT metadata to record the independently verified first establishment.

Final remote readback:
- GitHub `pcmmad/project-control` = **`174ba730f691a50f332b77bb8803370ed642cae4`**;
- GitHub `main` remains **`1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`**;
- GitHub `forge/app-shell-rd` = **`328249429cc6e86e15db9797bd58eff5fabc5a2d`**.

Fresh remote clone fast-forwarded to `174ba730...` and `python project_control/VERIFY_CHECKPOINT.py` returned **PASS with 52 manifested files**.

## Control-tree contents
`project_control/` contains:
- `README.md` with cross-thread re-entry read order;
- `CHECKPOINT.json` machine-readable checkpoint manifest;
- `VERIFY_CHECKPOINT.py` self-verifier;
- `PUSH_RECEIPT_20260903.md`;
- Main Live Shadow, DTS, RES;
- Current, Doctrine, Next, Trace, Revisit;
- R4.1 adoption/deep-read proof and double-helix maintenance notes;
- a Git-safe derivative of all 34 active R4.1 non-ancestry files;
- exact source member hashes and Git-safe transformation manifest.

## Git-safe transformation boundary
The live server continuity remains the full-fidelity working copy.
The Git checkpoint is intentionally safe/portable:
- DTS machine-local drive roots are redacted in the Git copy only;
- exact server-source hashes are preserved in `CHECKPOINT.json`;
- R4.1 evidence-only machine paths and a test-fixture key literal are redacted in the Git-safe SOP derivative;
- canonical R4.1 source member hashes remain in `SOURCE_ACTIVE_FILE_HASHES.json`;
- Git-safe transforms are explicit in `GIT_SAFE_TRANSFORMS.json`;
- Git checkpoint text is normalized to LF for cross-platform deterministic blobs.

Therefore the Git-safe SOP directory must not be falsely described as byte-identical canonical R4.1. Canonical carrier identity remains:
`af4364fbcf8e5d33aa2ad06e4da9c4669d4be2ffcbc332e416742bec1543f4d2`.

## Current live cross-arm observation
App branch `forge/app-shell-rd` advanced beyond the prior double-helix checkpoint and is now independently observed local/remote exact and clean at:
`328249429cc6e86e15db9797bd58eff5fabc5a2d`
subject: `singularity-works: qualify operation lifecycle reconciliation v0.1`.

No Core semantic-interface implication is inferred from the commit subject alone. The earlier double-helix note remains historically correct for its own checkpoint.

## Re-entry contract
A fresh thread should resolve the current remote `pcmmad/project-control` HEAD live, then read:
1. `project_control/README.md`;
2. `project_control/CHECKPOINT.json`;
3. Live Shadow;
4. Current State;
5. Doctrine / Next / Trace / Revisit;
6. RES when research frontier matters;
7. DTS only as needed for recovery;
8. R4.1 Git-safe process surface when process re-entry is required.

Then reconcile against current server state and remotes before mutation.

## Ongoing checkpoint rule
After a load-bearing state change or before a forced thread switch:
1. update live continuity/state first;
2. update bounded Git control snapshot;
3. run checkpoint verifier + Git safety scan + diff check;
4. commit/push `pcmmad/project-control`;
5. read back remote branch SHA;
6. record the new durable anchor server-side.

Public Main promotion remains a separate gate.
