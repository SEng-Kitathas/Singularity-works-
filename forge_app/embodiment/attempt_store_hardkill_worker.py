from __future__ import annotations

"""Child process used by the Attempt Store hard-kill discriminator."""

import argparse
import os
from pathlib import Path

from forge_app.recovery import AttemptStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument(
        "--kill-phase",
        required=True,
        choices=["after_rows_before_commit", "after_commit_before_readback"],
    )
    args = parser.parse_args()

    store = AttemptStore(Path(args.store))

    def hook(phase: str) -> None:
        if phase == args.kill_phase:
            os._exit(91 if phase == "after_rows_before_commit" else 92)

    store.capture(
        b"ATTEMPT-0-HARD-KILL-PAYLOAD\n",
        artifact_class="embodiment.hardkill",
        producer="forge-app-attempt-store-worker",
        intent=f"hard-kill discriminator at {args.kill_phase}",
        metadata={"kill_phase": args.kill_phase},
        attempt_id=args.attempt_id,
        phase_hook=hook,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
