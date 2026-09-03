from __future__ import annotations

"""Reference persistent renderer worker for protocol v0.1."""

import json
import sys

from forge_app.ergo.launch_model import ErgoLaunchModel, LaunchFact, LaunchMode, RecentAttempt, render_minimal_text
from forge_app.render.persistent_host import PROTOCOL


def _model_from_dict(data: dict) -> ErgoLaunchModel:
    return ErgoLaunchModel(
        schema=data["schema"],
        title=data["title"],
        subtitle=data["subtitle"],
        posture=data["posture"],
        posture_reason=data["posture_reason"],
        observer_authority=data["observer_authority"],
        facts=tuple(LaunchFact(**item) for item in data["facts"]),
        modes=tuple(LaunchMode(**item) for item in data["modes"]),
        recent_attempts=tuple(RecentAttempt(**item) for item in data["recent_attempts"]),
        reasons=tuple(data["reasons"]),
    )


def emit(value: dict) -> None:
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> int:
    generation_id: str | None = None
    renderer_id = "forge-persistent-minimal/0.1"
    for raw in sys.stdin:
        message = json.loads(raw)
        if message.get("protocol") != PROTOCOL:
            return 4
        msg_type = message.get("type")
        if msg_type == "hello":
            generation_id = str(message.get("generation_id") or "")
            if not generation_id:
                return 5
            emit(
                {
                    "protocol": PROTOCOL,
                    "type": "hello_ack",
                    "generation_id": generation_id,
                    "renderer_id": renderer_id,
                    "capabilities": ["heartbeat", "frame", "text/plain", "minimal"],
                }
            )
        elif msg_type == "heartbeat":
            if message.get("generation_id") != generation_id:
                return 6
            emit(
                {
                    "protocol": PROTOCOL,
                    "type": "heartbeat_ack",
                    "generation_id": generation_id,
                    "renderer_id": renderer_id,
                    "heartbeat_seq": int(message["heartbeat_seq"]),
                }
            )
        elif msg_type == "frame":
            if message.get("generation_id") != generation_id:
                return 7
            model = _model_from_dict(json.loads(message["model_json"]))
            payload = render_minimal_text(model, width=int(message.get("width", 80)))
            emit(
                {
                    "protocol": PROTOCOL,
                    "type": "frame_ack",
                    "generation_id": generation_id,
                    "frame_seq": int(message["frame_seq"]),
                    "model_sha256": message["model_sha256"],
                    "renderer_id": renderer_id,
                    "tier": "minimal",
                    "payload_kind": "text/plain",
                    "payload": payload,
                }
            )
        else:
            return 8
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
