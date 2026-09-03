from __future__ import annotations

"""Dependency-free hostile worker for persistent renderer protocol tests."""

import argparse
import json
import os
from pathlib import Path
import sys

PROTOCOL = "forge-persistent-render/0.1"


def emit(value: dict) -> None:
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--crash-first-frame-sentinel", default=None)
    parser.add_argument("--wrong-generation", action="store_true")
    args = parser.parse_args()

    generation_id: str | None = None
    renderer_id = "forge-hostile-test-renderer/0.1"
    for raw in sys.stdin:
        message = json.loads(raw)
        if message.get("protocol") != PROTOCOL:
            return 4
        msg_type = message.get("type")
        if msg_type == "hello":
            generation_id = str(message.get("generation_id") or "")
            emit(
                {
                    "protocol": PROTOCOL,
                    "type": "hello_ack",
                    "generation_id": "stale-generation" if args.wrong_generation else generation_id,
                    "renderer_id": renderer_id,
                    "capabilities": ["test"],
                }
            )
        elif msg_type == "heartbeat":
            emit(
                {
                    "protocol": PROTOCOL,
                    "type": "heartbeat_ack",
                    "generation_id": "stale-generation" if args.wrong_generation else generation_id,
                    "renderer_id": renderer_id,
                    "heartbeat_seq": int(message["heartbeat_seq"]),
                }
            )
        elif msg_type == "frame":
            if args.crash_first_frame_sentinel:
                sentinel = Path(args.crash_first_frame_sentinel)
                if not sentinel.exists():
                    sentinel.parent.mkdir(parents=True, exist_ok=True)
                    sentinel.write_text("first renderer generation crashed\n", encoding="utf-8")
                    os._exit(94)
            emit(
                {
                    "protocol": PROTOCOL,
                    "type": "frame_ack",
                    "generation_id": "stale-generation" if args.wrong_generation else generation_id,
                    "frame_seq": int(message["frame_seq"]),
                    "model_sha256": message["model_sha256"],
                    "renderer_id": renderer_id,
                    "tier": "test",
                    "payload_kind": "text/plain",
                    "payload": "HOSTILE-TEST-RENDERED\n",
                }
            )
        else:
            return 8
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
