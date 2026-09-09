# Control Currentness — v0.2.7.2 Concurrent Duplicate-Execution Correction — 2026-09-09

Status: **CHECKPOINT CANDIDATE / BOUNDED WMI RESULT RETAINED / EXECUTION-LINEAGE CORRECTED / ORCHESTRATION GATE OPEN**

Immutable predecessor: `pcmmad/project-control@ebfbd0e0615073e36c38e97ac91929d283701925`, CHECKPOINT SHA-256 `609b6906e889b6f251d7110bdd59d82c32821ae917b5de1cc179e7915f371e79`, independently verified from a clean fresh clone with 207 manifested files. Main remains `e66c071fc25f8d08bfc7ebf0551948392d652f35`; Core semantic anchor `a7b4511734b1a1e507230308e75b31175aef4c4a`; App `43aa7feac7e8a15828116bd700b644560714496d`, clean/remote-exact; Gen14 remains current LKG/MATCH/NORMAL.

## Correction
The frozen v0.2.7.2 artifact `4bf2403ee909154172512bd0c3d0c681fe47c048ffb1eae741331005b005f9dc` was executed twice by concurrent workers under one immutable Attempt identity. This was an orchestration race, not authorized replay.

Chronological first execution:
- stdout `03bde566428ee513656267b8317d558520ed975a8dc4c4e715f9ac68826f8a68`
- control Git LF projection `a906c8a563e7d3da6868fc769f95fd1efd02ec607ceb969181a90a010966a8f5`
- creation UTC `2026-09-09T21:03:42.9222286Z`
- positive WMI child PID 30880

Later concurrent execution captured by the nominal Store result/admission:
- stdout `e7ec25ee0e09ede487c5a71bb6c02c1bc86fd4fe74be574af34080392004e4a2`
- creation UTC `2026-09-09T21:03:45.5317191Z`
- positive WMI child PID 15276

The chronological first preceded the later execution by approximately 2.61 seconds. App append-only correction receipt: `ea2525a04df310c194eb824b4d605245270097e6f291966e7f0176075226689d`. Control Git LF projection: `66041fd85aab779bb6eec87b68b0a32c75918665829b90adaa92676bfcd5fa9a`. App Attempt Store after correction: **209 blobs / 223 attempts / 302 events**, integrity ok / WAL / FULL.

## Semantic result retained
Both executions match on consequence-bearing fields: artifact and command hashes, positive child alive, `WmiPrvSE.exe` parent, cleanup success, protected AppContainer verified, immediate Job verified, capability count 0, inherited handles false, protected `WMI_CLASS_BIND_FAILURE`, and HRESULT low16 `0x1501`.

Nominal result `fa355f068636714e3fc6584a2377c783dd5c23a7de369546d7b835acdfe69fb9` and bounded admission `e82527f7d05ed8e51e355b624a47f94391738ac8cbfa7dfbdcf30a1ae2e08aca` therefore remain semantically supported, but they refer to the later concurrent execution rather than the chronological first.

Claim ceiling remains **positive WMI service mediation + protected WMI class-bind failure under the combined exact boundary only**. Job-specific causality, protected Create denial, all-COM/RPC/service/task generality, network egress, Main/Core promotion, and runtime law remain unearned.

## New mandatory gate
No further effectful discriminator may launch until Forge-App has an atomic single-Attempt reservation/lease/idempotency mechanism that prevents a competing worker from crossing the process-launch boundary for the same immutable Attempt identity, and that guard has been race-verified. Result-absence preflight alone is now disproven as sufficient serialization.

`CONCURRENT_DUPLICATE_EXECUTION != AUTHORIZED_REPLAY`  
`PREFLIGHT_RESULT_ABSENCE != EXECUTION_SERIALIZATION`  
`BOUNDED_RESULT_SURVIVES != PROVENANCE_ERROR_IGNORED`  
`WMI_BIND_DENIAL != JOB_SPECIFIC_DENIAL`
