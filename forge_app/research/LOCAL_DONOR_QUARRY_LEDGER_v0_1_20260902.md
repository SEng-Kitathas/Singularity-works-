# Forge Application — Local Donor Quarry Ledger v0.1 — 2026-09-02

Status: evidence-bearing research ledger. Donor material is non-authoritative until a mechanism survives embodiment/promotion.
Primary quarry root: `E:\new pc`.

## Disposition vocabulary
- **KEEP** — mechanism/invariant fits Forge strongly enough to carry into design pressure.
- **REFORGE** — useful invariant, donor implementation/ontology is not suitable as-is.
- **DEFER** — potentially useful, insufficient evidence or lower priority.
- **REJECT** — explicitly unsuitable mechanism for this program under current evidence.

## Ergo-Light / Ergo launcher lineage
Primary source family:
`E:\new pc\AI_Pushes_Sandbox\projects\ergo_light_engine_lab_20260427`

High-signal exact files:
- `reports/ERGO_LIGHT_MASTER_SYNTHESIS_v0_3_2026-04-28.md` SHA `246c6ef851e5bd051324b768a8603b23ef9adcbb989b2b658af64bf6a2ac97dc`.
- `reports/ERGO_LIGHT_CONSOLE_IMPLEMENTATION_MAP_2026-04-27.md` SHA `d8f853aac4ca69e6c76d5851f16e7d8aa9a1016eb91662224b8149111db7dbe3`.
- `runtime/ergo_launcher.py` SHA `ca7eeb5479d6fe15b91af80942236b90682ceb99531598933381402cee2c177f`.
- `runtime/ergo_boot.py` SHA `1b4624629f7385e296864aa1f87bda1f639d8a5330f4549426dc2e1fa339fef9`.
- `runtime/ergo_checkpoint.py` SHA `27857ff676bb9e15df4e8acaf3a74de6ac4bbcb054e3b8aaf8ac250fb3b11d2b`.
- `runtime/ergo_session.py` SHA `f8b04e6fbcaf99d5dd1055e845c346f8a84e17a99dbca3885d57c81daa5d3710`.
- `tests/test_ergo_launcher.py` SHA `0711df2dce3ca6e9149f5727dd22cbeba1eb2be80a36f4b2b74c8fe36ddf233e`.
- `tests/test_ergo_checkpoint.py` SHA `f9f23f7aa8573046d97d990bc6f06fb96e0d32efaa8667ee00713bc0f6e59c6e`.

Verified mechanisms:
- real phase-driven boot runtime, including `COLD_BOOT`, `LAUNCHER_ORBIT`, `HOLON_SELECTION`, and later transition phases;
- launcher state, selected item, session handoff and resume candidate surfaces;
- checkpoint records, checkpoint validation, latest/preferred checkpoint selection, restoration and resume;
- session state plus replay/payload hash records;
- tests that exercise launcher resume candidates and checkpoint round-trip behavior;
- recovered core phrase: **one shell, many holons, one substrate**.

Disposition:
- **KEEP:** Ergo identity as Forge front door; boot-phase state machine; launcher/project/workspace selection; resume candidate presentation; launch receipts; recovery selection; checkpoint validation concepts.
- **REFORGE:** holon selection becomes Forge project/workspace/recovery-context selection; game/world session identity becomes project/semantic/runtime session identity.
- **REJECT for zombie durability:** existing JSON persistence boundary as final Forge persistence mechanism.

### Durability scar
`tools/csc_native/strict_json_boundary.py::write_json_boundary()` renders JSON and calls `Path.write_text(...)`. Checkpoint/session code uses this boundary and file copies; no source-level evidence was found for temp-file + atomic replacement, write-ahead transaction protocol, fsync/FlushFileBuffers durability barrier, or crash-safe transaction recovery around these writes.

**Locked donor scar:** `ERGO_CHECKPOINT_MODEL != ZOMBIE_SAFE_PERSISTENCE`.

