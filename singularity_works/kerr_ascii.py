from __future__ import annotations
# complexity_justified: Kerr console rendering couples geometric shells, orbitals, and state-driven frame drag in one bounded viewport renderer.
from dataclasses import dataclass, field
from math import atan2, cos, sin, sqrt
from typing import Iterable

from .hud_theme import HUDTheme, VOID_PURPLE_THEME


@dataclass(frozen=True)
class FrameCell:
    glyph: str = " "
    fg_code: str = ""

    def render(self) -> str:
        return f"{self.fg_code}{self.glyph}\x1b[0m" if self.fg_code else self.glyph


@dataclass
class AsciiFramebuffer:
    width: int
    height: int
    rows: list[list[FrameCell]] = field(init=False)

    def __post_init__(self) -> None:
        self.rows = [[FrameCell() for _ in range(self.width)] for _ in range(self.height)]

    def set(self, x: int, y: int, cell: FrameCell) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.rows[y][x] = cell

    def render_lines(self) -> list[str]:
        return ["".join(cell.render() for cell in row) for row in self.rows]


@dataclass(frozen=True)
class KerrVisualState:
    phase_label: str = "launcher"
    frame_time_s: float = 0.0
    horizon_radius: float = 0.36
    ergosphere_radius: float = 0.52
    photon_radius: float = 0.66
    singularity_radius: float = 0.10
    drag: float = 0.0
    throughput: float = 0.0
    escalation: float = 0.0
    embodiment_pressure: float = 0.0
    holon_count: int = 3
    anchor_note: str = ""


_DENSITY = " .·:;oO0@"


def _density(value: float) -> str:
    idx = min(len(_DENSITY) - 1, max(0, int(value * (len(_DENSITY) - 1))))
    return _DENSITY[idx]


class KerrViewport:
    def __init__(self, theme: HUDTheme = VOID_PURPLE_THEME) -> None:
        self.theme = theme

    def _color_codes(self) -> dict[str, str]:
        return {
            "purple": self.theme.kerr.purple_core.fg(),
            "blue": self.theme.kerr.ergosphere_blue.fg(),
            "white": self.theme.kerr.photon_white.fg(),
            "cyan": self.theme.kerr.singularity_cyan.fg(),
            "lilac": self.theme.kerr.dim_lilac.fg(),
            "red": self.theme.kerr.warning_red.fg(),
        }

    def _cell_for_point(
        self,
        state: KerrVisualState,
        x: int,
        y: int,
        *,
        cx: float,
        cy: float,
        scale: float,
        colors: dict[str, str],
    ) -> FrameCell:
        nx = (x - cx) / scale * 2.0
        ny = (y - cy) / scale * 2.0
        r = sqrt(nx * nx + ny * ny)
        theta = atan2(ny, nx)
        frame_drag = state.drag * 0.35 * sin(theta + state.frame_time_s * 2.1)
        warped_r = max(0.0, r + frame_drag)
        if abs(warped_r - state.photon_radius) < 0.03:
            return FrameCell(glyph=_density(0.95), fg_code=colors["white"])
        if abs(warped_r - state.ergosphere_radius) < 0.05:
            return FrameCell(glyph=_density(0.65 + state.throughput * 0.3), fg_code=colors["blue"])
        if abs(warped_r - state.horizon_radius) < 0.04:
            return FrameCell(glyph=_density(0.75 + state.embodiment_pressure * 0.2), fg_code=colors["lilac"])
        if warped_r < state.singularity_radius:
            return FrameCell(glyph=_density(1.0), fg_code=colors["cyan"] if state.escalation < 0.7 else colors["red"])
        if warped_r < state.horizon_radius:
            shadow = max(0.1, 1.0 - warped_r / max(state.horizon_radius, 0.001))
            return FrameCell(glyph=_density(shadow * 0.25), fg_code=colors["purple"])
        return FrameCell()

    def _orbital_cells(
        self,
        state: KerrVisualState,
        *,
        cx: float,
        cy: float,
        scale: float,
        colors: dict[str, str],
    ) -> list[tuple[int, int, FrameCell]]:
        orbit_radius = min(0.88, state.ergosphere_radius + 0.10)
        cells: list[tuple[int, int, FrameCell]] = []
        for i in range(max(1, state.holon_count)):
            phase = state.frame_time_s * (0.55 + i * 0.07) + i * (6.28318 / max(1, state.holon_count))
            hx = int(round(cx + cos(phase) * orbit_radius * scale * 0.45))
            hy = int(round(cy + sin(phase) * orbit_radius * scale * 0.25))
            cells.append((hx, hy, FrameCell(glyph="•", fg_code=colors["purple"] if i % 2 == 0 else colors["cyan"])))
        return cells

    def render_panel(self, state: KerrVisualState, width: int, height: int) -> list[str]:
        width = max(18, width)
        height = max(8, height)
        fb = AsciiFramebuffer(width=width, height=height)
        cx = (width - 1) / 2.0
        cy = (height - 1) / 2.0
        scale = min(width, height)
        colors = self._color_codes()
        for y in range(height):
            for x in range(width):
                cell = self._cell_for_point(state, x, y, cx=cx, cy=cy, scale=scale, colors=colors)
                if cell.glyph != " ":
                    fb.set(x, y, cell)
        for hx, hy, cell in self._orbital_cells(state, cx=cx, cy=cy, scale=scale, colors=colors):
            fb.set(hx, hy, cell)
        return fb.render_lines()


@dataclass(frozen=True)
class ForgeSignalState:
    verdict: str
    pass_count: int
    warn_count: int
    fail_count: int
    event_count: int
    risk_count: int
    phase_label: str
    anchor_note: str = ""


def kerr_state_from_forge(signal: ForgeSignalState, frame_time_s: float) -> KerrVisualState:
    total = max(1, signal.pass_count + signal.warn_count + signal.fail_count)
    throughput = min(1.0, signal.event_count / 8.0)
    escalation = min(1.0, (signal.fail_count + signal.risk_count) / max(1, total))
    embodiment = min(1.0, (signal.pass_count + signal.warn_count * 0.5) / total)
    horizon = 0.30 + embodiment * 0.12
    ergosphere = horizon + 0.14 + throughput * 0.08
    photon = min(0.82, ergosphere + 0.12)
    drag = 0.25 + throughput * 0.55 + escalation * 0.20
    return KerrVisualState(
        phase_label=signal.phase_label,
        frame_time_s=frame_time_s,
        horizon_radius=horizon,
        ergosphere_radius=ergosphere,
        photon_radius=photon,
        singularity_radius=0.07 + escalation * 0.05,
        drag=drag,
        throughput=throughput,
        escalation=escalation,
        embodiment_pressure=embodiment,
        holon_count=max(2, min(7, signal.pass_count + signal.warn_count + 1)),
        anchor_note=signal.anchor_note,
    )
