# Next Steps — Singularity Works / Forge LBE

Last updated: 2026-09-02 UTC

## Immediate P0 — coordinated Core/Main + App work
| Priority | Action | Why it matters | Dependency / trigger | Done when |
|---|---|---|---|---|
| P0 | Treat `singularity-works-forge-app` as the isolated application embodiment of the same Forge product, not a competing fork | prevents architectural divergence and duplicated core truth | active immediately | both projects carry same convergence doctrine and exact verbatim context |
| P0 | Periodically merge qualified Main forward into `forge/app-shell-rd` | keeps app current while drift is small | whenever qualified Main advances | app branch contains current qualified Main ancestry without history rewrite |
| P0 | Do not casually rebase/force-push app history | Attempt Store/qualification records reference exact app Git commits | active immediately | app lineage remains append-oriented and provenance references stay meaningful |
| P0 | Bridge canonical Forge/LBE behavior into App rather than copying it | avoids an internal fork inside one repository | before LBE/core integration | App consumes canonical interfaces/implementations or deliberate moved ownership, never convenience duplicate truth |
| P0 | Use integration/promotion branch for eventual App -> Main convergence | separates Git mergeability from product qualification | commander authorizes convergence | exact integrated commit passes architecture/source/release gates before Main advance |
| P0 | Continue semantic/materialization/core work with App relationship in mind | App needs canonical field rather than its own fork | ongoing | core candidates expose stable boundaries suitable for App bridge |

Exact commander-selected convergence reasoning:
`notes/maintenance/MAIN_APP_CONVERGENCE_CONTEXT_VERBATIM_20260902.md`
SHA `c9e491567ac1fa99e5332891104f3343074d1d46177db82edb624a66cf85c48e`.
App Git copy is commit `9aa8b14` on `forge/app-shell-rd`.

Operating law:
**`MAIN_DRIFT_SHOULD_BE_INGESTED_EARLY; APP_PROMOTION_SHOULD_BE_INGESTED_LATE`.**

## Existing semantic/core P0
| Priority | Action | Why it matters | Dependency / trigger | Done when |
|---|---|---|---|---|
| P0 | Build/retain semantic-delta -> source-patch -> reparse/readback round-trip evidence | core bridge from interactive map to actual code manipulation | semantic field/index/delta qualified | intended semantic delta reproduces exactly after source materialization/readback |
| P0 | Advance capability/provider substitution semantics | proves puzzle-piece composition beyond route deletion | round-trip substrate | provider/composite swap preserves qualified capability/authority evidence |
| P0 | Begin language-native primitive fact lowerings | collapsed security bridges should not become permanent ontology | round-trip substrate stable | origin/flow/binding/persistence/render/validation/effect facts share same IR |
| P0 | Acquire fresh independent language holdouts before tuned vNext qualification | spent holdouts cannot validate tuned descendants | before security/language promotion | corpus fixed before new version sees holdout result |

## Current semantic-field incumbent candidate
- IR v0.1.2 SHA `5d019792cd72a58b261a9a7945eb23e3973befeb337a8625853f245fcd81a524`.
- adapters v0.1.5 SHA `d99b1c5196f5ff2c79819fc83b01144f6935879a9ecb2535986895d0c5674e72`.
- index v0.2 SHA `b8744b0825acf45c5943dec70b9fb44c1d8828ab462301e0eb3a29cdcc12c7d8`.
- delta v0.3 SHA `2e6785ad1951f609f325388ed5e838d620fb29d61500c233c9a41a666cdd4de3`.
- real 4-language scale: 26/26 PASS, 511 sources, 731 facts, 18 UNKNOWNs, ~73.9x indexed-query speedup.
- PyGoat currentness: 23/23 PASS; harmless comment 0 semantic churn; homepage route removal exactly one semantic removal.

## Core/App integration boundary
When the App is ready for LBE integration:
1. inspect/fetch then-current qualified Main;
2. merge Main forward into App;
3. define a bounded bridge/interface to canonical semantic field/read snapshots/index/delta/materialization;
4. do not duplicate the field implementation under `forge_app/`;
5. pressure headless/CLI and App consumers against the same canonical semantics;
6. only later decide whether final product structure warrants moving shared code.

## HUD/QOL continuation
The App is expected to become the primary human embodiment of existing protected LBE/HUD/QOL ideas, but Main remains the canonical source of shared semantics until explicit movement:
- semantic zoom;
- evidence/source cross-probe;
- history/currentness;
- runtime/debug trace;
- blast radius;
- counterfactual/provider substitution;
- Attention Reservoir;
- capability-aware command surface;
- mindful coprocessor.

## Independent maintenance
- Do not bulk stage/reset/clean the old dirty local repo.
- Public Main remains release qualification gated.
- App branch exists to isolate product/front-end/recovery work while preserving eventual convergence.

## Demotion triggers
- If App starts maintaining copied canonical core/LBE implementations, stop and rework the boundary before continuing.
- If repeated Main->App merges become structurally conflict-heavy, investigate ownership/package boundaries before allowing further divergence.
- If exact provenance Git commits are rewritten, treat lineage as damaged and recover from preserved references rather than smoothing it away.


## RAHL R4.0 / currentness correction — 2026-09-03 UTC
R4.0 is now the canonical project-agnostic process/cold-start SOP for Main, with project-local Forge doctrine stronger where more specific.

