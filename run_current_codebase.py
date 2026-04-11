from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERIFY_BUILD = ROOT / "examples" / "verify_build.py"


def main() -> int:
    if not VERIFY_BUILD.exists():
        print(f"Missing verification script: {VERIFY_BUILD}", file=sys.stderr)
        return 1
    result = subprocess.run([sys.executable, str(VERIFY_BUILD)], cwd=str(ROOT))
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
