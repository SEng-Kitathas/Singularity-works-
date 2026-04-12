from __future__ import annotations
# compatibility wrapper: canonical vessel launcher now lives in singularity_works.vessel

from .vessel import ClaudeProcessTarget, TerminalHostKind, TerminalHostSpec, VesselLaunchPlan, build_vessel_launch_plan, launch_claude_vessel

__all__ = [
    "ClaudeProcessTarget",
    "TerminalHostKind",
    "TerminalHostSpec",
    "VesselLaunchPlan",
    "build_vessel_launch_plan",
    "launch_claude_vessel",
]
