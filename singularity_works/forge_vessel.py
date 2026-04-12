from __future__ import annotations
# complexity_justified: vessel CLI stitches doctor, boot, runtime HUD, and terminal launch into one typed operator surface.

from dataclasses import dataclass
from pathlib import Path
import argparse
import json
import time

from .claude_vessel import launch_forge_vessel
from .ergo_boot import play_boot_sequence
from .forge_doctor import run_vessel_doctor
from .hud import ConsoleHUD, HudSnapshot
from .runtime import demo_run
from .window_anchor import maybe_apply_runtime_anchor


@dataclass(frozen=True)
class VesselHUDState:
    attach_title: str = "Claude"
    base_dir: str = "."


def _hud_loop(state: VesselHUDState) -> None:
    play_boot_sequence()
    anchor_plan = maybe_apply_runtime_anchor(state.attach_title)
    snap = HudSnapshot(
        mode="vessel",
        provider="local",
        session_id="forge-vessel",
        project_tag="singularity-works",
        phase="orbit",
        requirement="Claude vessel",
        radical="VESSEL+KERR",
        validator="doctor",
        progress_label="operator ready",
        progress_value=1.0,
        verdict="green",
        warranted_claims=1,
        total_claims=1,
        counts={"pass": 1, "warn": 0, "fail": 0, "residual": 0},
        stats={
            "terminal": "console-first",
            "theme": "void-purple",
            "attach": state.attach_title,
        },
        events=[
            "ergo boot complete",
            f"attach_title={state.attach_title}",
            f"window_anchor={(anchor_plan or {}).get('note', 'none')}",
        ],
    )
    hud = ConsoleHUD()
    with hud:
        hud.render(snap)
        time.sleep(1.25)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="forge-vessel")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor")
    boot_p = sub.add_parser("boot")
    boot_p.add_argument("--base-dir", default=".")
    hud_p = sub.add_parser("hud")
    hud_p.add_argument("--base-dir", default=".")
    hud_p.add_argument("--attach-title", default="Claude")
    launch_p = sub.add_parser("launch")
    launch_p.add_argument("--base-dir", default=".")
    launch_p.add_argument("--attach-title", default="Claude")
    demo_p = sub.add_parser("demo")
    demo_p.add_argument("--base-dir", default=".")

    args = parser.parse_args(argv)
    if args.cmd == "doctor":
        report = run_vessel_doctor()
        print(json.dumps({
            "passed": report.passed,
            "checks": [check.__dict__ for check in report.checks],
            "probes": [probe.__dict__ for probe in report.probes],
        }, indent=2))
        return 0 if report.passed else 1
    if args.cmd == "boot":
        play_boot_sequence()
        return 0
    if args.cmd == "hud":
        _hud_loop(VesselHUDState(attach_title=args.attach_title, base_dir=args.base_dir))
        return 0
    if args.cmd == "launch":
        receipt = launch_forge_vessel(Path(args.base_dir))
        print(json.dumps(receipt.__dict__, indent=2))
        return 0 if receipt.launched else 1
    if args.cmd == "demo":
        demo_run(Path(args.base_dir), good=False, show_hud=True)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