Current semantic delta incumbent is **v0.4**, not the historical v0.3 line above:
`code/forge_semantic_snapshot_delta_v0_4.py`
SHA `d7c71ee3ce6d3db4bdd227d4696cad526721462814a15a6908d80d5ce6c1c0cb`.

Provider substitution is no longer an open P0 seam: bounded Microseed provider substitution passed 34/34 and earned `CONTRACT_IDENTITY_SAME != PROVIDER_BEHAVIOR_EQUIVALENT` plus `EXISTING_TEST_PASS != PROVIDER_SUBSTITUTION_EQUIVALENCE`.

### Immediate P0 now
1. Re-read current source/candidate identity before execution (`REMEMBERED_POINTER != CURRENT_STATE_EVIDENCE`).
2. Finish exact committed-artifact replay/promotion qualification for the current semantic-field Core candidate; historical pointer is `a7b4511734b1a1e507230308e75b31175aef4c4a` until live verification confirms or supersedes it.
3. If shared Core is promoted, perform early qualified Main -> App forward sync before App implements semantic-field consumption.
4. Shape the Core bridge to satisfy App checkpoint identity needs (`core_contract_version`, `core_currentness_id`, `semantic_snapshot_id`, compatibility discriminator, restoration/readback proof) without importing App renderer/recovery implementation into Core.
5. Maintain `continuity/research_epistemic_shadow/res.md` as a zero-authority research frontier surface when learned meaning changes.

## RAHL R4.1 supersession / active process queue — 2026-09-03
This section supersedes earlier R4.0 process-default wording in this mutable queue.

- Current universal process/cold-start SOP: **RAHL R4.1**, carrier SHA `af4364fbcf8e5d33aa2ad06e4da9c4669d4be2ffcbc332e416742bec1543f4d2`.
- Nontrivial work must supply the causal functions of PDVER + hostile engineering + Semantic Helix + Attention Reservoir + Loop+ + OARR + CSC + additive AI co-processing, proportionally and without mandatory visible ritual.
- PDVER: `PROBE -> DERIVE -> VERIFY -> EMBODY -> RECURSE`; post-embodiment consequence readback/attack remains active.
- No universal fixed research-pass count; bounds must be justified by the active discriminator/consequence surface.
- Deep recursive read proof: `notes/maintenance/RAHL_R4_1_DEEP_LINEAR_READ_PROOF_20260903.md` SHA `a19f4a0851ffaf8e6c7109c76ad42828a70a674dbddfd4d893e3055f0c9a6ff0`.

The product/Core next action remains currentness re-read followed by exact committed-artifact replay/promotion qualification of the current semantic-field Core candidate, then early Main -> App sync if shared Core actually advances.


## Git control-plane persistence queue — 2026-09-03 UTC
### Immediate P0
1. Materialize a bounded Main control snapshot from the freshly reconciled Live Shadow, DTS, RES, Current, Doctrine, Next, Trace and Revisit surfaces.
2. Include the canonical R4.1 SOP identity, adoption/deep-read proof, double-helix synchronization law, current qualified Main SHA, current candidate/currentness labels, open seams and exact resume point.
3. Commit the snapshot on a dedicated Git control branch derived from qualified Main lineage; do not advance public `main` merely for continuity persistence.
4. Push the control branch and read back the exact remote SHA plus committed control-file identities.
5. Record the resulting branch/SHA in Live Shadow, DTS, Current, Trace and Revisit so the next chat thread has an explicit Git rehydration anchor.

Done when a fresh thread can start from the Git control checkpoint and recover the current project control state without relying on the previous chat transcript.


## Cross-thread Git control ongoing queue — 2026-09-03 UTC
Initial durability establishment is complete: GitHub `pcmmad/project-control` verified at `174ba730f691a50f332b77bb8803370ed642cae4`; fresh remote-clone checkpoint verifier PASS with 52 files.

### Ongoing checkpoint hygiene
After any load-bearing state change or before a forced thread switch:
1. update Live Shadow + DTS + RES;
2. reconcile Current / Doctrine / Next / Trace / Revisit;
3. refresh the bounded Git-safe `project_control/` snapshot;
4. run privacy/credential scan, `VERIFY_CHECKPOINT.py`, and Git diff checks;
5. commit and push `pcmmad/project-control`;
6. independently read back remote branch SHA and verify content from remote state;
7. record the new anchor in live server continuity.

### Product/Core P0 remains
The control-plane task is complete for initial establishment and no longer blocks Core work. Resume with live currentness verification followed by exact committed-artifact replay/promotion qualification of the current Main semantic-field Core candidate. If shared Core advances, perform early Main -> App sync before App binds to semantic-field Core.


## Linear human read gate — active execution rule — 2026-09-03 UTC
Before any readable artifact is promoted, sealed, published, admitted, or treated as load-bearing, require a complete linear semantic read. Automated checks may precede/support this gate but SHALL NOT substitute for it.

Immediate consequence for the current Core promotion frontier: exact committed-artifact replay/testing alone is not sufficient for promotion. Any readable candidate artifacts crossing the promotion boundary must also receive the complete linear semantic read required by the new doctrine addendum.


Exact bound text:
If an artifact can be meaningfully read, it SHALL receive a complete linear semantic read before it is promoted, sealed, published, admitted, or treated as load-bearing. Automated checks may precede and support the gate; they SHALL NOT substitute for it.
