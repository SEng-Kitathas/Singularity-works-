# App v0.2.7.2 Concurrent Duplicate Execution — Cross-Arm Awareness — 2026-09-09

Status: **APPEND-ONLY PROVENANCE CORRECTION / ZERO MAIN-CORE PROMOTION**

App frozen WMI v0.2.7.2 artifact `4bf2403ee909154172512bd0c3d0c681fe47c048ffb1eae741331005b005f9dc` was executed twice by concurrent workers under the same immutable Attempt identity. Chronological-first stdout is `03bde566428ee513656267b8317d558520ed975a8dc4c4e715f9ac68826f8a68`; later nominal Store stdout is `e7ec25ee0e09ede487c5a71bb6c02c1bc86fd4fe74be574af34080392004e4a2`. App correction receipt is `ea2525a04df310c194eb824b4d605245270097e6f291966e7f0176075226689d`.

Both executions independently converge on the same bounded App observation: unprotected WMI `Win32_Process.Create` is service-mediated by `WmiPrvSE.exe`; under the exact verified zero-capability AppContainer + immediate Forge Job boundary, local WMI class binding fails at `0x20001501` / low16 `0x1501` before Create. Existing nominal result `fa355f068636714e3fc6584a2377c783dd5c23a7de369546d7b835acdfe69fb9` and bounded admission `e82527f7d05ed8e51e355b624a47f94391738ac8cbfa7dfbdcf30a1ae2e08aca` remain semantically valid but refer to the later concurrent execution.

No Main/Core semantic or product promotion follows. Job-specific causality, general COM/RPC/process-tree authority, network authority, and runtime law remain unearned. Further effectful App discriminators are blocked until single-Attempt execution serialization/idempotency is verified.

`CONCURRENT_DUPLICATE_EXECUTION != AUTHORIZED_REPLAY`  
`APP_BOUNDED_RESULT != MAIN_CORE_PROMOTION`
