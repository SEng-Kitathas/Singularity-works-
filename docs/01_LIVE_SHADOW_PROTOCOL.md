# 01 — LIVE SHADOW PROTOCOL

## Purpose
This document defines the **Live Shadow**: a minimum high-fidelity state record of the current conversation, maintained continuously as a bounded reinforcing sub-context window.

Its function is to preserve operational continuity across drift, summarization, compaction, and long-thread degradation by maintaining a compact but load-bearing reflection of the thread’s active state.

The Live Shadow is **not** a full transcript.
It is the smallest artifact that still preserves the current operational truth of the thread.

---

## Core Role
The Live Shadow SHALL serve as:
- the current state spine of the thread
- the bounded sub-context window for continuity reinforcement
- the handoff surface between turns
- the minimum viable high-fidelity state artifact
- the first recovery surface when thread continuity is threatened

---

## Required Behavior
Before EVERY reply:
1. Re-read the **last 10 conversational turns**.
2. Re-read the current Live Shadow document.
3. Reconcile both against the immediate user request.
4. Update the Live Shadow before or alongside the response if state has changed.

This forms a bounded reinforcing sub-context window.

The purpose is not perfect total recall.
The purpose is to preserve **active operational continuity** through deliberate repeated re-grounding.

---

## Scope of the Live Shadow
The Live Shadow SHALL capture only load-bearing state.
It SHALL NOT become a duplicate raw transcript.

It SHOULD include:
- current objective
- current phase or mode
- key constraints
- active decisions
- unresolved tensions or open questions
- current architecture direction
- immediate next steps
- risk notes
- any changes to method, doctrine, or operating rules that occurred in-thread

It SHOULD exclude:
- full dialogue duplication
- ornamental wording
- low-signal chatter
- already superseded detail unless still operationally relevant

---

## Structure
The Live Shadow SHALL contain the following sections in this order.

### 1. Thread Identity
- thread name or working label
- current date/time stamp of last update
- current operational mode
- current dominant objective

### 2. Active User Intent
A compact restatement of what the user is currently trying to accomplish.

### 3. Current Authoritative State
A concise summary of what is currently considered true in the thread.
Only active and load-bearing truths belong here.

### 4. Active Constraints
All constraints currently governing the work.
Examples:
- methodological constraints
- architecture constraints
- delivery constraints
- memory/continuity constraints
- implementation vs discourse state

### 5. Decisions Locked In
A running list of decisions that have been made and are currently treated as authoritative.

### 6. Open Loops
A running list of unresolved questions, tensions, risks, or pending validations.

### 7. Immediate Next Step
The next concrete move that follows from the current state.

### 8. Last 10 Turn Reinforcement Window
A structured recap of the last 10 turns.
Each item SHOULD be compact, but specific enough to restore local continuity.

Recommended per entry:
- turn index or relative order
- speaker
- essence of the turn
- whether it changed state

### 9. Delta Since Previous Shadow
A compact change log of what changed in the Live Shadow this turn.
This keeps the artifact legible and helps identify drift.

---

## Update Discipline
The Live Shadow SHALL be updated:
- whenever a decision changes the thread state
- whenever a key architecture direction changes
- whenever the user introduces new constraints or doctrinal rules
- whenever the immediate next step changes materially
- whenever recovery or checkpointing is needed

It MAY be left unchanged only if the turn produced no material state change.
If unchanged, note: **No load-bearing state change this turn.**

---

## Fidelity Standard
The Live Shadow is a **minimum high-fidelity** document.
That means:
- compact, but not vague
- selective, but not lossy on load-bearing state
- updated continuously
- resistant to thread compaction drift

If forced to choose, preserve:
1. current intent
2. current constraints
3. current decisions
4. immediate next step
5. last-10-turn continuity

---

## Relationship to Other Artifacts
The Live Shadow is distinct from the raw design thread stream.

- **Live Shadow** = compressed active state
- **Design Thread Stream** = raw chronological conversational record

The Live Shadow is for continuity.
The Design Thread Stream is for forensic recovery.

They are paired artifacts and SHOULD be maintained together.

---

## Recovery Use
If thread continuity is damaged, summarized poorly, compacted, or partially lost:
1. Read the current Live Shadow first.
2. Read the Last 10 Turn Reinforcement Window.
3. Read the Design Thread Stream for chronological recovery.
4. Reconstruct active state.
5. Resume from the last authoritative next step.

---

## Operating Rule
The Live Shadow exists to counter context erosion.
It is a deliberate, bounded, repeatedly reinforced continuity layer.

It SHALL remain small enough to reread frequently.
It SHALL remain rich enough to preserve the thread’s active truth.

---

## Template

```md
# LIVE SHADOW

## Thread Identity
- Thread:
- Last Updated:
- Mode:
- Dominant Objective:

## Active User Intent
- 

## Current Authoritative State
- 

## Active Constraints
- 

## Decisions Locked In
- 

## Open Loops
- 

## Immediate Next Step
- 

## Last 10 Turn Reinforcement Window
1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 

## Delta Since Previous Shadow
- 
```

---

## Final Principle
The Live Shadow is not memory theater.
It is a bounded continuity instrument.
Its value is not that it stores everything.
Its value is that it repeatedly preserves what currently matters most.
