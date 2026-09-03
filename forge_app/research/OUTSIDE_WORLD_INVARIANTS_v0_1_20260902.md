# Forge Application — Outside-World Invariants v0.1 — 2026-09-02

Status: comparative research. External systems are non-authoritative quarry. Mechanisms below are candidates/discriminators, not implementation commitments.

## Windows composition materials — Mica / Acrylic
Sources reviewed: current Microsoft Learn materials/Mica/Acrylic documentation (August–September 2026 crawl/current docs).

Verified mechanisms:
- Mica is explicitly designed as a performant long-lived base material and samples the desktop wallpaper once rather than continuously blurring arbitrary content.
- Windows system materials already have fallback semantics: insufficient hardware, disabled transparency, Remote Desktop/VM contexts and high-contrast modes can produce solid fallbacks; Acrylic is additionally disabled under Battery Saver.
- Microsoft explicitly describes Acrylic as GPU-intensive and recommends opaque backgrounds for many persistent/vertical content panes rather than applying Acrylic indiscriminately.
- Solid fallback colors are part of the material APIs and are expected to remain visually usable.

Forge disposition:
- **KEEP:** OS-compositor-backed Mica as a possible cheap Windows-only shell/background enhancement when the eventual native shell stack can use it cleanly.
- **KEEP:** system/user accessibility/power conditions must be allowed to collapse materials to solid presentation without reducing functionality.
- **REFORGE:** Aero identity should come from Forge geometry, typography, depth, edges and localized effects; do not require full-window blur to look correct.
- **REJECT:** broad persistent Acrylic/backdrop blur as the default panel material.

External source titles/domains:
- Microsoft Learn — Materials overview (`learn.microsoft.com/windows/apps/develop/ui/materials`).
- Microsoft Learn — Mica material.
- Microsoft Learn — Acrylic material.
- Microsoft Learn — Apply Mica in Win32 desktop apps.

## Zed / GPUI — native GPU UI economy
Sources reviewed: Zed engineering blog and current 2026 Zed release material.

Verified mechanisms/lessons:
- Zed deliberately left Chromium/Electron lineage and built a custom native Rust UI framework around GPU rendering to remove the performance ceiling they experienced in Atom.
- GPUI's original rendering strategy did not require a general arbitrary-graphics engine; it focused on the common primitives the product actually needed: rectangles, shadows, text, icons and images, represented as data and pushed to GPU shaders.
- GPUI application state is centrally owned while views/entities remain dynamic and asynchronously updateable.
- Later Zed work shows the cost of owning a custom UI stack: conventional focus navigation, tab groups/forms and state organization still required explicit framework work.

Forge disposition:
- **KEEP:** bespoke native shell can be justified by operator latency and custom semantic-canvas needs rather than aesthetics alone.
- **KEEP:** optimize the primitive set Forge actually needs before reaching for a maximal general-purpose graphics abstraction.
- **KEEP:** focus/navigation/accessibility/form behavior must be first-class acceptance criteria, not assumed to appear automatically in a custom renderer.
- **DEFER:** GPUI itself as a dependency until platform/licensing/API/fit and Forge-specific benchmark pressure are completed.

External source titles/domains:
- Zed Blog — “Leveraging Rust and the GPU to render user interfaces at 120 FPS.”
- Zed Blog — “Zed is 1.0” (2026).
- Zed Blog — GPUI ownership/data-flow and Settings UI posts.

## Vello / wgpu rendering family
Sources reviewed: current Linebender Vello repository and release notes.

Verified current state:
- Vello offers multiple implementations rather than one fixed backend: GPU-compute Vello, CPU-only Vello CPU, and a Hybrid path using CPU preprocessing plus GPU rasterization.
- Vello CPU is described as broadly usable/competitive but does not promise API stability.
- Vello Hybrid aims toward production use, but current releases still describe it as early-stage without API stability or complete feature parity.
- Current work includes glyph atlas/cache APIs, blur/filter support and render-resource configuration.
- The main Vello repository still labels the GPU-compute renderer experimental/alpha and lists blur/filter, GPU memory strategy and glyph caching as active work areas.

Forge disposition:
- **KEEP:** render-backend/tier abstraction is more important than choosing one renderer early.
- **KEEP:** CPU, Hybrid and GPU are legitimate implementation tiers that can share a higher-level scene/material contract where evidence permits.
- **REFORGE:** use Vello-class APIs as benchmark/donor targets, not as semantic-field architecture.
- **REJECT:** hard-coding Forge product/state interfaces directly around an alpha renderer's unstable API.

External source:
- Linebender/Vello official GitHub repository and releases.

## Terminal rendering — WezTerm / Windows Terminal
Sources reviewed: current WezTerm front-end documentation and Windows Terminal AtlasEngine materials.

Verified mechanisms:
- WezTerm exposes distinct OpenGL, WebGPU and Software rasterization front ends; software fallback is a supported operational path and is automatically selected in some Windows Remote Desktop conditions.
- Windows Terminal's AtlasEngine history demonstrates the complexity of a high-quality terminal text renderer: overlapping/italic glyphs, emoji/complex scripts, box-drawing clipping, ClearType/blending and shader behavior all require dedicated treatment.

Forge disposition:
- **KEEP:** terminal/SmartCanvas rendering backend must have an explicit software fallback and cannot assume healthy GPU drivers.
- **KEEP:** text/glyph correctness is a specialist subsystem; never treat “draw glyph atlas” as solved by a generic UI renderer.
- **KEEP:** terminal command/output selection and history semantics belong in the operator model, not only the visual layer.
- **DEFER:** borrowing any terminal renderer wholesale until PTY/ANSI/IME/accessibility/input requirements are separately bounded.

