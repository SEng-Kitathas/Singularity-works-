# Control Currentness — Attempt Execution Idempotency Guard — 2026-09-09

Status: **CHECKPOINT CANDIDATE / SERVER EXECUTION RAIL QUALIFIED / ZERO PRODUCT OR SECURITY PROMOTION**

Predecessor control `07c0d657654d5f4f759dfa67bebadcea2a4d5626` / CHECKPOINT `7657e49a7d2db2c14e43f35afd9f2760268d38ceef7c02f8d5392b3b65552af9`, independently fresh-clone verified PASS 211. Main `e66c071fc25f8d08bfc7ebf0551948392d652f35`; Core semantic anchor `a7b4511734b1a1e507230308e75b31175aef4c4a`; App source `43aa7feac7e8a15828116bd700b644560714496d` unchanged.

## Qualification
App evidence `f0e49f29d6c55a03d5da16a57124340847586032aae3b96e73e41334d8db5ac2`; maintenance receipt `a41c2a5e8bacdb25c32e4bb7660d9b93d985e09be6964123a886512a60f0bbcc`; both exact captured/read back. Attempt Store after capture: **211 blobs / 225 attempts / 304 events**, integrity ok / WAL / FULL.

Current tested server `submitProjectExecution` rail:
- completed same-payload duplicate under one key returns the same job with `replayed=true`;
- reusing a key with a different command fails closed `IDEMPOTENCY_KEY_CONFLICT`;
- two in-flight same-payload duplicate probes failed closed `PROJECT_MUTATION_GUARD_BUSY` while originals remained the only jobs and later completed rc0;
- execution journal confirms earlier Forge-App Attempts already used idempotency keys.

The v0.2.7.2 duplicate race is therefore localized to use of keyless `runSync` for an immutable effectful first execution, not absence of an available server idempotency rail.

## Active execution law
Every immutable effectful first execution SHALL use `submitProjectExecution` with an `idempotency_key` deterministically bound to the immutable Attempt identity and with payload-defining command/cwd/mode/timeout parameters frozen. `runSync` SHALL NOT serve as that first-execution rail.

Claim ceiling: current server/project submission path only. This does not prove all restart/cross-host semantics and does not widen process-tree, network, product, Main/Core, or runtime authority.

## Next gate
After this successor is non-force published and independently fresh-clone verified, R5 may select/freeze/read/preserve a NEW causal-isolation or materially distinct broker/service process-tree discriminator. Its first effectful execution remains blocked until exact artifact/Attempt preservation and SHALL use the Attempt-bound idempotent submission rail.

`EFFECTFUL_FIRST_EXECUTION_REQUIRES_IDEMPOTENT_SUBMISSION`  
`RUNSYNC_WITHOUT_ATTEMPT_KEY_IS_NOT_A_FIRST_EXECUTION_RAIL`  
`EXECUTION_CONTROL_QUALIFICATION != SECURITY_AUTHORITY`
