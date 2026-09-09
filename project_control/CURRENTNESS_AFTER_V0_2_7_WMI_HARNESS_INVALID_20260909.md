# Control Currentness — v0.2.7 WMI Win32_Process.Create HARNESS_INVALID — 2026-09-09

Status: **CHECKPOINT CANDIDATE / NO WMI CONTAINMENT OR DENIAL ADMISSION / ZERO PRODUCT OR CORE PROMOTION**

Predecessor control `b8c5e6f9c7032e2a25c25ac4b4e50de91183d64c` / CHECKPOINT `59643050ecd2c741ca81253c59f1ce88e9344866a683420a9f90c702d46c1520`. Main `e66c071...`; Core semantic anchor `a7b45117...`; App `43aa7fea...`; Gen14 current. Governance Contact remains locally binding on both development arms; ACTIVE receipt absent; global ACTIVE unearned.

## v0.2.7 first result
- artifact `01461d5f61a7e1cc85a8365ff11565df7ada1069c46b9a90ea036394dbc762b5`, first synchronous execution rc3.
- exact structured result `3dbc3f7b0dda8cf13ec3f4d59933d0bdda992b914123e33ee62324fa391bf236`; diagnosis `6f0c88e6419a09c60d969a5c9ab58e04e0642898fcf3a5b9637ebda79dd07655`.
- positive WMI `Win32_Process.Create` reached a successful return far enough that the next statement attempted to assign the returned ProcessId. The script used reserved PowerShell automatic variable `$PID`, causing unhandled root exit 1 before child PID encoding/supervision.
- protected phase was not reached. No WMI lifecycle/containment/denial claim is admitted. No attributable 30-second child remained at later inspection; no forced cleanup was required.
- App Attempt Store: **196 blobs / 207 attempts / 286 events**, integrity `ok`.

## Repair boundary
After this successor is directly committed/pushed/fresh-clone verified, NEW v0.2.7.1 may change only the PowerShell local variable `$pid` to a non-reserved child-PID variable and update the corresponding encoder reference. WMI class path, `Win32_Process.Create`, child command, failure encodings, Toolhelp lineage/liveness, protected primitive, non-network scope and claim ceiling remain unchanged.

`WMI_CREATE_SUCCESS_RETURN != VALID_CHILD_LIFECYCLE_OBSERVATION`
`POSITIVE_PID_CAPTURE_FAILURE != PROTECTED_WMI_DENIAL`
`PROTECTED_PHASE_NOT_REACHED != WMI_CONTAINMENT`
`HARNESS_INVALID != SAFE_TO_REPLAY_SAME_ATTEMPT`
`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

Privacy projection: live DTS unchanged. Main source DTS `5649d40540c76a356cbcf0841675bcd051e39c16beac0088641d738f8d51724b`; App source DTS `b168d9efd486a9508b2fd868fb73884e25b73211ef6c1b1d059d1847de3c0a66`. Control DTS copies LF-normalized and local project roots placeholdered only.
