# Wider Egress v0.2.7 — WMI Win32_Process.Create Lifecycle — Pre-Execution Design

Date: 2026-09-09 UTC
Status: **FROZEN CANDIDATE / NOT EXECUTED**
Parent admission: `06161c25977979e740fbc05e826f8bdc56d83759f136c2178a70f7b2a4af965f`.
Durable control: `b8c5e6f9c7032e2a25c25ac4b4e50de91183d64c` / CHECKPOINT `59643050ecd2c741ca81253c59f1ce88e9344866a683420a9f90c702d46c1520`.
Artifact SHA: `01461d5f61a7e1cc85a8365ff11565df7ada1069c46b9a90ea036394dbc762b5`.

Mechanism: local WMI `Win32_Process.Create`, materially distinct from direct CreateProcessW and ShellExecuteExW. Non-creating feasibility probe verified WMI class binding unprotected (probe exit 44) and class-binding failure under the verified protected primitive (probe exit 199); no Process.Create was invoked by the feasibility probe.

The frozen Attempt performs an actual positive WMI Create of a 30-second sleeping PowerShell child, supervises returned PID, records Toolhelp parent PID/executable, and requires cleanup. Protected execution attempts the exact same WMI path. Failures are stage-classified; a protected bind/invocation/return failure is bounded denial at that WMI stage only. If protected WMI Create returns a PID, post-return liveness decides containment vs bypass.

`WMI_PROCESS_CREATE != ALL_COM_RPC_PROCESS_CREATION`
`WMI_BIND_DENIAL != JOB_SPECIFIC_DENIAL`
`WMI_PARENT_IDENTITY != GENERAL_SERVICE_BROKER_LAW`
`NON_NETWORK_RESULT != NETWORK_EGRESS_RESULT`
