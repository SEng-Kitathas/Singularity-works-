from __future__ import annotations
# complexity_justified: vessel launcher must handle terminal host differences, claude availability, and paired HUD launch.

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Sequence

from .forge_doctor import ForgeDoctorReport, run_vessel_doctor


@dataclass(frozen=True)
class TerminalHostSpec:
    command: str
    gpu_accelerated: bool
    split_capable: bool


@dataclass(frozen=True)
class ClaudeVesselSpec:
    claude_command: str = "claude"
    target_title: str = "Claude"
    terminal: TerminalHostSpec = TerminalHostSpec(command="wt", gpu_accelerated=True, split_capable=True)


@dataclass(frozen=True)
class VesselLaunchReceipt:
    launched: bool
    mode: str
    detail: str


def _python_invocation(module: str, *args: str) -> list[str]:
    return [sys.executable, "-m", module, *args]


def launch_forge_vessel(base_dir: str | Path, spec: ClaudeVesselSpec = ClaudeVesselSpec()) -> VesselLaunchReceipt:
    report: ForgeDoctorReport = run_vessel_doctor()
    base_dir = Path(base_dir)
    terminal_path = shutil.which(spec.terminal.command)
    claude_path = shutil.which(spec.claude_command)
    hud_cmd = _python_invocation("singularity_works.forge_vessel", "hud", "--base-dir", str(base_dir), "--attach-title", spec.target_title)
    if terminal_path and spec.terminal.command == "wt" and claude_path:
        args = [
            terminal_path,
            "new-tab",
            claude_path,
            ";",
            "split-pane",
            "-H",
            *hud_cmd,
        ]
        subprocess.Popen(args, cwd=str(base_dir))
        return VesselLaunchReceipt(launched=True, mode="wt_split", detail="Windows Terminal launched Claude + Forge HUD")
    if claude_path:
        subprocess.Popen([claude_path], cwd=str(base_dir))
    subprocess.Popen(hud_cmd, cwd=str(base_dir))
    if claude_path:
        return VesselLaunchReceipt(launched=True, mode="dual_process", detail="Claude launched separately; Forge HUD launched in python process")
    if report.passed:
        return VesselLaunchReceipt(launched=True, mode="hud_only", detail="Claude unavailable; Forge HUD launched alone")
    return VesselLaunchReceipt(launched=False, mode="doctor_blocked", detail="vessel doctor did not find a viable launch path")
