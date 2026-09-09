# Egress Wider v0.2.7.2 — Concurrent Duplicate Execution Lineage Correction — 2026-09-09

Status: **VERIFIED APPEND-ONLY PROVENANCE CORRECTION**  
Mode: RECOVERY / AUDIT  
Scope: correct execution chronology and `same_attempt_rerun` lineage only; preserve the bounded WMI result without widening it.

## Why this correction exists
The frozen v0.2.7.2 artifact was executed twice by two concurrent workers in a narrow race window under the same immutable Attempt identity:
`attempt-egress-wider-v0-2-7-2-wmi-win32-process-create-hresult-encoder-repair-first`.

The Attempt Store later preserved the second execution as the nominal `...-stdout`, `...-stderr`, `...-result` lineage and the bounded admission `attempt-egress-wider-v0-2-7-2-wmi-class-bind-bounded-admission`. Those immutable records SHALL NOT be rewritten. Their bounded semantic conclusion survives, but their chronology label and `same_attempt_rerun=false` metadata are superseded by this correction.

## Verified execution ordering
Chronological first execution:
- server log: `.pcmmad_sync_runs/sync-805d26615197.stdout.log`
- creation UTC: `2026-09-09T21:03:42.9222286Z`
- last-write UTC: `2026-09-09T21:03:43.4761996Z`
- stdout SHA-256: `03bde566428ee513656267b8317d558520ed975a8dc4c4e715f9ac68826f8a68`
- stdout bytes: `3033`
- positive child PID: `30880`

Later concurrent execution that was preserved under the nominal first-result lineage:
- server log: `.pcmmad_sync_runs/sync-bbef0542b157.stdout.log`
- creation UTC: `2026-09-09T21:03:45.5317191Z`
- last-write UTC: `2026-09-09T21:03:46.0335621Z`
- stdout SHA-256: `e7ec25ee0e09ede487c5a71bb6c02c1bc86fd4fe74be574af34080392004e4a2`
- stdout bytes: `3035`
- positive child PID: `15276`

The first log therefore predates the later log by approximately 2.61 seconds at creation time.

## Semantic equivalence across both executions
Both executions independently verified the same consequence-bearing fields:
- artifact SHA `4bf2403ee909154172512bd0c3d0c681fe47c048ffb1eae741331005b005f9dc`
- status `PASS_BOUNDED_PROTECTED_WMI_PROCESS_CREATE_PATH_DENIED`
- root command SHA `3bae6c52d81a9c94dc0e4a20806bc55b7d987a258a2bf8fa0a1d0e17f262dc2c`
- protected command SHA `d023b57baf116651948743bc4e5b158d49856a9ce6437c7718de0ce6ba2d89ce`
- positive WMI child alive after root exit
- positive parent executable `WmiPrvSE.exe`
- positive cleanup terminated and waited successfully
- protected AppContainer verified
- protected immediate Forge Job verified
- protected capability count `0`
- protected inherited handles `false`
- protected decoded stage `WMI_CLASS_BIND_FAILURE`
- protected HRESULT low16 `5377` / `0x1501`

Only volatile execution fields such as PIDs and elapsed timing differ.

## Corrected interpretation
The existing bounded admission receipt:
`e82527f7d05ed8e51e355b624a47f94391738ac8cbfa7dfbdcf30a1ae2e08aca`
remains semantically supported by two convergent executions, but its supporting Store result
`fa355f068636714e3fc6584a2377c783dd5c23a7de369546d7b835acdfe69fb9`
is the later concurrent execution, not the chronological first execution.

The chronological first execution SHALL be preserved separately under correction-specific Attempt IDs. The immutable prior metadata field `same_attempt_rerun=false` is no longer current: **a concurrent duplicate execution did occur**. This was an orchestration race, not an intentional replay authorization.

## Claim ceiling
What is earned remains narrow:
- positive WMI `Win32_Process.Create` service-mediated child lifecycle is verified on the unprotected path, including `WmiPrvSE.exe` parent identity;
- under the exact zero-capability AppContainer + immediate Forge Job boundary, WMI class binding failed with HRESULT low16 `0x1501` before `Win32_Process.Create` was reached.

What is NOT earned:
- Job-specific causation for the WMI class-bind failure;
- all-COM/RPC/service process-creation containment;
- general process-tree authority;
- network egress authority;
- runtime law promotion;
- permission to execute this same frozen Attempt again.

Laws:
`WMI_BIND_DENIAL != JOB_SPECIFIC_DENIAL`  
`WMI_CLASS_BIND_FAILURE != ALL_COM_RPC_PROCESS_CREATION`  
`NON_NETWORK_RESULT != NETWORK_EGRESS_RESULT`  
`CONCURRENT_DUPLICATE_EXECUTION != AUTHORIZED_REPLAY`  
`APPEND_ONLY_CORRECTION != SILENT_REWRITE`
