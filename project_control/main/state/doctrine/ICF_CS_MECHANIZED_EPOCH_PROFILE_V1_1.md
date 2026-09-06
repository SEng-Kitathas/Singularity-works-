# ICF-CS v1.1 — Mechanized Epoch / Compare-and-Swap Profile

Status: OPTIONAL MECHANIZED PROFILE; PREFERRED WHEN DURABLE LOCAL STATE AND DETERMINISTIC TOOLING ARE AVAILABLE

## Purpose
ICF-CS is structurally similar to a cache-coherence problem: Intent, Constraints, Frontier, and History have different update rates, stale copies are dangerous, and mutation after a stale read must be rejected. The profile below converts that currentness discipline into an executable validity-token mechanism.

This is an isomorphism used for engineering leverage, not a claim that project continuity literally implements a hardware coherence protocol.

## Class validity token
Each class has a token:
- `epoch` — monotonically increasing integer local to that class;
- `sha256` — digest of the canonical serialized class content or source bytes;
- `source_id` — stable logical identity used for provenance;
- `source_path` — authoritative local file whose current bytes are re-hashed before readback/CAS.

`CLASS_EPOCH != GLOBAL_TIME`
`EPOCH_EQUAL != CONTENT_EQUAL`
`TOKEN_MATCH != FACTUAL_TRUTH`
`EPOCH_MATCH != AUTHORITY_MATCH`

Epoch and hash are checked together. The epoch detects known mutation; the hash prevents an unchanged/stale epoch from hiding changed bytes. Neither field establishes semantic truth or authority.

## Read token
A reader obtains the four class tokens before consequential work. This is the read-side snapshot.

## Compare before mutation
Before writing a class, compare the expected token from the read-side snapshot with the current persisted token.

If epoch or hash differs:
`STALE_TOKEN -> CONFLICT -> RECOVERY/AUDIT`

Do not mutate.

If both match, the reference compare-and-swap operation serializes writers with a cross-process local file lock and performs this guarded sequence while the lock is held:
1. re-hashes the authoritative source file and rejects untracked out-of-band drift;
2. verifies expected epoch/hash/source identity;
3. writes proposed bytes to the authoritative source path while the lock is held;
4. increments that class epoch;
5. stores the new content hash;
6. returns the new token.

`READBACK_REQUESTED != READBACK_CURRENT`
`CAS_CHECK != AUTHORITY_CHECK`
`CAS_SUCCESS != SEMANTIC_VALIDITY`

The CAS guard answers "did the state I read change before my mutation?" It does not answer "is the proposed mutation authorized, correct, or true?"

## Multi-class dependency rule
If a mutation depends on multiple classes, verify every dependency token before applying the mutation. A change in any dependency invalidates the stale plan and routes to conflict recovery.

## Durable state requirement
The epoch store SHALL live on the same authoritative local/server plane as the consequence-bearing continuity state or be reconciled atomically enough that a false green token cannot be produced by split-brain storage.

`EPOCH_STORE != PARALLEL_UNRECONCILED_TRUTH`
`LOCAL_FILE_LOCK != DISTRIBUTED_CONSENSUS`
`LOCK_HELD_SEQUENCE != CRASH_ATOMIC_TRANSACTION`

## Reference implementation
`tools/icf_epoch_guard.py` implements deterministic local JSON state with:
- initialization from class files;
- token snapshot;
- token verification;
- single-class compare-and-swap update;
- dependency-set verification;
- stale-token rejection with no mutation;
- out-of-band authoritative-source drift rejection;
- serialized concurrent writers so one stale competing CAS cannot also succeed.

The reference implementation is a mechanism example, not a universal storage mandate. Its source-file write and epoch-state write are separate atomic replacements inside one lock-held sequence; a crash between them can leave source/state disagreement, which subsequent validation detects and rejects rather than silently treating as current.

## Evidence ceiling
This profile is mechanically self-tested inside the overlay qualification. That is evidence that the reference guard rejects its defined stale-token cases. It is **not yet evidence of cross-project efficacy**. Project-level adoption must separately show that the mechanism catches consequence-bearing stale-state defects in real work.

`SELF_TEST_PASS != CROSS_PROJECT_EFFICACY`
`DOCTRINE_PRESENT != DOCTRINE_EMBODIED`
