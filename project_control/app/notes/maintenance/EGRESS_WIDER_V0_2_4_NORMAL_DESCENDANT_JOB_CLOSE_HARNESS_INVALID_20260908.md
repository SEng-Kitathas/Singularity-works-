# Wider Egress v0.2.4 — Normal Descendant Job-Close — First Result HARNESS_INVALID

Date: 2026-09-08 UTC
Status: **FIRST ATTEMPT IMMUTABLE / HARNESS_INVALID / NO JOB-CONTAINMENT CLAIM**
Authority: App/security evidence only. No Main/Core, provider, Governance Contact, network, runtime-law, or promotion authority.

## Preserved Attempt
- Attempt: `attempt-egress-wider-v0-2-4-normal-descendant-job-close-lifecycle-first`
- Artifact SHA-256: `b3e8470932b446edc2fdcdf6f6151b8d3ffea3b2962b56114bb3423c627f52cf`
- Artifact: `state/attempt_artifacts/EGRESS_WIDER_V0_2_4_NORMAL_DESCENDANT_JOB_CLOSE_LIFECYCLE_20260908.py`
- Parent: v0.2.3 bounded admission `59623224fd455cb7590d59682330740920a51a7fc2f7ab2217071d72a65227f3`
- Network activity intended: false

## First execution
- Job: `job-0705e689d74c`
- Executor finality: FAILED / rc1
- Protected phase: **not reached**
- stdout: empty SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- stderr SHA `934b03ff7bd0d7703ad4f260ec880df49deaea7be0fd264f51cd59e048879b67`, 1,764 bytes
- structured first result SHA `c6366904038e45cb0ec9712b9aeb34f016220786e731bdfb7a654097e2601710`

## Diagnosis
The unprotected positive-control root launched the intended 30-second sleeping PowerShell descendant. Because the harness invoked the root through `subprocess.run(... capture_output=True ...)`, the descendant inherited the capture-pipe handles. Python `communicate()` therefore waited for pipe EOF and timed out after 10 seconds even though the root had exited. Executor duration of about 30.6 seconds is consistent with the sleeping descendant retaining those handles until natural exit.

Classification: `HARNESS_INVALID / POSITIVE_CONTROL_PIPE_INHERITANCE_TIMEOUT`.

No protected lifecycle observation exists from this Attempt. Therefore no normal-descendant Job-close containment result and no explicit Job-breakaway result is earned.

## Repair boundary
A NEW v0.2.4.1 Attempt may change only the unprotected positive-control stdio from captured pipes to `DEVNULL`. Root/child command, 30-second sleep, protected phase, `cwd=powershell.parent`, PID liveness probe, cleanup, claim ceiling and non-network scope SHALL remain unchanged. The original Attempt/result remain immutable.

`POSITIVE_CONTROL_PIPE_TIMEOUT != JOB_CONTAINMENT_RESULT`
`UNPROTECTED_HARNESS_INVALID != PROTECTED_LIFECYCLE_FAILURE`
`HARNESS_REPAIR != PERMISSION_TO_EDIT_ATTEMPT_0`
