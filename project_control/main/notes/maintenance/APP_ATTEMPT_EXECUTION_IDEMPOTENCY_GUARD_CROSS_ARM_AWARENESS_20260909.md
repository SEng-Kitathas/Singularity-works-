# App Attempt Execution Idempotency Guard — Cross-Arm Awareness — 2026-09-09

Status: **EXECUTION-CONTROL QUALIFICATION / ZERO MAIN-CORE PROMOTION**

App qualified a bounded server-side first-execution rail after the v0.2.7.2 duplicate-execution race. Evidence `f0e49f29d6c55a03d5da16a57124340847586032aae3b96e73e41334d8db5ac2`; maintenance receipt `a41c2a5e8bacdb25c32e4bb7660d9b93d985e09be6964123a886512a60f0bbcc`; both captured/read back in Attempt Store. Store after capture: **211 blobs / 225 attempts / 304 events**, integrity ok / WAL / FULL.

Bounded verified behavior on current server `submitProjectExecution` path:
- completed same-payload duplicate with same idempotency key resolves to the same job with `replayed=true`;
- same key with a different command fails closed `IDEMPOTENCY_KEY_CONFLICT`;
- same-payload duplicate submitted while harmless jobs were still running failed closed `PROJECT_MUTATION_GUARD_BUSY`, with no second job created;
- historical execution journal shows earlier Forge-App Attempts already used idempotency keys; v0.2.7.2 raced because effectful first execution used `runSync`, which has no such key.

Current App law: every immutable effectful first execution must use `submitProjectExecution` with an idempotency key deterministically bound to the immutable Attempt identity; `runSync` is forbidden as that first-execution rail. This qualification is server-execution-control evidence only and does not widen Main/Core, security, network, product, or runtime authority.

`EFFECTFUL_FIRST_EXECUTION_REQUIRES_IDEMPOTENT_SUBMISSION`  
`RUNSYNC_WITHOUT_ATTEMPT_KEY_IS_NOT_A_FIRST_EXECUTION_RAIL`  
`EXECUTION_CONTROL_QUALIFICATION != MAIN_CORE_PROMOTION`
