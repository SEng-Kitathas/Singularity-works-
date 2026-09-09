# Attempt Execution Idempotency Guard Qualification — 2026-09-09

Status: **VERIFIED BOUNDED SERVER EXECUTION RAIL / ZERO PRODUCT OR SECURITY PROMOTION**

## Trigger
v0.2.7.2 exposed a real orchestration failure: two workers executed one immutable Attempt about 2.61 seconds apart because both used the synchronous `runSync` command plane, which has no Attempt-bound idempotency key.

The duplicate-execution evidence was corrected append-only and checkpointed at control `07c0d657654d5f4f759dfa67bebadcea2a4d5626` / CHECKPOINT `7657e49a7d2db2c14e43f35afd9f2760268d38ceef7c02f8d5392b3b65552af9`, fresh-clone verifier PASS 211.

## Qualified replacement rail
Use server `submitProjectExecution` for every future **effectful first execution**, with `idempotency_key` deterministically bound to the immutable Attempt identity and with the complete execution payload held fixed.

`runSync` remains valid for read-only/currentness/diagnostic work where duplicate process launch has no consequence, but SHALL NOT be used as the first-execution rail for an immutable effectful Attempt.

## Pressure results
### Completed duplicate
Key `guard-probe-attempt-idempotency-20260909-v1` produced job `job-a0682dc18715`. A same-payload resubmission returned that same job with `replayed=true`. Reusing the same key with a different command failed closed as `IDEMPOTENCY_KEY_CONFLICT` and named the existing job; the different payload did not launch.

### In-flight duplicate — v2
Key `guard-probe-attempt-idempotency-20260909-v2-running` produced job `job-d5dcaf349f3e`. While that harmless 10-second job was still running, a same-payload resubmission failed closed as `PROJECT_MUTATION_GUARD_BUSY`; no second job appeared. After completion, the same key replayed the exact original job with `replayed=true`.

### In-flight duplicate — v3
Key `guard-probe-attempt-idempotency-20260909-v3-inflight` produced job `job-2800e7eea40e`. While that harmless 20-second job was still running, a same-payload resubmission again failed closed as `PROJECT_MUTATION_GUARD_BUSY`; the original completed rc0 and no duplicate job was created.

The execution journal after the probes showed 0 queued / 0 running and one job for each probe key.

## Historical consistency
The execution journal also shows that several earlier Forge-App security/diagnostic executions already used `submitProjectExecution` with stable idempotency keys. The v0.2.7.2 race was therefore a regression to a less-governed synchronous plane, not proof that Forge lacked an available idempotent execution primitive.

## Current law
For immutable effectful Attempts:
1. artifact bytes and Attempt identity are preserved first;
2. durable control/currentness gate is satisfied;
3. execution uses `submitProjectExecution` only;
4. `idempotency_key` is deterministically bound to the immutable Attempt identity;
5. command/cwd/mode/timeout and other payload-defining execution parameters are frozen before submission;
6. an in-flight duplicate must fail closed or resolve to the same job; a completed duplicate must replay the same job; a payload mismatch under the same key must conflict;
7. stdout/stderr/result are preserved before interpretation;
8. no same-Attempt execution through `runSync` is permitted.

## Claim ceiling
Qualified only for the currently observed server-side `submitProjectExecution` path on this project/runtime. This does not prove all restart persistence, all cross-host systems, product runtime authority, or any security discriminator outcome. The project mutation guard contributed to in-flight fail-closed behavior; this note does not relabel that layer as Attempt-key idempotency.

`EFFECTFUL_FIRST_EXECUTION_REQUIRES_IDEMPOTENT_SUBMISSION`  
`RUNSYNC_WITHOUT_ATTEMPT_KEY_IS_NOT_A_FIRST_EXECUTION_RAIL`  
`IDEMPOTENCY_KEY_CONFLICT_FAILS_CLOSED`  
`INFLIGHT_DUPLICATE_FAILS_CLOSED`  
`EXECUTION_CONTROL_QUALIFICATION != SECURITY_AUTHORITY`
