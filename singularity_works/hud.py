from __future__ import annotations
# complexity_justified: integrated forge runtime surface

from dataclasses import dataclass, field
import ctypes
import os
import shutil
import sys
import time

STD_OUTPUT_HANDLE = -11
ENABLE_PROCESSED_OUTPUT = 0x0001
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004


@dataclass
class HudSnapshot:
    app_name: str = "Singularity Works"
    mode: str = "idle"
    provider: str = "n/a"
    session_id: str = "n/a"
    project_tag: str = "default"
    uptime_s: float = 0.0
    phase: str = "boot"
    requirement: str = "n/a"
    radical: str = "n/a"
    validator: str = "n/a"
    branch: str = "main"
    progress_label: str = "overall"
    progress_value: float = 0.0
    counts: dict[str, int] = field(default_factory=dict)
    stats: dict[str, str] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)


def _enable_vt_windows() -> bool:
    if os.name != "nt":
        return True
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    if handle == 0:
        return False
    mode = ctypes.c_uint()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
        return False
    new_mode = mode.value | ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
    return kernel32.SetConsoleMode(handle, new_mode) != 0


class ConsoleHUD:
    def __init__(self, use_alt_screen: bool = True) -> None:
        self.use_alt_screen = use_alt_screen
        self.vt_enabled = _enable_vt_windows()
        self._active = False

    def __enter__(self) -> "ConsoleHUD":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self._active:
            return
        self._active = True
        if self.vt_enabled and self.use_alt_screen:
            sys.stdout.write("\x1b[?1049h\x1b[?25l")
            sys.stdout.flush()

    def stop(self) -> None:
        if not self._active:
            return
        if self.vt_enabled and self.use_alt_screen:
            sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
            sys.stdout.flush()
        self._active = False

    def render(self, snap: HudSnapshot) -> None:
        if self.vt_enabled:
            sys.stdout.write(self._render_vt(snap))
        else:
            sys.stdout.write(self._render_plain(snap))
        sys.stdout.flush()

    def _render_vt(self, snap: HudSnapshot) -> str:
        cols, rows = shutil.get_terminal_size(fallback=(120, 40))
        lines = self._build_lines(snap, cols=max(60, cols))
        body = "\n".join(lines[: rows - 1])
        return "\x1b[H\x1b[2J" + body

    def _render_plain(self, snap: HudSnapshot) -> str:
        cols, _ = shutil.get_terminal_size(fallback=(120, 40))
        body = "\n".join(self._build_lines(snap, cols=max(60, cols)))
        return "\n" + body + "\n"

    def _top_line(self, snap: HudSnapshot) -> str:
        parts = [
            snap.app_name,
            f"mode={snap.mode}",
            f"provider={snap.provider}",
            f"project={snap.project_tag}",
            f"session={snap.session_id}",
            f"up={int(snap.uptime_s)}s",
        ]
        return " | ".join(parts)

    def _build_lines(self, snap: HudSnapshot, cols: int) -> list[str]:
        def crop(text: str, width: int) -> str:
            return text if len(text) <= width else text[: max(0, width - 3)] + "..."

        def bar(width: int, value: float) -> str:
            value = max(0.0, min(1.0, value))
            fill = int(width * value)
            return "[" + ("#" * fill) + ("-" * (width - fill)) + "]"

        top = crop(self._top_line(snap), cols)
        left_w = max(28, cols // 3)
        right_w = max(28, cols // 3)
        center_w = max(24, cols - left_w - right_w - 4)

        left = [
            f"PHASE      : {crop(snap.phase, left_w - 13)}",
            f"REQ/CLAIM  : {crop(snap.requirement, left_w - 13)}",
            f"RADICAL    : {crop(snap.radical, left_w - 13)}",
            f"VALIDATOR  : {crop(snap.validator, left_w - 13)}",
            f"BRANCH     : {crop(snap.branch, left_w - 13)}",
        ]
        counts = " ".join(f"{k}={v}" for k, v in snap.counts.items())
        center = [
            f"PROGRESS   : {crop(snap.progress_label, center_w - 13)}",
            bar(max(10, center_w - 2), snap.progress_value),
            f"COUNTS     : {crop(counts or 'n/a', center_w - 13)}",
        ]
        for key, value in list(snap.stats.items())[:6]:
            center.append(f"{crop(key.upper(), 10):10}: {crop(str(value), center_w - 13)}")

        right = [f"RISKS      : {len(snap.risks)}", f"WARNINGS   : {len(snap.warnings)}"]
        for item in snap.risks[:4]:
            right.append(f"! {crop(item, right_w - 2)}")
        for item in snap.warnings[:4]:
            right.append(f"? {crop(item, right_w - 2)}")

        height = max(len(left), len(center), len(right))
        left += [""] * (height - len(left))
        center += [""] * (height - len(center))
        right += [""] * (height - len(right))

        lines = [top, "=" * min(cols, max(20, len(top)))]
        for a, b, c in zip(left, center, right):
            lines.append(f"{a:<{left_w}} | {b:<{center_w}} | {c:<{right_w}}")

        lines.append("-" * cols)
        lines.append("EVENTS")
        lines.append("-" * cols)
        for item in snap.events[-10:]:
            lines.append(crop(f"- {item}", cols))
        return lines


if __name__ == "__main__":
    hud = ConsoleHUD()
    start = time.monotonic()
    with hud:
        for i in range(101):
            snap = HudSnapshot(
                mode="dialectic",
                provider="local",
                session_id="demo",
                project_tag="singularity-works",
                uptime_s=time.monotonic() - start,
                phase="qa-research",
                requirement="HUD operator surface",
                radical="STATE+TRUST",
                validator="shadow-audit",
                branch="main",
                progress_label="demo progress",
                progress_value=i / 100.0,
                counts={"pass": 12, "warn": 2, "fail": 0, "residual": 5},
                stats={
                    "latency_ms": str(20 + i),
                    "throughput": "steady",
                    "events": str(i),
                },
                risks=["Residual assurance gap", "Traceability incomplete"],
                warnings=["VT fallback disabled" if not hud.vt_enabled else "none"],
                events=[f"checkpoint {j}" for j in range(max(0, i - 5), i + 1)],
            )
            hud.render(snap)
            time.sleep(0.01)