Forge should inherit the recovery/launcher model while replacing the durability substrate.

---

## Voidstar / VSE / Ergo-Light rendering economy
Primary high-signal source:
`E:\new pc\everything\Download\Download\VOIDSTAR_ENGINE_OMEGA_v73_CANONICAL.rs` (~718 KB).
Numerous earlier/later Voidstar/VSE Rust generations are preserved under `E:\new pc\everything\Download\Download` and `VSE-ALL`.

Verified mechanisms in v73 canonical:
- `InterlacedRenderer`: checkerboard parity renders half the pixels per frame and alternates parity; explicitly documented as low-end / potato-PC optimization;
- `render_tiled`: tiled rendering intended for cache efficiency;
- `SimulationTier`: `Full`, `Reduced`, `Minimal`, `Dormant`, `Suspended` with tick multipliers 1, 2, 4, 16, never;
- explicit tier degradation operation;
- recurring cache-conscious SoA/alignment/hot-path allocation discipline;
- documented graceful degradation under thermal/resource constraints.

Disposition:
- **KEEP:** work proportional to relevance; explicit degradation tiers; ability to suspend dormant work; tiled/cache-local updates; hot-path allocation discipline; low-end path as an intentional product path.
- **REFORGE:** interlacing becomes a general partial-update/temporal-sampling idea for expensive decorative layers or dense canvases, not literal checkerboard text/UI rendering by default.
- **DEFER:** SDF/raymarch/procedural reconstruction where it might help visual effects or very dense semantic fields.
- **REJECT as default UI architecture:** game-specific raymarcher, ballistic visualization and world-simulation ontology.

**Forge invariant:** rendering/simulation cost must be tiered and relevance-aware; expensive layers may update less frequently than operator-critical layers.

---

## ALCI / Liquid Aero / YuiUI cockpit lineage
Primary directory:
`E:\new pc\everything\Download\Download\AI\UI-HUD-Cockpit`

Exact high-signal files:
- `ALCI_v7.2_LiquidGlass_Complete.html` SHA `735ee20b4404312f605e80dd442b38310cb5fdc434323f7f37d856d235b70a01`.
- `ALCI_v7.2_UI_Specification.md` SHA `27cd0966fc960bc000b8c6a4ef59a008eb88f7b6838991976b1bb66d3fb04b4a`.
- `LIQUID_AERO_DESIGN_SYSTEM.md` SHA `c5cca3a3448260fc7a541577c171844ea98ed1740721fa0d1ddfe964b28b02d0`.
- `LIQUID_AERO_UI_v2.md` SHA `169fb88aa8f4d2d90e7098d254dc16bd1d548e97f1ae60c5d4554c7363a0a31e`.
- `NEAL_YUI_v1_1_QA_CORRECTED.md` SHA `a1f2b4f4e81074fa15157d36bf0cae9ee73f2e29652a7afb0873a1dd34b5129a`.
- `YuiUI_CP_v1_0_OMEGA.md` SHA `237aeb99f1e670328f5b2a59b2d72dc8bad22484b9870a699e95e6a20947b569`.
- `YuiUI_Ultimate.html` SHA `f535280cff53f8f407d07af152be04f5a546ed23fbd38b3119fdff2df37d32e8`.
- `UI ingredients/CogOS UI/UI.html` SHA `d2542e2116ba9622e746981f639dc4766fe5e06f1ed81d6f65b77ec2adc2716d`.

### Verified ALCI tier system
- FULL: liquid refraction, chromatic fringe, cursor warp, internal luminescence, richer text/parallax effects.
- BALANCED: static curvature, time-sampled warp, reduced fringe, interaction-only internal light, commit-only expensive state visuals.
- MINIMAL: flat translucent panels, no blur/refraction/motion, high-contrast text and essential indicators.
- Explicit threshold: **liquid distortion disabled below 45 FPS**.

