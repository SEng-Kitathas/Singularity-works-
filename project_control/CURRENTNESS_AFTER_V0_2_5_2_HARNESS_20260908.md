# Control Currentness — v0.2.5.2 HARNESS_INVALID Child-Membership Seam — 2026-09-08

Status: **CHECKPOINT CANDIDATE / NO BREAKAWAY ADMISSION / ZERO PRODUCT OR CORE PROMOTION**

Predecessor control `56fb5b70ffee7c58d60c34118338d12c30313e46` / CHECKPOINT `2a4ce4baf905bd3698d228cbb9a0575dcc78efa577593a69de6118b9fa49cec6`. Main `e66c071...`, Core `a7b45117...`, App `43aa7fea...`; Gen14 current; Governance Contact exact local locator+token on both targets, ACTIVE receipt absent, global ACTIVE unearned.

## v0.2.5.2 first result
- post-checkpoint synchronous-plane currentness `f32909d4c430a33e2eb3c80a4ea8aec0c6d6b0a6c1f73b3be3f34b2f70399f88`: outer Job `0x1800`, BREAKAWAY_OK and SILENT_BREAKAWAY_OK true, kill-on-close false; execution-plane currentness only.
- artifact `d7f444287c6903fab28b58e9423cfc99ec53dced03457e964348eb587c1f2602`, executed once synchronously; first result `af0ce57433f71ad41dd74f06d922b88bad8fc8f69d0f8ca13496eafb47ab4601` = `HARNESS_INVALID_POSITIVE_ROOT_STILL_IN_OUTER_JOB`, NOT_ADMITTED, non-replayable.
- positive helper normal-child baseline/cleanup succeeded; explicit `CREATE_BREAKAWAY_FROM_JOB` child creation succeeded and returned PID; root itself remained in a Job. Harness stopped before measuring returned child's Job membership/liveness and before protected execution.
- Attempt Store current: **172 blobs / 179 attempts / 258 events**, integrity `ok`.

## Next gate
After this successor is directly committed/pushed/fresh-clone verified, NEW v0.2.5.3 may repair observation logic only: query returned explicit child's actual Job membership and liveness in positive and protected phases. Helper source/DLL, exact breakaway call, normal-child baseline, outer-Job gate, protected AppContainer+immediate-Job primitive, non-network scope and claim ceiling stay unchanged.

`POSITIVE_ROOT_IN_JOB != BREAKAWAY_CHILD_IN_JOB`
`EXPLICIT_CHILD_CREATION_SUCCESS != CHILD_JOB_MEMBERSHIP_PROOF`
`PROTECTED_PHASE_NOT_REACHED != BREAKAWAY_DENIAL`
`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

Privacy projection: live DTS untouched. Main source DTS `8ac61902bbc3a4621f9baa9be232d30d0d8300b6868503696c100bd6bdfedecd`; App source DTS `beb465690e3c8a488480ad6445545a39602c536992c4544f718d7a18b9131cb8`. Control copies LF-normalized and local project roots placeholdered only.
