# 02 — DESIGN THREAD STREAM PROTOCOL

## Purpose
This document defines the **Design Thread Stream**: the raw chronological shadow document of the conversation.

Its job is to preserve a direct running record of the design thread so that compaction, summarization, thread instability, or partial loss of live context do not destroy the recoverable structure of the conversation.

If the Live Shadow is the compressed active state,
then the Design Thread Stream is the raw temporal spine.

---

## Core Role
The Design Thread Stream SHALL serve as:
- the raw chat stream shadow document
- the chronological recovery surface
- the direct design-thread record
- the forensic continuity artifact
- the backing artifact for reconstructing state after loss, corruption, or drift

---

## Core Principle
This document SHOULD preserve the conversation in temporal order with minimal interpretation.

It is not meant to be pretty.
It is meant to be reliable.

The Design Thread Stream exists to preserve:
- what was said
- when it was said
- by whom
- in what sequence
- with what apparent effect on state

---

## Required Behavior
After EVERY turn pair or meaningful exchange:
1. Append the new user message.
2. Append the assistant reply.
3. Optionally append a brief metadata line if useful for later recovery.
4. Do not heavily summarize or compress the contents.
5. Preserve chronology.

If the exact full raw content is too large for practical maintenance, use the highest-fidelity practical paraphrase possible while preserving sequence, intent, and operational meaning.

The standard is:
**as raw as practical, as compressed as necessary, never so compressed that reconstruction becomes unreliable.**

---

## Scope
The Design Thread Stream SHOULD contain:
- each user turn in chronological order
- each assistant turn in chronological order
- timestamps when available
- section breaks for major phase changes
- optional markers for state-changing moments

It MAY contain:
- turn IDs
- tags like `STATE CHANGE`, `DECISION`, `RISK`, `REVISION`, `CHECKPOINT`
- pointers to generated artifacts

It SHOULD NOT over-interpret the thread.
Interpretation belongs primarily in the Live Shadow.

---

## Structure
The Design Thread Stream SHALL use a stable chronological format.

Recommended structure:

### Header
- thread name
- start date
- last updated
- purpose

### Chronological Entry Format
For each entry:
- turn number or relative order
- timestamp if available
- speaker (`USER` or `ASSISTANT`)
- content block
- optional tags

Example:

```md
## Turn 014 — USER
Timestamp: 2026-04-03 22:41 ET
Tags: STATE CHANGE, REQUEST

User requested creation of two new SOP documents:
1. a live shadow document with last-10-turn reread discipline
2. a direct raw design-thread shadow stream document

---

## Turn 015 — ASSISTANT
Timestamp: 2026-04-03 22:42 ET
Tags: ACKNOWLEDGED, EMBODIMENT

Assistant agreed and began drafting two documents designed to counter compaction and preserve continuity.
```

---

## Fidelity Standard
The Design Thread Stream is a **raw continuity artifact**.
Its fidelity priority order is:
1. chronology
2. speaker attribution
3. content preservation
4. state-change recoverability
5. compactness

This means the stream should prefer preserving order and content over elegance.

---

## Relationship to the Live Shadow
The Design Thread Stream and Live Shadow are paired but distinct.

### Design Thread Stream
- chronological
- raw or near-raw
- wide
- forensic
- recovery-oriented

### Live Shadow
- compressed
- state-oriented
- narrow and load-bearing
- continuity-oriented
- actively re-read each turn

The stream backs the shadow.
The shadow guides active work.

---

## Update Discipline
The Design Thread Stream SHALL be updated continuously.

At minimum:
- append each new user turn
- append each new assistant turn
- preserve order exactly

Where practical, update immediately after each exchange.

For long sessions, it MAY be updated in batches, but order MUST remain exact and no meaningful content SHOULD be silently omitted.

---

## Recovery Use
If the active conversation loses coherence:
1. Read the Live Shadow for current operational state.
2. Read backward through the Design Thread Stream to reconstruct chronology.
3. Identify the last stable state-changing exchange.
4. Rebuild active context from there.

This document exists specifically so that thread compaction cannot fully erase the design path.

---

## Design Thread Phase Markers
The stream SHOULD include explicit markers when the conversation enters a new phase, such as:
- bootstrap
- architecture
- verification
- implementation
- failure analysis
- merge
- checkpoint
- recovery
- doctrine revision

These markers improve navigability without sacrificing chronology.

---

## Compression Rule
If exact raw preservation becomes impractical, compress only under the following rule:
- preserve sequence
- preserve speaker
- preserve state changes
- preserve design logic
- preserve operational consequences

Do not compress away:
- key reversals
- rule changes
- architecture shifts
- failure discoveries
- implementation decisions
- recovery logic

---

## Template

```md
# DESIGN THREAD STREAM

## Header
- Thread:
- Start Date:
- Last Updated:
- Purpose:

---

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

---

## Final Principle
The Design Thread Stream is the anti-compaction raw spine.
It is not optimized for elegance.
It is optimized for reconstructability.

When continuity fails, this document is the trail back.