External source titles/domains:
- WezTerm documentation — `front_end` rendering backends.
- Microsoft Terminal repository/discussions — AtlasEngine development.

## Git content-addressed objects
Sources reviewed: official Git documentation (`git-hash-object`, Pro Git Git Objects chapter).

Verified mechanism:
- Git's core object database is a content-addressable key/value store; object IDs are derived from object content and permit later exact retrieval.
- `git hash-object` can hash/write arbitrary blob content independent of the normal working-tree history.

Forge disposition:
- **KEEP as invariant:** immutable Attempt 0 artifacts should be content-addressed by their exact bytes, while mutable labels/lineage live in a separate transactional index/journal.
- **REFORGE:** do not simply use the source repository's `.git/objects` as the application Attempt Store. Forge needs explicit artifact class, producer, intent, privacy, retention, lineage and recovery semantics that source Git does not provide by itself.

External source titles/domains:
- Git SCM — `git-hash-object` documentation.
- Pro Git — Git Internals / Git Objects.

## SQLite transaction / WAL behavior
Sources reviewed: official SQLite WAL, atomic-commit, synchronous pragma and corruption/durability documentation.

Verified mechanisms:
- SQLite provides atomic transactions and recovery after interrupted writes; rollback-journal and WAL modes use different mechanisms.
- WAL permits concurrent readers with a writer and uses sequential appends, but the WAL file is part of persistent state and must not be separated from the database while relevant transactions exist.
- Durability differs from consistency: WAL + `synchronous=NORMAL` remains consistent/atomic but can lose recently committed transactions after power loss; `synchronous=FULL` syncs the WAL on each transaction commit.
- SQLite itself explicitly depends on OS/filesystem sync barriers and documents limitations of those durability guarantees on real hardware/filesystems.

Forge disposition:
- **KEEP:** SQLite is a strong candidate for the mutable Attempt/Journal metadata index because it already solves transactional concurrency/recovery better than ad-hoc JSON files.
- **KEEP:** durability mode must be explicit and testable; normal interactive performance and “must survive power loss” events need not use identical sync policy if the authoritative blob is separately durable/content-addressed.
- **KEEP:** the database plus WAL/SHM must be treated as one recovery unit where WAL is enabled.
- **DEFER:** final WAL vs rollback-journal/synchronous policy until deliberate kill/power-loss-equivalent benchmarks and Windows filesystem behavior are tested.

External source titles/domains:
- SQLite — Write-Ahead Logging.
- SQLite — Atomic Commit.
- SQLite — PRAGMA synchronous documentation.
- SQLite — How To Corrupt An SQLite Database File.

## Windows file replacement / durability
Sources reviewed: current Win32 `MoveFileEx`, `ReplaceFile`, and moving/replacing file documentation.

Verified mechanisms:
- `ReplaceFile` is a first-class Windows operation to replace one file with another and may retain a backup copy.
- `MoveFileEx` supports `MOVEFILE_REPLACE_EXISTING`; `MOVEFILE_WRITE_THROUGH` documents a write-through guarantee for moves that become copy/delete operations.
- `ReplaceFile`'s documented `REPLACEFILE_WRITE_THROUGH` flag is not supported, so “ReplaceFile means durable-to-disk” must not be assumed.

Forge disposition:
- **KEEP:** stage-new-file then OS-level replace is a better file mutation boundary than in-place `write_text` for authoritative flat files.
- **KEEP:** preimage/postimage hashes and readback remain required because filesystem API success is not semantic success.
- **REFORGE:** Windows durability helper must deliberately choose/verify appropriate replace/flush semantics and be kill-tested; no single API call is granted “aerospace-grade” by name.

External source titles/domains:
- Microsoft Learn — MoveFileEx.
- Microsoft Learn — ReplaceFile.
- Microsoft Learn — Moving and Replacing Files.

## Cross-world convergence
1. **Renderer abstraction beats renderer religion.** Local NEXUS/VSE + current Vello/WezTerm all support multiple rendering paths and explicit fallback.
2. **Minimal/solid/software modes are first-class product surfaces.** Windows, WezTerm and local ALCI converge on graceful fallback rather than “effects disabled = broken UI.”
3. **Content-addressed immutable bytes + transactional mutable index is a strong Attempt Store shape.** Git supplies the CAS invariant; SQLite supplies transactional metadata/journal semantics.
4. **Atomic/transactional does not automatically equal power-loss durable.** Sync policy and underlying filesystem/hardware remain separate qualification dimensions.
5. **Custom native UI buys control but creates responsibility.** Focus, accessibility, text, forms, IME, crash boundaries and update scheduling must be deliberately engineered.
6. **Use the OS compositor when it is cheaper and safe.** Windows Mica demonstrates a base material can look bespoke without continuously sampling/blur-rendering the whole desktop.
7. **Renderer death must stay a bounded failure.** External terminal/GPU fallback plus local NEXUS crash-domain separation reinforce this.

## Immediate discriminators suggested by external research
- CAS blob write interrupted before/after rename: either exact old/no blob or exact hash-addressed new blob; never a blob whose name/hash disagrees with bytes.
- SQLite transaction killed at multiple statement/commit/checkpoint phases: recover to an internally consistent journal/attempt graph.
- GPU renderer loss: semantic/application state remains alive; relaunch/fallback to software/minimal renderer.
- Full/Balanced/Minimal rendering under identical operator task: semantic selection/input latency must remain inside budget before visual fidelity is considered.
- Windows system backdrop unavailable/Battery Saver/high contrast/RDP: shell stays visually coherent and fully functional with solid material.

No external source is promoted by this research document.
