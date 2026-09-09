# Control Currentness — v0.2.7.1 WMI Positive Service Mediation / Protected HARNESS_INVALID — 2026-09-09

Status: **CHECKPOINT CANDIDATE / POSITIVE WMI SERVICE MEDIATION VERIFIED / PROTECTED WMI OUTCOME NOT ADMITTED / ZERO PRODUCT OR CORE PROMOTION**

Predecessor control `8da21c41eac3cc2153970341b2259f4148bf6845` / CHECKPOINT `0753ee643f38a2f911e1a5fe315be811d1c62d7f979a54bb3b59589f2c9c9456`. Main `e66c071...`; Core `a7b45117...`; App `43aa7fea...`; Gen14 current. Governance Contact locally binding on both arms; ACTIVE receipt absent; global ACTIVE unearned.

## v0.2.7.1 first result
- artifact `dc4683167124b70883a6940026f28575fcaf745b51d1f4975df298f6ca36c352`, first synchronous execution rc3.
- exact structured result `4a10e2fa70fe620ebcaed8d23163b48f2b565a4230831cbc34e771a9b0b585b5`; diagnosis `71898d70a9fcb7758eaeffd344761d5d1f1d92d02edc198a3896bcc765abb04a`.
- positive WMI `Win32_Process.Create` returned PID 23160; child alive after root exit; Toolhelp parent PID 39080 / `WmiPrvSE.exe`; any-Job=true; cleanup succeeded. This directly verifies service-mediated positive WMI lineage for the exact path.
- protected receipt valid: AppContainer+immediate Job verified, zero capabilities, no inherited handles, no timeout. Protected root returned raw1, so stage outcome was unclassified.
- non-creating protected diagnostic proved the HRESULT encoder defect: signed low16 masking on the same class-bind exception emits `0x20001501`, whereas `[uint32]` conversion collapses under Stop. No protected Create was invoked by that diagnostic.
- App Attempt Store: **202 blobs / 214 attempts / 293 events**, integrity `ok`.

## Repair boundary
After this successor is committed/pushed/fresh-clone verified, NEW v0.2.7.2 may change only the two WMI exception encoders from `[uint32]$_.Exception.HResult` to signed low16 masking while retaining existing stage prefixes. WMI class path/Create call, child command, success encoding, ReturnValue encoding, Toolhelp lineage/liveness/cleanup, protected primitive, non-network scope and claim ceiling remain unchanged.

`POSITIVE_WMI_SERVICE_MEDIATION != PROTECTED_WMI_CONTAINMENT`
`PROTECTED_CLASS_BIND_EXCEPTION != JOB_SPECIFIC_DENIAL`
`HRESULT_ENCODER_FAILURE != WMI_PATH_RESULT`
`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

Privacy projection: live DTS unchanged. Main source DTS `29dbf14c18a305089fbe0c0123dc425d388c2a3faba335325a82a56947ba67c6`; App source DTS `712b7554c14988501506fd8fc1a7894803befcccf87b93cb0ab6f919e3bfe52a`. Control DTS copies LF-normalized and local project roots placeholdered only.
