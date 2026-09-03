# GitHome Product Surface v0.1

Status: **WORKING product/UI architecture contract** — promoted from sidebar discourse on 2026-09-03.
Authority: Singularity Works App/product surface candidate. GitHome is not the canonical semantic authority.

## Purpose
GitHome is the Singularity Works project/repository/workspace home. It should feel familiar to users of GitHub while being local-first, Vault-aware, checkpoint-aware, provenance-aware, and Forge/LBE-enhanced.

## Core identity
Locked laws:
- `GITHOME != GIT_ONLY`.
- `PROJECT_IDENTITY != GIT_IDENTITY`.
- `GITHOME_OWNS_PROJECT_NAVIGATION; FORGE_OWNS_PROJECT_UNDERSTANDING`.
- `LAZY_RENDERING != INCOMPLETE_PROJECT_MODEL`.

GitHome may present Git strongly, but it must also support:
- ordinary source folders;
- Git repositories;
- multi-repository products;
- imported archives;
- mounted collections;
- generated projects;
- recovery/re-entry lanes;
- projects not yet under Git.

## Primary layout grammar
Target interaction grammar:

```text
SINGULARITY WORKS / GITHOME
Project: <project>      Branch: <branch>      Vault: <state>      Remote: <state>

+----------------------+--------------------------------+----------------------+
| PROJECT TREE         | PROJECT HOME / CONTENT         | EVIDENCE / STATUS    |
|                      |                                |                      |
| src/                 | README / file / diff / LBE    | currentness          |
| tests/               |                                | security             |
| docs/                | activity / history / branch   | semantic delta       |
| .singularity/        | checkpoint / import / export  | provenance           |
|                      |                                | external state       |
+----------------------+--------------------------------+----------------------+
| branch | dirty/clean | Vault | connector armed state | push/publish posture  |
+-------------------------------------------------------------------------+
```

The exact visual style remains a later native-UI concern. The information architecture is the load-bearing part.

## Real project tree
The tree must model the complete project, even when display is virtualized.

Potential status dimensions:
- tracked / untracked / ignored;
- staged / modified / deleted / renamed;
- generated;
- binary;
- symlink;
- external-origin;
- quarantined;
- secret-sensitive;
- checkpoint membership;
- evidence/currentness state;
- LBE finding count/severity;
- provenance / import lineage.

Virtualized rendering is an optimization only. It must not create hidden/unknown project state merely because nodes are offscreen.

## Project home tabs/surfaces
Candidate first-class surfaces:
- README / Overview;
- Files;
- Activity;
- Branches;
- Commits / History;
- LBE;
- Evidence;
- Security;
- Recovery / Checkpoints;
- Imports;
- Exports;
- Connections;
- Settings / Vault state.

## Forge-enhanced Git interactions
GitHome should extend familiar Git operations with Forge evidence rather than replacing Git semantics.

Examples:
### File row
May expose:
- Git status;
- semantic delta count;
- evidence currentness;
- blast radius/dependents;
- external-origin/quarantine state.

### Commit/diff view
May expose:
- exact source diff;
- Forge semantic delta;
- affected entities/capabilities/effects;
- test/qualification receipts;
- provenance/currentness notes.

### Re-import view
May expose:
- known export ancestor;
- bit identity match/mismatch;
- changed files;
- semantic changes;
- new network/filesystem/privilege effects;
- dependency changes;
- test status;
- LBE/security/quality disposition;
- isolated open / compare / reject / promote actions.

## Push ergonomics
A deliberately armed, branch-scoped connector should make ordinary push easy.

Example operator envelope:
- provider identity verified;
- repo exact;
- branch exact;
- read/write/push granted;
- delete/admin/force-push denied;
- session armed.

Within that envelope, ordinary push can be one clear confirmation or direct action according to user policy.

Push UI should show consequence-critical facts without forcing ritual:
- remote;
- branch;
- commit count;
- file count;
- protected-boundary status;
- connector/authority state;
- egress receipt status.

Higher-consequence operations should route through stronger Connection Gate policy.

## Vault relationship
GitHome operates on projects in the Singularity Vault by default.

External filesystem destinations, remotes, exports and imports must visibly cross the secure-environment boundary.

GitHub/remotes are not “just another folder”; pushes are egress events with receipts even when ergonomically streamlined by a pre-armed connector.

## Manual parity / operator agency
Anything GitHome does automatically that is reasonably useful to invoke manually should expose a manual action unless a concrete safety reason forbids it.

Examples:
- refresh/reindex;
- run LBE analysis;
- compare branches/checkpoints;
- create isolated re-entry;
- export;
- import/requalify;
- arm/disarm connector;
- inspect receipts;
- pin/archive recovery state.

## Security / authority display
A single “connected” green badge is insufficient.
GitHome should separately expose:
- provider identity verified?;
- credential present?;
- grant scope?;
- resource scope?;
- session armed?;
- effective capability?;
- elevated consequence pending?;

Locked law:
`VERIFIED_PLATFORM != FULL_AUTHORITY`.

## Donor disposition
PCMMAD GitHome concepts are donor material only. Singularity Works adopts the useful mechanisms:
- authenticated ingress boundary;
- project identity broader than Git;
- explicit separation of file/Git/execution/continuity/archive surfaces;
- mounted/imported/recovery project forms;
- real project-tree/context/search/read surfaces.

No PCMMAD runtime dependency, namespace, branding, or authority transfers into Singularity Works by default.

## v0.1 open seams
- exact native visual design;
- search/filter/tree scaling benchmark;
- multi-repository project UX;
- branch protection/consequence policy implementation;
- connector UI/state machine implementation;
- Vault path/container integration;
- source-secret classification display;
- LBE semantic overlay performance budget;
- project-level permissions in future multi-user mode.
