# Project Control Git Establishment Receipt — 2026-09-03

This receipt records the first successful establishment of the durable cross-thread control branch.

## Initial control checkpoint
- Branch: `pcmmad/project-control`
- Commit: `8226f2ffb1e9e96bfca7f1ba91b32d47a904388e`
- Base qualified Main: `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`
- Commit message: `control: establish R4.1 cross-thread project checkpoint`

## Remote verification
Independent GitHub `ls-remote` readback after push returned:
- `pcmmad/project-control` = `8226f2ffb1e9e96bfca7f1ba91b32d47a904388e`
- `main` = `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`
- `forge/app-shell-rd` = `328249429cc6e86e15db9797bd58eff5fabc5a2d`

A fresh single-branch clone was then made from GitHub. Its HEAD was exactly `8226f2ffb1e9e96bfca7f1ba91b32d47a904388e`, and `python project_control/VERIFY_CHECKPOINT.py` returned PASS with 51 manifested files, qualified Main `1b8f6bd...`, and canonical process `RAHL Engineering Canonical SOP R4.1`.

## Authority boundary
This proves durable establishment/readback of the control checkpoint. It does **not** promote the semantic-field candidate, advance public `main`, or make the control branch a release branch.

`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

`GIT_PUSH_SUCCESS != CONTROL_STATE_COHERENCE`

The latter was satisfied for the initial checkpoint only after the fresh-clone verifier passed.

## Currentness rule
This receipt identifies the initial establishment commit. Future readers must still resolve the current remote `pcmmad/project-control` HEAD rather than assuming this commit remains branch tip.
