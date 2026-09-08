# Wider Egress v0.2.5.2 — Explicit Job Breakaway — HARNESS_INVALID

Date: 2026-09-08 UTC
Status: **FIRST ATTEMPT IMMUTABLE / HARNESS_INVALID / NO BREAKAWAY ADMISSION**
Authority: App/process-lifecycle evidence only. No Main/Core, network, provider, Governance Contact global, production, or runtime-law authority.

## Currentness / lineage
- durable control `56fb5b70ffee7c58d60c34118338d12c30313e46` / CHECKPOINT `2a4ce4baf905bd3698d228cbb9a0575dcc78efa577593a69de6118b9fa49cec6`, independently fresh-clone verified PASS 158 before execution;
- post-checkpoint synchronous execution-plane record `f32909d4c430a33e2eb3c80a4ea8aec0c6d6b0a6c1f73b3be3f34b2f70399f88` directly measured outer Job `0x1800`: `BREAKAWAY_OK=true`, `SILENT_BREAKAWAY_OK=true`, `KILL_ON_JOB_CLOSE=false`;
- v0.2.5.2 artifact `d7f444287c6903fab28b58e9423cfc99ec53dced03457e964348eb587c1f2602`, 17,834 bytes / 382 lines, complete semantic reread + exact Attempt Store capture before execution;
- helper source `77927e4fcf9c874428d78415cda05f52998e59e2133af1d41126348cc8fa7a34`, DLL `8019c83a601e76be23a8762f61ed1f557f940dc11f9328893a785c6b42b8903a`; discriminator logic unchanged from preserved v0.2.5/v0.2.5.1.

## Exact first execution
- execution plane: synchronous `server.runSync.command`; return code 3;
- exact stdout `8396d1cbea2d1263a7b3a469f56e9a718840064c53d902956d701bc9da56b921`, 1,884 bytes;
- exact stderr empty SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
- structured first result `af0ce57433f71ad41dd74f06d922b88bad8fc8f69d0f8ca13496eafb47ab4601`, 2,098 bytes.

The artifact remeasured its outer execution Job as `0x1800` and passed the silent-breakaway compatibility gate. The positive helper then successfully performed the normal-child baseline/cleanup and successfully called `CreateProcessW(... CREATE_BREAKAWAY_FROM_JOB ...)`, returning sleeping child PID 2332. The helper encoded `BREAKAWAY_CREATE_SUCCESS_IN_JOB` because **the helper/root process itself remained in a Job**. The artifact incorrectly required `BREAKAWAY_CREATE_SUCCESS_NOT_IN_JOB` for the positive control and therefore stopped before checking the created child's liveness/Job membership and before protected execution.

Classification: `HARNESS_INVALID_POSITIVE_ROOT_STILL_IN_OUTER_JOB`. Admission: **NOT_ADMITTED**. Same Attempt SHALL NOT be rerun.

## What is verified vs missing
Verified:
- synchronous outer Job is compatible with explicit/silent breakaway at first execution;
- positive helper root is in a Job;
- positive helper's explicit child creation call succeeded.

Missing:
- whether that positive child is itself outside all Jobs;
- any protected explicit-breakaway observation;
- explicit breakaway denial or bypass under Forge immediate Job.

`POSITIVE_ROOT_IN_JOB != BREAKAWAY_CHILD_IN_JOB`
`EXPLICIT_CHILD_CREATION_SUCCESS != CHILD_JOB_MEMBERSHIP_PROOF`
`PROTECTED_PHASE_NOT_REACHED != BREAKAWAY_DENIAL`
`HARNESS_INVALID != SAFE_TO_REPLAY_SAME_ATTEMPT`

## Repair boundary
A NEW v0.2.5.3 may change only the positive/protected observation logic needed to query the returned explicit child PID's **actual Job membership and liveness**. Helper source/DLL, exact `CREATE_BREAKAWAY_FROM_JOB` call, normal-child baseline/cleanup, outer-Job gate, AppContainer+immediate-Job protected primitive, non-network scope and claim ceiling remain unchanged. No prior Attempt is edited/replayed.
