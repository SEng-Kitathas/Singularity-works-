from __future__ import annotations

"""Runtime health lease connecting a resumed session to checkpoint reputation."""

from dataclasses import dataclass
import time
from typing import Callable
from uuid import uuid4

from .resume_checkpoint import ResumeCheckpointManager, CheckpointView


Clock = Callable[[], float]


@dataclass
class SessionHealthLease:
    manager: ResumeCheckpointManager
    checkpoint_id: str
    resume_id: str
    started_at: float
    clock: Clock
    meaningful_operations: int = 0
    stable_recorded: bool = False

    @classmethod
    def begin(
        cls,
        manager: ResumeCheckpointManager,
        checkpoint_id: str,
        *,
        resume_id: str | None = None,
        clock: Clock = time.monotonic,
    ) -> "SessionHealthLease":
        resume_id = resume_id or f"resume-{uuid4().hex}"
        manager.record_resume(checkpoint_id, resume_id=resume_id)
        return cls(
            manager=manager,
            checkpoint_id=checkpoint_id,
            resume_id=resume_id,
            started_at=float(clock()),
            clock=clock,
        )

    def elapsed_seconds(self) -> float:
        return max(0.0, float(self.clock()) - self.started_at)

    def note_meaningful_operation(self, count: int = 1) -> bool:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.meaningful_operations += int(count)
        return self.maybe_mark_stable()

    def heartbeat(self) -> bool:
        """Heartbeat may advance time evidence but never invent meaningful operations."""
        return self.maybe_mark_stable()

    def maybe_mark_stable(self) -> bool:
        if self.stable_recorded:
            return True
        stable = self.manager.record_health(
            self.checkpoint_id,
            resume_id=self.resume_id,
            healthy_seconds=self.elapsed_seconds(),
            meaningful_operations=self.meaningful_operations,
        )
        if stable:
            self.stable_recorded = True
        return self.stable_recorded

    def promote_lkg(self, *, promotion_id: str | None = None) -> CheckpointView:
        if not self.stable_recorded:
            self.maybe_mark_stable()
        promotion_id = promotion_id or f"lkg-{uuid4().hex}"
        self.manager.promote_lkg(self.checkpoint_id, promotion_id=promotion_id)
        return self.manager.inspect(self.checkpoint_id)

    def record_session_crash(
        self,
        *,
        crash_id: str,
        failure_domain: str,
        detail: str = "",
    ) -> CheckpointView:
        return self.manager.record_crash(
            self.checkpoint_id,
            resume_id=self.resume_id,
            crash_id=crash_id,
            seconds_since_resume=self.elapsed_seconds(),
            failure_domain=failure_domain,
            detail=detail,
        )
