# Wider Egress v0.2.5.3 — Explicit Job Breakaway — HARNESS_INVALID

Date: 2026-09-08 UTC
Status: **FIRST ATTEMPT IMMUTABLE / HARNESS_INVALID / NO BREAKAWAY ADMISSION**
Authority: App/process-lifecycle evidence only. No Main/Core, network, provider, Governance Contact global, production, or runtime-law authority.

## Bindings
- control `8071b0945ee7f9a7709eef0ef62c42141a2ebc39` / CHECKPOINT `1002110708b3bd53db376249dd384cfe26dcfb2d6aa6340880124f8cea6cb021`, fresh-clone verified before execution;
- synchronous plane `df57157d14dff5648027a7fd7d3ab1354f9c4b298f276b44098768ae705cf003` remeasured `0x1800` with explicit+silent breakaway allowed;
- artifact `e6913d1b923153a6943b3f3fb34e50c7054f9123a3d940e33d8719d89cf2031d`, 19,557 bytes / 411 lines, complete read + exact Attempt Store capture before execution;
- helper source/DLL remain exact `77927e4f...` / `8019c83a...`.

## Exact first execution
- synchronous `runSync.command`, rc3;
- stdout `25351c8c9c380a42d3e155f8cdfae3c5f9ae6928b24b0e5264f7cedbd791a701`, 2,167 bytes; stderr empty;
- structured first result `27af68192010146a421ea95900407bdc58c47984496fba98a163bbfc069854bf`, 2,345 bytes.

Positive path observations:
- outer plane remained `0x1800`;
- helper normal-child baseline and cleanup completed before explicit creation;
- explicit `CREATE_BREAKAWAY_FROM_JOB` creation succeeded, returning PID 9320;
- returned child was alive after root exit (`WAIT_TIMEOUT`);
- `IsProcessInJob(child,NULL)` returned true: the child belonged to **some Job**;
- artifact stopped because it required the positive child to be outside *all* Jobs; protected phase was not reached;
- artifact `finally` cleanup ran; independent post-run probe found PID 9320 absent (`OpenProcess` Win32 87).

Classification: `HARNESS_INVALID_POSITIVE_CHILD_IN_SOME_JOB`; admission **NOT_ADMITTED**; same Attempt SHALL NOT be rerun.

## Refined diagnosis
The positive-control requirement `child.in_any_job == false` is over-strong. The synchronous execution plane itself is Job-governed. The positive control only needs to establish that the exact explicit-child creation call succeeds and that the sleeping child survives the helper/root's exit in the **absence of the Forge immediate Job primitive**. Those facts are already observed.

For the protected phase, the decisive escape signal does not require naming every outer Job: if explicit creation succeeds inside the Forge-protected root and the returned sleeping child is still alive **after `run_zero_network_process` returns and closes the immediate kill-on-close Forge Job**, that is direct bypass evidence for the Forge immediate-Job boundary. If protected explicit creation instead fails in the verified immediate Job with Win32 `ERROR_ACCESS_DENIED`, that is bounded explicit-breakaway-denial evidence.

`ANY_JOB_MEMBERSHIP != FORGE_IMMEDIATE_JOB_MEMBERSHIP`
`POSITIVE_EXPLICIT_CREATE_SUCCESS + CHILD_SURVIVAL_AFTER_ROOT_EXIT == VALID_POSITIVE_LIFECYCLE_SIGNAL`
`PROTECTED_CHILD_SURVIVAL_AFTER_FORGE_JOB_CLOSE == BREAKAWAY_BYPASS_EVIDENCE`
`PROTECTED_CREATE_FAILURE_ERROR_ACCESS_DENIED_IN_VERIFIED_JOB == BOUNDED_DENIAL_EVIDENCE`

## Repair boundary
A NEW v0.2.5.4 may remove only the positive-control requirement that the returned child be outside all Jobs. It SHALL retain and report child any-Job membership as context. Helper source/DLL, exact `CREATE_BREAKAWAY_FROM_JOB` call, normal-child baseline/cleanup, outer-plane gate, protected AppContainer+immediate-Job primitive, protected survival test, non-network scope and claim ceiling remain unchanged.
