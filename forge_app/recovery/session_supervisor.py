from __future__ import annotations

"""Externally supervised session coordinator process boundary v0.1."""

from dataclasses import asdict, dataclass
import json
import os
import signal
from pathlib import Path
import subprocess
import time
from typing import Sequence
from uuid import uuid4

from .resume_checkpoint import CheckpointView, ResumeCheckpointManager

READY_PROTOCOL = "singularity-session-child-ready/0.1"


class SessionSupervisorError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChildReadyReceipt:
    protocol: str
    checkpoint_id: str
    resume_id: str
    pid: int
    instance_token: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ChildExitReceipt:
    checkpoint_id: str
    resume_id: str
    crash_id: str | None
    pid: int
    launch_pid: int
    returncode: int
    seconds_since_resume: float
    expected: bool
    checkpoint_status: str | None
    quarantined: bool | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class SessionProcessSupervisor:
    def __init__(
        self,
        manager: ResumeCheckpointManager,
        *,
        checkpoint_id: str,
        resume_id: str,
        command: Sequence[str],
        ready_path: str | Path,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        clock=time.monotonic,
        instance_token: str | None = None,
    ) -> None:
        if not resume_id:
            raise ValueError("resume_id is required")
        if not command:
            raise ValueError("command is required")
        self.manager = manager
        self.checkpoint_id = checkpoint_id
        self.resume_id = resume_id
        self.command = tuple(str(x) for x in command)
        self.ready_path = Path(ready_path)
        self.cwd = Path(cwd) if cwd is not None else None
        self.env = dict(env) if env is not None else None
        self.clock = clock
        self.instance_token = instance_token or uuid4().hex
        self.started_at: float | None = None
        self.process: subprocess.Popen[str] | None = None
        self.ready_receipt: ChildReadyReceipt | None = None
        self._expected_shutdown = False

    def _resume_seen(self) -> bool:
        for event in self.manager.store.events_for_attempt(self.checkpoint_id):
            if event["event_type"] != "checkpoint_resumed":
                continue
            if str(event["payload"].get("resume_id") or "") == self.resume_id:
                return True
        return False

    def start(self) -> int:
        if self.process is not None:
            raise SessionSupervisorError("supervised process already started")
        if self._resume_seen():
            raise SessionSupervisorError(
                f"resume_id already used for checkpoint: {self.checkpoint_id} {self.resume_id}"
            )
        if self.ready_path.exists():
            raise SessionSupervisorError(
                f"ready path already exists; refusing to overwrite prior evidence: {self.ready_path}"
            )
        self.ready_path.parent.mkdir(parents=True, exist_ok=True)
        self.manager.record_resume(self.checkpoint_id, resume_id=self.resume_id)
        self.started_at = float(self.clock())
        child_env = os.environ.copy()
        if self.env is not None:
            child_env.update(self.env)
        child_env["SINGULARITY_SESSION_INSTANCE_TOKEN"] = self.instance_token
        self.process = subprocess.Popen(
            list(self.command),
            cwd=str(self.cwd) if self.cwd is not None else None,
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return int(self.process.pid)

    def elapsed_seconds(self) -> float:
        if self.started_at is None:
            raise SessionSupervisorError("supervised process has not started")
        return max(0.0, float(self.clock()) - self.started_at)

    def _parse_ready(self) -> ChildReadyReceipt:
        if self.process is None:
            raise SessionSupervisorError("supervised process has not started")
        try:
            payload = json.loads(self.ready_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SessionSupervisorError(f"ready receipt unreadable: {type(exc).__name__}: {exc}") from exc
        receipt = ChildReadyReceipt(
            protocol=str(payload.get("protocol") or ""),
            checkpoint_id=str(payload.get("checkpoint_id") or ""),
            resume_id=str(payload.get("resume_id") or ""),
            pid=int(payload.get("pid") or 0),
            instance_token=str(payload.get("instance_token") or ""),
        )
        expected_identity = {
            "protocol": READY_PROTOCOL,
            "checkpoint_id": self.checkpoint_id,
            "resume_id": self.resume_id,
            "instance_token": self.instance_token,
        }
        actual_identity = {
            "protocol": receipt.protocol,
            "checkpoint_id": receipt.checkpoint_id,
            "resume_id": receipt.resume_id,
            "instance_token": receipt.instance_token,
        }
        if actual_identity != expected_identity or receipt.pid <= 0:
            raise SessionSupervisorError(
                f"ready identity mismatch: expected={expected_identity} actual={receipt.as_dict()}"
            )
        return receipt

    def wait_ready(self, *, timeout_seconds: float = 5.0, poll_seconds: float = 0.01) -> ChildReadyReceipt:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if poll_seconds <= 0:
            raise ValueError("poll_seconds must be > 0")
        if self.process is None:
            raise SessionSupervisorError("supervised process has not started")
        deadline = float(self.clock()) + float(timeout_seconds)
        while float(self.clock()) < deadline:
            if self.ready_path.exists():
                receipt = self._parse_ready()
                self.ready_receipt = receipt
                return receipt
            rc = self.process.poll()
            if rc is not None:
                raise SessionSupervisorError(
                    f"child exited before ready: pid={self.process.pid} returncode={rc}"
                )
            time.sleep(poll_seconds)
        raise SessionSupervisorError(
            f"ready timeout after {timeout_seconds:.3f}s: checkpoint={self.checkpoint_id} resume={self.resume_id}"
        )

    def worker_pid(self) -> int:
        if self.ready_receipt is not None:
            return int(self.ready_receipt.pid)
        if self.process is None:
            raise SessionSupervisorError("supervised process has not started")
        return int(self.process.pid)

    def _terminate_worker(self) -> None:
        if self.process is None:
            raise SessionSupervisorError("supervised process has not started")
        worker_pid = self.worker_pid()
        if worker_pid == int(self.process.pid):
            if self.process.poll() is None:
                self.process.kill()
            return
        try:
            os.kill(worker_pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    def deterministic_crash_id(self) -> str:
        return f"session-process-crash:{self.checkpoint_id}:{self.resume_id}"

    def _require_terminal_returncode(self, *, wait_timeout_seconds: float = 5.0) -> int:
        if self.process is None:
            raise SessionSupervisorError("supervised process has not started")
        rc = self.process.poll()
        if rc is None:
            try:
                rc = self.process.wait(timeout=wait_timeout_seconds)
            except subprocess.TimeoutExpired as exc:
                raise SessionSupervisorError("child is still running; no exit to observe") from exc
        return int(rc)

    def _existing_crash_event(self, crash_id: str):
        for event in self.manager.store.events_for_attempt(self.checkpoint_id):
            if event["event_type"] != "checkpoint_crash_associated":
                continue
            payload = event["payload"]
            if str(payload.get("crash_id") or "") != crash_id:
                continue
            if str(payload.get("resume_id") or "") != self.resume_id:
                raise SessionSupervisorError(
                    f"crash_id already belongs to different resume: crash_id={crash_id}"
                )
            return event
        return None

    def record_unexpected_exit(
        self,
        *,
        crash_id: str | None = None,
        failure_domain: str = "session_coordinator_process",
        detail: str = "",
        wait_timeout_seconds: float = 5.0,
    ) -> tuple[ChildExitReceipt, CheckpointView]:
        rc = self._require_terminal_returncode(wait_timeout_seconds=wait_timeout_seconds)
        if self.process is None:
            raise SessionSupervisorError("supervised process has not started")
        crash_id = crash_id or self.deterministic_crash_id()
        existing = self._existing_crash_event(crash_id)
        if existing is not None:
            elapsed = float(existing["payload"].get("seconds_since_resume") or 0.0)
            view = self.manager.inspect(self.checkpoint_id)
            return (
                ChildExitReceipt(
                    checkpoint_id=self.checkpoint_id,
                    resume_id=self.resume_id,
                    crash_id=crash_id,
                    pid=self.worker_pid(),
                    launch_pid=int(self.process.pid),
                    returncode=rc,
                    seconds_since_resume=elapsed,
                    expected=False,
                    checkpoint_status=view.status,
                    quarantined=view.quarantined,
                ),
                view,
            )
        elapsed = self.elapsed_seconds()
        detail_text = (
            f"launch_pid={self.process.pid} worker_pid={self.worker_pid()} launch_returncode={rc} supervisor_observed=true"
            + (f"; {detail}" if detail else "")
        )
        view = self.manager.record_crash(
            self.checkpoint_id,
            resume_id=self.resume_id,
            crash_id=crash_id,
            seconds_since_resume=elapsed,
            failure_domain=failure_domain,
            detail=detail_text,
        )
        receipt = ChildExitReceipt(
            checkpoint_id=self.checkpoint_id,
            resume_id=self.resume_id,
            crash_id=crash_id,
            pid=self.worker_pid(),
            launch_pid=int(self.process.pid),
            returncode=rc,
            seconds_since_resume=elapsed,
            expected=False,
            checkpoint_status=view.status,
            quarantined=view.quarantined,
        )
        return receipt, view

    def kill_and_record(
        self,
        *,
        crash_id: str | None = None,
        failure_domain: str = "session_coordinator_process",
        detail: str = "external supervisor hard kill",
        wait_timeout_seconds: float = 5.0,
    ) -> tuple[ChildExitReceipt, CheckpointView]:
        if self.process is None:
            raise SessionSupervisorError("supervised process has not started")
        self._terminate_worker()
        return self.record_unexpected_exit(
            crash_id=crash_id,
            failure_domain=failure_domain,
            detail=detail,
            wait_timeout_seconds=wait_timeout_seconds,
        )

    def terminate_expected(self, *, wait_timeout_seconds: float = 5.0) -> ChildExitReceipt:
        if self.process is None:
            raise SessionSupervisorError("supervised process has not started")
        self._expected_shutdown = True
        self._terminate_worker()
        rc = self._require_terminal_returncode(wait_timeout_seconds=wait_timeout_seconds)
        return ChildExitReceipt(
            checkpoint_id=self.checkpoint_id,
            resume_id=self.resume_id,
            crash_id=None,
            pid=self.worker_pid(),
            launch_pid=int(self.process.pid),
            returncode=rc,
            seconds_since_resume=self.elapsed_seconds(),
            expected=True,
            checkpoint_status=None,
            quarantined=None,
        )

    def close(self) -> None:
        if self.process is not None and self.process.poll() is None:
            try:
                self._terminate_worker()
            except Exception:
                self.process.kill()
            try:
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def __enter__(self) -> "SessionProcessSupervisor":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
