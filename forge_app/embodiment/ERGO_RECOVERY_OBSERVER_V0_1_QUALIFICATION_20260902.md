# Ergo Recovery Observer v0.1 — Qualification — 2026-09-02

Status: **READY_WITH_EVIDENCE for read-only recovery inspection under the bounded Attempt Store v0.1 target**.

## Attempt-0 preservation
The Ergo observer and hostile test were committed and pushed before first execution:
- Git commit `ba3fcf013f86a3cc7340b99d74ccff413f4c8203` — `forge-app: preserve Ergo recovery observer attempt zero`.
- `forge_app/ergo/recovery_summary.py` Attempt-0 SHA `891d0f89b2285a54d7672c6327ee51d25afe4cdb874148acbe69ef006f88760a`.
- `forge_app/embodiment/test_ergo_recovery_summary_v0_1.py` Attempt-0 SHA `9a9779d981ef3f7a2df9e2818d4dd8133e906c2175aa3a1a28b29a4cf0749c2c`.

Both Attempt-0 files were subsequently captured into the live Attempt Store with exact readback verification.

## Test execution
Command:
`python -m unittest forge_app.embodiment.test_ergo_recovery_summary_v0_1 -v`

Result: return code 0; 4 tests; all PASS.

Verified behaviors:
1. missing store -> `MISSING`, normal mode denied, recovery required, and **no store directory/database is created**;
2. healthy store -> `READY`, exact blob/attempt/event counts and latest attempt are reported;
3. repeated healthy inspection -> database bytes and database mtime remain exactly unchanged;
4. corrupt database bytes -> `UNREADABLE`, normal mode denied, recovery required, and the corrupt bytes remain exactly untouched.

The observer carries `observer_authority = NONE`.

## Live program readback
After the gate passed, the observer inspected the real program store and source clone.

Real durable state at readback:
- Attempt Store status: `READY`;
- integrity: `ok`;
- journal mode: `wal`;
- schema: `forge-attempt-store/0.1`;
- blobs: 9;
- attempts: 9;
- events: 9;
- source repo: available;
- source branch: `forge/app-shell-rd`;
- source HEAD: `ba3fcf013f86a3cc7340b99d74ccff413f4c8203`;
- source dirty: false;
- normal mode allowed: true;
- safe mode available: true;
- recovery mode required: false;
- reasons: none;
- observer authority: `NONE`.

Derived live readback:
`state/attempt_store_v0_1/ergo_recovery_summary_latest.json`

## Architectural promotion
The original Ergo-Light donor's launcher/recovery **model** is now partially embodied over the new Forge durability substrate rather than direct JSON files.

Current bounded pipeline:
`Attempt Store durable state -> read-only Ergo inspection -> launch/recovery posture`

Ergo does not create, repair, checkpoint, or mutate the Attempt Store during inspection.

## Not yet qualified
- graphical/native launcher presentation;
- actual safe/recovery launch actions;
- pending transaction discovery beyond attempts/events;
- semantic snapshot/runtime process health integration;
- external recovery bundle selection;
- automatic renderer fallback/restart;
- power-loss/storage corruption recovery;
- concurrent multi-process inspection/writes;
- accessibility/operator usability;
- formal aerospace certification.

## Next cut
The next Ergo slice should render this same read-only recovery model through the eventual native/minimal shell without changing its authority. Rendering failure must not threaten the store or source. Before choosing the renderer, benchmark a minimal native text/vector surface and a higher-fidelity tier against the same recovery model and operator latency budget.