Disposition:
- **KEEP:** explicit FULL/BALANCED/MINIMAL visual tiers; dynamic feature shedding; professional minimal mode; interaction-only expensive effects; commit/event-driven rather than per-frame updates for expensive state visualizations.
- **REFORGE:** hardware detection becomes only one input; actual frame/latency budget and operator interaction state must drive tier changes dynamically.

### YuiUI / cockpit invariants
Verified source statements/mechanisms:
- “Glass Cockpit Principle”: make invisible state visible;
- SCRAM/safety state unmissable;
- safety-critical panels cannot be dismissed;
- panel-holon lifecycle model;
- zero-allocation hot-path aspiration / preallocated buffers;
- center Smart Canvas / command surface;
- glass physics vocabulary: layered depth, frost, refraction, Fresnel/edge reflection.

Disposition:
- **KEEP:** hidden-state visibility, permanent critical safety/recovery strip, center semantic canvas, command surface, bounded hot-path allocation, panel lifecycle concept.
- **REFORGE:** panel holons become capability/query-driven projections over Forge state; SCRAM becomes recovery/system consequence status; visual glass vocabulary becomes localized interaction material.
- **REJECT:** visual effects as epistemic truth; full-screen deep blur as default implementation.

### CogOS UI prototype
Verified HTML mechanisms:
- central Starmap canvas;
- glass cards using DOM `backdrop-filter` blur;
- bottom command capsule;
- WebGL particle canvas.

Disposition:
- **KEEP/REFORGE:** spatial hierarchy, central semantic canvas, command capsule.
- **REJECT as final implementation:** broad DOM backdrop-filter strategy as the basis of the native Forge shell.

### Liquid-Aero native tree
`E:\new pc\everything\Download\Download\Documents\Holonic_Linux\userspace\liquid-aero` exists, but the directly recovered tree in this pass contains only a README plus empty/near-empty structural directories. Historical references to richer native glass implementations are not enough to claim they are currently present.

Current exact search did **not** locate `glass.wgsl` or `glass_panel.wgsl` under the scanned E:\new pc roots. They remain **DEFERRED / NOT CURRENTLY VERIFIED PRESENT**.

---

## CogTerm
Exact primary files:
- `E:\new pc\everything\Download\Download\files (2) (3)\COGTERM_v5.0_SPEC.md` SHA `0af5a359395d0a15278d19f0b015840bc9e8116e26ce2c102d2c58743efe38f7`.
- `E:\new pc\everything\Download\Download\files (2) (5)\COGTERM_v5.0_UNIFIED_TERMINAL.md` SHA `b1971fbcfca3fc3f2ccd7a509e6409526657a37b8e7764bdaeb2106d4f4adf32`.

Verified mechanisms:
- “Glass Box Principle”;
- show history, not only current state;
- sparklines/history surfaces;
- layout degrades from large screens to 80x24 terminal;
- explicit panel architecture and layout modes;
- top status bar + bottom command line;
- event log panel;
- explicit command system/interface.

Disposition:
- **KEEP:** graceful resolution degradation; history-visible operator surfaces; command system separated from status/rendering; event log; context-sensitive panels.
- **REFORGE:** cognitive-specific panels into LBE/evidence/currentness/runtime/recovery panels.
- **REJECT:** second independent truth/state model behind terminal panels.

---

## NEXUS
Exact high-signal documents:
- `E:\new pc\everything\Download\Download\ingredients for NEXUS\NEXUS_TABS_MONOSPEC.md` SHA `3abe2574ee764307127181a15ff9891938a28c89f44fcab9f6493f79494499c1`.
- `E:\new pc\everything\Download\Download\ingredients for NEXUS\NEXUS_CORE_MONOSPEC.md` SHA `c0b0e8b8d22efee5cb1c727f3f8362b86407e4b17012c03a76cf2e448570241b`.

