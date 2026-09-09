# Wider Egress v0.2.6.1 — ShellExecuteExW Process Lifecycle — Bounded Admission

Date: 2026-09-09 UTC
Mode: AUDIT -> CHECKPOINT
Role: R5 Reality Pressure Engine -> R1 Conservative Auditor
Status: **BOUNDED SHELLEXECUTEEXW CHILD-LIFECYCLE CONTAINMENT QUALIFIED / SHELL BROKER & GENERAL ESCAPE CLAIMS UNEARNED**
Authority: App/process-lifecycle security evidence only. No Main/Core, network, provider, Governance Contact global, production-launch, or runtime-law authority.

## Bindings
- App source `43aa7feac7e8a15828116bd700b644560714496d`, clean/remote-exact before and after run.
- durable control `3b17cb3ab64606b98244c979bf8cf4b023323aeb` / CHECKPOINT `defeaca590c0d62eb9c32584f1b745dce1c56fcaf0949cad0daf2ba2aaa99f06`, fresh-clone verifier PASS 179 before execution.
- helper source `312d666b624bd182a4c201090cd5ecd9da5996ab96fbc5df4c799a3b7496e28d`; helper DLL `8922a45ce1814a86edbed007a6e444f0f42556b3e3e5a67f30b16552c98892b4`.
- stale-control v0.2.6 `1f2bd6a10477b3c03119420e98044068f96d7fd039b2a12c098f2312c51fff41` preserved/unexecuted.
- currentness-only v0.2.6.1 artifact `f649b0c341c53de9988c0bc3fdc0a0d5975904726546121569224dacceec0399`, 15,324 bytes / 319 lines, full semantic reread + syntax PASS + exact capture before first execution.

## Exact first result
- synchronous executor rc0;
- stdout `554b7af88035c2ab55c2a9dd108c13600426a8291946adc3837a0fa620d5f4e9`, 3,175 bytes; stderr empty;
- structured first result `4438e2e5ce5f2bdcb77d88f513af39483ec8f6e8e693ed9b100c4236a2eb2a3e`, 3,464 bytes, fully reread before admission.

Positive lifecycle control:
- exact `ShellExecuteExW` helper returned PID 36220;
- child was alive after root exit (`WAIT_TIMEOUT`);
- any-Job telemetry true;
- cleanup succeeded and reached `WAIT_OBJECT_0`.

Protected discriminator:
- AppContainer verified; immediate Job verified; capability count 0; inherited handles false; no timeout;
- protected `ShellExecuteExW` also returned a supervised PID, 15092;
- after `run_zero_network_process` returned and closed the immediate Forge Job, PID 15092 was absent (`OpenProcess` Win32 87 / `ERROR_INVALID_PARAMETER`);
- no protected child cleanup was required because the child was already gone.

## Qualified claim
> On this exact tested Windows/App/control boundary, the preserved ShellExecuteExW helper launches a sleeping PowerShell child that survives root exit on the positive lifecycle path, while under the verified zero-capability AppContainer + immediate Forge Job the same ShellExecuteExW path returns a child PID that is no longer alive after the protected primitive closes the immediate Job and returns.

This qualifies only **bounded ShellExecuteExW child-lifecycle containment for the exact tested launch path**.

## Explicitly unearned
- proof that ShellExecuteExW used an out-of-process shell broker;
- `Shell.Application` COM broker behavior;
- service/WMI/COM/RPC/task-scheduler/WSL or other brokered process creation;
- arbitrary shell verbs/file associations;
- network/Internet egress behavior from this non-network test;
- production launch integration or product runtime law.

`SHELLEXECUTEEX_PATH != PROVEN_OUT_OF_PROCESS_BROKER`
`SHELLEXECUTEEX_CONTAINMENT != ALL_PROCESS_TREE_ESCAPE_RESISTANCE`
`NON_NETWORK_RESULT != NETWORK_EGRESS_RESULT`
`BOUNDED_SHELLEXECUTEEX_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`

## Next frontier
Checkpoint this qualification before selecting another distinct class. A future broker-specific discriminator must prove the broker mechanism itself rather than infer it from ShellExecuteExW. No network-bearing escape pressure is justified from this result.
