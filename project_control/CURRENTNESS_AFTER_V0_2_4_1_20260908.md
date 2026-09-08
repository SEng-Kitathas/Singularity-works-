# Control Currentness — Post-v0.2.4.1 Bounded Job-Close Qualification — 2026-09-08

Status: **CHECKPOINT CANDIDATE / ZERO PRODUCT OR CORE PROMOTION**

This generation advances durable control from `d76299e728b5026df87c39c17ad9d723f759ce5f` only after v0.2.4.1 current-control execution, exact result preservation, bounded admission, concurrent-sibling reconciliation, and Live Shadow repair.

## Live refs / semantic anchors
- public Main: `e66c071fc25f8d08bfc7ebf0551948392d652f35`
- semantic Core qualification anchor: `a7b4511734b1a1e507230308e75b31175aef4c4a`
- App source: `43aa7feac7e8a15828116bd700b644560714496d`
- predecessor durable control: `d76299e728b5026df87c39c17ad9d723f759ce5f`
- predecessor CHECKPOINT: `1f6e82c8515981b45667899f5f1eb120247ee31805a7e401f277643c41b72c05`
- recovery ingress: `checkpoint-app-live-0014-43aa7feac7e8`, MATCH/NORMAL/READY, Core IDs null.

## Governance Contact
Both local development-arm targets retain exact locator SHA `380059a4e8204c35f82b3a232d45f962bb20038eec3d9eecb44f4411809346bd` and exact token SHA `b5a2e35f300c6f72d93fc80b877ef0478a3628442b705e50f6893cbceafb5094`. ACTIVE receipt is absent on both targets. Local binding is valid; global ACTIVE remains unearned.

## v0.2.4.1 admitted current lineage
- immutable v0.2.4 HARNESS_INVALID result: `c6366904038e45cb0ec9712b9aeb34f016220786e731bdfb7a654097e2601710`; protected phase never reached.
- current-control stdio-repair artifact: `81d8d42b2280e249f13d4a5c30f588a1784d9c6bc0c60e4fee0279f611ad53c8`; exact first execution `job-c4852891e585`, executor rc0.
- exact stdout `28860b0febb229c61a87003257438d33ff1de606a18d1f741cfe8166e2dca340`, 2,746 bytes; exact stderr empty SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- exact structured first result `709ba15edfbdc640c313f236daeb8c8abe889a64e03cc8feb50aedcade2ac173`, 2,882 bytes, mirrored as `app/evidence/egress_wider_v0_2_4_1_normal_descendant_job_close_first_result_20260908.json`.
- bounded admission `518c15f8464ea69487a4db5b7d23605b4d18983a684c1819c3d03792dbdf6085`.
- positive normal descendant remained alive after unprotected root exit and cleanup was confirmed.
- protected AppContainer+immediate Job/zero-capability/no inherited-handle/no-timeout receipt valid; returned descendant PID was absent after the primitive returned following kill-on-close Job closure.
- App Attempt Store current readback: **157 blobs / 162 attempts / 241 events**, integrity `ok`.

Qualified only: **normal-descendant Job-close termination for the exact `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` path**. Explicit `CREATE_BREAKAWAY_FROM_JOB`, breakaway flags, service/WMI/COM/RPC/WSL escape, network egress, production launch integration, and `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` remain unearned.

## Concurrent sibling classification
- stale-control DEVNULL sibling `1faa37259781fd0b3f09b50855a27b2000c72807396701a31cbdd7d65c41194e` is preserved/unexecuted under predecessor control; it is not current execution lineage.
- currentness-only sibling `541d471035e6667be61e281e4f08078e7a22f10165cd38ee40982548f7ecee53` is now preserved in Attempt Store as `attempt-egress-wider-v0-2-4-1-1-normal-descendant-job-close-lifecycle-currentness-repair-first`, metadata `behavioral_delta_from_parent=NONE`, executed=false. No execution job exists. It remains a separate unexecuted sibling and does not supersede the admitted `81d8d42b... -> 709ba15e... -> 518c15f8...` lineage.

`PRESERVED_SIBLING != CURRENT_EXECUTION_LINEAGE`
`FILE_PRESENCE != EXECUTION`

## Privacy projection
Live DTS artifacts remain untouched. Current source SHAs at snapshot are Main `59e3a181b67351fb1adece8ab200aa595f4355a8858a440ddd71f89e9b4b2154` and App `8743cf5f0a0415e739246c5ec13f941de58248c50997c074f4784b36f5e2482b`. Control DTS copies normalize line endings and replace workstation-local project roots with explicit placeholders only.

## Next gate
After this successor is committed directly above live control, non-force pushed, and independently fresh-clone verified, App may design a **NEW non-network explicit `CREATE_BREAKAWAY_FROM_JOB` discriminator**. Neither preserved v0.2.4.1 sibling is authorized as a substitute execution. No network-bearing breakaway test is authorized before the lifecycle prerequisite.

`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`
`NORMAL_DESCENDANT_JOB_CLOSE_TERMINATION != CREATE_BREAKAWAY_FROM_JOB_DENIAL`
`NON_NETWORK_LIFECYCLE_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`
