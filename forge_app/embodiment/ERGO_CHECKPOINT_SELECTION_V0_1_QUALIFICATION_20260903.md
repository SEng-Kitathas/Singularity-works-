# Ergo Read-Only Checkpoint Selection v0.1 — Qualification — 2026-09-03

Status: **READY_WITH_EVIDENCE for read-only savestate selection/currentness presentation**.

## Attempt-0 preservation
Pure checkpoint derivation/selection helpers, read-only Ergo checkpoint summary, launch-model checkpoint facts, minimal CLI integration, and hostile tests were committed and pushed before first execution:

`0c5a872` — `forge-app: preserve read-only Ergo savestate selection attempt zero`.

The checkpoint reputation logic remains single-source: `derive_checkpoint_view()` and `choose_recovery_view()` live in the recovery checkpoint module and are reused by both the mutating checkpoint manager and the read-only Ergo observer.

Ergo opens the SQLite store with `mode=ro` + `PRAGMA query_only=ON` and does not instantiate an `AttemptStore` writer merely to inspect recovery selection.

## First targeted execution
Targeted checkpoint/launch integration result: **19/19 PASS**.

Verified:
- missing store reported without creation;
- healthy store with no checkpoints reports NONE;
- VERIFIED checkpoint is selected read-only;
- DB bytes and mtime unchanged by checkpoint selection inspection;
- quarantined newest checkpoint is not selected over older LKG;
- launch model surfaces checkpoint status/generation/policy/source/Core-snapshot absence without minting authority.

## Live launcher scar discovered before qualification
The first real live Ergo render against the actual project exposed a new safety seam.

At that moment:
- current source HEAD: `0c5a872877c6...`;
- selected checkpoint generation 1 source HEAD: `e0f59ee07cc8...`;
- checkpoint itself: VERIFIED;
- Ergo presentation: POSTURE READY / Resume policy NORMAL.

Although both source hashes were visibly different, the launcher had not yet converted that mismatch into recovery policy.

Classification: **unsafe currentness interpretation**.

Earned law:
**`CHECKPOINT_VALID != CURRENT_SOURCE_COMPATIBLE`**.

A checkpoint can be byte-valid and runtime-unproven or source-stale relative to the currently running App.

## Source-currentness repair
Descendant repair preserved before retest:

`e784596` — `forge-app: downgrade stale-source savestate to safe-only resume`.

Repair behavior:
- read-only checkpoint summary accepts the current source HEAD as an external currentness reference;
- selected checkpoint reports source currentness `MATCH`, `MISMATCH`, or `UNKNOWN`;
- source mismatch does not rewrite checkpoint reputation events;
- effective resume policy is downgraded from NORMAL to SAFE_ONLY on mismatch;
- launcher posture becomes CAUTION;
- Normal remains available as a fresh launch path but is not recommended for automatic checkpoint resume;
- Safe becomes recommended;
- mismatch reason and both source identities remain visible;
- missing Core semantic snapshot remains explicitly `not bridged` / UNKNOWN rather than fabricated.

Targeted post-repair result: **20/20 PASS**.

## Live post-repair evidence
Real launcher after repair:
- current source HEAD: `e78459641fcd...`;
- selected checkpoint source HEAD: `e0f59ee07cc8...`;
- POSTURE: `CAUTION`;
- Resume checkpoint: `VERIFIED`;
- Resume policy: `SAFE_ONLY`;
- Resume source match: `MISMATCH`;
- Normal: available, not recommended;
- Safe: available, recommended;
- Core semantic snapshot: `not bridged` / UNKNOWN;
- observer authority: NONE.

## Package surface
Qualified recovery/renderer/checkpoint surfaces were then exported through package `__init__` modules and preserved at:

`292d460` — `forge-app: expose qualified recovery and renderer surfaces`.

## Full stack regression
After package-surface wiring, all existing recovery/Ergo/renderer/checkpoint/persistent-host tests plus the new read-only checkpoint-currentness tests were run with `ResourceWarning` promoted to error.

Result: **48/48 PASS** in 3.045 seconds.

## Current laws
- `LATEST_CHECKPOINT != BEST_RECOVERY_POINT`.
- `PERSISTENCE_VALID != RUNTIME_STABLE`.
- `CHECKPOINT_VALID != CURRENT_SOURCE_COMPATIBLE`.
- `CRASH_ASSOCIATION_CAUSES_QUARANTINE_NOT_DELETION`.
- `RECOVERY_OBSERVER != RECOVERY_AUTHORITY`.
- `PRESENTATION_STATE != TRUTH_AUTHORITY`.
- `STALE_SESSION_LEASE != CURRENT_RESUME_HEALTH`.
- `STALE_RENDERER_GENERATION_ACK != CURRENT_FRAME_ACK`.

## Cross-strand boundary
Source-currentness matching is currently App-side exact Git revision compatibility. Semantic migration/currentness beyond exact source identity remains a Core/Main interface concern.

Until that Core bridge is qualified, App must fail conservative: a savestate tied to a different source revision is SAFE_ONLY rather than silently presumed compatible.

## Next cut
After this report is committed/pushed, create checkpoint generation 2 against the exact final clean source HEAD. Resume that checkpoint through a real monitored development session with the persistent renderer host, actual wall-clock health, and explicit meaningful operations. Promote to STABLE/LKG only if the v0.1 lease is genuinely earned and source identity remains exact.
