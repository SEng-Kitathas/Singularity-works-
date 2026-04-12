from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class RGB:
    r: int
    g: int
    b: int

    def fg(self) -> str:
        return f"\x1b[38;2;{self.r};{self.g};{self.b}m"

    def bg(self) -> str:
        return f"\x1b[48;2;{self.r};{self.g};{self.b}m"


@dataclass(frozen=True)
class KerrZonePalette:
    void_black: RGB
    glass: RGB
    purple_core: RGB
    pale_orchid: RGB
    dim_lilac: RGB
    ergosphere_blue: RGB
    photon_white: RGB
    singularity_cyan: RGB
    warning_red: RGB


@dataclass(frozen=True)
class HUDTheme:
    name: str
    kerr: KerrZonePalette


VOID_PURPLE_THEME = HUDTheme(
    name="void-purple",
    kerr=KerrZonePalette(
        void_black=RGB(3, 1, 8),
        glass=RGB(10, 6, 18),
        purple_core=RGB(167, 139, 250),
        pale_orchid=RGB(240, 234, 255),
        dim_lilac=RGB(139, 127, 168),
        ergosphere_blue=RGB(59, 130, 246),
        photon_white=RGB(255, 255, 255),
        singularity_cyan=RGB(34, 211, 238),
        warning_red=RGB(239, 68, 68),
    ),
)
