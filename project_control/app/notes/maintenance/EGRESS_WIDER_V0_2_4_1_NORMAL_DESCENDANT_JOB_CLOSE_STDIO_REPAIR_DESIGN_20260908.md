# Wider Egress v0.2.4.1 — Normal Descendant Job-Close — Stdio Repair Design

Date: 2026-09-08 UTC
Status: **FROZEN CANDIDATE / NOT EXECUTED**
Parent result: `c6366904038e45cb0ec9712b9aeb34f016220786e731bdfb7a654097e2601710` (`HARNESS_INVALID / POSITIVE_CONTROL_PIPE_INHERITANCE_TIMEOUT`).
Durable control: `d76299e728b5026df87c39c17ad9d723f759ce5f` / CHECKPOINT `1f6e82c8515981b45667899f5f1eb120247ee31805a7e401f277643c41b72c05`.
Artifact: `state/attempt_artifacts/EGRESS_WIDER_V0_2_4_1_NORMAL_DESCENDANT_JOB_CLOSE_LIFECYCLE_STDIO_REPAIR_20260908.py`
SHA-256: `81d8d42b2280e249f13d4a5c30f588a1784d9c6bc0c60e4fee0279f611ad53c8`

Behavioral delta from immutable v0.2.4 Attempt 0: **only** the unprotected positive-control `subprocess.run` stdio changes from captured pipes to `stdout=DEVNULL, stderr=DEVNULL`. The exact PowerShell root/child command, 30-second child sleep, protected phase, qualified `cwd=powershell.parent`, PID-liveness probe, cleanup logic, non-network scope and claim ceiling remain unchanged. Lineage/version/control identifiers change only to bind the new Attempt.

`HARNESS_REPAIR != EDIT_ATTEMPT_0`
`POSITIVE_STDIO_DEVNULL != JOB_CONTAINMENT_RESULT`
`NORMAL_DESCENDANT_JOB_CLOSE_TERMINATION != CREATE_BREAKAWAY_FROM_JOB_DENIAL`
