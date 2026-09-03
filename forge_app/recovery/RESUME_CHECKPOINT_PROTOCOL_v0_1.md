# Forge Resume Checkpoint / Savestate Protocol v0.1

Status: Attempt-0 design contract. App-owned recovery/embodiment mechanism; it may reference Core identity/currentness but may not invent Core semantics.

## Intent
Give Forge emulator-like instant resume without creating an infinite crash loop or treating the newest checkpoint as automatically trustworthy.

## Governing laws
- `LATEST_CHECKPOINT != BEST_RECOVERY_POINT`.
- `PERSISTENCE_VALID != RUNTIME_STABLE`.
- `CRASH_ASSOCIATION_CAUSES_QUARANTINE_NOT_DELETION`.
- `CHECKPOINT_BYTES != PROCESS_IMAGE`.
- `CHECKPOINT_REPUTATION_IS_EVENT_DERIVED`.
- `APP_RESUME_STATE_REFERENCES_CORE_TRUTH; IT_DOES_NOT REIMPLEMENT IT`.

## Storage model
Checkpoint payload bytes are immutable Attempt Store artifacts (`artifact_class = recovery.resume_checkpoint`).

Checkpoint lifecycle is append-only event history in the same Attempt Store database. No mutable “slot 0/current.sav” row exists.

Lifecycle events:
- `checkpoint_verified` — exact payload readback + structural validation succeeded;
- `checkpoint_resumed` — a runtime/session resumed from this checkpoint;
- `checkpoint_stable` — resumed runtime earned the configured health lease;
- `checkpoint_lkg_promoted` — stable checkpoint selected as Last Known Good;
- `checkpoint_crash_associated` — runtime failed soon after resuming this checkpoint;
- `checkpoint_quarantined` — checkpoint is preserved but excluded from normal automatic resume.

The existing immutable `attempt_captured` event remains the initial persistence receipt.

## State progression
Nominal:
`CAPTURED -> VERIFIED -> RESUMED -> STABLE -> LKG`

Failure:
`VERIFIED/RESUMED -> CRASH_ASSOCIATED -> QUARANTINED`

A checkpoint may remain VERIFIED forever without becoming STABLE. A cryptographically intact checkpoint is not promoted merely because it exists.

## Stability lease
v0.1 default discriminator:
- checkpoint must have been resumed;
- healthy runtime duration >= 10 seconds;
- meaningful operation count >= 3;
- no early crash association after the latest resume.

Only then may `checkpoint_stable` be appended. LKG promotion requires STABLE and non-quarantined state.

These thresholds are App policy, not Core semantics, and remain revisitable.

## Early-crash / quarantine rule
A crash occurring <= 15 seconds after resume is an early crash association in v0.1.

- first early crash: preserve crash evidence and demote the checkpoint from automatic preference;
- second distinct early crash: append `checkpoint_quarantined`;
- quarantine never deletes checkpoint bytes or crash evidence.

Distinct crashes require distinct crash IDs so retrying the same crash receipt is idempotent rather than incrementing the count.

## Recovery selection
Automatic selection is evidence-ranked rather than newest-file-wins.

Preference order:
1. latest non-quarantined STABLE checkpoint;
2. latest non-quarantined VERIFIED checkpoint with no early-crash association;
3. latest non-quarantined VERIFIED checkpoint with one early-crash association, SAFE/inspection only;
4. no automatic candidate -> Ergo recovery selection required.

A prior LKG remains discoverable even after newer checkpoints exist. LKG promotion is append-only; previous LKG history is retained.

## What checkpoint payloads contain
Meaningful reconstructible operator/session state only, such as:
- Forge project/workspace identity;
- source branch/head identity;
- Core interface/currentness identity references;
- semantic snapshot ID reference when available;
- selected/open referents;
- history cursor;
- UI layout ID and semantic-canvas camera/zoom;
- SmartCanvas/command cursor state;
- active immutable Attempt IDs;
- pending transaction IDs;
- counterfactual branch ID;
- session/generation lineage.

## What checkpoint payloads do NOT contain
Rebuildable/transient process machinery:
- GPU/device/window handles;
- renderer caches/glyph atlases;
- mutexes/threads/stacks;
- sockets/PTY handles;
- parser-native trees/nodes;
- semantic indexes/projections that can be rebuilt;
- renderer process identity as authoritative state.

## Core/Main boundary
Main/Core owns canonical semantics/currentness/contracts. App checkpoints may carry exact Core contract/snapshot/currentness identifiers as references.

If App needs to encode private semantic meaning to resume, that is a cross-strand interface defect and must be escalated upstream rather than silently duplicated.

## Crash-safe checkpoint capture
1. construct canonical checkpoint payload;
2. capture bytes in Attempt Store as immutable artifact;
3. verify exact readback/hash/structure;
4. append `checkpoint_verified` event;
5. only VERIFIED checkpoints enter automatic recovery selection.

A crash between steps 2 and 4 leaves a preserved CAPTURED artifact that is not automatically resumed.

## Renderer/session integration
The persistent host will later attach runtime health/heartbeat evidence to the checkpoint it resumed from. Renderer death alone does not automatically quarantine a checkpoint unless the coordinator/session itself becomes unhealthy; renderer failure is already a bounded replaceable domain.

## Not claimed in v0.1
- full editor/source transaction replay;
- power-loss durability beyond Attempt Store's current bounded evidence;
- persistent renderer heartbeat integration;
- automated safe launch execution;
- final LKG lease thresholds;
- semantic snapshot restoration implementation;
- cross-machine resume portability.
