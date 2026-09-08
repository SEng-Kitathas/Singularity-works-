# Wider Egress v0.2.5.4 — Explicit CREATE_BREAKAWAY_FROM_JOB — Bounded Admission

Date: 2026-09-08 UTC
Mode: AUDIT -> CHECKPOINT
Role: R5 Reality Pressure Engine -> R1 Conservative Auditor
Status: **BOUNDED EXPLICIT CREATE_BREAKAWAY_FROM_JOB DENIAL QUALIFIED / GENERAL PROCESS-ESCAPE & RUNTIME LAW UNEARNED**
Authority: App/process-lifecycle security evidence only. No Main/Core, network, provider, Governance Contact global, production-launch, or product-wide runtime-law authority.

## Bindings
- App source `43aa7feac7e8a15828116bd700b644560714496d`, clean/remote-exact before and after run.
- Gen14 `checkpoint-app-live-0014-43aa7feac7e8`, MATCH/NORMAL/READY, Core IDs null.
- durable control `2726d4edbfa2d1af3977b4dda81c26da9385320d` / CHECKPOINT `6378560c5ed9993a302fc88386cb47d789cdc01f8895fa99e460dbc0b90bd264`, fresh-clone verified before execution.
- synchronous execution-plane currentness `de4e66d5a24666dea371088290a133085566f2965b309e1f6d1d0da216d91a04`: outer Job `0x1800`, BREAKAWAY_OK + SILENT_BREAKAWAY_OK true, kill-on-close false.
- frozen helper source `77927e4fcf9c874428d78415cda05f52998e59e2133af1d41126348cc8fa7a34`; helper DLL `8019c83a601e76be23a8762f61ed1f557f940dc11f9328893a785c6b42b8903a`.
- v0.2.5.4 artifact `1f7db5a043a755c0598f572de8ce2da979abe2de8ec5e40d52db66a18a9eb24e`, 19,306 bytes / 407 lines, complete semantic read + syntax PASS + exact capture before first execution.

## Exact first result
- synchronous executor return code 0;
- stdout `af8ed618e9b3652207017cc5fb3e20505e4dc5c61a0d487c67738eda08314952`, 3,353 bytes; stderr empty;
- structured first result `7ae2edac96df296f278b0a552c42cc913fd27402f65e705f2cadc7ad761cd6aa`, 3,688 bytes, fully reread before admission.

Positive lifecycle control:
- helper/root was on the non-Forge synchronous baseline path;
- normal same-child `CreateProcessW` baseline and cleanup must have succeeded, otherwise the helper would have returned its dedicated baseline failure/cleanup code before the explicit-breakaway call;
- explicit `CREATE_BREAKAWAY_FROM_JOB` creation succeeded, returning child PID 18484;
- child was alive after root exit (`WAIT_TIMEOUT`);
- any-Job membership telemetry was true; this does not identify Forge immediate-Job membership;
- explicit child cleanup succeeded and reached `WAIT_OBJECT_0`.

Protected discriminator:
- AppContainer verified true; immediate Job verified true; capability count 0; inherited handles false; timed_out false;
- root was verified in a Job;
- helper again passed its normal-child baseline/cleanup stages;
- explicit `CreateProcessW(... CREATE_BREAKAWAY_FROM_JOB ...)` failed inside that verified Job;
- Win32 error was exactly `ERROR_ACCESS_DENIED (5)`;
- no protected breakaway child was created.

## Qualified claim
> On this exact tested Windows/App/control boundary, the preserved helper can create the sleeping child explicitly with `CREATE_BREAKAWAY_FROM_JOB` on the non-Forge positive lifecycle path, but the same helper/root inside the verified zero-capability AppContainer + immediate Forge Job cannot create that child with `CREATE_BREAKAWAY_FROM_JOB`: `CreateProcessW` returns `ERROR_ACCESS_DENIED (5)`.

This qualifies only **bounded denial of this explicit `CREATE_BREAKAWAY_FROM_JOB` path** under the tested immediate Job configuration.

## Explicitly unearned
- `SILENT_BREAKAWAY_OK` behavior inside the Forge immediate Job (that flag is not configured there);
- service/WMI/COM/RPC/task-scheduler/WSL/process-broker escape resistance;
- arbitrary handle duplication or privileged helper escape;
- browser/plugin/import helper generality;
- any network or Internet-egress result from this non-network test;
- production launch-site integration;
- `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` as product/runtime fact.

`EXPLICIT_CREATE_BREAKAWAY_FROM_JOB_DENIAL != ALL_PROCESS_TREE_ESCAPE_RESISTANCE`
`EXPLICIT_BREAKAWAY_DENIAL != SERVICE_WMI_COM_RPC_WSL_ESCAPE_RESISTANCE`
`NON_NETWORK_BREAKAWAY_RESULT != NETWORK_EGRESS_RESULT`
`BOUNDED_BREAKAWAY_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`

## Next frontier
Checkpoint this qualification before any new consequence-bearing class. The next distinct process-tree pressure should not repeat `CREATE_BREAKAWAY_FROM_JOB`; candidate classes include broker/service/task-style process creation or a controlled `SILENT_BREAKAWAY_OK` configuration discriminator. No network-bearing escape test is justified until its non-network prerequisite is separately defined and preserved.
