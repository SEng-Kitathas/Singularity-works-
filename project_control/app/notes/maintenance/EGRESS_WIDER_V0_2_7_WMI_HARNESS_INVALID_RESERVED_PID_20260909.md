# Wider Egress v0.2.7 — WMI Win32_Process.Create — HARNESS_INVALID

Date: 2026-09-09 UTC
Status: **FIRST ATTEMPT IMMUTABLE / HARNESS_INVALID / NO WMI CONTAINMENT OR DENIAL ADMISSION**

Bindings: control `b8c5e6f9c7032e2a25c25ac4b4e50de91183d64c` / CHECKPOINT `59643050ecd2c741ca81253c59f1ce88e9344866a683420a9f90c702d46c1520`; artifact `01461d5f61a7e1cc85a8365ff11565df7ada1069c46b9a90ea036394dbc762b5`; first structured result `3dbc3f7b0dda8cf13ec3f4d59933d0bdda992b914123e33ee62324fa391bf236`; exact stdout `a93898b48fc9b807fc3b68a40439397b8dfdf2b7a5bfddd693aa0bdc21e2a5eb`.

The positive root exited 1 with internal stderr flagged nonempty; protected phase was not reached. Exact outer stderr was empty because the artifact captured only a boolean for the inner PowerShell stderr. Static reconstruction + PowerShell parser validation showed the root script is syntactically valid. The harness then revealed a deterministic runtime defect: after `$r=$c.Create($cmd)` returns non-null with `ReturnValue == 0`, it executes `$pid=[uint32]$r.ProcessId`. PowerShell automatic variable `$PID` is read-only, so that assignment throws outside the guarded WMI calls and the root exits 1 before encoding the returned child PID.

This means the WMI Create call reached a success return, but the Attempt did **not** capture the child PID, liveness, parent lineage, cleanup, or any protected observation. A later non-mutating process query found no attributable 30-second child remaining; no forced cleanup was necessary.

Classification: `HARNESS_INVALID_RESERVED_POWERSHELL_PID_ASSIGNMENT_AFTER_WMI_CREATE_SUCCESS_RETURN`. Admission: **NOT_ADMITTED**. Same Attempt SHALL NOT be rerun.

`WMI_CREATE_SUCCESS_RETURN != VALID_CHILD_LIFECYCLE_OBSERVATION`
`POSITIVE_PID_CAPTURE_FAILURE != PROTECTED_WMI_DENIAL`
`PROTECTED_PHASE_NOT_REACHED != WMI_CONTAINMENT`
`HARNESS_INVALID != SAFE_TO_REPLAY_SAME_ATTEMPT`

Repair boundary: a NEW v0.2.7.1 may change only the PowerShell local variable from reserved `$pid` to a non-reserved child-PID variable and corresponding encoding reference. WMI class path, `Win32_Process.Create`, child command, failure encodings, Python supervision/lineage, protected primitive, non-network scope and claim ceiling remain unchanged.
