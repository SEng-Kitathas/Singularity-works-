# Forge Workbench Frontend v0.1 — Qualification — 2026-09-09

Status: **READY_WITH_EVIDENCE — BOUNDED RENDERER-NEUTRAL READ MODEL / REDUCER / CORE REPLAY PREVIEW**  
Authority: App frontend/user-experience only. No Core semantic authority, source-edit authority, native-window qualification, or consequence authority.

## Preserved lineage
Attempt-0 App commit: `f14ed1dd677bfabdb93c8a6b18fdcf6c14e404b9` — original Workbench contract/model/tests preserved before first execution.  
Harness-repair App commit: `1170b94cf4b923e902aa5bccd530111e1e286567` — test expectation only; production model/contract unchanged.  
Real-Core integration harness App commit: `9d86925c0cfd84fa7de4941bb3e7b68e78e98a3b` — preserved before first integration execution.

Current upstream bound during qualification:
- Main `e66c071fc25f8d08bfc7ebf0551948392d652f35`;
- qualified Core semantic anchor `a7b4511734b1a1e507230308e75b31175aef4c4a`;
- control `d9b7c5e8b1854b705f134a2d6e1dca6acc9a1a47` / CHECKPOINT `b8333e3758cc98edb14c1302744bc3ef44210678dd1122e27648c51def6b588e`, clean fresh-clone PASS 248;
- Core semantic-delta replay v0.1.3 admission `84c1faef40e41842549b4880459f9fa240f0b9940ee6e3e5be9c5a08a4e70bbb`.

## Exact qualified App source blobs at `9d86925c...`
- contract `forge_app/design/FORGE_WORKBENCH_FRONTEND_CONTRACT_v0_1.md` — `0f9875d90582f203e0d9ddd1da32cb7de79c2aa8f31dfff1a5ec12cb7e2a4831`;
- Workbench model `forge_app/hud/workbench_model.py` — `c035a3d7a38a91adf2fc13daf67076e2604efc31f8009cf87d30a4924c7d24cc`;
- HUD export `forge_app/hud/__init__.py` — `b7cf00594fcce3b3b8c85d017c8e98233be09d27e95dcbc52e6254e81b5900ba`;
- repaired test suite — `d216e69dc2ec8b868055bcc25159b0d915f882a4b25bac9c3fff728f4825e363`;
- Core replay integration harness — `a5c294d9b36295ca156e1980b0d2bde9c8f88593ac4c92518c8bd4682cc9f19c`.

## First execution scar
Job `job-652321b01d46`, idempotency key `attempt-forge-workbench-frontend-v0-1-f14ed1dd-tests-first`, returned rc1: **10 PASS / 1 FAIL**.

The sole failing test searched a fact `object_value` string even though the frozen v0.1 contract limits search to entity identity/name/kind, source path, fact predicates, and UNKNOWN question/reason text. The exact first result was preserved before repair:
`ad36a6145abd809fe0d72abd07d183aafa3abec73df6f731759f36a82cf6bb1c`.

Classification: **HARNESS_INVALID_CONTRACT_MISMATCH**. No production implementation change was permitted or made.

## Repaired unit-suite qualification
Job `job-e3568c97b4e0`, idempotency key `attempt-forge-workbench-frontend-v0-1-1-1170b94-tests-first`:
- **11/11 PASS**;
- rc0;
- production contract/model unchanged from Attempt-0;
- exact preserved result `bfdf87fb8ca70e4949d21b20ca8b15e1c28e1e1c517794178767400886f58327`.

The suite verifies bounded deterministic model identity, authority NONE, visible UNKNOWN state, exact evidence referents, mechanical lenses/search, selection fail-closed behavior, delta validation, materialization denial, read-only command reduction, and cheap text rendering of currentness/authority/UNKNOWN boundaries.

## Real Core replay integration
Integration job `job-739ed7341c2f`, idempotency key `attempt-forge-workbench-core-replay-integration-v0-1-9d86925-first`, consumed exact artifacts from the clean control `d9b7c5e8...` clone:
- Core summary SHA `f49a1f61b1a8d2fd22380d9bde219cbf952147523bc7c694faa914ce43cf25a1`;
- comment plan SHA `e8c91926daf774486c02b75e0bf389a1d79686c70426e2aa9a93737c72fe8507`;
- output manifest SHA `141206785ce04072821334e75f72873a0dd09c6297ced83532cb0809f2c179a7`.

Result: **14/14 PASS**, rc0, exact preserved result `ae88c1f62fe9135e7cee83999b09109e2cb3f403e981c84b6caec02d3a3a4117`.

Verified presentation facts:
- plan `sdelta:6024689a273f9100b90eadcb`;
- base `bundle:24bab65bcaa508bc81d64367` -> target `bundle:40261aed9ca36002ffaf4a5b`;
- 456 operations;
- facts 113 REMOVE / 113 UPSERT;
- evidence 113 REMOVE / 113 UPSERT;
- entities 1 REMOVE / 1 UPSERT;
- sources 1 REMOVE / 1 UPSERT;
- all 14 upstream Core replay checks remain visible;
- reverse replay evidence remains visible;
- delta authority remains NONE;
- claim ceiling remains `EXACT_SEMANTIC_BUNDLE_REPLAY_OVER_QUALIFIED_PYGOAT_SNAPSHOTS_ONLY`;
- materialization remains disabled.

## Qualified behavior
v0.1 is qualified, within this exact ceiling, to provide a renderer-neutral frontend read model over `FrozenSemanticFactBundle` plus a validated read-only presentation of the qualified Core semantic replay plan. It can expose deterministic entity lists, mechanical lenses/search, evidence inspector rows, canonical UNKNOWN seams, currentness, read-only command state, semantic replay preview, model canonical JSON/hash, and minimal text fallback.

## Not qualified
- source-code edit/materialization;
- real GitHome project tree/status integration;
- native shell/window/docking/input;
- GPU/vector SmartCanvas rendering;
- interactive graph layout/semantic zoom usability;
- operator task latency/usability;
- arbitrary Core replay versions;
- App semantic authority;
- runtime/network/security authority.

## Next product-facing cut
Bind a real Core frozen semantic snapshot/currentness interface into the Workbench model and then render that exact model through an App shell surface. Preserve source/project navigation as GitHome-owned context and keep semantic truth Core-owned.

`FIELD != MAP`  
`PROJECTION != AUTHORITY`  
`SELECTION != PROMOTION`  
`EXACT_BUNDLE_REPLAY != SOURCE_EDIT_MATERIALIZATION`  
`APP_FRONTEND_PRESENTATION != CORE_SEMANTIC_AUTHORITY`
