# Forge Double-Helix Synchronization Checkpoint — 2026-09-03

Mode: CHECKPOINT
Role: R4 Convergence Refiner
Purpose: bind Forge Core/Main and Forge App as two coordinated, independently pressured strands of one eventual product without collapsing their qualification boundaries.

## Helix model
Forge is one product lineage expressed through two temporarily isolated strands:

- **Main/Core strand** — owns canonical shared semantic/runtime/core truth, language-agnostic Forge/LBE semantics, exact semantic-field/currentness/materialization behavior, and shared interfaces.
- **App strand** — owns application embodiment: recovery/Attempt Store, Ergo launch/recovery, renderer isolation, shell/terminal/SmartCanvas/HUD interaction, operator UX, and native presentation work.

The strands are expected to advance at different speeds and on different problems. Divergence of function is healthy. Divergence of canonical truth is not.

## Verified synchronization vector
### Qualified public Main
`1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`

### Main local promotion candidate
Branch: `pcmmad/semantic-field-core-v01`
Commit: `a7b4511734b1a1e507230308e75b31175aef4c4a`
Working tree: clean at sync readback.
Status: **LOCAL CANDIDATE ONLY — NOT REMOTE, NOT PUBLIC, NOT YET PROMOTED**.
Candidate contains the earned canonical semantic-field/currentness/materialization surface and thin `semantic_field_bridge` consumer facade. Pre-commit source/wheel/install qualification passed; exact post-commit detached replay remains the next Main gate.

### App strand
Branch: `forge/app-shell-rd`
Local/remote HEAD: `2a21ce9a80b1a67fc9225834575d490a8bfb9471`
Working tree: clean at sync readback.
Qualified Main observed by App: `1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`.
App remains intentionally ahead in recovery/Ergo/renderer embodiment and has **not** copied canonical Core/LBE truth.

## Shared laws
1. **`MAIN_DRIFT_SHOULD_BE_INGESTED_EARLY; APP_PROMOTION_SHOULD_BE_INGESTED_LATE`.**
2. Main -> App uses forward merge after a shared Main change is itself qualified/promoted; keep drift small.
3. No casual rebase/force rewrite of provenance-bearing App history.
4. App must not vendor/copy Main semantic-field/LBE implementations merely to keep moving.
5. Main must not absorb App recovery/renderer/operator implementation merely because it works locally.
6. Cross-strand communication should exchange **interfaces, qualification packets, hashes, states and obligations**, not duplicated ownership.
7. Git mergeability is not product/architectural qualification.
8. Eventual App -> Main convergence occurs through an integration/promotion branch from then-current qualified Main and qualifies the exact integrated commit.

## Base-pair handshake rule
A new cross-arm handshake is mandatory when any of the following happens:
- qualified/public Main moves;
- a shared Core interface/schema changes;
- App begins consuming a new Core interface;
- App creates a product-level behavior that would pressure or alter Core semantics;
- either arm discovers a contradiction in the other's assumptions;
- App reaches a promotion candidate intended for eventual Main convergence.

Every handshake records at minimum:
- qualified Main SHA;
- Main candidate SHA/status if one exists;
- App SHA/status;
- shared interface/schema versions;
- what each arm owns;
- what each arm must **not** duplicate;
- unresolved cross-arm seams;
- next synchronization trigger.

## Current cross-arm seam
The Main semantic-field Core candidate is **not yet consumable by App** because its post-commit replay/promotion verdict is incomplete. App should therefore continue renderer/recovery work against the existing qualified Main and reserve only a consumer boundary for future canonical semantic-field access.

Main's next cross-arm obligation is to finish exact replay qualification of `a7b4511734b1a1e507230308e75b31175aef4c4a`. If it earns promotion and qualified Main advances, App should perform an early forward-sync before building any LBE semantic-field consumer.

App's next cross-arm obligation is to continue the persistent renderer-host/crash-isolation frontier without introducing a private semantic-field/LBE truth implementation.

## Double-helix principle
**Separate pressure, shared identity. Independent embodiment, shared canonical truth. Frequent base-pair checkpoints, no premature strand collapse.**
