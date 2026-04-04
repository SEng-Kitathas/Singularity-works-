from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from .forge_context import ForgeContext
from .orchestration import evaluate_artifact


def _demo() -> int:
    workspace = Path(".sw_runs")
    context = ForgeContext(workspace=workspace, run_id=uuid4().hex[:12])
    sample = "def add(a, b):\n    return a + b\n"
    result = evaluate_artifact(context, "demo.py", sample)
    print(json.dumps({
        "accepted": result.accepted,
        "score": result.score,
        "accepted_because": result.accepted_because,
        "unresolved_because": result.unresolved_because,
        "operator_brief": result.operator_brief,
        "evidence_path": str(context.evidence_path),
    }, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="singularity-works")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="Run a small end-to-end intake demo.")
    args = parser.parse_args()
    if args.command == "demo":
        return _demo()
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
