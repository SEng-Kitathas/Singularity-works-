from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "CHECKPOINT.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors: list[str] = []
    expected_paths = {row["path"] for row in data.get("files", [])}

    for row in data.get("files", []):
        path = ROOT / row["path"]
        if not path.is_file():
            errors.append(f"MISSING {row['path']}")
            continue
        if path.stat().st_size != row["bytes"]:
            errors.append(f"SIZE {row['path']}")
        actual = sha256(path)
        if actual != row["sha256"]:
            errors.append(f"SHA {row['path']} expected={row['sha256']} actual={actual}")

    actual_paths = {
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in ROOT.rglob("*")
        if path.is_file() and path.name != "CHECKPOINT.json"
    }
    extras = sorted(actual_paths - expected_paths)
    missing_from_tree = sorted(expected_paths - actual_paths)
    if extras:
        errors.append(f"UNMANIFESTED {extras}")
    if missing_from_tree:
        errors.append(f"MANIFEST_ONLY {missing_from_tree}")

    if errors:
        print("PROJECT CONTROL CHECKPOINT: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PROJECT CONTROL CHECKPOINT: PASS")
    print(f"schema={data.get('schema')}")
    print(f"qualified_main={data.get('qualified_public_main_observed')}")
    print(f"canonical_process={data.get('canonical_process', {}).get('name')}")
    print(f"files={len(expected_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
