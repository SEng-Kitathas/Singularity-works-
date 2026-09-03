# Forge Checkpoint Re-entry Protocol v0.1

Status: Attempt-0 design contract.

## Commander intent
A useful recovery feature must never exist only as automation.

Quarantined checkpoints SHALL automatically prepare an isolated re-entry point, and the operator SHALL be able to manually prepare the same kind of re-entry point from any checkpoint.

Locked QOL law:
**`AUTO_CAPABILITY_WITHOUT_MANUAL_OPERATOR_PATH == INCOMPLETE_CAPABILITY`.**

## One primitive, two triggers
Both automatic quarantine recovery and manual checkpoint recovery use the same primitive:

`prepare_reentry(checkpoint_id, trigger)`

Allowed v0.1 triggers:
- `quarantine_auto`
- `manual`

There is no hidden auto-only recovery path.

## Re-entry preparation
Preparation is not automatic execution.

The service SHALL:
1. inspect the immutable checkpoint and its event-derived reputation;
2. read the exact immutable checkpoint payload;
3. create a dedicated isolated re-entry directory;
4. materialize the exact checkpoint work-state payload and a bounded Attempt-reference index;
5. when the recorded source commit is locally available, create a detached Git worktree at that exact commit inside the isolated re-entry directory;
6. create a renderer-neutral operator popup contract describing why the checkpoint is isolated and what the user can do;
7. create a canonical re-entry manifest;
8. preserve that manifest in the Attempt Store with the checkpoint as parent;
9. append an idempotent `checkpoint_reentry_prepared` lifecycle event to the checkpoint;
10. return the same `ReentryPoint` contract to both automatic and manual callers.

## Isolation rule
A quarantined checkpoint is not returned to the normal automatic resume pool merely because a re-entry point exists.

Automatic behavior:
`checkpoint -> QUARANTINED -> prepare isolated re-entry -> notify operator`

NOT:
`checkpoint -> QUARANTINED -> automatically boot dangerous state`.

Locked law:
**`QUARANTINE_REENTRY_PREPARED != QUARANTINE_CLEARED`.**

## Source worktree
When checkpoint `source_head` is present and the source repository contains that commit:
- create a detached worktree at the exact commit;
- place it under the re-entry directory;
- never switch/reset the active App working tree;
- never mutate qualified Git Main merely to inspect old work.

If the commit is unavailable:
- do not invent source state;
- create a state-only re-entry point;
- popup must say exact source materialization is unavailable.

## Work-state materialization
The re-entry directory contains:
- `checkpoint_payload.json` — exact canonical checkpoint payload;
- `attempt_index.json` — exact durable Attempt references named by the checkpoint, with found/missing status and hashes where available;
- `operator_popup.json` — renderer-neutral popup/action contract;
- `reentry_manifest.json` — canonical receipt and lineage;
- `source/` — detached exact-commit Git worktree when materialization succeeds.

Checkpoint payload fields remain references, not duplicated semantic truth.

## Popup / operator actions
The popup contract SHALL expose manual operator choices. v0.1 actions include:
- `open_isolated_reentry` — open the isolated checkpoint workspace;
- `inspect_checkpoint` — inspect checkpoint facts/reputation without entering it;
- `compare_to_current` — compare checkpoint source identity to current source when both exist;
- `return_to_lkg` — return to the currently preferred known-good checkpoint when different;
- `dismiss` — leave the prepared recovery point untouched.

The eventual native Ergo UI may render these differently but must not remove the manual paths.

## Manual path
Any checkpoint may be prepared manually, including:
- LKG;
- STABLE;
- VERIFIED;
- crash-associated;
- quarantined;
- older source revision.

Manual preparation does not rewrite checkpoint reputation.
Unsafe checkpoints remain unsafe; isolation exists specifically so the operator may inspect/recover useful work without pretending the state is normal.

## Idempotency
Automatic quarantine preparation SHALL use a deterministic re-entry ID per checkpoint and therefore be safely replayable after an uncertain response.

Exact replay returns the existing verified manifest/re-entry point.
Conflicting reuse of the same re-entry ID fails closed.

Manual re-entry IDs may be caller-supplied for reproducibility or generated uniquely.

## Authority
Re-entry preparation authority over Core semantics: **NONE**.
The service copies/references checkpoint state; it does not decide that old semantic state is current or compatible.

## Not claimed in v0.1
- native popup/window implementation;
- automatic editor/terminal process restoration;
- automatic source mutation replay;
- Core semantic snapshot restoration;
- cross-machine worktree materialization;
- clearing quarantine;
- user confirmation UX beyond the renderer-neutral popup contract.
