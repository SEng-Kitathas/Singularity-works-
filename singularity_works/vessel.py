from __future__ import annotations
# complexity_justified: vessel doctor and unified-front launch planning bridge host runtime, terminal host, and Claude process contracts.
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import os
import shutil
import subprocess
import sys
from typing import Sequence


class TerminalHostKind(str, Enum):
    WINDOWS_TERMINAL = "windows_terminal"
    WEZTERM = "wezterm"
    ALACRITTY = "alacritty"
    CONHOST = "conhost"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class VesselDoctorReport:
    checks: tuple[DoctorCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)




class VesselReadiness(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    HUD_ONLY = "hud_only"


@dataclass(frozen=True)
class VesselSurfaceState:
    readiness: VesselReadiness
    claude_available: bool
    gpu_terminal: bool
    anchor_supported: bool
    unified_front_possible: bool
    terminal_kind: str
    terminal_executable: str
    claude_target: str

    def to_stats(self) -> dict[str, str]:
        return {
            "vessel": self.readiness.value,
            "claude": self.claude_target or "not-found",
            "terminal": self.terminal_executable or self.terminal_kind,
            "gpu_term": "yes" if self.gpu_terminal else "no",
            "unified_front": "yes" if self.unified_front_possible else "no",
            "anchor": "yes" if self.anchor_supported else "no",
        }

@dataclass(frozen=True)
class ClaudeProcessTarget:
    executable: str
    args: tuple[str, ...] = field(default_factory=tuple)
    title_hint: str = "Claude"


@dataclass(frozen=True)
class TerminalHostSpec:
    kind: TerminalHostKind
    executable: str = ""
    gpu_accelerated: bool = False
    title_supported: bool = False


@dataclass(frozen=True)
class VesselLaunchPlan:
    python_executable: str
    forge_command: tuple[str, ...]
    claude_target: ClaudeProcessTarget | None
    terminal_host: TerminalHostSpec
    project_root: str


def _which_many(candidates: Sequence[str]) -> str | None:
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _detect_terminal_host() -> TerminalHostSpec:
    if executable := _which_many(['wt', 'wt.exe']):
        return TerminalHostSpec(TerminalHostKind.WINDOWS_TERMINAL, executable, gpu_accelerated=True, title_supported=True)
    if executable := _which_many(['wezterm', 'wezterm.exe']):
        return TerminalHostSpec(TerminalHostKind.WEZTERM, executable, gpu_accelerated=True, title_supported=True)
    if executable := _which_many(['alacritty', 'alacritty.exe']):
        return TerminalHostSpec(TerminalHostKind.ALACRITTY, executable, gpu_accelerated=True, title_supported=True)
    if os.name == 'nt' and (executable := _which_many(['cmd', 'cmd.exe'])):
        return TerminalHostSpec(TerminalHostKind.CONHOST, executable, gpu_accelerated=False, title_supported=True)
    return TerminalHostSpec(TerminalHostKind.UNKNOWN)


def _detect_claude_target() -> ClaudeProcessTarget | None:
    executable = _which_many(['claude', 'claude.exe', 'claude-code', 'claude-code.exe'])
    return ClaudeProcessTarget(executable=executable) if executable else None


def run_vessel_doctor(project_root: str | Path) -> VesselDoctorReport:
    root = Path(project_root)
    terminal = _detect_terminal_host()
    claude_target = _detect_claude_target()
    checks = [
        DoctorCheck('project_root', root.exists(), str(root)),
        DoctorCheck('forge_runtime', (root / 'singularity_works' / 'runtime.py').exists(), 'runtime.py present'),
        DoctorCheck('python', bool(sys.executable), sys.executable),
        DoctorCheck('terminal_host', terminal.kind is not TerminalHostKind.UNKNOWN, terminal.executable or 'no preferred terminal found'),
        DoctorCheck('gpu_terminal', terminal.gpu_accelerated, 'preferred gpu terminal available' if terminal.gpu_accelerated else 'fallback terminal only'),
        DoctorCheck('claude_target', claude_target is not None, claude_target.executable if claude_target else 'Claude executable not found'),
    ]
    return VesselDoctorReport(tuple(checks))


def build_vessel_launch_plan(project_root: str | Path) -> VesselLaunchPlan:
    root = Path(project_root)
    terminal = _detect_terminal_host()
    return VesselLaunchPlan(
        python_executable=sys.executable,
        forge_command=(sys.executable, '-m', 'singularity_works.runtime'),
        claude_target=_detect_claude_target(),
        terminal_host=terminal,
        project_root=str(root),
    )


def _spawn_in_terminal(host: TerminalHostSpec, title: str, command: Sequence[str], cwd: str) -> subprocess.Popen[str] | None:
    if host.kind is TerminalHostKind.WINDOWS_TERMINAL:
        argv = [host.executable, 'new-tab', '--title', title, *command]
    elif host.kind is TerminalHostKind.WEZTERM:
        argv = [host.executable, 'start', '--cwd', cwd, '--', *command]
    elif host.kind is TerminalHostKind.ALACRITTY:
        argv = [host.executable, '--title', title, '-e', *command]
    elif host.kind is TerminalHostKind.CONHOST:
        argv = [host.executable, '/c', 'start', f'"{title}"', *command]
    else:
        return None
    return subprocess.Popen(argv, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)


def launch_claude_vessel(plan: VesselLaunchPlan) -> tuple[subprocess.Popen[str], ...]:
    procs: list[subprocess.Popen[str]] = []
    forge_proc = _spawn_in_terminal(plan.terminal_host, 'Singularity Works Forge', plan.forge_command, plan.project_root)
    if forge_proc is not None:
        procs.append(forge_proc)
    if plan.claude_target is not None:
        claude_command = (plan.claude_target.executable, *plan.claude_target.args)
        claude_proc = _spawn_in_terminal(plan.terminal_host, plan.claude_target.title_hint, claude_command, plan.project_root)
        if claude_proc is not None:
            procs.append(claude_proc)
    return tuple(procs)


def evaluate_vessel_surface(project_root: str | Path, *, anchor_supported: bool) -> VesselSurfaceState:
    doctor = run_vessel_doctor(project_root)
    plan = build_vessel_launch_plan(project_root)
    claude_available = plan.claude_target is not None
    gpu_terminal = plan.terminal_host.gpu_accelerated
    unified_front_possible = claude_available and plan.terminal_host.kind is not TerminalHostKind.UNKNOWN
    readiness = (
        VesselReadiness.READY if doctor.passed and unified_front_possible
        else VesselReadiness.HUD_ONLY if doctor.passed
        else VesselReadiness.DEGRADED
    )
    return VesselSurfaceState(
        readiness=readiness,
        claude_available=claude_available,
        gpu_terminal=gpu_terminal,
        anchor_supported=anchor_supported,
        unified_front_possible=unified_front_possible,
        terminal_kind=plan.terminal_host.kind.value,
        terminal_executable=plan.terminal_host.executable,
        claude_target=plan.claude_target.executable if plan.claude_target else "",
    )
