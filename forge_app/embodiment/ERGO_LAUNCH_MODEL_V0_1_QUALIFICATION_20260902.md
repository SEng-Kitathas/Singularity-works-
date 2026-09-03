# Ergo Launch Model v0.1 — Qualification — 2026-09-02

Status: **READY_WITH_EVIDENCE as renderer-neutral launch/recovery presentation contract and minimal text reference tier**.
Not a native-shell/render-backend qualification.

## Attempt-0 preservation
The first renderer-neutral launch model, minimal renderer, CLI and semantic tests were committed and pushed **before first execution**:
`5b44adc` — `forge-app: preserve renderer-neutral Ergo launch model attempt zero`.

Attempt-0 test source:
`forge_app/embodiment/test_ergo_launch_model_v0_1.py` SHA `1aaeb0e50af64a0460fa7da189c2fdf4593413155a954d55dcbc6d6041073e79`.

## Architecture
Pipeline:
`ErgoRecoverySummary -> ErgoLaunchModel -> renderer/presentation tier`.

The launch model is deterministic and renderer-neutral. It contains:
- overall launch posture;
- posture reason;
- observer authority;
- bounded system facts;
- explicit Normal/Safe/Recovery launch-mode availability/recommendation;
- bounded recent preserved-attempt summaries;
- explicit recovery/source reasons.

It does **not** execute launch actions, mutate recovery state, or mint confidence/authority from presentation state.

Minimal reference renderer:
- plain text;
- no ANSI/GPU/terminal capability assumptions;
- bounded width with 48-column operable floor;
- displays posture, authority, system facts, launch modes, reasons and preserved-work history;
- explicitly states `Presentation does not create truth.`

## First execution scar
Initial semantic/presentation test result: **5/6 PASS**.

Failure:
- at 64 columns the final combined invariant sentence was intentionally truncated by the width bound, while the test expected the complete phrase `Presentation does not create truth.`.

Classification:
- presentation/readability defect, not recovery-model semantic failure.

Repair:
- footer split into two invariant lines:
  - `Ergo is observing durable state.`
  - `Presentation does not create truth.`

Repair commit preserved before retest:
`ed15b9d` — `forge-app: keep Ergo minimal invariants visible at narrow width`.

Retest: **6/6 PASS**.

## Live program rendering
The minimal CLI was run against the actual program Attempt Store and source branch.

Observed live presentation state:
- title: `ERGO // FORGE`;
- posture: `READY`;
- observer authority: `NONE`;
- recovery store: `READY`;
- integrity: `ok`;
- journal mode: `wal`;
- preserved attempts/events at that read: 14 / 14;
- source branch: `forge/app-shell-rd`;
- source HEAD at that read: `ed15b9d6b415...`;
- source clean: yes;
- Normal: available + recommended;
- Safe: available;
- Recovery: available, not required;
- recent preserved Attempt-0/qualification/convergence artifacts shown from durable store.

## Evidence acquisition performance baseline
Initial benchmark before Git inspection optimization:
- recovery summary including source: median **89.8035 ms**, p95 **95.0222 ms** (n=60);
- store-only recovery summary: median **5.3625 ms**, p95 **6.6473 ms** (n=100);
- Git source inspection using three Git subprocesses: median **83.2128 ms**, p95 **91.0902 ms** (n=100);
- launch-model construction: median **0.0191 ms**, p95 **0.0226 ms** (n=20,000);
- minimal render: median **0.0152 ms**, p95 **0.0177 ms** (n=20,000);
- canonical JSON: median **0.0657 ms**, p95 **0.0778 ms** (n=10,000).

Conclusion: presentation/model generation was negligible; evidence acquisition, specifically three-process Git inspection, dominated latency.

## Git inspection optimization
Candidate preserved before regression/benchmark:
`2b03d5d6a1d91a37ca2b40133e253aa71cca4be8` — `forge-app: preserve single-call Git recovery inspection candidate`.

Current `forge_app/ergo/recovery_summary.py` SHA:
`37c4582ac515a4d3abff44aa52744d7e550a196c153861307ccc4725231676a9`.

Change:
- replace three Git subprocesses (`rev-parse`, `branch --show-current`, `status --porcelain=v1`) with one stable `git status --porcelain=v2 --branch` call;
- parse `branch.oid`, `branch.head`, and non-header dirty records from that single response.

Full relevant regression after optimization:
**19/19 PASS** across Attempt Store v0.1, Zombie v0.2, Ergo Recovery Observer v0.1, and Ergo Launch Model v0.1.

Post-optimization benchmark:
- single-call Git source inspection: median **31.11125 ms**, p95 **32.1837 ms** (n=100);
- complete live recovery summary: median **38.84935 ms**, p95 **40.8772 ms** (n=100);
- launch-model construction: median **0.0187 ms**, p95 **0.0217 ms** (n=20,000);
- minimal render: median **0.0151 ms**, p95 **0.0178 ms** (n=20,000).

Measured median full-summary improvement:
`89.8035 ms -> 38.84935 ms` = approximately **56.7% lower latency**.

## Current source hashes
- `forge_app/ergo/launch_model.py` SHA `500475baf78c34b3df64ca3a2a30cb970c7c68bcfb95948457592c214b87fd7f`.
- `forge_app/ergo/minimal_cli.py` SHA `16ad9d98d2c83a144099b6e5e4c7947b59542209ad0eb6f54f25b43b7a976a70`.
- `forge_app/ergo/recovery_summary.py` SHA `37c4582ac515a4d3abff44aa52744d7e550a196c153861307ccc4725231676a9`.
- launch-model test SHA `1aaeb0e50af64a0460fa7da189c2fdf4593413155a954d55dcbc6d6041073e79`.

## Earned laws / implications
- `RECOVERY_FACTS != PRESENTATION_BACKEND`.
- `PRESENTATION_STATE != TRUTH_AUTHORITY`.
- `EVIDENCE_ACQUISITION_COST != RENDERING_COST`.
- The minimal tier is a reference product surface, not a failure fallback.
- Future native/Aero renderers must consume the same launch model or an explicitly versioned successor; they do not get to reinterpret recovery truth independently.

## Next discriminator
Define and test a native-shell/render abstraction against this exact model. Candidate backends may differ, but must preserve:
- identical launch posture/mode semantics;
- renderer failure isolation from durable state;
- usable minimal/software path;
- bounded text/focus/input behavior;
- measurable frame/input/startup budgets;
- graceful loss of expensive effects before loss of operator function.