Verified mechanisms:
- `TabRenderingTier` is an explicit architectural fork;
- native tabs are treated differently from WebView/OSR/Chromium surfaces despite sharing a high-level “tab” label;
- lifecycle systems separated from ECS component ownership;
- Chromium renderer-process death routed through a renderer crash notifier/tab crash path, explicitly distinct from internal-holon apoptosis;
- Rust workspace separates render/input/tab concerns; documented dependencies include `wgpu` and `vello`.

Disposition:
- **KEEP:** rendering tier/type is explicit capability, not hidden implementation detail; crash domains distinguished; lifecycle-system vs state-component separation; renderer death must not imply application/semantic death.
- **REFORGE:** tab model into Forge workspace/panel/render-surface capability; browser surfaces optional bounded capability, not architectural default.

**Forge invariant:** `RENDERER_PROCESS_DEATH != FORGE_STATE_DEATH`.

---

## DEJISEITAI / NEAL visualization lineage
Correct recovered spelling is **DEJISEITAI**.
Exact source:
`E:\new pc\everything\Download\Download\AI\NEAL\DEJISEITAI_UNIFIED_v2_0_OMEGA (2).md`
SHA `6150843976a9588ae7d6242b1f7f97768e96ab1800b0ee2984d60f7a922281fe`.

Verified mechanisms/invariants:
- visualization panel set includes trajectory/phase history, attention flow, current cycle state, active domains, confidence, operating mode, permanently visible SCRAM and Smart Canvas entity-completed input;
- salience/attention routing tied to resource prioritization;
- priority-based feature shedding;
- explicit “frame budget mentality”;
- source describes moving panel rendering toward CPU/SDF primitives and claims ~0.47 GB VRAM reclaimed for actual model/context workload.

Disposition:
- **KEEP:** history/trajectory as first-class navigation; always-visible safety/recovery state; attention/relevance may drive feature/render shedding; command entity completion; resource budget belongs to the useful workload first.
- **REFORGE:** cognitive cycle/entropy/domain ontology into Forge-specific currentness/runtime/evidence/resource concepts.
- **DEFER:** CPU/SDF rendering mechanism until measured against modern vector/GPU/hybrid alternatives.
- **REJECT:** treating synthetic cognitive confidence/attention values as Forge truth authority.

**Forge rendering law reinforced:** visualization yields resources to semantic/operator work, not vice versa.

---

## Cross-donor convergence earned in pass 01
1. **Ergo recovery UX/state machine + new durability substrate** rather than Ergo's direct JSON write implementation.
2. **Explicit degradation tiers** across VSE + ALCI + DEJI: Full/Reduced/Minimal/Dormant/Suspended is a general work-budget pattern, not merely graphics settings.
3. **Critical state always visible**: SCRAM/safety/recovery/system integrity must not disappear behind ordinary workspace customization.
4. **History is navigation**, not just logging: CogTerm + DEJI + existing Forge SnapshotDelta converge on trajectory/time scrub.
5. **Renderer crash is a bounded failure domain**, not application death: NEXUS makes this explicit.
6. **Main canvas gets resources first**: expensive visual decoration is lower priority than text, semantic interaction, runtime/debug information and AI/model workload.
7. **Panel existence should be capability/query driven**, not a fixed dashboard taxonomy.
8. **Minimal mode is a product**, not a failure mode.
9. **Donor implementation claims remain untrusted until benchmarked**; source comments such as VRAM/cache-hit estimates are hypotheses, not measured Forge truth.

## Open local quarry
- Broader CogOS generations and NEAL UI code.
- Receiver/PCMMAD launcher and restart audit artifacts.
- CFE launcher/rendering selection policy.
- old Forge cockpit/HUD implementations and boot patches.
- ClassicBoy/Citra layout-edit and diagnostic-overlay mechanisms.
- TQ2 rendering primitives.
- additional terminal, compositor and low-end-rendering projects under E:\new pc.

No broad source transplantation is authorized by this ledger.
