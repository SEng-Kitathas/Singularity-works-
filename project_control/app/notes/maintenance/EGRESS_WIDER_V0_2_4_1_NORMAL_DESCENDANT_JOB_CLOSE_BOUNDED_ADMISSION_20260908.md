# Wider Egress v0.2.4.1 — Normal Descendant Job-Close — Bounded Admission

Date: 2026-09-08 UTC
Mode: AUDIT -> CHECKPOINT
Role: R5 Reality Pressure Engine -> R1 Conservative Auditor
Status: **BOUNDED NORMAL-DESCENDANT JOB-CLOSE TERMINATION QUALIFIED / EXPLICIT BREAKAWAY UNEARNED**
Authority: App/process-lifecycle security evidence only. No Main/Core, network, provider, Governance Contact global, production-launch, or product-wide runtime-law authority.

## Lineage / currentness
- immutable v0.2.4 Attempt 0: artifact `b3e8470932b446edc2fdcdf6f6151b8d3ffea3b2962b56114bb3423c627f52cf`; first result `c6366904038e45cb0ec9712b9aeb34f016220786e731bdfb7a654097e2601710`; `HARNESS_INVALID / POSITIVE_CONTROL_PIPE_INHERITANCE_TIMEOUT`; protected phase never reached.
- separately preserved stale-control repair sibling `1faa37259781fd0b3f09b50855a27b2000c72807396701a31cbdd7d65c41194e` remains unexecuted and is not collapsed into this lineage.
- live repair artifact `81d8d42b2280e249f13d4a5c30f588a1784d9c6bc0c60e4fee0279f611ad53c8`, 12,908 bytes / 323 lines, complete semantic read and syntax PASS before exact capture.
- App source `43aa7feac7e8a15828116bd700b644560714496d` remained clean/remote-exact.
- durable control `d76299e728b5026df87c39c17ad9d723f759ce5f` / CHECKPOINT `1f6e82c8515981b45667899f5f1eb120247ee31805a7e401f277643c41b72c05` was non-force published and independently fresh-clone verified before execution.
- current primitive reread confirmed `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` is set and neither `BREAKAWAY_OK` nor `SILENT_BREAKAWAY_OK` is configured.

## Exact first execution
Job `job-c4852891e585` completed normally with executor rc0.
- exact stdout `28860b0febb229c61a87003257438d33ff1de606a18d1f741cfe8166e2dca340`, 2,746 bytes;
- exact stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, 0 bytes;
- structured first result `709ba15edfbdc640c313f236daeb8c8abe889a64e03cc8feb50aedcade2ac173`, 2,882 bytes.

Positive control:
- exact unprotected root returned descendant PID 40676;
- descendant was alive after root exit (`WAIT_TIMEOUT`);
- harness then terminated it successfully and observed `WAIT_OBJECT_0`.

Protected discriminator:
- AppContainer verified; immediate Job verified; capability count 0; inherited handles false; environment inherited; timed_out false;
- protected root returned descendant PID 28800;
- immediately after `run_zero_network_process` returned (after its `finally` closed the immediate Job), that PID was absent: `OpenProcess` failed with Win32 87 / `ERROR_INVALID_PARAMETER`, classified alive=false.

The child command is a 30-second `Start-Sleep`; the protected observation occurred in ~0.375 seconds. The positive control establishes the same normal descendant remains alive after root exit when not contained. Together these observations qualify only normal-descendant termination across the exact immediate kill-on-close Job lifecycle.

## Qualified claim
> On this tested Windows/App source/control boundary, a normally-created descendant launched by the exact PowerShell Process.Start root survives the root's exit when unprotected, while under the zero-capability AppContainer + immediate `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` primitive the returned descendant PID is no longer alive after the primitive closes the Job and returns.

## Explicitly unearned
- explicit `CREATE_BREAKAWAY_FROM_JOB` denial;
- `BREAKAWAY_OK` / `SILENT_BREAKAWAY_OK` configurations;
- service/WMI/COM/RPC/task-scheduler/WSL escape resistance;
- browser/plugin/import helper generality;
- any network or Internet-egress claim from this non-network test;
- production launch-site integration;
- `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` as runtime fact.

`NORMAL_DESCENDANT_JOB_CLOSE_TERMINATION != CREATE_BREAKAWAY_FROM_JOB_DENIAL`
`JOB_MEMBERSHIP_AT_ROOT != ALL_PROCESS_TREE_ESCAPE_RESISTANCE`
`NON_NETWORK_LIFECYCLE_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`

## Next frontier
Checkpoint this bounded lifecycle qualification before any next consequence-bearing discriminator. Then use a NEW non-network Attempt to request explicit Job breakaway and discriminate whether the current Job configuration rejects the creation flag or permits a child to survive Job close. No network-bearing breakaway pressure is justified before that prerequisite is measured.
