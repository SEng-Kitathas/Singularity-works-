# Control Currentness — v0.2.5.3 Positive-Criterion Harness Seam — 2026-09-08

Status: **CHECKPOINT CANDIDATE / NO BREAKAWAY ADMISSION / ZERO PRODUCT OR CORE PROMOTION**

Predecessor control `8071b0945ee7f9a7709eef0ef62c42141a2ebc39` / CHECKPOINT `1002110708b3bd53db376249dd384cfe26dcfb2d6aa6340880124f8cea6cb021`. Main `e66c071...`; Core `a7b45117...`; App `43aa7fea...`; Gen14 current. Governance Contact remains locally binding on both targets with ACTIVE receipt absent; global ACTIVE unearned.

## v0.2.5.3 first result
- post-control synchronous plane record `df57157d14dff5648027a7fd7d3ab1354f9c4b298f276b44098768ae705cf003`: `0x1800`, explicit+silent breakaway true, kill-on-close false; currentness only.
- artifact `e6913d1b923153a6943b3f3fb34e50c7054f9123a3d940e33d8719d89cf2031d`, executed exactly once synchronously; first result `27af68192010146a421ea95900407bdc58c47984496fba98a163bbfc069854bf` = `HARNESS_INVALID_POSITIVE_CHILD_IN_SOME_JOB`, NOT_ADMITTED, non-replayable.
- positive explicit child creation succeeded; child PID 9320 was alive after root exit and `IsProcessInJob(child,NULL)=true`; protected phase not reached. Independent post-run probe confirmed PID 9320 absent after artifact finally-cleanup.
- Attempt Store current: **177 blobs / 185 attempts / 264 events**, integrity `ok`.

## Refined next seam
Any-Job membership is not equivalent to Forge immediate-Job membership on this Job-governed server plane. Positive control is already valid at the lifecycle level when exact explicit child creation succeeds and the sleeping child survives root exit without the Forge immediate Job primitive. A NEW v0.2.5.4 may therefore remove only the positive rejection `child.in_any_job == true`; it must retain membership telemetry and cleanup. Protected logic remains decisive: surviving child after `run_zero_network_process` closes the immediate Forge Job => bypass; verified in-Job `ERROR_ACCESS_DENIED` on explicit creation => bounded denial.

`ANY_JOB_MEMBERSHIP != FORGE_IMMEDIATE_JOB_MEMBERSHIP`
`POSITIVE_CREATE_SUCCESS_AND_SURVIVAL != PROTECTED_BYPASS`
`PROTECTED_CHILD_SURVIVAL_AFTER_FORGE_JOB_CLOSE == BREAKAWAY_BYPASS_EVIDENCE`
`PROTECTED_CREATE_FAILURE_ERROR_ACCESS_DENIED_IN_VERIFIED_JOB == BOUNDED_DENIAL_EVIDENCE`
`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

Privacy projection: live DTS unchanged. Main source DTS `721da58d9c2cdc25ebbf1a8e45ee31a567637e62cf5af970a4dddfff053a9b70`; App source DTS `17c8e77fab407dbad18241985f088fc4b4dc1297484cbd04e14252b58eddbf13`. Control DTS copies LF-normalized and local project roots placeholdered only.
