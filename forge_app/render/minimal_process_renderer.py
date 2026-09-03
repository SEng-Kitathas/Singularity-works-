from __future__ import annotations

"""Reference out-of-process minimal renderer for protocol v0.1."""

import json
import sys

from forge_app.ergo.launch_model import ErgoLaunchModel, LaunchFact, LaunchMode, RecentAttempt, render_minimal_text
from forge_app.render.renderer_host import REQUEST_PROTOCOL, RESPONSE_PROTOCOL


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


def main() -> int:
    raw = sys.stdin.read()
    request = json.loads(raw)
    if request.get("protocol") != REQUEST_PROTOCOL:
        return 4
    model = _model_from_dict(json.loads(request["model_json"]))
    payload = render_minimal_text(model, width=int(request.get("width", 80)))
    response = {
        "protocol": RESPONSE_PROTOCOL,
        "request_id": request["request_id"],
        "model_sha256": request["model_sha256"],
        "renderer_id": "forge-minimal-process/0.1",
        "tier": "minimal",
        "payload_kind": "text/plain",
        "payload": payload,
    }
    sys.stdout.write(json.dumps(response, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
