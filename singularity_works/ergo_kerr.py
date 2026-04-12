from __future__ import annotations
# complexity_justified: console-first Ergo-Light/Kerr embodiment for Forge HUD boot and live panel.

from dataclasses import dataclass, field
from enum import Enum
import math
import time


class BootPhase(str, Enum):
    COLD_BOOT = "cold_boot"
    SINGULARITY_IGNITION = "singularity_ignition"
    ERGOSPHERE_FORMATION = "ergosphere_formation"
    ORBIT_LOCK = "orbit_lock"
    HANDOFF = "handoff"


@dataclass(frozen=True)
class RGB:
    r: int
    g: int
    b: int

    def fg(self) -> str:
        return f"[38;2;{self.r};{self.g};{self.b}m"


@dataclass(frozen=True)
class VoidKerrTheme:
    void_black: RGB = RGB(3, 1, 8)
    glass: RGB = RGB(10, 6, 18)
    pale_orchid: RGB = RGB(240, 234, 255)
    lavender: RGB = RGB(192, 185, 229)
    dim_lavender: RGB = RGB(139, 127, 168)
    accent_purple: RGB = RGB(167, 139, 250)
    horizon_black: RGB = RGB(8, 8, 14)
    ergosphere_blue: RGB = RGB(59, 130, 246)
    photon_white: RGB = RGB(255, 255, 255)
    singularity_cyan: RGB = RGB(34, 211, 238)
    warning_red: RGB = RGB(239, 68, 68)
    caution_amber: RGB = RGB(245, 158, 11)
    stable_green: RGB = RGB(16, 185, 129)


DEFAULT_VOID_KERR_THEME = VoidKerrTheme()
_RESET = "[0m"


@dataclass(frozen=True)
class KerrState:
    phase: BootPhase = BootPhase.COLD_BOOT
    normalized_progress: float = 0.0
    horizon_radius: float = 0.18
    ergosphere_radius: float = 0.30
    photon_radius: float = 0.36
    singularity_radius: float = 0.06
    drag: float = 0.0
    spin: float = 0.95
    blue_shift_bias: float = 0.0
    hazard_pressure: float = 0.0
    proof_pressure: float = 0.0
    orbitals: int = 3
    label: str = "Forge boot"
    sublabel: str = ""


@dataclass(frozen=True)
class KerrPanelState:
    state: KerrState = KerrState()
    width: int = 40
    height: int = 14
    lines: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BootFrame:
    phase: BootPhase
    label: str
    sublabel: str
    progress: float


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * _clamp(t)


def derive_kerr_state(
    *,
    verdict: str,
    fail_count: int,
    warn_count: int,
    pass_count: int,
    chain_count: int,
    event_count: int,
    progress: float,
    phase: str,
    label: str,
    sublabel: str,
) -> KerrState:
    hazard_pressure = _clamp((fail_count * 0.18) + (warn_count * 0.08) + (chain_count * 0.12))
    proof_pressure = _clamp((pass_count * 0.03) + (event_count * 0.02) + progress * 0.4)
    blue_shift = 0.55 if verdict == "green" else 0.25 if verdict == "amber" else 0.10
    drag = _clamp((chain_count * 0.15) + (event_count * 0.03) + progress * 0.35)
    phase_map = {
        "boot": BootPhase.COLD_BOOT,
        "ignition": BootPhase.SINGULARITY_IGNITION,
        "formation": BootPhase.ERGOSPHERE_FORMATION,
        "orbit": BootPhase.ORBIT_LOCK,
        "complete": BootPhase.HANDOFF,
    }
    derived_phase = phase_map.get(phase, BootPhase.ORBIT_LOCK if progress >= 1.0 else BootPhase.ERGOSPHERE_FORMATION)
    return KerrState(
        phase=derived_phase,
        normalized_progress=_clamp(progress),
        horizon_radius=_lerp(0.14, 0.22, proof_pressure),
        ergosphere_radius=_lerp(0.24, 0.38, drag),
        photon_radius=_lerp(0.31, 0.43, hazard_pressure),
        singularity_radius=_lerp(0.05, 0.08, proof_pressure),
        drag=drag,
        spin=0.95,
        blue_shift_bias=blue_shift,
        hazard_pressure=hazard_pressure,
        proof_pressure=proof_pressure,
        orbitals=max(3, min(8, 3 + fail_count + warn_count)),
        label=label,
        sublabel=sublabel,
    )


