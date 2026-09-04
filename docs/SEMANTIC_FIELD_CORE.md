# Semantic Field Core

The semantic field is the exact, currentness-aware substrate underneath Forge analysis models and the LBE/HUD. It does **not** replace `facts.FactBus`, `semantic_ir.UniversalSemanticIR`, or the Blueprint. Those remain analysis/result surfaces; this layer binds semantic claims to exact source/evidence revisions and provides immutable read snapshots, bounded projections, snapshot deltas, and reversible evidence-bound materialization.

## Ownership

Core/Main owns this implementation. Application code should consume `singularity_works.semantic_field_bridge` rather than copy the field implementation. The bridge is deliberately thin and carries no parser/security/donor-specific lowering logic.

## Truth boundaries

- Source/evidence identity is exact and hash-bound.
- Mutable build state is verified before it becomes an immutable read snapshot.
- Indexes and projections are disposable read accelerators with authority `NONE`.
- Exact fact revision identity is distinct from semantic continuity across revisions.
- Evidence proves/disambiguates a claim; generic evidence text is not automatically the claim's semantic meaning.
- Materialization plans verify preimage/snippet hashes and produce an inverse patch; semantic correctness still requires reparse/readback.

## Current public bridge

`semantic_field_bridge` exposes snapshot description, frozen index construction, bounded fact selection, snapshot comparison, verification/freeze, and exact evidence-bound patch planning/application. Lowerers remain separate producers.

## Explicitly not promoted here

- Microseed-specific capability adapters.
- Security benchmark adapters/findings.
- Tree-sitter/runtime parser ownership.
- Language-specific relation lowerers.

Those surfaces must earn their own source-promotion gates.
