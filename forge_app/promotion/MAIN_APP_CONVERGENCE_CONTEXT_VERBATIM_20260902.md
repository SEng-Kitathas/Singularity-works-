# Forge Main / App Convergence Context — Verbatim Commander-Selected Assistant Reply

Date: 2026-09-02
Purpose: preserve the exact assistant reasoning the commander selected for Main-side discussion. The block between the markers below is reproduced verbatim from the user's supplied quotation and is not paraphrased.

--- BEGIN VERBATIM BLOCK ---

Mode: BUILD-PLAN
Role: R4 Convergence Refiner

No—not if we keep managing the separation the way we are now. In fact, making forge_app/ additive and isolated was specifically the right move for eventual convergence.

Right now the application branch diverges from qualified main primarily by adding its own subtree. That is the easiest possible merge topology. The danger starts later if both branches begin independently modifying the same core files, package structure, entrypoints, dependency manifests, semantic engine internals, etc.

There is one particularly important rule now that we have Attempt-0 provenance:

We should prefer merging main forward into forge/app-shell-rd, not rebasing the app branch.

We are already storing exact Git commit hashes in Attempt Store metadata. Rebasing would rewrite those commits and turn references like 766fe181… or ba3fcf0… into historical objects no longer on the active branch. The artifacts would still exist, but lineage would become unnecessarily awkward.

So from here I would operate like this:

main continues independently → periodically merge main into forge/app-shell-rd → resolve drift while it is small → keep building.

No force-pushes. No history rewriting just to make the graph pretty.

That aligns nicely with the corpus’s own append-oriented rule: preserve prior artifacts and record supersession/evolution instead of silently rewriting history. 90 SHALL_READ_APPEND_ONLY_PROTOCOL_BEFORE_MUTATING_CORPUS.md

When you’re eventually ready to converge

I would not simply click “merge entire development branch into main” and hope.

We create a temporary promotion/integration branch from the then-current qualified main.

Something conceptually like:

main
→ forge/app-integration-rc1

Then bring the app branch into that.

At that point we evaluate the convergence as a product transformation:

old Forge + Forge App → one coherent Forge

rather than as a Git operation.

We would check things such as:

* Does forge_app/ remain a clean subsystem, or should some pieces move?
* Which old launch/UI paths become superseded by Ergo?
* Does LBE code currently in another location get bridged, moved, or imported?
* Are there duplicate render/runtime/state mechanisms?
* Are CLI/headless Forge paths still useful?
* Which existing entrypoints remain?
* Does packaging/install behavior still work?
* Does recovery operate correctly after installation?
* Are existing qualified behaviors preserved?
* Are previously captured Attempt-0 Git references still reachable?
* Does the old dirty/local lineage have anything absent from GitHub that needs rescue first?

Only after the integrated tree passes those gates does that exact integration commit become a candidate for main.

The likely final architecture actually helps us

I don’t think the end state should be:

old Forge + separate app forever

I expect something more like:

Singularity Works
│
├─ Forge semantic/runtime core
├─ LBE
├─ Forge App
│  ├─ Ergo
│  ├─ Shell
│  ├─ Render
│  ├─ HUD
│  └─ SmartCanvas/CogTerm
│
├─ CLI / headless interfaces
└─ shared persistence/recovery

In other words, the application becomes another first-class embodiment of the Forge core, albeit probably the primary human interface.

The core shouldn’t need to know that Aero glass exists.

The renderer shouldn’t own semantic truth.

Ergo shouldn’t own LBE.

LBE shouldn’t own persistence.

That separation makes convergence substantially easier.

There is one future problem worth preventing now

If we start copying existing Forge/LBE code into forge_app/ instead of depending on or deliberately moving the canonical implementation, we’ll create a fork inside the repository.

That would be bad.

So when we get to LBE integration, the rule should be:

Bridge first. Move deliberately later. Never duplicate canonical truth just to make the app self-contained.

“Self-contained software” means one distributable system.

It does not mean every subsystem contains its own copy of everything else.

Git convergence versus product convergence

Those are two separate gates.

The Git merge will probably be relatively easy if we maintain isolation.

The architectural convergence is where we should spend our effort.

Fortunately we’ve already created the structures that make that safer:

* separate branch;
* separate subtree;
* exact qualified ancestor;
* no mutation of main;
* Attempt-0 commit lineage;
* recovery artifacts outside source Git;
* promotion directory;
* trace/revisit state;
* explicit donor lineage;
* eventual promotion gate.

So I don’t see this becoming one of those nightmare “we worked for six months and now the branches are two unrelated products” situations unless we allow shared-core divergence to accumulate.

I would therefore add one operating rule going forward:

MAIN_DRIFT_SHOULD_BE_INGESTED_EARLY; APP_PROMOTION_SHOULD_BE_INGESTED_LATE.

Meaning: regularly bring improvements from main into the app branch so we stay current.

But don’t push app work back into main until it is actually qualified.

That gives us low merge debt without sacrificing the clean baseline.

And because Git commit identity is now part of our provenance system, I would treat the app branch as effectively append-oriented from here forward: merges, descendants, explicit reversals—no casual rebasing or force rewriting.

So: no, I’m not worried about eventual convergence yet. The structure we created is actually the topology I’d choose if convergence were planned from day one. The thing that will keep it easy is being disciplined about shared-core duplication and regularly absorbing main while this branch grows.

--- END VERBATIM BLOCK ---
