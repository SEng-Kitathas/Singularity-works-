# Design Thread Stream
_Version: 2026-04-03a_

## Purpose
This file SHALL preserve the raw chronological shadow stream of the design thread.
Its function is forensic recovery when compaction, drift, or thread instability damages active context.

## Operating rule
After each meaningful exchange or turn pair:
1. Append the new user turn.
2. Append the new assistant turn.
3. Preserve chronology and speaker attribution.
4. Compress only when necessary, never so far that reconstruction becomes unreliable.

## Recommended entry format
```md
## Turn 001 — USER
Timestamp:
Tags:

...

---

## Turn 002 — ASSISTANT
Timestamp:
Tags:

...
```

## Compression rule
Preserve sequence, speaker, state changes, design logic, and operational consequences.
Do not compress away reversals, rule changes, architecture shifts, failures, or recovery logic.

---
## Provenance tail
- Artifact ID: `10B SHALL_INIT_DESIGN_THREAD_STREAM_NEXT.md`
- Artifact class: `design_thread_stream`
- Authority scope: `raw chronological design-thread continuity and recovery`
- Default read-next file: `10C SHALL_MAINTAIN_SHADOW_PAIR_EACH_TURN_NEXT.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `append-preferred; preserve chronology; batch append permitted if order is exact`
- This artifact SHALL NOT be treated as authoritative in isolation.
