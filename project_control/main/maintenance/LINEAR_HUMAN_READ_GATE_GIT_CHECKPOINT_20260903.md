# Linear Human Read Gate — Git Control Checkpoint Receipt

Date: 2026-09-03
Mode: BUILD-COMMIT -> CHECKPOINT
Role: R4 Convergence Refiner / R5 Reality Pressure Engine

## Doctrine bound
**LINEAR HUMAN READ / SEMANTIC GATE**

If an artifact can be meaningfully read, it SHALL receive a complete linear semantic read before it is promoted, sealed, published, admitted, or treated as load-bearing. Automated checks may precede and support the gate; they SHALL NOT substitute for it.

## Git checkpoint generation
Previous verified control tip: `174ba730f691a50f332b77bb8803370ed642cae4`
Published control commit: `061cb8dac4eaf608fb1c07a77cba626712e52ce0`
Commit message: `control: bind linear human semantic-read gate`
Branch: `pcmmad/project-control`

## Human semantic-read gate applied before publication
A deterministic linear stream was constructed over every readable file in the Git control tree before publication.

Full-tree read phase:
- readable files: 55
- lines: 5,481
- bytes: 349,333
- stream SHA-256: `8661b5fb6b3e6a9dd6814f625eea456ffe25b28f980db0033c8f0d69a228260f`

Semantic findings during the read:
1. the Git-safe derivative evidence README still implied historical machine paths were preserved although the public derivative intentionally redacts them;
2. the canonical R4.1 manifest/verifier retained inside `git_safe_active` describe original carrier bytes, not the transformed Git-safe derivative.

Both findings were corrected before publication. The affected derivative artifacts plus `GIT_SAFE_TRANSFORMS.json` were then reread completely. The updated `CHECKPOINT.json` was reread completely after it recorded the two-stage semantic gate.

Blocking semantic findings at publication: **0**.

## Supporting automated gates
After the human semantic gate:
- `project_control/VERIFY_CHECKPOINT.py`: PASS, 54 manifested files;
- privacy/credential scan: PASS, 55 files, 0 hits;
- `git diff --cached --check`: PASS;
- every staged Git blob matched the CHECKPOINT manifest hash/byte count;
- staged CHECKPOINT bytes matched the reread working copy.

## Commit-level semantic gate
The resulting Git commit object was also read before publication:
- commit `061cb8dac4eaf608fb1c07a77cba626712e52ce0`;
- expected message and author identity;
- 15 expected project-control files changed;
- no `project_control/` working-tree delta from committed bytes.

## Remote verification
Pre-push remote control tip was independently read as `174ba730f691a50f332b77bb8803370ed642cae4`, so the push was a non-force fast-forward.

Post-push independent GitHub readback:
- `pcmmad/project-control` = `061cb8dac4eaf608fb1c07a77cba626712e52ce0`;
- public `main` = `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9` unchanged;
- `forge/app-shell-rd` = `328249429cc6e86e15db9797bd58eff5fabc5a2d`.

Fresh remote readback clone:
- HEAD = `061cb8dac4eaf608fb1c07a77cba626712e52ce0`;
- working tree clean;
- `project_control/VERIFY_CHECKPOINT.py` PASS with 54 manifested files.

## Authority boundary
This checkpoint makes the human semantic-read gate durable across thread switches. It does not promote product code or move public `main`.

`AUTOMATED_CHECKS != LINEAR_HUMAN_SEMANTIC_READ`
`MACHINE_PASS != HUMAN_SEMANTIC_GATE_PASS`
`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

## Fixed-point rule for checkpoint receipts
This post-push server receipt is intentionally not followed by an immediate recursive Git checkpoint solely to checkpoint the receipt of the checkpoint. It will enter the next bounded Git control generation alongside the next load-bearing project change or forced-thread handoff. The live server state records the current remote anchor now; the Git branch itself is already durably current at `061cb8d...`.
