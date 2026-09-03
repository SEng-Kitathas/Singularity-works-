# Persistent Renderer Host + Session Health v0.1 — Qualification — 2026-09-03

Status: **READY_WITH_EVIDENCE for bounded persistent renderer generation/restart semantics and checkpoint runtime-health leasing**.
Not yet a native-window/GPU/input/session-process qualification.

## Attempt-0 preservation
Persistent renderer protocol, host, reference worker, hostile worker/tests, and session-health lease/tests were committed and pushed before first execution:

`4a02ab6` — `forge-app: preserve persistent renderer host and session lease attempt zero`.

Attempt-0 source hashes:
- `forge_app/render/PERSISTENT_RENDERER_PROTOCOL_v0_1.md` SHA `1406f89e0b5bc64552be96702d12806f95feed13eb2a6e693863122714ae439d`.
- `forge_app/render/persistent_process_renderer.py` SHA `7062cb6e080605c1f49324a7f8f7851521de4f4efa7a38f3afb130fa1df5c233`.
- `forge_app/recovery/session_health.py` SHA `46b9b2723bbffb9632c02e7bffb166d4eee517d18c272a90262c764f9b12bb6b`.
- persistent-host hostile test SHA `d652b380a3394ba8c8dbfd47cdc8ca791250e98bd43b7bf810148fd082b69545`.
- session-health test SHA `7b23f1ceedea1698e0b24309dd38b5d25f144f9e94fce68980be740df15de47f`.

## Persistent renderer protocol
Coordinator owns renderer generation identity and monotonic frame/heartbeat sequence.

Handshake:
`hello -> hello_ack` with exact protocol + generation ID.

Heartbeat:
`heartbeat(seq) -> heartbeat_ack(seq)` with exact generation.

Frame:
`frame(generation, frame_seq, model_sha256, canonical_model_json) -> frame_ack` with exact generation, frame sequence, and model hash.

Failure or mismatch drops the worker generation and renders the current frame through the already-qualified same-model minimal fallback. A later frame starts a new renderer generation.

Renderer authority: `NONE`.

## Session-health lease
A resumed checkpoint receives an immutable `resume_id` through `SessionHealthLease`.

The lease can promote a checkpoint to STABLE only when:
- elapsed healthy session time reaches the checkpoint policy threshold;
- meaningful-operation count reaches the policy threshold;
- the lease still matches the latest resume generation.

Renderer heartbeat does not count as meaningful operator/runtime work.

Session crash association uses the exact checkpoint + resume ID and elapsed time. A stale lease cannot promote or crash-mark a newer resumed generation.

## First execution result
Initial persistent-host + session-health run: **10/10 behavioral tests PASS**.

However the crash/restart path emitted Python `ResourceWarning` messages for unclosed subprocess stdin/stdout/stderr pipe objects.

Classification:
**behavioral pass, lifecycle-hygiene failure**. The host was not qualified from this run.

Execution scar:
`BEHAVIOR_PASS != PROCESS_LIFECYCLE_HYGIENE_PASS`.

## Cleanup repair
Descendant repair preserved before hygiene rerun:

`146f77ab5a590754bb2c536de490b98c30ef6f0c` — `forge-app: close persistent renderer generation pipes deterministically`.

Current persistent host SHA:
`ac690fa5d092cca7199ea93cb5c26a675d94325f94af69abbef30f1a13e9e951`.

Repair behavior:
- terminate/kill renderer if still alive;
- allow stdout reader thread to observe EOF;
- join reader thread boundedly;
- close stdin/stdout/stderr pipe objects deterministically for both normal and crash exits.

## Hygiene rerun
Command used `-W error::ResourceWarning` so leaked process resources could not remain advisory.

Result: **10/10 PASS with ResourceWarning promoted to error**.

Verified persistent-host behaviors:
1. handshake + repeated heartbeat remain on one renderer generation;
2. persistent minimal frame output equals the in-process minimal reference exactly;
3. first renderer generation may crash during frame handling, current frame falls back, and next frame automatically starts a new generation;
4. host-level frame sequence remains monotonic across renderer restart;
5. wrong/stale generation acknowledgement is rejected and falls back;
6. renderer authority remains NONE.

Verified session-health behaviors:
1. healthy elapsed time alone cannot promote STABLE without meaningful operations;
2. meaningful operations alone cannot promote STABLE before healthy-time threshold;
3. elapsed health + meaningful operations promote STABLE;
4. explicit LKG promotion succeeds only after stability is earned;
5. early session crash associates the resumed checkpoint;
6. two early crashes across distinct resume generations quarantine the risky checkpoint and recovery falls back to older LKG;
7. stale session lease cannot promote after a newer resume generation starts.

## Full stack regression
After cleanup repair, all prior App recovery/Ergo/renderer/checkpoint tests plus persistent host/session health were run with `ResourceWarning` promoted to error.

Result: **42/42 PASS** in 2.449 seconds.

Coverage groups:
- Attempt Store v0.1;
- Zombie v0.2;
- Ergo Recovery Observer v0.1;
- Ergo Launch Model v0.1;
- one-shot Renderer Process Protocol v0.1;
- Resume Checkpoint v0.1;
- Persistent Renderer Host v0.1;
- Session Health v0.1.

## Earned laws
- `STALE_RENDERER_GENERATION_ACK != CURRENT_FRAME_ACK`.
- `RENDERER_HEARTBEAT != SESSION_STABILITY`.
- `SESSION_STABILITY_REQUIRES_TIME_AND_MEANINGFUL_WORK`.
- `STALE_SESSION_LEASE != CURRENT_RESUME_HEALTH`.
- `BEHAVIOR_PASS != PROCESS_LIFECYCLE_HYGIENE_PASS`.
- Existing `RENDERER_PROCESS_DEATH != FORGE_STATE_DEATH` remains active and strengthened by persistent restart evidence.

## Current bounded architecture
`Attempt Store -> Resume Checkpoint generations -> SessionHealthLease -> Ergo recovery selection`

and independently:

`ErgoLaunchModel -> PersistentRendererHost -> renderer generation(s) -> same-model minimal fallback`.

Renderer liveness does not change checkpoint reputation by itself. Session health does.

## Cross-strand boundary
This is App-owned embodiment behavior. Checkpoint payloads reference Core interface/currentness/snapshot identity but do not define Core semantics. Main/Core remains canonical for what Forge means; App owns how a running operator session survives and resumes.

## Remaining seams
- actual session coordinator process death rather than method-level crash receipt;
- renderer death during simultaneous input/focus/IME activity;
- heartbeat watchdog running independently rather than request/response calls;
- frame backpressure/pacing and stale in-flight response handling;
- native window/process handle ownership;
- GPU device loss without process death;
- checkpoint recovery surfaced through Ergo UI;
- first live VERIFIED checkpoint and later actual resumed-session STABLE/LKG promotion;
- source/editor pending-transaction reconstruction;
- semantic snapshot restoration through a qualified Core interface.

## Next cut
Create the first real App checkpoint as VERIFIED only, expose selected checkpoint status in Ergo recovery presentation, and then run a real resumed App session long enough to earn STABLE/LKG without synthetic promotion.
