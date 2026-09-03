# Forge Renderer Process Protocol v0.1

Status: first crash-domain embodiment contract. Renderer backend/language remains provisional.

## Purpose
Keep renderer failure outside durable Forge state and outside recovery truth.

`ErgoRecoverySummary -> ErgoLaunchModel -> canonical model bytes/hash -> renderer process`

The renderer receives presentation facts. It does not read/write the Attempt Store, source repository, or semantic field directly.

## v0.1 snapshot request
Transport: UTF-8 JSON over child stdin/stdout for the first discriminator.

Request fields:
- `protocol = forge-render-request/0.1`;
- `request_id`;
- `model_schema`;
- `model_sha256` over exact canonical model JSON bytes;
- `model_json` exact canonical JSON string;
- `tier`;
- `width` for text/reference presentation.

Successful response fields:
- `protocol = forge-render-response/0.1`;
- same `request_id`;
- same `model_sha256`;
- renderer identity;
- tier;
- payload kind;
- rendered payload for snapshot/reference renderers.

The coordinator verifies request identity + model hash before accepting a response.

## Crash/failure rule
If the renderer:
- exits non-zero;
- times out;
- returns malformed JSON;
- returns a wrong request ID;
- returns a wrong model hash;

then the response is rejected and the coordinator may render the same already-built model with the first-class minimal fallback.

The renderer must never be asked to reconstruct recovery truth independently.

## Authority
Renderer authority: **NONE**.
Presentation state never promotes source/recovery/semantic truth.

## Durable-state boundary
The renderer process receives no Attempt Store write capability in this protocol. Renderer death must not alter the store or source tree.

Locked law:
**`RENDERER_PROCESS_DEATH != FORGE_STATE_DEATH`.**

## v0.1 limitations
- one-shot snapshot process rather than persistent window/render loop;
- minimal fallback payload is text;
- no input/focus/window protocol yet;
- no GPU/device-loss semantics yet;
- no shared-memory scene transport yet;
- no native-window embedding yet.

These are deliberate. v0.1 exists to prove the failure boundary and semantic handoff before backend lock-in.
