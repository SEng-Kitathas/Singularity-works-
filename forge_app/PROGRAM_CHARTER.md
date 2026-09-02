# Forge Application Program Charter

## Mission
Build Forge as self-contained, bespoke operator software centered on the LBE semantic field: Forge produces the map; the HUD navigates, interrogates, composes and materializes it.

## Product identity
- **Ergo Boot / Launcher** is the front door and recovery captain.
- **Forge Shell** is the native operator workspace, not a generic IDE skin.
- **LBE** is the semantic canvas and composition/debugging core.
- **CogTerm / SmartCanvas lineage** informs the command/terminal surface.
- **Aero / YuiUI / ALCI / CogOS** inform visual and interaction language.
- **VSE / Voidstar / Ergo-Light / NEXUS** inform rendering economy, frame discipline, compositor structure and native interaction.
- Security remains an optional evidence lens, never Forge identity.

## Reliability posture
Aim for aerospace-grade engineering discipline without claiming aerospace certification unless deliberately earned. Forge should be a zombie: process death, renderer death, interrupted mutation, AI disconnect or failed retries should not cause irrevocable work loss.

### Load-bearing laws
- `ATTEMPT_0_IS_EVIDENCE_NOT_SCRATCH_SPACE`.
- First significant AI/code/design/research output is preserved before downstream execution or repair.
- Retries and repairs branch from preserved attempts; they do not overwrite them.
- Generate once -> preserve -> diagnose -> smallest evidence-bearing repair -> compare.
- Preserve broadly; promote narrowly.
- Mutations are transactional, precondition-bound, hash-read-back and recoverable.
- Derived indexes/projections/layout/caches are disposable and rebuildable.
- Significant lifecycle events belong in an append-only operational journal.
- Recovery is a first-class product path, not an afterthought.

## Rendering economy
Pretty must be cheap. Useful must never become expensive because pretty exists.
- Attractive flat/minimal rendering path is first-class.
- Rendering tiers degrade gracefully.
- Frame budget is authoritative; interaction latency outranks effects.
- Retained/cache-heavy rendering and dirty updates where practical.
- Semantic zoom doubles as LOD.
- Text/glyph work is cached and bounded.
- Glass/refraction/frost is localized punctuation, not a whole-screen tax.
- Operator attention may choose rendering budget; it never chooses truth.

## Donor / outside-world doctrine
Strip mechanisms and invariants, not identities. Local projects and the outside world are quarry wherever they can improve, falsify or simplify Forge. No donor gains authority by age, popularity, similarity or aesthetics.

## Truth / UI doctrine
- FIELD != MAP.
- Projection != authority.
- Focus/selection != active != preferred != promoted != authoritative.
- UNKNOWN stays visible.
- Green is expensive.
- UI state may route attention; it cannot create truth.

## Program domains
- `research/` — local and outside-world quarry; exploratory, non-authoritative.
- `design/` — product/interaction/visual contracts and preserved QOL.
- `recovery/` — zombie architecture, attempts, journaling, transactional writes, recovery bundles.
- `ergo/` — boot, integrity, recovery, project/workspace selection, launch receipts.
- `render/` — compositor, text, scene, glass, tiers, frame budgets, LOD.
- `shell/` — native application chrome, docking/workspaces, input/focus.
- `lbe/` — semantic canvas integration and map interaction.
- `terminal/` — CogTerm/SmartCanvas command and terminal integration.
- `hud/` — evidence/currentness/runtime/history/debug lenses and QOL surfaces.
- `prototypes/` — disposable trials; no promotion by existence.
- `embodiment/` — discriminators, benchmarks, receipts and hostile testing.
- `promotion/` — explicit qualified candidates only.

## Immediate engineering order
1. Preserve/rehydrate program intent and donor ledger.
2. Define zombie/attempt/journal/recovery contract before implementation churn.
3. Research local + outside-world render/shell/recovery invariants.
4. Pressure native shell/rendering architecture with cheap-rendering benchmarks.
5. Build Ergo boot/recovery vertical slice.
6. Bind frozen semantic-field snapshot into the shell without duplicating truth.
7. Add LBE canvas, terminal/SmartCanvas and HUD lenses incrementally.
8. Run deliberate kill/recovery and operator-latency campaigns before promotion.
