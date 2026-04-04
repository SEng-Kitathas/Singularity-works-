# Blueprint Engine Architecture Bridge
_Version: 2026-04-03 — Extracted from upstream ChatGPT build session (Law_Ω_active v1.0-v1.18)_

## What This Is

Five canonical spec documents produced at the end of the ChatGPT upstream forge build session,
representing the next architectural layer above the current v1.19 forge front gate.
These existed only in ChatGPT canvas and this transcript. Now committed.

## The Stack

```
┌────────────────────────────────────────────────────┐
│  HUD / Cognitive Cockpit (NEXUS)                   │
│  Operator inspection surface                       │
└──────────────────────┬─────────────────────────────┘
                       │ blobs + verdicts
┌──────────────────────▼─────────────────────────────┐
│  Logic Blueprint Engine (LBE)                      │
│  Deep semantic behavior cartography                │
│  Modes: Triage / Construction / Manual             │
│  Five layers: StructFrontEnd → SemanticIR →        │
│               PathEngine → BlobEmitter → Verdict   │
└──────────────────────┬─────────────────────────────┘
                       │ Forge IR substrate
┌──────────────────────▼─────────────────────────────┐
│  Forge IR (common semantic intermediate rep)       │
│  4 layers: Structural / Operational /              │
│            Semantic State / Analysis Annotation    │
│  Node kinds: Source / Transform / Effect /         │
│              Recovery / Control                    │
└──────────────────────┬─────────────────────────────┘
                       │ escalation trigger
┌──────────────────────▼─────────────────────────────┐
│  Singularity Works Forge v1.19 (FRONT GATE)        │
│  Fast, broad, pattern-led, repair-led              │
│  28 modules, 37 capsules, 36 strategies            │
│  12 monitors, 46/46 battery                        │
└────────────────────────────────────────────────────┘
```

## Current Forge → Blueprint Engine Mappings

| Current Forge Artifact | Blueprint Engine Role |
|---|---|
| `semantic_ir.py` (188 lines) | Embryonic Forge IR — partial Layer 2 (Operational) |
| `interprocedural.py` (890 lines) | Embryonic Path Engine — cross-function taint is proto-Path Engine |
| `pattern_ir.py` (92 lines) | Embryonic Layer 1 (Structural Front-End) |
| `assurance.py` (301 lines) | Embryonic Verdict layer — precursor to Blob Schema |
| Cross-function SSRF taint (v1.19) | Proto-path walking with taint state propagation |
| Trust boundary IR nodes | Proto-trust model (claims/earned distinct) |
| `genome_gate_factory.py` strategies | Front Gate — these stay, they don't move to LBE |
| `monitoring.py` protocol monitors | Front Gate — these stay |

## Escalation Classes (summary)

- **Class A (Hard):** Any red result, wrapper theater + sink, cross-class blended risk, suspicious-clean above threshold, sensitive subsystem touched
- **Class B (Strong):** Amber result, unknown-heavy path, wrapper claims without earned trust, new code in auth/proxy/template/token modules
- **Class C (Soft):** High novelty, recovered fragment, moderate suspicious-clean, construction anti-naivety pass
- **Class D (Manual):** Operator-forced regardless of score

## The Suspicious-Clean Seam

The most architecturally significant escalation trigger is **A7: Suspicious-clean above hard threshold**:
code where complexity + unknownness + effect surface are high but Forge remained implausibly clean.

This is the failure mode our current front gate cannot catch. It is the primary motivation for the LBE.

## Implementation Order (from spec)

1. Forge IR substrate (normalize Python first)
2. Tiny Python lowering pilot into Forge IR  
3. Path Engine (bounded static walker)
4. Blob Schema emitter
5. Escalation gate wired into front gate
6. HUD/cockpit inspection surface (NEXUS integration)

## Files in This Directory

- `LBE_LOGIC_BLUEPRINT_ENGINE_SPEC_v0.1.md` — full spec: purpose, doctrine, modes, 5-layer architecture
- `FORGE_IR_SPEC_v0.1.md` — IR substrate: node kinds, edge kinds, trust model, top-level schema
- `BLOB_SCHEMA_SPEC_v0.1.md` — blob artifact: schema, scoring axes, trust fields, creation triggers
- `PATH_STATE_SPEC_v0.1.md` — path state vector: all axes (trust/taint/ownership/invariant/effect/capability/role)
- `ESCALATION_CRITERIA_SPEC_v0.1.md` — when front gate escalates to LBE: 4 classes, explicit triggers
