# Semantic Field Core v0.1 — Remote Candidate Publication Receipt

Date: 2026-09-04 UTC
Mode: BUILD-COMMIT -> CHECKPOINT
Role: R5 Reality Pressure Engine
Canonical process: RAHL Engineering Canonical SOP R4.2
Status: **REMOTE CANDIDATE DURABLE / PUBLIC MAIN UNCHANGED**

## Exact candidate
Candidate commit:
`a7b4511734b1a1e507230308e75b31175aef4c4a`
subject: `forge: add canonical semantic field core`
parent: qualified public Main `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`.

Qualification receipt:
`notes/maintenance/SEMANTIC_FIELD_CORE_EXACT_COMMIT_REPLAY_QUALIFICATION_20260904.md`
SHA `d2f5377027de444b066979beab1ac3a7eeb08591d376215abfc34dde41cc54e3`.

Verdict before publication:
**PROMOTION_READY_WITH_EVIDENCE for bounded semantic-field source integration.**

`PROMOTION_READY_WITH_EVIDENCE != PUBLIC_MAIN_PROMOTED`

## Pre-publication remote readback
Independent GitHub readback immediately before candidate-branch publication:
- `main` = `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`;
- `pcmmad/project-control` = `819cf6fc8d470bb5a8b5bfbf72e1791b7d480c8e`;
- `forge/app-shell-rd` = `328249429cc6e86e15db9797bd58eff5fabc5a2d`;
- `pcmmad/semantic-field-core-v01` = absent.

Dry-run explicit push of the exact object to `refs/heads/pcmmad/semantic-field-core-v01`: PASS, new branch only.

## Publication
Non-force explicit GitHub push:
`a7b4511734b1a1e507230308e75b31175aef4c4a:refs/heads/pcmmad/semantic-field-core-v01`

Push output reported new branch creation.

## Independent remote verification
Independent App-side `git ls-remote` after publication returned:
- `main` = `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`;
- `pcmmad/project-control` = `819cf6fc8d470bb5a8b5bfbf72e1791b7d480c8e`;
- `pcmmad/semantic-field-core-v01` = **`a7b4511734b1a1e507230308e75b31175aef4c4a`**;
- `forge/app-shell-rd` = `328249429cc6e86e15db9797bd58eff5fabc5a2d`.

A fresh single-branch GitHub clone of `pcmmad/semantic-field-core-v01` was created and independently verified:
- HEAD exact `a7b4511734b1a1e507230308e75b31175aef4c4a`;
- parent exact `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`;
- tracked tree clean;
- exact nine-file candidate delta;
- `git diff --check` PASS;
- semantic-field tests 8/8 PASS;
- five semantic-field production-module hashes exactly matched the qualified replay source.

## Authority boundary
This publication makes the **qualified candidate durable and reviewable**. It does not:
- advance public `main`;
- make the candidate the qualified public Main baseline;
- authorize App to consume/copy the semantic-field implementation;
- repair inherited package-description debt;
- promote parser/security/language-specific lowerers.

Public Main promotion remains a distinct PROMOTION gate requiring fresh remote-main currentness, exact lineage, explicit promotion action, post-promotion verification, and immediate Main->App handshake if shared Core advances.

## Inherited packaging-description debt
The exact replay established inherited package metadata/long-description debt on qualified Main. It was not introduced by this candidate and does not invalidate installed semantic-field correctness, but remains visible as a separately scoped packaging/documentation seam.

`INHERITED_METADATA_DEBT != CANDIDATE_SEMANTIC_REGRESSION`

## Next state
Main/Core frontier changes from “candidate replay pending” to:
1. candidate branch durable + promotion-ready;
2. public Main promotion gate pending;
3. inherited package-description debt separately queued;
4. App remains on its current product frontier and MUST NOT consume semantic-field Core until qualified Main actually advances and an early forward-sync handshake completes.
