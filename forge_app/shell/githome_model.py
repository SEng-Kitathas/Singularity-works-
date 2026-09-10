from __future__ import annotations

"""Renderer-neutral GitHome project-context model v0.1.

This module performs read-only local project/Git observation and builds a disposable
frontend navigation projection. It does not mutate files, Git state, semantic state,
or runtime authority.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import subprocess
from typing import Any, Iterable

from forge_app.hud.workbench_model import WorkbenchModel


PROJECT_SNAPSHOT_SCHEMA = "forge-githome-project-snapshot/0.1"
GITHOME_MODEL_SCHEMA = "forge-githome-model/0.1"
GITHOME_STATE_SCHEMA = "forge-githome-interaction-state/0.1"
GIT_TIMEOUT_SECONDS = 5.0
_MUTATING_GIT_VERBS = frozenset(
    {"add", "commit", "checkout", "switch", "restore", "reset", "clean", "push", "pull", "fetch", "merge", "rebase"}
)


class GitHomeModelError(ValueError):
    """Fail-closed invalid project/read-model input."""


@dataclass(frozen=True)
class ProjectEntry:
    path: str
    name: str
    kind: str
    exists: bool
    size_bytes: int | None
    tracked: bool
    ignored: bool
    git_code: str | None
    git_state: str
    descendant_file_count: int
    direct_child_count: int
    descendant_git_states: tuple[str, ...]


@dataclass(frozen=True)
class ProjectSnapshot:
    schema: str
    root_path: str
    root_name: str
    git_available: bool
    git_error: str | None
    head: str | None
    branch: str | None
    upstream: str | None
    ahead: int | None
    behind: int | None
    dirty: bool | None
    entries: tuple[ProjectEntry, ...]
    file_count: int
    directory_count: int
    ignored_file_count: int
    untracked_file_count: int
    changed_tracked_file_count: int
    scan_errors: tuple[str, ...]
    observer_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @property
    def snapshot_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GitHomeInteractionState:
    schema: str = GITHOME_STATE_SCHEMA
    query: str = ""
    selected_path: str | None = None
    show_ignored: bool = False


@dataclass(frozen=True)
class GitHomeWorkbenchBinding:
    model_sha256: str
    source_bundle_id: str
    currentness: str
    projection_authority: str


@dataclass(frozen=True)
class GitHomeModel:
    schema: str
    project_snapshot_sha256: str
    project_observer_authority: str
    state: GitHomeInteractionState
    root_name: str
    git_available: bool
    head: str | None
    branch: str | None
    upstream: str | None
    ahead: int | None
    behind: int | None
    dirty: bool | None
    visible_entries: tuple[ProjectEntry, ...]
    total_entry_count: int
    visible_entry_count: int
    breadcrumb: tuple[str, ...]
    selected_entry: ProjectEntry | None
    workbench: GitHomeWorkbenchBinding | None
    scan_errors: tuple[str, ...]
    projection_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @property
    def model_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GitHomeCommandResult:
    accepted: bool
    state: GitHomeInteractionState
    ui_intent: str
    message: str
    consequence_scope: str = "READ_ONLY_UI"


def _run_git(repo: Path, args: Iterable[str], *, nul: bool = False) -> subprocess.CompletedProcess[bytes]:
    """Run an explicitly read-only Git query and return raw bytes."""
    argv = list(args)
    if not argv:
        raise GitHomeModelError("empty Git query")
    if argv[0].casefold() in _MUTATING_GIT_VERBS:
        raise GitHomeModelError(f"mutating Git verb forbidden in GitHome observer: {argv[0]}")
    return subprocess.run(
        ["git", "-C", str(repo), *argv],
        capture_output=True,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="surrogateescape")


def _split_nul(data: bytes) -> list[str]:
    if not data:
        return []
    return [_decode(part) for part in data.split(b"\0") if part]


def _git_header(repo: Path) -> tuple[bool, str | None, str | None, str | None, int | None, int | None, str | None]:
    result = _run_git(repo, ["status", "--porcelain=v2", "--branch", "--untracked-files=no"])
    if result.returncode != 0:
        return False, None, None, None, None, None, _decode(result.stderr).strip() or "not a Git working tree"
    head = branch = upstream = None
    ahead = behind = None
    for line in _decode(result.stdout).splitlines():
        if line.startswith("# branch.oid "):
            value = line[len("# branch.oid ") :].strip()
            head = None if value == "(initial)" else value
        elif line.startswith("# branch.head "):
            value = line[len("# branch.head ") :].strip()
            branch = None if value == "(detached)" else value
        elif line.startswith("# branch.upstream "):
            upstream = line[len("# branch.upstream ") :].strip() or None
        elif line.startswith("# branch.ab "):
            parts = line[len("# branch.ab ") :].split()
            try:
                ahead = int(parts[0][1:])
                behind = int(parts[1][1:])
            except (IndexError, ValueError):
                ahead = behind = None
    return True, head, branch, upstream, ahead, behind, None


def _tracked_paths(repo: Path) -> set[str]:
    result = _run_git(repo, ["ls-files", "-z"])
    if result.returncode != 0:
        raise GitHomeModelError(_decode(result.stderr).strip() or "git ls-files failed")
    return set(_split_nul(result.stdout))


def _ignored_paths(repo: Path) -> set[str]:
    result = _run_git(repo, ["ls-files", "-z", "--others", "--ignored", "--exclude-standard"])
    if result.returncode != 0:
        raise GitHomeModelError(_decode(result.stderr).strip() or "git ignored-file query failed")
    return set(_split_nul(result.stdout))


def _status_codes(repo: Path) -> dict[str, str]:
    result = _run_git(repo, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=matching"])
    if result.returncode != 0:
        raise GitHomeModelError(_decode(result.stderr).strip() or "git status failed")
    records = _split_nul(result.stdout)
    out: dict[str, str] = {}
    i = 0
    while i < len(records):
        record = records[i]
        if len(record) < 3:
            raise GitHomeModelError(f"malformed porcelain-v1 record: {record!r}")
        code = record[:2]
        path = record[3:] if record[2] == " " else record[2:].lstrip()
        out[path] = code
        if ("R" in code or "C" in code) and i + 1 < len(records):
            original = records[i + 1]
            out.setdefault(original, "D ")
            i += 1
        i += 1
    return out


def _normalize_git_state(code: str | None, *, tracked: bool, ignored: bool, exists: bool, git_available: bool) -> str:
    if not git_available:
        return "NOT_GIT"
    if ignored or code == "!!":
        return "IGNORED"
    if code == "??":
        return "UNTRACKED"
    if code is None:
        if tracked and not exists:
            return "DELETED"
        return "CLEAN" if tracked else "UNKNOWN"
    x, y = code[0], code[1]
    if "U" in code or code in {"AA", "DD"}:
        return "CONFLICTED"
    if "R" in code:
        return "RENAMED"
    if "C" in code:
        return "COPIED"
    if "D" in code:
        return "DELETED"
    index_changed = x != " "
    worktree_changed = y != " "
    if index_changed and worktree_changed:
        return "STAGED_AND_MODIFIED"
    if index_changed:
        return "STAGED"
    if worktree_changed:
        return "MODIFIED"
    return "CLEAN"


def _safe_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def inspect_project(root_path: str | Path) -> ProjectSnapshot:
    root = Path(root_path).resolve()
    if not root.exists():
        raise GitHomeModelError(f"project root missing: {root}")
    if not root.is_dir():
        raise GitHomeModelError(f"project root is not a directory: {root}")

    git_available, head, branch, upstream, ahead, behind, git_error = _git_header(root)
    tracked: set[str] = set()
    ignored: set[str] = set()
    codes: dict[str, str] = {}
    scan_errors: list[str] = []
    if git_available:
        try:
            tracked = _tracked_paths(root)
            ignored = _ignored_paths(root)
            codes = _status_codes(root)
        except (GitHomeModelError, subprocess.SubprocessError, OSError) as exc:
            scan_errors.append(f"Git detail scan failed: {type(exc).__name__}: {exc}")

    file_meta: dict[str, tuple[str, bool, int | None]] = {}
    directories: set[str] = {"."}

    def onerror(exc: OSError) -> None:
        scan_errors.append(f"filesystem scan error: {type(exc).__name__}: {exc}")

    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False, onerror=onerror):
        current_path = Path(current)
        dirnames[:] = sorted(name for name in dirnames if not (current_path == root and name == ".git"))
        for dirname in dirnames:
            path = current_path / dirname
            rel = _safe_rel(path, root)
            directories.add(rel)
            if path.is_symlink():
                try:
                    size = path.lstat().st_size
                except OSError:
                    size = None
                file_meta[rel] = ("symlink", True, size)
        for filename in sorted(filenames):
            path = current_path / filename
            rel = _safe_rel(path, root)
            try:
                if path.is_symlink():
                    kind = "symlink"
                    size = path.lstat().st_size
                else:
                    kind = "file"
                    size = path.stat().st_size
                file_meta[rel] = (kind, True, size)
            except OSError as exc:
                file_meta[rel] = ("file", True, None)
                scan_errors.append(f"stat failed for {rel}: {type(exc).__name__}: {exc}")

    # Deleted tracked files do not exist on disk but must remain visible in the complete project model.
    for rel in sorted(tracked | set(codes)):
        if rel not in file_meta and rel not in directories and not rel.endswith("/"):
            file_meta[rel] = ("missing", False, None)
            parent = PurePosixPath(rel).parent
            while str(parent) not in {"", "."}:
                directories.add(parent.as_posix())
                parent = parent.parent

    file_entries: dict[str, ProjectEntry] = {}
    for rel, (kind, exists, size) in sorted(file_meta.items()):
        is_tracked = rel in tracked
        is_ignored = rel in ignored or codes.get(rel) == "!!"
        code = codes.get(rel)
        state = _normalize_git_state(code, tracked=is_tracked, ignored=is_ignored, exists=exists, git_available=git_available)
        file_entries[rel] = ProjectEntry(
            path=rel,
            name=PurePosixPath(rel).name,
            kind=kind,
            exists=exists,
            size_bytes=size,
            tracked=is_tracked,
            ignored=is_ignored,
            git_code=code,
            git_state=state,
            descendant_file_count=0,
            direct_child_count=0,
            descendant_git_states=(),
        )

    all_paths = set(file_entries) | directories
    entries: list[ProjectEntry] = list(file_entries.values())
    for rel in sorted(directories, key=lambda value: (value.count("/"), value)):
        prefix = "" if rel == "." else rel + "/"
        descendant_files = [entry for path, entry in file_entries.items() if path.startswith(prefix)]
        direct_children = {
            path[len(prefix) :].split("/", 1)[0]
            for path in all_paths
            if path != rel and path.startswith(prefix) and path[len(prefix) :]
        }
        entries.append(
            ProjectEntry(
                path=rel,
                name=root.name if rel == "." else PurePosixPath(rel).name,
                kind="directory",
                exists=True,
                size_bytes=None,
                tracked=any(item.tracked for item in descendant_files),
                ignored=bool(descendant_files) and all(item.ignored for item in descendant_files),
                git_code=None,
                git_state="NOT_GIT" if not git_available else "AGGREGATE",
                descendant_file_count=len(descendant_files),
                direct_child_count=len(direct_children),
                descendant_git_states=tuple(sorted({item.git_state for item in descendant_files})),
            )
        )

    entries.sort(key=lambda entry: (entry.path != ".", entry.path.casefold(), entry.kind))
    changed_states = {"MODIFIED", "STAGED", "STAGED_AND_MODIFIED", "DELETED", "RENAMED", "COPIED", "CONFLICTED"}
    return ProjectSnapshot(
        schema=PROJECT_SNAPSHOT_SCHEMA,
        root_path=str(root),
        root_name=root.name,
        git_available=git_available,
        git_error=git_error,
        head=head,
        branch=branch,
        upstream=upstream,
        ahead=ahead,
        behind=behind,
        dirty=(any(entry.git_state not in {"CLEAN", "IGNORED"} for entry in file_entries.values()) if git_available else None),
        entries=tuple(entries),
        file_count=len(file_entries),
        directory_count=len(directories),
        ignored_file_count=sum(entry.ignored for entry in file_entries.values()),
        untracked_file_count=sum(entry.git_state == "UNTRACKED" for entry in file_entries.values()),
        changed_tracked_file_count=sum(entry.tracked and entry.git_state in changed_states for entry in file_entries.values()),
        scan_errors=tuple(scan_errors),
    )


def _breadcrumb(selected_path: str | None) -> tuple[str, ...]:
    if selected_path is None or selected_path == ".":
        return ()
    return tuple(PurePosixPath(selected_path).parts)


def build_githome_model(
    snapshot: ProjectSnapshot,
    *,
    state: GitHomeInteractionState | None = None,
    workbench: WorkbenchModel | None = None,
) -> GitHomeModel:
    if snapshot.observer_authority != "NONE":
        raise GitHomeModelError("project observer authority must remain NONE")
    state = state or GitHomeInteractionState()
    by_path = {entry.path: entry for entry in snapshot.entries}
    if state.selected_path is not None and state.selected_path not in by_path:
        raise GitHomeModelError(f"selection references unknown project path: {state.selected_path}")
    needle = state.query.strip().casefold()
    visible = [
        entry
        for entry in snapshot.entries
        if (state.show_ignored or not entry.ignored)
        and (not needle or needle in entry.path.casefold() or needle in entry.git_state.casefold())
    ]
    binding = None
    if workbench is not None:
        if workbench.projection_authority != "NONE":
            raise GitHomeModelError("Workbench projection authority must remain NONE")
        binding = GitHomeWorkbenchBinding(
            model_sha256=workbench.model_sha256,
            source_bundle_id=workbench.source_bundle_id,
            currentness=workbench.currentness,
            projection_authority=workbench.projection_authority,
        )
    return GitHomeModel(
        schema=GITHOME_MODEL_SCHEMA,
        project_snapshot_sha256=snapshot.snapshot_sha256,
        project_observer_authority=snapshot.observer_authority,
        state=state,
        root_name=snapshot.root_name,
        git_available=snapshot.git_available,
        head=snapshot.head,
        branch=snapshot.branch,
        upstream=snapshot.upstream,
        ahead=snapshot.ahead,
        behind=snapshot.behind,
        dirty=snapshot.dirty,
        visible_entries=tuple(visible),
        total_entry_count=len(snapshot.entries),
        visible_entry_count=len(visible),
        breadcrumb=_breadcrumb(state.selected_path),
        selected_entry=by_path.get(state.selected_path) if state.selected_path else None,
        workbench=binding,
        scan_errors=snapshot.scan_errors,
    )


def apply_githome_command(
    state: GitHomeInteractionState,
    command: str,
    *,
    snapshot: ProjectSnapshot,
) -> GitHomeCommandResult:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        return GitHomeCommandResult(False, state, "NONE", f"command parse error: {exc}")
    if not tokens:
        return GitHomeCommandResult(False, state, "NONE", "empty command")
    name = tokens[0].casefold()
    if name == "home" and len(tokens) == 1:
        return GitHomeCommandResult(True, GitHomeInteractionState(), "RESET_PROJECT_VIEW", "GitHome view reset.")
    if name == "clear" and len(tokens) == 1:
        return GitHomeCommandResult(True, GitHomeInteractionState(show_ignored=state.show_ignored), "CLEAR_FILTER_SELECTION", "Search and selection cleared.")
    if name == "find" and len(tokens) >= 2:
        query = " ".join(tokens[1:]).strip()
        return GitHomeCommandResult(True, GitHomeInteractionState(query=query, selected_path=state.selected_path, show_ignored=state.show_ignored), "SET_QUERY", f"Project search set to {query!r}.")
    if name == "select" and len(tokens) == 2:
        path = tokens[1].replace("\\", "/")
        if path not in {entry.path for entry in snapshot.entries}:
            return GitHomeCommandResult(False, state, "NONE", f"unknown project path: {path}")
        return GitHomeCommandResult(True, GitHomeInteractionState(query=state.query, selected_path=path, show_ignored=state.show_ignored), "SELECT_PROJECT_PATH", f"Selected {path}.")
    if name == "show-ignored" and len(tokens) == 1:
        return GitHomeCommandResult(True, GitHomeInteractionState(query=state.query, selected_path=state.selected_path, show_ignored=True), "SHOW_IGNORED", "Ignored project paths visible.")
    if name == "hide-ignored" and len(tokens) == 1:
        return GitHomeCommandResult(True, GitHomeInteractionState(query=state.query, selected_path=state.selected_path, show_ignored=False), "HIDE_IGNORED", "Ignored project paths hidden from presentation only.")
    if name in _MUTATING_GIT_VERBS:
        return GitHomeCommandResult(False, state, "NONE", f"Git mutation disabled in read-only GitHome v0.1: {name}", consequence_scope="DISABLED")
    return GitHomeCommandResult(False, state, "NONE", f"unsupported read-only GitHome command: {name}")


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: max(0, width - 1)] + "…"


def render_githome_text(model: GitHomeModel, *, width: int = 110, row_limit: int = 18) -> str:
    width = max(72, min(int(width), 180))
    row_limit = max(1, int(row_limit))
    lines: list[str] = []

    def add(value: str = "") -> None:
        lines.append(_truncate(value, width))

    add("SINGULARITY WORKS / GITHOME")
    add(f"PROJECT {model.root_name}  BRANCH {model.branch or '—'}  HEAD {(model.head or '—')[:12]}  DIRTY {model.dirty}")
    if model.upstream:
        add(f"UPSTREAM {model.upstream}  AHEAD {model.ahead if model.ahead is not None else '—'}  BEHIND {model.behind if model.behind is not None else '—'}")
    add(f"SNAPSHOT {model.project_snapshot_sha256[:16]}  AUTHORITY {model.project_observer_authority}/{model.projection_authority}")
    if model.workbench is not None:
        add(f"FORGE {model.workbench.source_bundle_id}  CURRENTNESS {model.workbench.currentness}  MODEL {model.workbench.model_sha256[:12]}")
    add("─" * width)
    add(f"TREE  visible={model.visible_entry_count}/{model.total_entry_count}  query={model.state.query or '—'}  ignored={'shown' if model.state.show_ignored else 'hidden'}")
    for entry in model.visible_entries[:row_limit]:
        marker = ">" if model.state.selected_path == entry.path else " "
        size = "—" if entry.size_bytes is None else str(entry.size_bytes)
        add(f"{marker} {entry.git_state:<19} {entry.kind:<9} {entry.path}  {size}")
    if len(model.visible_entries) > row_limit:
        add(f"… {len(model.visible_entries) - row_limit} more entries retained in model")
    add("─" * width)
    if model.selected_entry is not None:
        add("BREADCRUMB  " + " / ".join(model.breadcrumb))
        add(f"SELECTED {model.selected_entry.path}  state={model.selected_entry.git_state} tracked={model.selected_entry.tracked} ignored={model.selected_entry.ignored}")
    else:
        add("SELECTED (none)")
    if model.scan_errors:
        add("SCAN ERRORS")
        for error in model.scan_errors:
            add("! " + error)
    return "\n".join(lines) + "\n"
