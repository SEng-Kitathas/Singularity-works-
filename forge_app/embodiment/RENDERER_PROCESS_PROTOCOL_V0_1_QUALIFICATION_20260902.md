# Forge Renderer Process Protocol v0.1 — Qualification — 2026-09-02

Status: **READY_WITH_EVIDENCE for bounded snapshot-renderer crash-domain semantics with verified minimal fallback**.
Not a native-window/GPU/persistent-render-loop qualification.

## Attempt-0 preservation
Protocol, host, reference child renderer, crash worker and hostile tests were committed and pushed before first execution:
`f7ca9db68711a1f408b5cbeceb083b6fd121c5d2` — `forge-app: preserve renderer crash-domain protocol attempt zero`.

Exact source hashes:
- `forge_app/render/renderer_host.py` SHA `2306abf80fd1fb65d5794cb3eabc0540704b7cef3b132b6e05c99942be325e9d`.
- `forge_app/render/minimal_process_renderer.py` SHA `b84c19d434aff153fca394b3b049995a2da639bcc98f0db1e9da2335967d0707`.
- `forge_app/render/RENDERER_PROCESS_PROTOCOL_v0_1.md` SHA `82df28379d5abc3aafe9a2d4a5dd14a7292a38dcb4184889782f948ea8e3c967`.
- `forge_app/embodiment/test_renderer_process_protocol_v0_1.py` SHA `5f0e570fc2148db050598867894d898ea83b17a60d83b4fc4f58e5f273b530fa`.
- `forge_app/embodiment/renderer_crash_worker_v0_1.py` SHA `89f4719657879b27c923dc5c210108419be859712e5523e3d45d10c03b2f908f`.

## v0.1 protocol
The coordinator sends one canonical `ErgoLaunchModel` snapshot to a renderer child over UTF-8 JSON/stdin.

Request binds:
- protocol version;
- request ID;
- launch-model schema;
- exact SHA-256 over canonical model JSON bytes;
- exact canonical model JSON;
- requested tier;
- width for the text/reference renderer.

A successful renderer response must echo the exact request ID and exact model SHA. Any malformed response, protocol mismatch, request mismatch, model-hash mismatch, non-zero exit or timeout is rejected.

Fallback uses the already-built same launch model through the first-class in-process minimal renderer. The renderer receives no Attempt Store write capability in this protocol.

Renderer authority: `NONE`.

## Hostile test execution
Command:
`python -m unittest forge_app.embodiment.test_renderer_process_protocol_v0_1 -v`

Result: **5/5 PASS**.

Verified discriminators:
1. out-of-process minimal renderer output equals the in-process minimal reference **exactly**;
2. deliberate renderer process death falls back to the same model;
3. renderer process death leaves a real temporary durable Attempt Store byte/mmtime/count/integrity state unchanged;
4. malformed renderer output is rejected and falls back;
5. renderer response with wrong model SHA is rejected and falls back.

## Live-project kill evidence
A live render/fallback discriminator was then run against:
- the actual program Attempt Store;
- the actual `forge/app-shell-rd` source branch;
- the actual live `ErgoLaunchModel` derived from those facts.

### First live invocation scar
The first live child invocation died with exit code 1 from `ModuleNotFoundError: No module named 'forge_app'` because the direct file-path child inherited a cwd/PYTHONPATH that did not contain the source package.

Fallback still succeeded and durable/source state remained exact, but this run is classified only as **renderer launch/environment failure**, not deliberate process-kill evidence.

This scar is preserved; it was not upgraded by tone.

### Deliberate live renderer death
A second live child required no Forge imports: it read stdin and executed `os._exit(93)`.

Verified:
- renderer failure reason contains exact `renderer exited 93`;
- fallback used: true;
- fallback renderer: `forge-minimal-inprocess/0.1`;
- fallback launch model remained `POSTURE  READY`;
- model SHA echoed by host receipt: `64b14db4e3991f14f9d87afc39b1d85df1c7f1f6987aeee239c4dabe657e4173`;
- Attempt Store DB SHA before/after exact: `6b7551c410d3ba4f22ae1ab6c365fd136ab1308fcf65dd9500b4c0a6e6d9d14b`;
- Attempt Store DB mtime before/after exact: unchanged;
- source HEAD before/after exact: `f7ca9db68711a1f408b5cbeceb083b6fd121c5d2`;
- source status before/after: clean/unchanged.

## Earned law
**`RENDERER_PROCESS_DEATH != FORGE_STATE_DEATH`** is now embodied and verified for the bounded one-shot snapshot renderer path.

Additional bounded law:
**`RENDERER_ACK != MODEL_TRUTH`** — a renderer response is accepted only when it references the exact canonical model hash the coordinator supplied.

## Architectural consequence
Future native/Aero/GPU renderers should be workers behind a stable semantic/presentation boundary rather than owners of recovery/source/semantic truth. A renderer may die and be restarted/replaced/fallback without asking Forge to regenerate the underlying launch state.

## Toolchain observation
At this qualification point:
- Rust/Clang/Zig were not executable on PATH;
- `C:\Users\ancal\.cargo\bin\cargo.exe` and `rustc.exe` existed as zero-byte/non-executable placeholders and failed with WinError 193;
- CMake 4.4.2 was available.

No compiler/toolchain was installed merely to create motion. Backend/toolchain selection remains evidence-driven.

## Remaining seams
- persistent renderer process/window loop;
- native input/focus/accessibility/IME;
- GPU device-loss/recreation;
- software/native accelerated renderer comparison;
- window/compositor crash and restart;
- renderer watchdog/restart policy;
- interprocess transport beyond one-shot stdio;
- render-frame timing and backpressure;
- semantic-canvas scene transport;
- Aero/material tiers;
- native packaging/distribution;
- deliberate renderer crash during active interaction rather than snapshot handoff.

## Next discriminator
Build a persistent renderer-host state machine with explicit handshake/heartbeat/frame-ack/restart semantics, while keeping `ErgoLaunchModel` and durable state in the coordinator. Only after that boundary is stable should a native backend/toolchain be installed or selected.
