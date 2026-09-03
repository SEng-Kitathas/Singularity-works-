from __future__ import annotations

"""Persistent renderer host v0.1.

Renderer workers are replaceable, authority-NONE presentation processes. The host
owns generation and frame identity, verifies every acknowledgement, and falls back
to the qualified minimal presentation on any liveness/protocol failure.
"""

from dataclasses import dataclass, asdict
import hashlib
import json
import queue
import subprocess
import threading
from typing import Any, Sequence
from uuid import uuid4

from forge_app.ergo.launch_model import ErgoLaunchModel, render_minimal_text

PROTOCOL = "forge-persistent-render/0.1"


class PersistentRendererError(RuntimeError):
    pass


@dataclass(frozen=True)
class PersistentRenderReceipt:
    generation_id: str
    frame_seq: int
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


@dataclass(frozen=True)
class HeartbeatReceipt:
    generation_id: str
    heartbeat_seq: int
    renderer_id: str
    authority: str = "NONE"


class _JsonLineWorker:
    def __init__(self, command: Sequence[str]) -> None:
        self.command = list(command)
        self.proc = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        if self.proc.stdin is None or self.proc.stdout is None:
            raise PersistentRendererError("renderer pipes unavailable")
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    def _read_stdout(self) -> None:
        assert self.proc.stdout is not None
        try:
            for line in self.proc.stdout:
                self._queue.put(line)
        finally:
            self._queue.put(None)

    def send(self, payload: dict[str, Any]) -> None:
        if self.proc.poll() is not None:
            raise PersistentRendererError(f"renderer exited {self.proc.returncode}")
        assert self.proc.stdin is not None
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        try:
            self.proc.stdin.write(raw + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise PersistentRendererError(f"renderer write failed: {type(exc).__name__}: {exc}") from exc

    def receive(self, timeout_seconds: float) -> dict[str, Any]:
        try:
            line = self._queue.get(timeout=timeout_seconds)
        except queue.Empty as exc:
            raise PersistentRendererError("renderer response timeout") from exc
        if line is None:
            rc = self.proc.poll()
            stderr = ""
            if self.proc.stderr is not None:
                try:
                    stderr = self.proc.stderr.read().strip()
                except OSError:
                    stderr = ""
            raise PersistentRendererError(f"renderer EOF/exit {rc}: {stderr}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PersistentRendererError(f"renderer malformed JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise PersistentRendererError("renderer response is not object")
        return value

    def terminate(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=1.5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=1.5)


class PersistentRendererHost:
    def __init__(
        self,
        renderer_command: Sequence[str],
        *,
        timeout_seconds: float = 2.0,
        fallback_width: int = 80,
    ) -> None:
        if not renderer_command:
            raise ValueError("renderer_command is required")
        self.renderer_command = list(renderer_command)
        self.timeout_seconds = float(timeout_seconds)
        self.fallback_width = int(fallback_width)
        self._worker: _JsonLineWorker | None = None
        self._generation_id: str | None = None
        self._renderer_id: str | None = None
        self._frame_seq = 0
        self._heartbeat_seq = 0
        self._generation_counter = 0

    @property
    def generation_id(self) -> str | None:
        return self._generation_id

    @property
    def renderer_id(self) -> str | None:
        return self._renderer_id

    def _new_generation_id(self) -> str:
        self._generation_counter += 1
        return f"renderer-generation-{self._generation_counter:04d}-{uuid4().hex}"

    def _validate_common(self, response: dict[str, Any], *, expected_type: str, generation_id: str) -> None:
        if response.get("protocol") != PROTOCOL:
            raise PersistentRendererError("renderer protocol mismatch")
        if response.get("type") != expected_type:
            raise PersistentRendererError(f"renderer response type mismatch: {response.get('type')!r}")
        if response.get("generation_id") != generation_id:
            raise PersistentRendererError("renderer generation mismatch")

    def _ensure_worker(self) -> None:
        if self._worker is not None and self._worker.proc.poll() is None:
            return
        self._drop_worker()
        generation_id = self._new_generation_id()
        worker = _JsonLineWorker(self.renderer_command)
        try:
            worker.send({"protocol": PROTOCOL, "type": "hello", "generation_id": generation_id})
            response = worker.receive(self.timeout_seconds)
            self._validate_common(response, expected_type="hello_ack", generation_id=generation_id)
            renderer_id = str(response.get("renderer_id") or "")
            if not renderer_id:
                raise PersistentRendererError("renderer_id missing from handshake")
        except BaseException:
            worker.terminate()
            raise
        self._worker = worker
        self._generation_id = generation_id
        self._renderer_id = renderer_id

    def _drop_worker(self) -> None:
        if self._worker is not None:
            self._worker.terminate()
        self._worker = None
        self._generation_id = None
        self._renderer_id = None

    def close(self) -> None:
        self._drop_worker()

    def heartbeat(self) -> HeartbeatReceipt:
        self._ensure_worker()
        assert self._worker is not None and self._generation_id is not None and self._renderer_id is not None
        self._heartbeat_seq += 1
        seq = self._heartbeat_seq
        generation = self._generation_id
        try:
            self._worker.send(
                {
                    "protocol": PROTOCOL,
                    "type": "heartbeat",
                    "generation_id": generation,
                    "heartbeat_seq": seq,
                }
            )
            response = self._worker.receive(self.timeout_seconds)
            self._validate_common(response, expected_type="heartbeat_ack", generation_id=generation)
            if int(response.get("heartbeat_seq", -1)) != seq:
                raise PersistentRendererError("heartbeat sequence mismatch")
            return HeartbeatReceipt(generation, seq, self._renderer_id, "NONE")
        except BaseException:
            self._drop_worker()
            raise

    def _fallback(
        self,
        model: ErgoLaunchModel,
        *,
        generation_id: str,
        frame_seq: int,
        model_sha256: str,
        reason: str,
        width: int,
    ) -> PersistentRenderReceipt:
        return PersistentRenderReceipt(
            generation_id=generation_id,
            frame_seq=frame_seq,
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

    def render_frame(self, model: ErgoLaunchModel, *, tier: str = "minimal", width: int | None = None) -> PersistentRenderReceipt:
        width = self.fallback_width if width is None else int(width)
        model_json = model.canonical_json()
        model_sha256 = hashlib.sha256(model_json.encode("utf-8")).hexdigest()
        self._frame_seq += 1
        frame_seq = self._frame_seq
        generation_for_receipt = self._generation_id or "unstarted"
        try:
            self._ensure_worker()
            assert self._worker is not None and self._generation_id is not None and self._renderer_id is not None
            generation = self._generation_id
            generation_for_receipt = generation
            self._worker.send(
                {
                    "protocol": PROTOCOL,
                    "type": "frame",
                    "generation_id": generation,
                    "frame_seq": frame_seq,
                    "model_schema": model.schema,
                    "model_sha256": model_sha256,
                    "model_json": model_json,
                    "tier": tier,
                    "width": width,
                }
            )
            response = self._worker.receive(self.timeout_seconds)
            self._validate_common(response, expected_type="frame_ack", generation_id=generation)
            if int(response.get("frame_seq", -1)) != frame_seq:
                raise PersistentRendererError("frame sequence mismatch")
            if response.get("model_sha256") != model_sha256:
                raise PersistentRendererError("frame model_sha256 mismatch")
            renderer_id = str(response.get("renderer_id") or "")
            if renderer_id != self._renderer_id:
                raise PersistentRendererError("renderer identity changed within generation")
            payload = response.get("payload")
            if not isinstance(payload, str):
                raise PersistentRendererError("frame payload must be string in v0.1")
            return PersistentRenderReceipt(
                generation_id=generation,
                frame_seq=frame_seq,
                model_sha256=model_sha256,
                renderer_id=renderer_id,
                tier=str(response.get("tier") or tier),
                payload_kind=str(response.get("payload_kind") or "text/plain"),
                payload=payload,
                renderer_failed=False,
                fallback_used=False,
                failure_reason=None,
                authority="NONE",
            )
        except BaseException as exc:
            self._drop_worker()
            return self._fallback(
                model,
                generation_id=generation_for_receipt,
                frame_seq=frame_seq,
                model_sha256=model_sha256,
                reason=f"persistent renderer failure: {type(exc).__name__}: {exc}",
                width=width,
            )
