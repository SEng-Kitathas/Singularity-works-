from __future__ import annotations
# complexity_justified: vessel preflight must bridge terminal host, claude process, python runtime, and optional anchor support.

from dataclasses import dataclass, field
import shutil
import sys
from typing import Iterable


@dataclass(frozen=True)
class ToolProbe:
    name: str
    found: bool
    path: str = ""
    note: str = ""


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    passed: bool
    detail: str
    severity: str = "info"


@dataclass
class ForgeDoctorReport:
    checks: list[DoctorCheck] = field(default_factory=list)
    probes: list[ToolProbe] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(check.passed or check.severity == "warn" for check in self.checks)

    def summary_lines(self) -> list[str]:
        lines = ["Forge Vessel Doctor"]
        for check in self.checks:
            prefix = "PASS" if check.passed else check.severity.upper()
            lines.append(f"[{prefix}] {check.name}: {check.detail}")
        return lines


def _probe(name: str, aliases: Iterable[str] = ()) -> ToolProbe:
    candidates = (name, *aliases)
    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            return ToolProbe(name=name, found=True, path=path, note=f"resolved via {candidate}")
    return ToolProbe(name=name, found=False, note="not found on PATH")


def run_vessel_doctor() -> ForgeDoctorReport:
    report = ForgeDoctorReport()
    python_path = sys.executable
    report.probes.append(ToolProbe(name="python", found=True, path=python_path, note="active runtime"))
    terminal_probe = _probe("wt", aliases=("wezterm", "alacritty", "ghostty"))
    claude_probe = _probe("claude", aliases=("claude-code",))
    report.probes.extend([terminal_probe, claude_probe])
    report.checks.append(DoctorCheck(name="python_runtime", passed=True, detail=python_path))
    report.checks.append(
        DoctorCheck(
            name="terminal_host",
            passed=terminal_probe.found,
            detail=terminal_probe.path or terminal_probe.note,
            severity="warn",
        )
    )
    report.checks.append(
        DoctorCheck(
            name="claude_command",
            passed=claude_probe.found,
            detail=claude_probe.path or claude_probe.note,
            severity="warn",
        )
    )
    try:
        import win32gui  # type: ignore
        report.checks.append(DoctorCheck(name="window_anchor", passed=True, detail="pywin32 present"))
    except Exception:
        report.checks.append(DoctorCheck(name="window_anchor", passed=False, detail="pywin32 missing; snap degraded", severity="warn"))
    return report
