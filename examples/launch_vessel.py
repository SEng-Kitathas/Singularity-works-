from __future__ import annotations
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from singularity_works.cockpit_runtime import build_vessel_launch_plan, run_vessel_doctor

if __name__ == "__main__":
    doctor = run_vessel_doctor(ROOT)
    plan = build_vessel_launch_plan(ROOT)
    print(json.dumps({
        "doctor_passed": doctor.passed,
        "checks": [check.__dict__ for check in doctor.checks],
        "plan": {
            "python_executable": plan.python_executable,
            "forge_entry": plan.forge_entry,
            "claude_target": plan.claude_target.executable if plan.claude_target else None,
            "terminal_host": plan.terminal_host,
            "project_root": plan.project_root,
        },
    }, indent=2))
