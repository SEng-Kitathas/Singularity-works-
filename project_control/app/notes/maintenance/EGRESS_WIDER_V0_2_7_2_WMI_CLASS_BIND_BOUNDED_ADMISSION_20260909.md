# Wider Egress v0.2.7.2 — WMI Win32_Process.Create Path — Bounded Admission

Date: 2026-09-09 UTC
Mode: AUDIT -> CHECKPOINT
Role: R5 Reality Pressure Engine -> R1 Conservative Auditor
Status: **POSITIVE WMI SERVICE MEDIATION VERIFIED / PROTECTED WMI CLASS-BIND FAILURE QUALIFIED / JOB-SPECIFIC CAUSALITY UNEARNED**
Authority: App/process-lifecycle security evidence only. No Main/Core, network, provider, Governance Contact global, production-launch, or runtime-law authority.

## Bindings
- App source `43aa7feac7e8a15828116bd700b644560714496d`, clean/remote-exact before and after run.
- durable control `dbe988b4a6773a79d31935b46984b17fb9c4c421` / CHECKPOINT `f84f5b8886dd56c7c9ec8baa52c34f5c08a3e1890074f76188d9e110a58e6f67`, fresh-clone verifier PASS 201 before execution.
- v0.2.7.2 artifact `4bf2403ee909154172512bd0c3d0c681fe47c048ffb1eae741331005b005f9dc`, 17,141 bytes / 338 lines, full semantic reread + syntax PASS + exact Attempt Store capture before first execution.

## Exact first result
- synchronous executor rc0;
- stdout `e7ec25ee0e09ede487c5a71bb6c02c1bc86fd4fe74be574af34080392004e4a2`, 3,035 bytes; stderr empty;
- structured first result `fa355f068636714e3fc6584a2377c783dd5c23a7de369546d7b835acdfe69fb9`, 3,581 bytes, fully reread before admission.

Positive service-mediated control:
- local WMI `Win32_Process.Create` returned child PID 15276;
- child was alive after root exit (`WAIT_TIMEOUT`);
- Toolhelp lineage identified child `powershell.exe`, parent PID 31628 / `WmiPrvSE.exe`;
- any-Job telemetry was true;
- cleanup succeeded and reached `WAIT_OBJECT_0`.

Protected discriminator:
- AppContainer verified true; immediate Job verified true; capability count 0; inherited handles false; timed_out false;
- the protected root failed while binding local WMI class `Win32_Process`, before `Create`;
- encoded result was `0x20001501`; low16 HRESULT evidence `0x1501` / decimal 5377;
- no protected WMI child was created.

## Qualified claim
> On this exact tested Windows/App/control boundary, local WMI `Win32_Process.Create` is demonstrably service-mediated on the positive path (`WmiPrvSE.exe` parent), while the same protected root under the verified zero-capability AppContainer + immediate Forge Job boundary cannot complete the local WMI `Win32_Process` class bind and therefore does not reach `Create`.

This qualifies only **bounded protected WMI class-bind failure for this exact path under the combined protected boundary**.

## Explicitly unearned
- attribution of the failure specifically to the immediate Job rather than AppContainer/token/security context or another part of the protected boundary;
- all COM/RPC/WMI namespaces/classes/methods;
- service/task-scheduler/WSL or arbitrary brokered process creation;
- protected WMI `Create` denial itself, because protected execution did not reach `Create`;
- network/Internet egress behavior;
- production integration or product-wide runtime law.

`PROTECTED_WMI_CLASS_BIND_FAILURE != JOB_SPECIFIC_DENIAL`
`WMI_CLASS_BIND_FAILURE != WMI_CREATE_DENIAL`
`WMI_WIN32_PROCESS_PATH != ALL_COM_RPC_PROCESS_CREATION`
`NON_NETWORK_RESULT != NETWORK_EGRESS_RESULT`
`BOUNDED_WMI_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`

## Next frontier
Checkpoint this qualification before any new consequence-bearing pressure. A future causal-isolation branch would need to vary AppContainer vs immediate-Job dimensions without conflating them, or select a different broker/service process-creation mechanism. No same WMI Attempt replay.
