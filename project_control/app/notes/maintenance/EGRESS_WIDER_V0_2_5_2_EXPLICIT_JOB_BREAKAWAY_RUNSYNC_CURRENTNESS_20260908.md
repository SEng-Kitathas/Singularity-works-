# Wider Egress v0.2.5.2 — Explicit Job Breakaway — runSync Currentness Sibling

Date: 2026-09-08 UTC
Status: **FROZEN CANDIDATE / NOT EXECUTED**
Parent execution-plane record: `f32909d4c430a33e2eb3c80a4ea8aec0c6d6b0a6c1f73b3be3f34b2f70399f88`.
Current durable control: `56fb5b70ffee7c58d60c34118338d12c30313e46` / CHECKPOINT `2a4ce4baf905bd3698d228cbb9a0575dcc78efa577593a69de6118b9fa49cec6`.
Artifact: `state/attempt_artifacts/EGRESS_WIDER_V0_2_5_2_EXPLICIT_JOB_BREAKAWAY_RUNSYNC_CURRENTNESS_20260908.py`
Artifact SHA: `d7f444287c6903fab28b58e9423cfc99ec53dced03457e964348eb587c1f2602`.

The current synchronous `runSync.command` plane was remeasured after control closure: outer Job `0x1800`, `BREAKAWAY_OK=true`, `SILENT_BREAKAWAY_OK=true`, `KILL_ON_JOB_CLOSE=false`. This is execution-plane currentness only; no breakaway result is inherited.

Compared with immutable v0.2.5.1, this sibling changes only version/currentness/lineage/schema/explanatory text and expected control bindings. The helper source `77927e4f...`, helper DLL `8019c83a...`, all executable discriminator logic, root commands, outer-Job gate, normal-child baseline proof, explicit `CREATE_BREAKAWAY_FROM_JOB` call, decoding, cleanup, PASS/FAIL criteria, non-network scope and claim ceiling are unchanged.

Execution plane for the first run SHALL be synchronous `runSync.command`, not the async worker plane that invalidated v0.2.5.1. The artifact rechecks the live outer Job itself and will abort if silent-breakaway compatibility is absent.

`CURRENTNESS_REBIND != BEHAVIORAL_CHANGE`
`EXECUTION_PLANE_CURRENTNESS != BREAKAWAY_RESULT`
`V0_2_5_2 != REPLAY_OF_V0_2_5_1`
