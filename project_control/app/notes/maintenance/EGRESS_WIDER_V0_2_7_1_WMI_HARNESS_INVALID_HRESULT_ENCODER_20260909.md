# Wider Egress v0.2.7.1 — WMI HARNESS_INVALID — Protected HRESULT Encoder

Date: 2026-09-09 UTC
Status: **FIRST ATTEMPT IMMUTABLE / HARNESS_INVALID / POSITIVE WMI SERVICE MEDIATION VERIFIED / PROTECTED WMI OUTCOME UNRESOLVED**

Bindings: control `8da21c41eac3cc2153970341b2259f4148bf6845` / CHECKPOINT `0753ee643f38a2f911e1a5fe315be811d1c62d7f979a54bb3b59589f2c9c9456`; artifact `dc4683167124b70883a6940026f28575fcaf745b51d1f4975df298f6ca36c352`; first result `4a10e2fa70fe620ebcaed8d23163b48f2b565a4230831cbc34e771a9b0b585b5`.

Positive control is valid and materially informative: WMI `Win32_Process.Create` returned PID 23160; the child was alive after root exit; Toolhelp lineage identified parent PID 39080 / `WmiPrvSE.exe`; any-Job telemetry was true; cleanup succeeded. This verifies service-mediated positive WMI process creation for the exact tested path.

Protected receipt was itself valid: AppContainer verified, immediate Job verified, capability count 0, inherited handles false, no timeout. The protected root returned raw 1, so no protected WMI stage was classifiable.

A non-creating protected diagnostic isolated the encoder defect. The protected WMI class bind throws. Using the frozen catch encoder's `[uint32]$_.Exception.HResult` conversion causes an unhandled conversion error under `$ErrorActionPreference='Stop'`, collapsing to exit 1. Replacing only that conversion with signed masking `($_.Exception.HResult -band 0xFFFF)` on the same non-creating class-bind probe produced encoded exit `0x20001501` (decimal 536876289; low16 `0x1501`). No `Win32_Process.Create` was invoked by this diagnostic.

Classification: `HARNESS_INVALID_PROTECTED_HRESULT_UINT32_ENCODER`. Admission: **NOT_ADMITTED for protected WMI denial/containment**. Same Attempt SHALL NOT be rerun. Positive service-mediated lineage is evidence, but not a protected admission.

`POSITIVE_WMI_SERVICE_MEDIATION != PROTECTED_WMI_CONTAINMENT`
`PROTECTED_CLASS_BIND_EXCEPTION != JOB_SPECIFIC_DENIAL`
`HRESULT_ENCODER_FAILURE != WMI_PATH_RESULT`
`HARNESS_INVALID != SAFE_TO_REPLAY_SAME_ATTEMPT`

Repair boundary: after checkpoint, NEW v0.2.7.2 may change only both WMI exception encoders from `[uint32]$_.Exception.HResult` to signed low16 masking while preserving stage prefixes. WMI class path/Create call, child command, success encoding, WMI ReturnValue encoding, Toolhelp lineage/liveness/cleanup, protected primitive, non-network scope and claim ceiling remain unchanged.
