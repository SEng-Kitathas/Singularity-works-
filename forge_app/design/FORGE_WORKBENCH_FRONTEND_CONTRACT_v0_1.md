# Forge Workbench Frontend Contract v0.1

Status: **ATTEMPT 0 — FRONTEND CONTRACT CANDIDATE / PRESERVE BEFORE FIRST EXECUTION**  
Date: 2026-09-09  
Authority: App frontend/user-experience contract only. No Forge semantic, source-mutation, security, or runtime authority.

## Purpose
Give Forge Shell, LBE, HUD, and CogTerm/SmartCanvas one renderer-neutral operator model instead of separate UI-specific truth stores.

The Workbench consumes already-frozen canonical semantic-field state and optional qualified semantic-delta replay artifacts. It may filter, select, search, summarize counts, and expose exact evidence/currentness. It SHALL NOT mint facts, rewrite semantic identity, or turn a preview into source mutation authority.

## Current upstream binding
- public Main: `e66c071fc25f8d08bfc7ebf0551948392d652f35`;
- qualified Core semantic anchor: `a7b4511734b1a1e507230308e75b31175aef4c4a`;
- current App source before this attempt: `43aa7feac7e8a15828116bd700b644560714496d`;
- current project-control at design freeze: `d9b7c5e8b1854b705f134a2d6e1dca6acc9a1a47` / CHECKPOINT `b8333e3758cc98edb14c1302744bc3ef44210678dd1122e27648c51def6b588e`, independently fresh-clone verified PASS 248;
- newly qualified Core replay lineage: module `870d5c76fd555744e77206b25aedf88cfa9c359890f970524003dd93275c8818`, summary `f49a1f61b1a8d2fd22380d9bde219cbf952147523bc7c694faa914ce43cf25a1`, bounded admission `84c1faef40e41842549b4880459f9fa240f0b9940ee6e3e5be9c5a08a4e70bbb`;
- upstream law: `EXACT_BUNDLE_REPLAY != SOURCE_EDIT_MATERIALIZATION`.

## Product laws embodied
- `FIELD != MAP`.
- `PROJECTION != AUTHORITY`.
- `SELECTION != PROMOTION`.
- `UNKNOWN_STAYS_VISIBLE`.
- `EXACT_BUNDLE_REPLAY != SOURCE_EDIT_MATERIALIZATION`.
- `UI_CURRENTNESS != SEMANTIC_TRUTH`.
- `READ_ONLY_COMMAND != CONSEQUENCE_AUTHORITY`.

## Workbench model
The model is a disposable frontend projection over a `FrozenSemanticFactBundle`.

It exposes:
1. exact source bundle identity and source authority;
2. explicit currentness (`MATCH`, `MISMATCH`, `UNKNOWN`);
3. mechanically derived entity nodes;
4. exact subject facts and evidence referents in the inspector;
5. all UNKNOWN seams as first-class rows;
6. renderer-neutral lens/search/selection state;
7. optional semantic-delta preview from serialized Core replay plan + qualification summary;
8. command affordances with consequence scope;
9. deterministic canonical JSON/model hash for renderer/session binding;
10. a minimal text renderer as a cheap first-class fallback.

## Lenses
v0.1 lenses are deliberately mechanical, not semantic classifiers:
- `all` — all entities;
- `capability` — canonical entity kind `capability` only;
- `implementation` — module/function/method/class/value/call/effect/record/source_span entities;
- `unknown` — entities referenced by one or more canonical UNKNOWN seams;
- `evidence` — entities with direct or fact/seam evidence references.

A lens routes attention. It never changes the underlying field.

## Search
Search is case-insensitive substring matching over existing presentation strings only:
- entity name/kind/id;
- source path;
- existing fact predicates;
- existing UNKNOWN questions/reasons.

Search SHALL NOT infer synonyms, create tags, or claim semantic equivalence.

## Evidence inspector
Selecting an entity presents:
- exact entity identity/kind/name/source path;
- all facts whose canonical `subject_id` equals the entity;
- fact evidence status and assurance ceiling;
- exact evidence IDs/source paths/line spans/snippet hashes;
- all UNKNOWN seams for the entity.

Objects are represented as canonical JSON display strings. The Workbench does not reinterpret them.

## Delta preview
A delta preview may be built only from a serialized plan with:
- version `forge.semantic-delta-replay/0.1.3`;
- `delta_authority == NONE`;
- unique operation IDs;
- only `REMOVE` and `UPSERT` actions;
- stable base/target/plan identities.

When a qualification summary is supplied, the Workbench marks replay `QUALIFIED_BOUNDED` only if:
- summary verdict is `PASS`;
- every named check is true;
- `pass_count == check_count`;
- the plan ID is named by the summary's `plans` map;
- the summary carries a non-empty claim ceiling.

Even then, **materialization remains disabled** in v0.1. A qualified replay preview means a bundle transition can be shown under the Core claim ceiling; it does not mean source files may be edited.

## Command surface
The first command reducer is intentionally read-only:
- `home`
- `clear`
- `lens <all|capability|implementation|unknown|evidence>`
- `select <entity-id>`
- `find <text>`
- `preview-delta`
- `reverse-preview`

`materialize` is recognized only to return a hard disabled result explaining that source materialization is unearned.
Unknown commands are rejected. No command invokes a shell, filesystem mutation, Git mutation, network action, or semantic transformation.

## Rendering contract
The text renderer is not the final visual identity. It proves that the exact same model is usable under the cheapest presentation tier. Native/vector/GPU renderers may later consume the canonical model JSON/hash without gaining authority.

## v0.1 qualification gates
The candidate is not qualified until hostile tests demonstrate:
1. deterministic model JSON/hash;
2. selection cannot reference an unknown entity;
3. lens/search only hide/show existing nodes;
4. all canonical UNKNOWN seams remain present in model state;
5. inspector evidence pointers remain exact;
6. source/currentness mismatch remains visible;
7. qualified delta preview validates exact Core plan/summary shape;
8. malformed/unqualified plans fail closed or remain visibly unqualified;
9. materialization stays disabled despite replay PASS;
10. command reducer performs no consequence-bearing action;
11. actual admitted Core v0.1.3 summary/plan can be parsed into a bounded preview without modifying either arm.

## Promotion ceiling
Passing v0.1 qualifies only the renderer-neutral **read-only Workbench presentation contract and reducer**. It does not qualify native shell/window/input, source materialization, graph layout usability, operator task performance, project-tree/GitHome integration, or runtime authority.