def _glyph_for(distance: float, state: KerrState) -> tuple[str, str]:
    t = DEFAULT_VOID_KERR_THEME
    if distance <= state.singularity_radius:
        return t.singularity_cyan.fg(), "◉"
    if abs(distance - state.horizon_radius) <= 0.012:
        return t.horizon_black.fg(), "⬤"
    if abs(distance - state.ergosphere_radius) <= 0.018:
        return t.ergosphere_blue.fg(), "◎"
    if abs(distance - state.photon_radius) <= 0.015:
        return t.photon_white.fg(), "◌"
    return t.dim_lavender.fg(), "·"


def render_kerr_panel(state: KerrState, width: int = 40, height: int = 14, tick: float = 0.0) -> KerrPanelState:
    width = max(24, width)
    height = max(8, height)
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    aspect = max(1.0, width / max(1.0, height))
    lines: list[str] = []
    t = DEFAULT_VOID_KERR_THEME
    orbital_positions: list[tuple[int, int, str]] = []
    for idx in range(state.orbitals):
        angle = tick * (0.9 + idx * 0.08) + (2.0 * math.pi * idx / max(1, state.orbitals))
        radius = state.photon_radius + 0.06 + (idx % 3) * 0.015
        ox = int(round(cx + math.cos(angle) * radius * width * 0.45))
        oy = int(round(cy + math.sin(angle) * radius * height * 0.35))
        color = t.accent_purple.fg() if idx % 2 == 0 else t.ergosphere_blue.fg()
        orbital_positions.append((ox, oy, color))
    for y in range(height):
        row_parts: list[str] = []
        for x in range(width):
            nx = ((x - cx) / max(1.0, width)) * 2.2 * aspect
            ny = ((y - cy) / max(1.0, height)) * 2.0
            theta = math.atan2(ny, nx)
            drag = math.cos(theta - tick * 0.7) * state.drag * 0.12
            d = math.sqrt((nx + drag) ** 2 + ny ** 2)
            color, glyph = _glyph_for(d, state)
            for ox, oy, orbit_color in orbital_positions:
                if x == ox and y == oy:
                    color, glyph = orbit_color, "•"
                    break
            row_parts.append(f"{color}{glyph}{_RESET}")
        lines.append("".join(row_parts))
    header = f"{t.accent_purple.fg()}{state.label}{_RESET}"
    sub = f"{t.lavender.fg()}{state.sublabel}{_RESET}" if state.sublabel else ""
    footer = (
        f"{t.dim_lavender.fg()}phase={state.phase.value}"
        f" drag={state.drag:.2f} hazard={state.hazard_pressure:.2f} proof={state.proof_pressure:.2f}{_RESET}"
    )
    return KerrPanelState(state=state, width=width, height=height, lines=(header, sub, *lines, footer))


def boot_frames(now: float) -> BootFrame:
    cycle = [
        (BootPhase.COLD_BOOT, 0.90, "Cold Boot", "Vacuum initialization"),
        (BootPhase.SINGULARITY_IGNITION, 1.10, "Singularity Ignition", "Core curvature rising"),
        (BootPhase.ERGOSPHERE_FORMATION, 1.20, "Ergosphere Formation", "Frame-drag field stabilizing"),
        (BootPhase.ORBIT_LOCK, 0.90, "Orbit Lock", "Claude vessel handoff window"),
        (BootPhase.HANDOFF, 0.40, "Handoff", "Forge cockpit online"),
    ]
    elapsed = max(0.0, now)
    cursor = 0.0
    total = sum(duration for _, duration, _, _ in cycle)
    for phase, duration, label, sublabel in cycle:
        if elapsed <= cursor + duration:
            progress = (elapsed - cursor) / duration if duration else 1.0
            return BootFrame(phase=phase, label=label, sublabel=sublabel, progress=_clamp(progress))
        cursor += duration
    return BootFrame(phase=BootPhase.HANDOFF, label="Handoff", sublabel="Forge cockpit online", progress=1.0)


def total_boot_duration() -> float:
    return 4.5
