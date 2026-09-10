# Forge Semantic Delta Replay v0.1 — Pre-Execution Design

Date: 2026-09-09 UTC
Status: **FROZEN CORE CANDIDATE / NOT EXECUTED**
Scope: Forge/Singularity Works whole-system semantic transformation kernel; no App/frontend dependency.

Selected frontier: add the missing replay side of the already-qualified semantic snapshot/delta substrate. The reference algebra transitions between exact verified frozen `SemanticFactBundle` snapshots using typed REMOVE/UPSERT operations over sources/evidence/entities/facts/unknowns, exact base/target bundle IDs, before/after object digests, dependency-ordered replay, target freeze verification and authority `NONE`.

First discriminator uses the existing real PyGoat semantic-currentness fixture from snapshot-delta v0.5. It must replay an evidence-only comment refresh exactly, replay a real semantic route removal exactly, reverse the semantic route-removal snapshot exactly back to baseline, reject stale/wrong base replay, reject tampered operation preconditions, preserve target Git cleanliness, and remain deterministic.

This does not materialize edits to source and does not claim arbitrary refactor equivalence.

`SEMANTIC_DELTA_REPLAY != SOURCE_EDIT_MATERIALIZATION`
`EXACT_BUNDLE_REPLAY != ARBITRARY_PROGRAM_EQUIVALENCE`
`DELTA_AUTHORITY = NONE`
