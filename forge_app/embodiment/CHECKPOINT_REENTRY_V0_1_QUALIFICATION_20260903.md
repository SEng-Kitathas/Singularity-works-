# Forge Checkpoint Re-entry v0.1 — Qualification — 2026-09-03

Status: **READY_WITH_EVIDENCE for bounded isolated checkpoint re-entry, automatic quarantine preparation, manual operator re-entry, and renderer-neutral popup/manual browser contracts**.
Not yet a native-GUI popup/open-action, Core semantic restoration, or cross-machine recovery qualification.

## Commander intent
Quarantined savestates should automatically isolate, pull the work state as it was, and provide a re-entry point with a user popup. The same capability must also be manually available from any checkpoint.

Locked QOL law:
**`AUTO_CAPABILITY_WITHOUT_MANUAL_OPERATOR_PATH == INCOMPLETE_CAPABILITY`.**

Additional laws:
- `QUARANTINE_REENTRY_PREPARED != QUARANTINE_CLEARED`.
- `REENTRY_PREPARATION != AUTOMATIC_EXECUTION`.
- `REENTRY_WORKTREE != ACTIVE_CHECKOUT`.
- `FILESYSTEM_REENTRY_POINT + DURABLE_MANIFEST_RECEIPT + CHECKPOINT_EVENT` must converge idempotently after uncertain outcome.

## Attempt-0 preservation
Protocol, re-entry service, manager-level automatic quarantine hook, manual CLI/popup surface, package export, and hostile tests were committed and pushed **before first execution**:

`3cd60be5fa68bed6041d13253f5efc1245f9815f` — `forge-app: preserve checkpoint reentry and manual recovery attempt zero`.

Attempt-0/current source hashes:
- `forge_app/recovery/reentry.py` SHA `36b1cff438490c14d8df7c91c9b94a3d40ea42250df16fe9513e1dbffdef16d2`.
- `forge_app/recovery/resume_checkpoint.py` SHA `ce9abeb22aecb1bdc0367c49c1403c2a7794ec9ac163d66054ad818748f2e0aa`.
- `forge_app/recovery/CHECKPOINT_REENTRY_PROTOCOL_v0_1.md` SHA `ab2832e998bf5d3b5ff7062eb1c443792c81815b8c2f93dfe958621246d3873d`.
- `forge_app/recovery/__init__.py` SHA `455c7b2a11df9a5b7e04b528c23b13ef727b576c80607bb5b022eeac728f4186`.

## One primitive, two triggers
Both automatic and manual paths use `CheckpointReentryService.prepare_reentry()`.

Triggers:
- `quarantine_auto` — deterministic re-entry ID per checkpoint;
- `manual` — explicit or generated re-entry ID.

There is no separate hidden auto-only reconstruction path.

The checkpoint manager registers the service as its quarantine handler. Any existing crash path that transitions a checkpoint to QUARANTINED therefore invokes the same preparation primitive automatically.

If quarantine commits but preparation fails afterward, a duplicate crash/replay observes the still-quarantined checkpoint and re-invokes the idempotent handler so the missing re-entry receipt can be repaired.

## Isolated re-entry contents
Each prepared re-entry lane contains:
- exact `checkpoint_payload.json`;
- `attempt_index.json` with checkpoint-referenced Attempt IDs, found/missing status and hashes/metadata where available;
- pending transaction ID references;
- renderer-neutral `operator_popup.json`;
- canonical `reentry_manifest.json`;
- detached exact-commit `source/` Git worktree when the recorded commit is locally available.

The active App checkout is never reset/switched merely to inspect a checkpoint.

If source commit/repo is unavailable, state-only re-entry still materializes and the popup reports the source limitation instead of fabricating code state.

## Popup contract
Renderer-neutral actions:
- `open_isolated_reentry`;
- `inspect_checkpoint`;
- `compare_to_current` when both source identities exist;
- `return_to_lkg` when a different preferred checkpoint exists;
- `dismiss` while leaving the isolated lane intact.

Preparing re-entry never clears quarantine or upgrades checkpoint reputation.

## First hostile execution
Command:
`python -W error::ResourceWarning -m unittest forge_app.embodiment.test_checkpoint_reentry_v0_1 -v`

Attempt-0 result: **6/6 PASS unchanged**.

Verified:
1. manual re-entry from an older checkpoint creates an exact detached source worktree while active repo HEAD/status remain exact unchanged;
2. exact checkpoint work-state fields and pending transaction IDs are materialized;
3. checkpoint-referenced Attempt IDs are indexed with exact blob identity;
4. two early crashes automatically quarantine and prepare one deterministic isolation lane + popup;
5. older LKG remains selected while risky checkpoint stays quarantined;
6. manual re-entry remains available for a quarantined checkpoint and does not clear quarantine;
7. missing source repo still creates a usable state-only re-entry lane;
8. same re-entry ID cannot be silently reused for a different checkpoint;
9. injected failure after quarantine/manfiest-file creation but before durable manifest receipt is repaired by duplicate crash replay without duplicating the lifecycle event.

No code repair was required after Attempt 0.

## Manual discoverability refinement
After Attempt-0 success, one QOL descendant added checkpoint enumeration so manual recovery does not require memorizing an opaque checkpoint ID.

Commit:
`7612593e2b4fe35bab4a824ae41c4df77093cdda` — `forge-app: add manual checkpoint browser for reentry`.

