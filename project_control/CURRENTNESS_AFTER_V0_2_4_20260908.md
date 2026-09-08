# Control Currentness — Post-v0.2.4 HARNESS_INVALID Fixed Point — 2026-09-08

Status: **CHECKPOINT CANDIDATE / NO PRODUCT PROMOTION**

This successor advances durable cross-thread control from `f59a32946cea1af64e427a4d9db64a7075f691dd` without rewriting sealed rollover history.

## Live refs / semantic anchors
- public Main: `e66c071fc25f8d08bfc7ebf0551948392d652f35`
- semantic Core qualification anchor: `a7b4511734b1a1e507230308e75b31175aef4c4a`
- App source: `43aa7feac7e8a15828116bd700b644560714496d`
- predecessor durable control: `f59a32946cea1af64e427a4d9db64a7075f691dd`
- predecessor CHECKPOINT: `64f1804e9d6ec64b1638cacbf25bd8963ad967958a1f2847e4d3a352c887a589`
- recovery ingress Gen14: `checkpoint-app-live-0014-43aa7feac7e8`, MATCH/NORMAL/READY, Core IDs null.

## Governance Contact target-local currentness
Both local development-arm targets contain exact locator SHA `380059a4e8204c35f82b3a232d45f962bb20038eec3d9eecb44f4411809346bd` and exact activation-token SHA `b5a2e35f300c6f72d93fc80b877ef0478a3628442b705e50f6893cbceafb5094`. `GOVERNANCE_CONTACT_V1_0_ACTIVE_RECEIPT.json` is absent on both targets. Therefore both targets resolve `GOVERNANCE_CONTACT_LOCALLY_BINDING_ADDITIVE_PROCESS_DOCTRINE`; global ACTIVE remains forbidden/unearned.

`CURRENT_LOCAL_TOKEN_VALID != GLOBAL_ACTIVE`.

## Current App security lineage
- rollover-selected v0.2.1.3 result `86833629ebd032f56dbc900145d40771dc38862fc1416c0ddfe88fd4e35af022` remains `NOT_ADMITTED / SUPERVISION_LOST`; same Attempt is not replayable.
- descendant DNS-helper loopback bounded admission `63e5a830b18bb8d6c5f291468e7a6b9ed491ed580f37a0a7aceb6e584dc79225`.
- descendant proxy/environment loopback bounded admission `59623224fd455cb7590d59682330740920a51a7fc2f7ab2217071d72a65227f3`, result `c60ee5e079b0eed9c99e7bd86142560a1d46ace1bd2a372283d3980be710e56c`.
- normal-descendant Job-close v0.2.4 artifact `b3e8470932b446edc2fdcdf6f6151b8d3ffea3b2962b56114bb3423c627f52cf` executed once; first result `c6366904038e45cb0ec9712b9aeb34f016220786e731bdfb7a654097e2601710` is `HARNESS_INVALID / POSITIVE_CONTROL_PIPE_INHERITANCE_TIMEOUT`; protected phase was never reached. No Job-containment or breakaway claim is earned.
- Attempt Store current readback: **151 blobs / 155 attempts / 234 events**, integrity `ok`, WAL/FULL.

## Next execution gate
The next valid specimen is a NEW v0.2.4.1 Attempt changing only unprotected positive-control stdio from captured pipes to DEVNULL. Root/child command, 30-second sleep, protected phase, `cwd=powershell.parent`, PID-liveness probe, cleanup, non-network scope and claim ceiling remain unchanged. Original v0.2.4 Attempt/result remain immutable.

No v0.2.4.1 execution is authorized by this document until this control successor is committed directly above live `pcmmad/project-control`, non-force pushed, and independently fresh-clone/readback verified.

`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`
`HARNESS_INVALID != JOB_CONTAINMENT_RESULT`
`NORMAL_DESCENDANT_JOB_CLOSE_TERMINATION != CREATE_BREAKAWAY_FROM_JOB_DENIAL`
`LOCAL_LOOPBACK_RESULT != GENERAL_NETWORK_AUTHORITY`

## Privacy projection note
The live Main/App Design Thread Stream source artifacts are not rewritten. Their live source SHAs are Main `859a653df06382f1a4933da405bd174779929f480ced4d13035aa56c25270a24` and App `b95f27368e7d6c82b4f5032d7bdc44b05588b9ad3c640b308740d61947d66c95`. The control-package DTS copies replace local absolute project-root strings with explicit placeholders only, so publication does not leak workstation paths. `CONTROL_PRIVACY_PROJECTION != SOURCE_MUTATION`.
