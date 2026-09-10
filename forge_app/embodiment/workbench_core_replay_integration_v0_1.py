from __future__ import annotations

"""Bounded cross-arm integration discriminator for Forge Workbench v0.1.

Reads exact already-qualified Core semantic-delta replay artifacts, verifies their
hashes/manifest identity, and projects them through the App Workbench read-only
preview contract. It performs no source mutation, Git mutation, network I/O, or
semantic replay itself.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from forge_app.hud.workbench_model import build_delta_preview


SCHEMA = "forge-workbench-core-replay-integration/0.1"
EXPECTED_SUMMARY_SCHEMA = "forge.semantic-delta-replay-pygoat/0.1.3"
EXPECTED_PLAN_VERSION = "forge.semantic-delta-replay/0.1.3"
EXPECTED_MANIFEST_SCHEMA = "forge.semantic-delta-replay-output-manifest/0.1.3"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_exact_json(path: Path, expected_sha256: str) -> tuple[bytes, dict[str, Any]]:
    data = path.read_bytes()
    actual = sha256_bytes(data)
    if actual != expected_sha256:
        raise ValueError(f"hash mismatch for {path.name}: expected {expected_sha256}, got {actual}")
    parsed = json.loads(data.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"JSON root must be object: {path.name}")
    return data, parsed


def manifest_entry(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("output manifest files must be a list")
    matches = [item for item in files if isinstance(item, dict) and item.get("path") == name]
    if len(matches) != 1:
        raise ValueError(f"output manifest must contain exactly one {name} entry")
    return matches[0]


def run(
    *,
    summary_path: Path,
    plan_path: Path,
    manifest_path: Path,
    summary_sha256: str,
    plan_sha256: str,
    manifest_sha256: str,
    expected_plan_id: str,
    expected_base_bundle_id: str,
    expected_target_bundle_id: str,
    expected_operation_count: int,
) -> dict[str, Any]:
    summary_bytes, summary = read_exact_json(summary_path, summary_sha256)
    plan_bytes, plan = read_exact_json(plan_path, plan_sha256)
    _manifest_bytes, manifest = read_exact_json(manifest_path, manifest_sha256)

    if summary.get("schema") != EXPECTED_SUMMARY_SCHEMA:
        raise ValueError(f"unexpected summary schema: {summary.get('schema')}")
    if plan.get("version") != EXPECTED_PLAN_VERSION:
        raise ValueError(f"unexpected plan version: {plan.get('version')}")
    if manifest.get("schema") != EXPECTED_MANIFEST_SCHEMA:
        raise ValueError(f"unexpected manifest schema: {manifest.get('schema')}")
    if manifest.get("count") != len(manifest.get("files", [])):
        raise ValueError("manifest count does not match file entries")

    summary_entry = manifest_entry(manifest, "summary.json")
    plan_entry = manifest_entry(manifest, "comment_plan.json")
    if summary_entry.get("sha256") != summary_sha256 or summary_entry.get("bytes") != len(summary_bytes):
        raise ValueError("summary manifest identity mismatch")
    if plan_entry.get("sha256") != plan_sha256 or plan_entry.get("bytes") != len(plan_bytes):
        raise ValueError("comment-plan manifest identity mismatch")

    preview = build_delta_preview(plan, summary)
    counts = {
        item.collection: {"remove": item.remove_count, "upsert": item.upsert_count}
        for item in preview.collection_counts
    }
    checks = {
        "qualified_bounded": preview.qualification_status == "QUALIFIED_BOUNDED",
        "authority_none": preview.delta_authority == "NONE",
        "plan_id_exact": preview.plan_id == expected_plan_id,
        "base_bundle_exact": preview.base_bundle_id == expected_base_bundle_id,
        "target_bundle_exact": preview.target_bundle_id == expected_target_bundle_id,
        "operation_count_exact": preview.operation_count == expected_operation_count,
        "all_core_checks_carried": preview.checks_passed == preview.checks_total == 14,
        "reverse_replay_evidence_visible": preview.reverse_replay_evidence is True,
        "materialization_disabled": preview.materialization_enabled is False,
        "claim_ceiling_exact": preview.claim_ceiling
        == "EXACT_SEMANTIC_BUNDLE_REPLAY_OVER_QUALIFIED_PYGOAT_SNAPSHOTS_ONLY",
        "fact_counts_exact": counts.get("facts") == {"remove": 113, "upsert": 113},
        "evidence_counts_exact": counts.get("evidence") == {"remove": 113, "upsert": 113},
        "entity_counts_exact": counts.get("entities") == {"remove": 1, "upsert": 1},
        "source_counts_exact": counts.get("sources") == {"remove": 1, "upsert": 1},
    }
    return {
        "schema": SCHEMA,
        "summary_sha256": summary_sha256,
        "plan_sha256": plan_sha256,
        "manifest_sha256": manifest_sha256,
        "plan_id": preview.plan_id,
        "base_bundle_id": preview.base_bundle_id,
        "target_bundle_id": preview.target_bundle_id,
        "operation_count": preview.operation_count,
        "collection_counts": counts,
        "qualification_status": preview.qualification_status,
        "claim_ceiling": preview.claim_ceiling,
        "materialization_enabled": preview.materialization_enabled,
        "materialization_reason": preview.materialization_reason,
        "checks": checks,
        "pass_count": sum(value is True for value in checks.values()),
        "check_count": len(checks),
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "authority": "APP_FRONTEND_INTEGRATION_EVIDENCE_ONLY",
        "not_proven": [
            "source-code edit materialization",
            "native shell/window/input qualification",
            "operator usability or task latency",
            "arbitrary semantic-delta versions",
            "App semantic authority",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--summary-sha256", required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--expected-plan-id", required=True)
    parser.add_argument("--expected-base-bundle-id", required=True)
    parser.add_argument("--expected-target-bundle-id", required=True)
    parser.add_argument("--expected-operation-count", type=int, required=True)
    args = parser.parse_args()
    result = run(
        summary_path=args.summary,
        plan_path=args.plan,
        manifest_path=args.manifest,
        summary_sha256=args.summary_sha256,
        plan_sha256=args.plan_sha256,
        manifest_sha256=args.manifest_sha256,
        expected_plan_id=args.expected_plan_id,
        expected_base_bundle_id=args.expected_base_bundle_id,
        expected_target_bundle_id=args.expected_target_bundle_id,
        expected_operation_count=args.expected_operation_count,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
