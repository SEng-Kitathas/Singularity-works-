"""Portable console-script shims for qualified Singularity Works release surfaces.

These wrappers intentionally reuse the existing module `__main__` behavior without
requiring those modules to expose a callable named ``__main__``.
"""

from __future__ import annotations

import runpy


def forge() -> None:
    """Run the existing bounty reporter CLI as a console-script callable."""
    runpy.run_module("singularity_works.bounty_reporter", run_name="__main__", alter_sys=True)


def forge_hud() -> None:
    """Run the existing HUD demo/CLI surface as a console-script callable."""
    runpy.run_module("singularity_works.hud", run_name="__main__", alter_sys=True)


__all__ = ["forge", "forge_hud"]
