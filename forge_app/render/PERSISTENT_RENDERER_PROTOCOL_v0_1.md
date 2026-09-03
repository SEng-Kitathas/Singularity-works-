# Forge Persistent Renderer Protocol v0.1

Status: Attempt-0 protocol candidate.

## Purpose
Extend the qualified one-shot renderer crash domain into a persistent renderer worker without letting renderer liveness become application/recovery truth.

## Ownership
Coordinator/App owns:
- canonical `ErgoLaunchModel`;
- renderer generation identity;
- frame sequence identity;
- restart/fallback policy;
- durable state and recovery/checkpoint reputation.

Renderer worker owns only presentation execution for the supplied model snapshot.
Renderer authority: `NONE`.

## Transport
UTF-8 JSON Lines over stdin/stdout for v0.1.
One JSON object per line. No binary/shared-memory transport yet.

## Generation
Every worker process is assigned a unique immutable `generation_id` by the coordinator.
All renderer responses must echo that generation.

A response from a prior/dead generation is stale and rejected even if frame/model hashes otherwise match.

Locked law:
`STALE_RENDERER_GENERATION_ACK != CURRENT_FRAME_ACK`.

## Handshake
Coordinator -> renderer:
- `type = hello`
- `protocol = forge-persistent-render/0.1`
- `generation_id`

Renderer -> coordinator:
- `type = hello_ack`
- same protocol;
- same generation;
- `renderer_id`;
- bounded capability list.

No frame traffic is accepted before handshake succeeds.

## Heartbeat
Coordinator -> renderer:
- `type = heartbeat`
- generation;
- monotonically increasing heartbeat sequence.

Renderer -> coordinator:
- `type = heartbeat_ack`
- same generation and sequence.

Heartbeat proves only renderer-process liveness. It does not promote a resume checkpoint to STABLE.

## Frame
Coordinator -> renderer:
- `type = frame`
- generation;
- monotonically increasing `frame_seq`;
- canonical model schema;
- exact model SHA-256;
- exact canonical model JSON;
- requested tier/width.

Renderer -> coordinator:
- `type = frame_ack`
- same generation;
- same frame sequence;
- same model SHA;
- renderer identity;
- tier;
- payload kind;
- v0.1 string payload.

Any mismatch is rejected.

## Failure/restart
Failure includes:
- non-zero renderer exit;
- EOF;
- handshake timeout/mismatch;
- heartbeat timeout/mismatch;
- malformed JSON;
- stale/wrong generation;
- frame-sequence mismatch;
- model-hash mismatch.

On failure:
1. current renderer generation is marked dead locally;
2. current frame may fall back to the same-model minimal renderer;
3. durable state/checkpoint bytes are untouched;
4. coordinator may start a new renderer generation for later frames.

Renderer failure alone does **not** append `checkpoint_crash_associated`.
Only failure of the resumed session/coordinator should affect checkpoint reputation.

## Restart identity
Each restart receives a new generation ID. Frame sequence may continue monotonically at the host level.
A late response from the old worker cannot be accepted because generation mismatches.

## v0.1 limitations
- one renderer worker at a time;
- line-oriented JSON;
- text/reference payloads only;
- no native window handle ownership transfer;
- no device-loss callback beyond process/protocol failure;
- no input/focus/IME protocol;
- no frame pacing/backpressure beyond one request/ack at a time.
