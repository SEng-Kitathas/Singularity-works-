# ADR — Forge Attempt Store / Operational Journal / Zombie Boundary v0.1

Status: Attempt 0 architecture proposal. Preserve before execution; hostile testing may narrow or replace it.

## Decision target
Forge needs a first persistence substrate that preserves significant AI/code/design/research artifacts before retries or downstream execution can overwrite them, while remaining recoverable after process death.

## Governing law
**ATTEMPT_0_IS_EVIDENCE_NOT_SCRATCH_SPACE.**

A significant generated artifact is not considered captured until the persistence transaction returns a receipt and immediate readback verifies the exact payload hash.

## v0.1 decision
Use **SQLite as the authoritative content-addressed Attempt Store and append-only Operational Journal** for the first embodiment.

The v0.1 database owns:
- content-addressed artifact bytes keyed by SHA-256;
- immutable attempt records referencing artifact hashes;
- parent-attempt lineage;
- immutable metadata/intent/producer/classification;
- append-only lifecycle events;
- store format/version metadata.

The same SQLite transaction inserts/deduplicates the blob, inserts the attempt, and appends the capture event. This deliberately avoids the two-file crash window that exists when a payload file becomes durable separately from its metadata index.

### Why not inherit Ergo direct JSON persistence
The recovered Ergo-Light checkpoint/session model is useful, but its current `write_json_boundary()` is a direct `Path.write_text(...)`. It does not embody a crash-safe transaction boundary. Ergo's recovery UX/state machine is a donor; its file-write helper is not the zombie substrate.

### Why SQLite first
- transactional atomicity/recovery is substantially stronger than ad-hoc JSON mutation;
- one transaction can bind payload bytes + metadata + lifecycle event;
- content-addressed blobs deduplicate naturally under a hash primary key;
- WAL permits read-heavy operator surfaces while one writer records lifecycle state;
- Python ships with SQLite, avoiding a new dependency for the discriminator;
- the authoritative v0.1 state is one database recovery unit plus its WAL/SHM while open.

## Durability policy
Initial qualification mode:
- `PRAGMA journal_mode=WAL`;
- `PRAGMA synchronous=FULL`;
- `PRAGMA foreign_keys=ON`;
- explicit transactions for capture;
- immediate post-commit readback and SHA verification;
- `PRAGMA integrity_check` available to Ergo/recovery diagnostics.

This does **not** claim immunity to broken storage hardware/filesystems. SQLite's own documentation separates atomic/consistent recovery from absolute physical-media durability. Forge must qualify the exact Windows/storage environment through kill/corruption tests rather than infer aerospace grade from `FULL`.

## Immutability
The database installs triggers that reject `UPDATE`/`DELETE` on:
- blobs;
- attempts;
- events.

Corrections are new attempts/events. They never rewrite Attempt 0.

## Attempt identity vs content identity
- `blob_sha256` = exact artifact content identity.
- `attempt_id` = immutable occurrence/lineage identity.

Two attempts may intentionally reference the same blob while preserving distinct intent/producer/parent lineage.

## Retry / repair lineage
A repair/regeneration supplies `parent_attempt_id` referencing the preserved earlier attempt. Nothing promotes because it is newer. Convergence compares preserved attempts and explicitly chooses promotion elsewhere.

## Event model
Initial events are intentionally small:
- `attempt_captured`;
- later versions may add `validation_started`, `validation_finished`, `mutation_planned`, `mutation_applied`, `promotion`, `demotion`, `recovery_started`, `recovery_completed`, etc.

Events are append-only receipts, not mutable status rows.

## Failure model / Zombie discriminator
The first hostile campaign must use separate processes and hard termination rather than friendly exceptions.

Required cuts:
1. kill after SQL rows are written but **before COMMIT** -> reopen must contain neither the attempt nor its capture event; integrity check must pass;
2. kill **after COMMIT returns** but before graceful close -> reopen must contain exact attempt/event/blob; integrity check and SHA readback must pass;
3. capture identical bytes twice -> one blob, two attempt records/events;
4. capture child retry -> parent lineage exact;
5. any attempted UPDATE/DELETE -> rejected by database trigger;
6. corrupted/readback-mismatched payload -> never reported as verified capture.

## Recovery / Ergo integration boundary
Ergo should initially consume a read-only recovery summary:
- database present/openable;
- integrity check result;
- journal mode/synchronous policy;
- attempt/blob/event counts;
- last durable event;
- latest attempts and lineage;
- pending mutation surfaces once those exist.

Ergo does not make persistence true by displaying it.

## External CAS / recovery bundles
A filesystem CAS mirror is **deferred** from v0.1 because a separate payload-file + metadata-index write introduces an additional crash-consistency protocol. Once the SQLite capture path is qualified, a later version may export immutable hash-named blobs and periodic recovery bundles as redundant surfaces.

Any mirror must be rebuildable from the authoritative store or explicitly promoted to co-authoritative only after a two-phase/transaction discriminator.

## Demotion triggers
Rework this ADR if:
- SQLite BLOB storage imposes unacceptable latency/size behavior under representative AI artifacts;
- hard-kill tests expose missing or phantom committed attempts;
- WAL/Windows locking conflicts with expected multi-process Forge use;
- a simpler store provides equal atomicity/lineage/recovery with lower operational complexity;
- recovery copies/bundles cannot safely capture database+WAL state.

## Not claimed
- formal aerospace certification;
- power-loss immunity on arbitrary storage hardware;
- multi-host/network filesystem support;
- distributed writer support;
- final long-term artifact retention policy;
- final encryption/privacy policy;
- source Git replacement.
