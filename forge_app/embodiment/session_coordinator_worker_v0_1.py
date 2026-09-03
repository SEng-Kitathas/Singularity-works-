from __future__ import annotations

"""Minimal supervised session-coordinator child used by v0.1 crash qualification.

The worker intentionally receives no Attempt Store path or recovery writer.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile
import time

from forge_app.recovery.session_supervisor import READY_PROTOCOL


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
        os.replace(temp_name, path)
    finally:
        try:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--resume", required=True)
    parser.add_argument("--ready", required=True)
    parser.add_argument("--ready-checkpoint", default=None)
    parser.add_argument("--ready-resume", default=None)
    parser.add_argument("--sleep-seconds", type=float, default=300.0)
    args = parser.parse_args()

    receipt = {
        "protocol": READY_PROTOCOL,
        "checkpoint_id": args.ready_checkpoint or args.checkpoint,
        "resume_id": args.ready_resume or args.resume,
        "pid": os.getpid(),
        "instance_token": os.environ.get("SINGULARITY_SESSION_INSTANCE_TOKEN", ""),
    }
    _atomic_write_json(Path(args.ready), receipt)
    time.sleep(max(0.0, args.sleep_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
