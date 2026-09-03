from __future__ import annotations

"""Concurrent writer child for Attempt Store zombie discriminator v0.2."""

import argparse
from pathlib import Path

from forge_app.recovery import AttemptStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--ordinal", required=True, type=int)
    args = parser.parse_args()

    ordinal = args.ordinal
    store = AttemptStore(Path(args.store))
    payload = f"concurrent-attempt-{ordinal:03d}\n".encode("utf-8")
    receipt = store.capture(
        payload,
        artifact_class="embodiment.concurrent_writer",
        producer="forge-app-attempt-store-concurrency-worker",
        intent=f"concurrent writer discriminator ordinal {ordinal}",
        metadata={"ordinal": ordinal},
        attempt_id=f"attempt-concurrent-{ordinal:03d}",
    )
    if not receipt.verified_readback:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
