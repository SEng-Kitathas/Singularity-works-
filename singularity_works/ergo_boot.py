from __future__ import annotations
# complexity_justified: startup boot player composes typed Kerr state, terminal timing, and HUD-safe rendering.

from dataclasses import dataclass
import shutil
import sys
import time

from .ergo_kerr import BootFrame, KerrState, boot_frames, render_kerr_panel, total_boot_duration
from .hud_theme import VOID_PURPLE_THEME

_RESET = "[0m"
_CLEAR = "[H[2J"


@dataclass(frozen=True)
class BootRenderConfig:
    width: int = 44
    height: int = 14
    use_alt_screen: bool = True
    frame_interval_s: float = 0.05
    hold_handoff_s: float = 0.22


def _boot_state(frame: BootFrame) -> KerrState:
    p = frame.progress
    phase = frame.phase
    if phase.value == "cold_boot":
        return KerrState(phase=phase, normalized_progress=p, horizon_radius=0.10 + p * 0.03, ergosphere_radius=0.18 + p * 0.06, photon_radius=0.26 + p * 0.04, singularity_radius=0.03 + p * 0.01, drag=0.05 + p * 0.12, hazard_pressure=0.08, proof_pressure=0.12 + p * 0.20, orbitals=1, label=frame.label, sublabel=frame.sublabel)
    if phase.value == "singularity_ignition":
        return KerrState(phase=phase, normalized_progress=p, horizon_radius=0.13 + p * 0.04, ergosphere_radius=0.24 + p * 0.05, photon_radius=0.31 + p * 0.05, singularity_radius=0.04 + p * 0.02, drag=0.18 + p * 0.20, hazard_pressure=0.15 + p * 0.10, proof_pressure=0.28 + p * 0.20, orbitals=2, label=frame.label, sublabel=frame.sublabel)
    if phase.value == "ergosphere_formation":
        return KerrState(phase=phase, normalized_progress=p, horizon_radius=0.16 + p * 0.03, ergosphere_radius=0.30 + p * 0.06, photon_radius=0.36 + p * 0.05, singularity_radius=0.05 + p * 0.02, drag=0.35 + p * 0.25, blue_shift_bias=0.35 + p * 0.20, hazard_pressure=0.18 + p * 0.12, proof_pressure=0.42 + p * 0.22, orbitals=3 + int(p * 2), label=frame.label, sublabel=frame.sublabel)
    if phase.value == "orbit_lock":
        return KerrState(phase=phase, normalized_progress=p, horizon_radius=0.19, ergosphere_radius=0.36, photon_radius=0.43, singularity_radius=0.065, drag=0.62, blue_shift_bias=0.62, hazard_pressure=0.22, proof_pressure=0.74, orbitals=5, label=frame.label, sublabel=frame.sublabel)
    return KerrState(phase=phase, normalized_progress=1.0, horizon_radius=0.20, ergosphere_radius=0.37, photon_radius=0.44, singularity_radius=0.07, drag=0.68, blue_shift_bias=0.70, hazard_pressure=0.20, proof_pressure=0.88, orbitals=6, label=frame.label, sublabel=frame.sublabel)


def _progress_bar(progress: float, width: int = 30) -> str:
    filled = max(0, min(width, int(round(progress * width))))
    return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"


def _render_frame(frame: BootFrame, *, width: int, height: int, tick: float) -> str:
    theme = VOID_PURPLE_THEME.kerr
    panel = render_kerr_panel(_boot_state(frame), width=width, height=height, tick=tick)
    cols, _ = shutil.get_terminal_size(fallback=(120, 40))
    body: list[str] = []
    body.append(f"{theme.purple_core.fg()}Singularity Works — Ergo-Light Boot{_RESET}")
    body.append(f"{theme.pale_orchid.fg()}{frame.label}{_RESET}  {theme.dim_lilac.fg()}{frame.sublabel}{_RESET}")
    body.append(f"{theme.dim_lilac.fg()}{_progress_bar(frame.progress, 34)} {int(frame.progress * 100):3d}%{_RESET}")
    body.extend(panel.lines)
    return _CLEAR + "\n".join(line[:cols] for line in body)


def play_boot_sequence(config: BootRenderConfig = BootRenderConfig()) -> None:
    start = time.monotonic()
    end = start + total_boot_duration()
    while True:
        now = time.monotonic()
        elapsed = now - start
        frame = boot_frames(elapsed)
        sys.stdout.write(_render_frame(frame, width=config.width, height=config.height, tick=elapsed))
        sys.stdout.flush()
        if now >= end:
            break
        time.sleep(config.frame_interval_s)
    time.sleep(config.hold_handoff_s)
