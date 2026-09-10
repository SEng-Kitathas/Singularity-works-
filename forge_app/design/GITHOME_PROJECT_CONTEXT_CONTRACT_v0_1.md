# GitHome Project Context Contract v0.1

Status: **ATTEMPT 0 — READ-ONLY FRONTEND CANDIDATE / PRESERVE BEFORE FIRST EXECUTION**  
Date: 2026-09-09  
Authority: App project-navigation/UI state only. GitHome does not own Forge semantic truth.

## Purpose
Give the Singularity Works shell a real project surface rather than a decorative file tree.

GitHome v0.1 observes a local project directory and, when present, its Git working tree. It builds a deterministic renderer-neutral snapshot containing the complete user-project tree outside VCS-internal `.git/`, file existence/type/size, tracked/untracked/ignored state, index/worktree status, branch/head/upstream/ahead-behind, and explicit scan errors.

The display model may filter or hide ignored paths for operator convenience, but the underlying snapshot retains them. `LAZY_OR_FILTERED_RENDERING != INCOMPLETE_PROJECT_MODEL`.

## Boundaries
- `GITHOME != GIT_ONLY` — non-Git folders still produce a project snapshot.
- `PROJECT_IDENTITY != GIT_IDENTITY` — the observed root is the project context; Git is one state dimension.
- `GITHOME_OWNS_PROJECT_NAVIGATION; FORGE_OWNS_PROJECT_UNDERSTANDING`.
- `.git/` internal object/database files are VCS implementation metadata, not project-content nodes in v0.1.
- Git commands used by inspection are read-only (`status`, `ls-files`).
- v0.1 performs no checkout, add, commit, reset, clean, push, pull, fetch, network access, file mutation, or semantic analysis.

## Project snapshot
Snapshot fields include:
- observed root path/name;
- Git availability/error;
- exact HEAD, branch, upstream, ahead/behind when Git reports them;
- dirty state;
- every observed project directory outside `.git/`;
- every filesystem file plus tracked paths that are currently deleted;
- file kind (`file`, `symlink`, `missing`);
- byte size when available;
- tracked / ignored booleans;
- exact two-character porcelain status code when present;
- normalized presentation state (`CLEAN`, `MODIFIED`, `STAGED`, `STAGED_AND_MODIFIED`, `DELETED`, `RENAMED`, `COPIED`, `CONFLICTED`, `UNTRACKED`, `IGNORED`, `NOT_GIT`, `UNKNOWN`);
- directory descendant counts and aggregate descendant Git states;
- scan errors rather than silent omission.

Snapshot canonical JSON and SHA-256 are deterministic for equal observed project state.

## Display / interaction state
GitHome presentation state may hold:
- substring query;
- selected project-relative path;
- show/hide ignored preference.

Filtering affects only visible rows. It never deletes nodes from the project snapshot.
Selection must reference an existing snapshot entry and produces a breadcrumb derived from the path; selection does not create semantic focus/promotion authority.

## Forge Workbench composition
GitHome may bind a qualified Workbench model by exact model SHA and source bundle ID. It carries only the binding/currentness metadata needed to place the semantic pane beside project navigation.

It SHALL NOT copy Forge facts into GitHome's project state, reinterpret semantic verdicts, or turn Git status into semantic truth.

`GIT_STATUS != SEMANTIC_VERDICT`  
`WORKBENCH_BINDING != SEMANTIC_AUTHORITY_TRANSFER`.

## Read-only command reducer
v0.1 commands:
- `home`
- `clear`
- `find <text>`
- `select <project-relative-path>`
- `show-ignored`
- `hide-ignored`

Any Git mutation-like command (`add`, `commit`, `checkout`, `reset`, `clean`, `push`, `pull`, `fetch`, `merge`, `rebase`) is rejected as unsupported read-only UI input. No shell fallback exists.

## Qualification gates
1. A real temporary Git fixture must expose clean, modified, staged, untracked, ignored, and deleted states correctly.
2. Deleted tracked paths remain represented even though absent from the filesystem.
3. Ignored files remain in the snapshot when hidden from the default presentation.
4. Non-Git directories remain inspectable without fabricated Git identity.
5. Selection/search never mint paths absent from the snapshot.
6. Snapshot/model canonical identity is deterministic.
7. Workbench composition carries exact Workbench hash/bundle/currentness while GitHome authority remains NONE.
8. Current App repository can be inspected read-only with independent file/status count cross-check and no source mutation.
9. No mutating Git verb exists in the implementation's subprocess command set.

## Promotion ceiling
Passing v0.1 qualifies only read-only project/Git observation and renderer-neutral navigation composition. It does not qualify Git mutation UX, remote/provider state, Vault integration, source-secret classification, native shell rendering, semantic overlays per file, or large-repository performance.
