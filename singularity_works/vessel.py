from __future__ import annotations
# complexity_justified: vessel doctor and launch planning bridge multiple host-runtime surfaces while preserving explicit launch contracts.
from dataclasses import dataclass, field
from pathlib import Path
import os
import shutil
import subprocess
import sys
from typing import Sequence


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


@dataclass(frozen=True)
class ClaudeProcessTarget:
    executable: str
    args: tuple[str, ...] = field(default_factory=tuple)
    title_hint: str = "Claude"


@dataclass(frozen=True)
class VesselLaunchPlan:
    python_executable: str
    forge_entry: str
    claude_target: ClaudeProcessTarget | None
    terminal_host: str
    project_root: str


def _which_many(candidates: Sequence[str]) -> str | None:
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def run_vessel_doctor(project_root: str | Path) -> VesselDoctorReport:
    root = Path(project_root)
    terminal = _which_many(['wt', 'wezterm', 'alacritty', 'cmd'])
    claude_exec = _which_many(['claude', 'claude.exe'])
    checks = [
        DoctorCheck("project_root", root.exists(), str(root)),
        DoctorCheck(
            "forge_runtime",
            (root / 'singularity_works' / 'runtime.py').exists(),
            'runtime.py present',
        ),
        DoctorCheck("python", bool(sys.executable), sys.executable),
        DoctorCheck(
            "terminal_host",
            bool(terminal),
            'preferred terminal available' if terminal else 'no preferred terminal found',
        ),
        DoctorCheck(
            "claude_target",
            bool(claude_exec),
            'Claude executable found' if claude_exec else 'Claude executable not found',
        ),
    ]
    return VesselDoctorReport(tuple(checks))


def build_vessel_launch_plan(project_root: str | Path) -> VesselLaunchPlan:
    root = Path(project_root)
    terminal = _which_many(['wt', 'wezterm', 'alacritty', 'cmd']) or 'cmd'
    claude_exec = _which_many(['claude', 'claude.exe'])
    claude_target = ClaudeProcessTarget(executable=claude_exec) if claude_exec else None
    forge_entry = str(root / 'examples' / 'demo_bad_run.py')
    return VesselLaunchPlan(
        python_executable=sys.executable,
        forge_entry=forge_entry,
        claude_target=claude_target,
        terminal_host=terminal,
        project_root=str(root),
    )


def launch_claude_vessel(plan: VesselLaunchPlan) -> list[subprocess.Popen[str]]:
    procs: list[subprocess.Popen[str]] = []
    forge_cmd = [plan.python_executable, plan.forge_entry]
    procs.append(subprocess.Popen(forge_cmd, cwd=plan.project_root, text=True))
    if plan.claude_target is not None:
        procs.append(
            subprocess.Popen(
                [plan.claude_target.executable, *plan.claude_target.args],
                cwd=plan.project_root,
                text=True,
            )
        )
    return procs