Current CLI/test hashes:
- `forge_app/ergo/reentry_cli.py` SHA `9702b38d378a79d0300d670b92fa6e93d35f63312e707946b610ca8a6024e718`.
- `forge_app/embodiment/test_checkpoint_reentry_v0_1.py` SHA `4402a0304e46a3314c3a0f37e2a76756c27221785b08f771dec21caf26f0cb77`.

Targeted descendant result: **7/7 PASS**.

Live `--list` output exposed every live checkpoint as manually reachable and marked the preferred one:
- generation 2 LKG `checkpoint-app-live-0002-0f1109ede732`;
- generation 1 VERIFIED `checkpoint-app-live-0001-e0f59ee07cc8`;
- generation 0 QUARANTINED probe `checkpoint-live-quarantine-auto-probe-v0-1`.

## Full App regression
After the manual browser descendant, the complete App recovery/Ergo/renderer/checkpoint/re-entry suite was run with `ResourceWarning` promoted to error.

Result: **55/55 PASS** in 7.877 seconds.

## Live manual re-entry proof
The real generation-2 LKG was manually prepared after the active App branch had advanced.

Checkpoint:
`checkpoint-app-live-0002-0f1109ede732`
recorded source:
`0f1109ede732a77a8e4f958edc7e1eb9006ce783`.

Active source during re-entry:
`3cd60be5fa68bed6041d13253f5efc1245f9815f`.

Manual re-entry ID:
`manual-live-lkg-generation-2`.

Verified:
- popup severity `MANUAL_REENTRY`;
- checkpoint status remained LKG;
- source currentness `MISMATCH` visible;
- isolated source status `EXACT_DETACHED_WORKTREE`;
- isolated source HEAD exact `0f1109ede732a77a8e4f958edc7e1eb9006ce783`;
- isolated source clean and detached;
- active App source HEAD remained exact `3cd60be5fa68bed6041d13253f5efc1245f9815f` and clean;
- checkpoint reputation remained LKG/not quarantined;
- manifest SHA `d1a328e7bff29adec5aff478a45d4f3899b1f9c64e38d5ff49bd062a54739ea9`;
- manifest preserved as `reentry-manifest-manual-live-lkg-generation-2`;
- exactly one `checkpoint_reentry_prepared` event recorded for that manual re-entry.

## Live automatic quarantine proof
A disposable live checkpoint was used to prove the automatic path without damaging the real LKG:

`checkpoint-live-quarantine-auto-probe-v0-1`.

Source at probe:
`3cd60be5fa68bed6041d13253f5efc1245f9815f`.

First deliberate early crash:
- status `CRASH_ASSOCIATED`;
- early crash count 1;
- SAFE_ONLY;
- not quarantined.

Second distinct early crash:
- status `QUARANTINED`;
- early crash count 2;
- INSPECT_ONLY;
- automatic quarantine handler invoked.

Automatically prepared re-entry:
`reentry-quarantine-checkpoint-live-quarantine-auto-probe-v0-1`.

Verified:
- trigger `quarantine_auto`;
- popup severity `RECOVERY_ISOLATED`;
- exact detached source worktree at the checkpoint commit;
- source currentness MATCH for the probe;
- quarantine remained active;
- popup exposed `open_isolated_reentry`, `inspect_checkpoint`, `compare_to_current`, `return_to_lkg`, and `dismiss`;
- `return_to_lkg` pointed to the real generation-2 LKG;
- real LKG remained the preferred recovery checkpoint.

Live store after the automatic proof:
- integrity `ok`;
- WAL;
- synchronous FULL;
- 46 blobs / 46 attempts / 59 events.

## Manual operator surface
Current CLI supports:

List every checkpoint:
`python -m forge_app.ergo.reentry_cli --store <store> --reentry-root <root> --list`

Prepare any checkpoint manually:
`python -m forge_app.ergo.reentry_cli --store <store> --reentry-root <root> --source-repo <repo> --checkpoint <checkpoint-id> [--reentry-id <id>]`

This CLI is not intended as the final UX. It guarantees manual reachability now; the native Ergo checkpoint browser/popup should call the same service later.

## Bounded claim
Forge App can now automatically isolate a quarantined checkpoint into an exact, durable re-entry lane and notify the operator through a renderer-neutral popup contract while preserving quarantine and the older known-good path.

The same isolation/reconstruction primitive is manually reachable from every checkpoint, including quarantined and older-source checkpoints.

Where the recorded Git commit is locally present, source is reconstructed in a detached isolated worktree without touching the active checkout. Work-state payload, Attempt references and pending transaction references are materialized alongside it.

## Remaining seams
- native popup/window and clickable action implementation;
- actual editor/terminal/SmartCanvas reopening from the materialized work-state fields;
- re-entry worktree retention/garbage-collection policy;
- user-driven delete/archive of old isolation lanes;
- source dependency/environment identity beyond Git commit;
- qualified Core semantic snapshot restoration;
- safe replay/inspection of pending source mutation transactions;
- cross-machine or missing-object source restoration;
- human usability testing of checkpoint browsing/re-entry workflow.

## Next pressure
Create a new current-source checkpoint/LKG after this qualification commit, then proceed to externally supervised coordinator-process death. That supervisor should use the same manager/service path so two early real process deaths automatically quarantine and materialize the risky checkpoint while the current LKG remains one-click/manual accessible.
