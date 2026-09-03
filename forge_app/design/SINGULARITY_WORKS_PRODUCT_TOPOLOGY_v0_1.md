# Singularity Works Product Topology v0.1

Status: **WORKING architecture contract** — promoted from sidebar discourse on 2026-09-03.
Authority: product-topology design for the isolated App strand; does not move canonical Forge semantics out of Core/Main.

## Product identity
**Singularity Works is the software/product as a whole. Forge is its semantic/evidence/transformation core.**

Locked distinctions:
- `SINGULARITY_WORKS != FORGE`.
- `FORGE_CORE != PRODUCT_WHOLE`.
- Main/Core and App are development/qualification strands, not intended permanent user-facing kingdoms.

## Product-level topology

```text
SINGULARITY WORKS
|
+-- Ergo
|   +-- boot / integrity / recovery
|   +-- checkpoint browser
|   +-- isolated re-entry
|   +-- session launch/recovery posture
|
+-- GitHome
|   +-- project/repository home
|   +-- real project tree
|   +-- branches / commits / remotes
|   +-- activity / provenance
|   +-- imports / exports
|   +-- checkpoint/recovery visibility
|   +-- Forge/LBE evidence overlays
|
+-- Forge                         <-- CORE
|   +-- LBE / semantic field
|   +-- evidence / currentness
|   +-- SnapshotDelta / comparison
|   +-- capability/effect reasoning
|   +-- materialization / verification
|   +-- semantic transformation
|
+-- Operator Surfaces
|   +-- SmartCanvas
|   +-- CogTerm / terminal
|   +-- HUD / lenses / maps
|
+-- Singularity Vault
|   +-- projects / source / Git objects
|   +-- Attempts / checkpoints / evidence
|   +-- re-entry lanes / recovery bundles
|   +-- secrets / connector credentials
|   +-- import quarantine / export receipts
|
+-- Connection Gate
    +-- OAuth / API / GitHub / registries / AI providers
    +-- explicit identity + capability + resource scopes
    +-- session arming / consequence gates
    +-- ingress / egress receipts
```

## Ownership laws
- `VAULT_OWNS_SECURE_STORAGE; FORGE_OWNS_SEMANTIC_REASONING`.
- `GITHOME_OWNS_PROJECT_NAVIGATION; FORGE_OWNS_PROJECT_UNDERSTANDING`.
- `CONNECTION_GATE_OWNS_EXTERNAL_AUTHORITY; FORGE_MAY_ADVISE_BUT_DOES_NOT_MINT_AUTHORITY`.
- `ERGO_OWNS_BOOT_AND_RECOVERY_PRESENTATION; CHECKPOINT_STORE_OWNS_DURABLE_RECOVERY_FACTS`.
- `PRESENTATION_STATE != TRUTH_AUTHORITY`.

## GitHome relationship
GitHome is a Singularity Works subsystem/surface, not a Forge subsystem and not a PCMMAD runtime dependency.

GitHome adopts GitHub-familiar interaction grammar while remaining broader than Git:
- Git repository;
- ordinary source tree;
- imported archive;
- mounted collection;
- recovery/re-entry lane;
- multi-repository product;
- generated/non-Git project.

Locked laws:
- `PROJECT_IDENTITY != GIT_IDENTITY`.
- `GITHOME != GIT_ONLY`.
- `LAZY_RENDERING != INCOMPLETE_PROJECT_MODEL`.

The project model must remain complete even when the UI virtualizes/lazily renders millions of entries.

## Forge relationship
Forge remains the canonical semantic core. GitHome, Ergo, Vault and Connection Gate may consume Forge reasoning/evidence surfaces but must not privately recreate Forge canonical semantics.

Core/Main remains the owner of canonical semantic/currentness/snapshot interfaces until explicit product convergence/promotion.

## App/Main convergence implication
The existing double-helix remains useful as a development topology:
- Core/Main evolves what Forge means;
- App evolves how Singularity Works is operated under runtime/product pressure.

Eventual product integration should present one Singularity Works system even if internal development responsibilities remain separate.
