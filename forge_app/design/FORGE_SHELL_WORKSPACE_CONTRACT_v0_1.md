# Forge Shell Workspace Contract v0.1

Status: **ATTEMPT 0 — FRONTEND COMPOSITION CANDIDATE / PRESERVE BEFORE FIRST EXECUTION**  
Date: 2026-09-09  
Authority: App shell focus/layout/composition only.

## Purpose
Turn qualified App frontend primitives into one operator-facing workspace instead of a collection of disconnected models.

Forge Shell Workspace v0.1 composes three existing bounded domains:
- **GitHome** — project navigation and Git/currentness observation;
- **Forge Workbench** — semantic/evidence/UNKNOWN/currentness presentation;
- **Ergo** — recovery / Attempt Store / source-health observation.

The shell owns only focus, layout, visible alerts, and exact model bindings. It does not merge or inherit the authority of the composed domains.

`SHELL_COMPOSITION != AUTHORITY_MERGE`.

## Current prerequisites
- Workbench v0.1 bounded admission `ad1e85f27e8ed61db5777341aaa3efe502988ba2a3dfc8897766d99129bacaea`;
- GitHome v0.1 bounded admission `3dd2681344f3d0591d22a5d8f543b365ae056733423698e9d7760eb515ef749e`;
- paired control `4783bf040546d0ba331879a104006540030d51fc` / CHECKPOINT `a537abe0c6b98ef5393b5fd0a8ea14cd5c7e270da1f3d8f46155419f189b0a26`, clean fresh-clone PASS 253;
- Ergo recovery observer remains authority NONE.

## Composition laws
- `GITHOME_OWNS_PROJECT_NAVIGATION`.
- `FORGE_OWNS_PROJECT_UNDERSTANDING`.
- `ERGO_OBSERVES_RECOVERY; ERGO_DOES_NOT_MINT_SUCCESS`.
- `SHELL_FOCUS != SEMANTIC_FOCUS`.
- `PROJECT_DIRTY != SEMANTIC_INVALID`.
- `SEMANTIC_MISMATCH != SOURCE_CORRUPTION`.
- `RECOVERY_REQUIRED != SOURCE_MUTATION_PERMISSION`.
- `SHELL_COMPOSITION != AUTHORITY_MERGE`.

## Workspace model
The renderer-neutral workspace stores only exact bindings and UI state:
- shell interaction state: active panel and layout mode;
- GitHome model hash, project snapshot hash, source HEAD/branch/dirty state;
- Workbench model hash, source bundle ID, semantic currentness, projection authority;
- Ergo summary hash, store status, recovery requirement, source HEAD when observed;
- explicit source alignment between GitHome and Ergo (`MATCH`, `MISMATCH`, `UNKNOWN`);
- explicit alerts derived mechanically from composed status;
- panel bindings with their original authority labels;
- shell projection authority `NONE`.

The workspace SHALL NOT copy semantic facts into shell state or copy Attempt Store payloads into GitHome state.

## Binding integrity
If GitHome already carries a Workbench binding, the shell must reject composition unless its model hash, source bundle ID, semantic currentness, and projection authority exactly match the supplied Workbench model.

Ergo source HEAD disagreement with GitHome is surfaced as `SOURCE_HEAD_MISMATCH`; it is not smoothed into a single currentness value.

Workbench `MISMATCH` is surfaced as `SEMANTIC_CURRENTNESS_MISMATCH`; Workbench `UNKNOWN` is surfaced as `SEMANTIC_CURRENTNESS_UNKNOWN`.

Ergo recovery-required state forces workspace policy mode `RECOVERY`; otherwise it is `NORMAL`. This policy is presentation/routing state only and grants no mutation authority.

## Layout/focus
v0.1 layout modes:
- `split` — project + Forge + recovery status;
- `project` — GitHome emphasis;
- `forge` — Workbench emphasis;
- `recovery` — Ergo emphasis.

Focus and layout are pure UI state. They never change Git state, semantic state, Attempt Store state, or recovery checkpoint state.

## Command reducer
Read-only commands:
- `home`
- `focus <project|forge|recovery>`
- `layout <split|project|forge|recovery>`

All other commands fail closed. There is no shell fallback and no Git/semantic/recovery mutation dispatch in v0.1.

## Text fallback
A deterministic text renderer SHALL provide a first-class low-cost workspace representation. It binds the exact component model hashes, makes authority/currentness visible, and renders the chosen panel(s) using the already-qualified GitHome/Workbench projections plus a bounded Ergo summary.

This fallback is a verification surface, not the final native visual identity.

## Qualification gates
1. exact Workbench/GitHome/Ergo bindings are deterministic;
2. GitHome-to-Workbench binding mismatch fails closed;
3. project/recovery source-head mismatch remains visible;
4. semantic MATCH/MISMATCH/UNKNOWN remains distinct from source alignment;
5. recovery-required forces visible RECOVERY policy without granting writes;
6. active-panel/layout commands mutate UI state only;
7. panel authority labels remain NONE and no combined authority is minted;
8. text fallback keeps all three domains and alerts/currentness visible;
9. real App repository + real Attempt Store can be composed read-only without source/store mutation;
10. actual qualified Core replay preview may remain visible inside Workbench while source materialization stays disabled.

## Promotion ceiling
Passing v0.1 qualifies only renderer-neutral shell composition and text fallback over already-qualified read-only component models. It does not qualify native windowing/docking/input, persistent panel state, source editing, Git mutation, semantic materialization, recovery mutation, operator task performance, or GPU/vector rendering.
