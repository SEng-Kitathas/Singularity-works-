# Wider Egress v0.2.7.1 — WMI Reserved-PID Repair — Pre-Execution

Date: 2026-09-09 UTC
Status: **FROZEN CANDIDATE / NOT EXECUTED**
Parent diagnosis: `6f0c88e6419a09c60d969a5c9ab58e04e0642898fcf3a5b9637ebda79dd07655`.
Durable control: `8da21c41eac3cc2153970341b2259f4148bf6845` / CHECKPOINT `0753ee643f38a2f911e1a5fe315be811d1c62d7f979a54bb3b59589f2c9c9456`, fresh-clone PASS 195.
Artifact SHA: `dc4683167124b70883a6940026f28575fcaf745b51d1f4975df298f6ca36c352`.

Behavioral delta from immutable v0.2.7: exactly two PowerShell references change: `$pid` -> `$childPid` for returned WMI ProcessId assignment and success encoding. This removes collision with read-only automatic `$PID`. WMI class path, `Win32_Process.Create`, child command, all failure encodings, Toolhelp lineage/liveness, cleanup, protected AppContainer+immediate-Job primitive, non-network scope and claim ceiling remain unchanged.
