from __future__ import annotations

"""Read-only real-repository integration discriminator for GitHome v0.1."""

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from forge_app.shell.githome_model import GitHomeInteractionState, build_githome_model, inspect_project, render_githome_text


SCHEMA = "forge-githome-real-repo-integration/0.1"


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False, timeout=5)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace") or f"git {' '.join(args)} failed")
    return result.stdout


def independent_fs_counts(root: Path) -> tuple[int, int]:
    files = 0
    directories = 1
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        dirnames[:] = [name for name in dirnames if not (current_path == root and name == ".git")]
        directories += len(dirnames)
        files += len(filenames)
    return files, directories


def run(repo: Path, expected_head: str, selected_path: str) -> dict[str, Any]:
    repo = repo.resolve()
    before = git(repo, "status", "--porcelain=v1", "--untracked-files=all").decode("utf-8", errors="replace").splitlines()
    snapshot = inspect_project(repo)
    fs_files, fs_dirs = independent_fs_counts(repo)
    tracked = [part for part in git(repo, "ls-files", "-z").split(b"\0") if part]
    ignored = [part for part in git(repo, "ls-files", "-z", "--others", "--ignored", "--exclude-standard").split(b"\0") if part]
    all_model = build_githome_model(snapshot, state=GitHomeInteractionState(show_ignored=True, selected_path=selected_path))
    default_model = build_githome_model(snapshot, state=GitHomeInteractionState(selected_path=selected_path))
    rendered = render_githome_text(default_model, width=120, row_limit=8)
    after = git(repo, "status", "--porcelain=v1", "--untracked-files=all").decode("utf-8", errors="replace").splitlines()
    file_entries = [entry for entry in snapshot.entries if entry.kind != "directory"]
    tracked_model = sum(entry.tracked for entry in file_entries)
    root_entry = next((entry for entry in snapshot.entries if entry.path == "."), None)
    checks = {
        "git_available": snapshot.git_available is True,
        "head_exact": snapshot.head == expected_head,
        "branch_present": isinstance(snapshot.branch, str) and bool(snapshot.branch),
        "source_clean_before": before == [],
        "source_clean_after": after == [],
        "snapshot_not_dirty": snapshot.dirty is False,
        "filesystem_file_count_exact": snapshot.file_count == fs_files,
        "filesystem_directory_count_exact": snapshot.directory_count == fs_dirs,
        "tracked_file_count_exact": tracked_model == len(tracked),
        "ignored_file_count_exact": snapshot.ignored_file_count == len(ignored),
        "entry_count_exact": len(snapshot.entries) == snapshot.file_count + snapshot.directory_count,
        "root_descendant_count_exact": root_entry is not None and root_entry.descendant_file_count == snapshot.file_count,
        "no_scan_errors": snapshot.scan_errors == (),
        "selection_exact": default_model.selected_entry is not None and default_model.selected_entry.path == selected_path,
        "ignored_retained_in_snapshot": all_model.visible_entry_count == all_model.total_entry_count,
        "default_projection_not_larger": default_model.visible_entry_count <= all_model.visible_entry_count,
        "authority_none": snapshot.observer_authority == "NONE" and default_model.projection_authority == "NONE",
        "render_contains_project": snapshot.root_name in rendered and (snapshot.branch or "") in rendered,
    }
    return {
        "schema": SCHEMA,
        "repo_name": snapshot.root_name,
        "head": snapshot.head,
        "branch": snapshot.branch,
        "upstream": snapshot.upstream,
        "ahead": snapshot.ahead,
        "behind": snapshot.behind,
        "snapshot_sha256": snapshot.snapshot_sha256,
        "model_sha256": default_model.model_sha256,
        "file_count": snapshot.file_count,
        "directory_count": snapshot.directory_count,
        "total_entry_count": len(snapshot.entries),
        "tracked_file_count": tracked_model,
        "ignored_file_count": snapshot.ignored_file_count,
        "visible_default": default_model.visible_entry_count,
        "visible_with_ignored": all_model.visible_entry_count,
        "selected_path": selected_path,
        "checks": checks,
        "pass_count": sum(value is True for value in checks.values()),
        "check_count": len(checks),
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "authority": "APP_FRONTEND_PROJECT_OBSERVATION_ONLY",
        "source_mutation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--selected-path", default="forge_app/hud/workbench_model.py")
    args = parser.parse_args()
    result = run(args.repo, args.expected_head, args.selected_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
