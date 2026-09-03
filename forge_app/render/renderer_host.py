from __future__ import annotations

"""Renderer process host v0.1.

A renderer is an untrusted presentation worker. The host sends one canonical launch
model snapshot and verifies that any response refers to exactly that snapshot.
Renderer failure falls back to the qualified minimal renderer over the same model.
"""

from dataclasses import dataclass, asdict
import hashlib
import json
import subprocess
from typing import Any, Sequence
from uuid import uuid4

from forge_app.ergo.launch_model import ErgoLaunchModel, render_minimal_text

REQUEST_PROTOCOL = "forge-render-request/0.1"
RESPONSE_PROTOCOL = "forge-render-response/0.1"


class RendererProtocolError(RuntimeError):
    pass


@dataclass(frozen=True)
class RenderReceipt:
    request_id: str
    model_sha256: str
    renderer_id: str
    tier: str
    payload_kind: str
    payload: str
    renderer_failed: bool
    fallback_used: bool
    failure_reason: str | None
    authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _model_identity(model: ErgoLaunchModel) -> tuple[str, str]:
    model_json = model.canonical_json()
    model_sha256 = hashlib.sha256(model_json.encode("utf-8")).hexdigest()
    return model_json, model_sha256


def _fallback(
    model: ErgoLaunchModel,
    *,
    request_id: str,
    model_sha256: str,
    tier: str,
    width: int,
    reason: str,
) -> RenderReceipt:
    return RenderReceipt(
        request_id=request_id,
        model_sha256=model_sha256,
        renderer_id="forge-minimal-inprocess/0.1",
        tier="minimal",
        payload_kind="text/plain",
        payload=render_minimal_text(model, width=width),
        renderer_failed=True,
        fallback_used=True,
        failure_reason=reason,
        authority="NONE",
    )


def render_snapshot_with_fallback(
    model: ErgoLaunchModel,
    *,
    renderer_command: Sequence[str],
    tier: str,
    width: int = 80,
    timeout_seconds: float = 5.0,
) -> RenderReceipt:
    if not renderer_command:
        raise ValueError("renderer_command is required")
    model_json, model_sha256 = _model_identity(model)
    request_id = f"render-{uuid4().hex}"
    request = {
        "protocol": REQUEST_PROTOCOL,
        "request_id": request_id,
        "model_schema": model.schema,
        "model_sha256": model_sha256,
        "model_json": model_json,
        "tier": tier,
        "width": int(width),
    }
    request_json = json.dumps(
        request,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )

    try:
        result = subprocess.run(
            list(renderer_command),
            input=request_json,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _fallback(
            model,
            request_id=request_id,
            model_sha256=model_sha256,
            tier=tier,
            width=width,
            reason=f"renderer launch/timeout failure: {type(exc).__name__}: {exc}",
        )

    if result.returncode != 0:
        return _fallback(
            model,
            request_id=request_id,
            model_sha256=model_sha256,
            tier=tier,
            width=width,
            reason=f"renderer exited {result.returncode}: {result.stderr.strip()}",
        )

    try:
        response = json.loads(result.stdout)
        if not isinstance(response, dict):
            raise RendererProtocolError("response is not a JSON object")
        if response.get("protocol") != RESPONSE_PROTOCOL:
            raise RendererProtocolError("response protocol mismatch")
        if response.get("request_id") != request_id:
            raise RendererProtocolError("response request_id mismatch")
        if response.get("model_sha256") != model_sha256:
            raise RendererProtocolError("response model_sha256 mismatch")
        renderer_id = str(response.get("renderer_id") or "")
        payload_kind = str(response.get("payload_kind") or "")
        payload = response.get("payload")
        if not renderer_id:
            raise RendererProtocolError("renderer_id missing")
        if not payload_kind:
            raise RendererProtocolError("payload_kind missing")
        if not isinstance(payload, str):
            raise RendererProtocolError("payload must be a string in v0.1")
    except (json.JSONDecodeError, RendererProtocolError, TypeError, ValueError) as exc:
        return _fallback(
            model,
            request_id=request_id,
            model_sha256=model_sha256,
            tier=tier,
            width=width,
            reason=f"renderer response rejected: {type(exc).__name__}: {exc}",
        )

    return RenderReceipt(
        request_id=request_id,
        model_sha256=model_sha256,
        renderer_id=renderer_id,
        tier=str(response.get("tier") or tier),
        payload_kind=payload_kind,
        payload=payload,
        renderer_failed=False,
        fallback_used=False,
        failure_reason=None,
        authority="NONE",
    )
