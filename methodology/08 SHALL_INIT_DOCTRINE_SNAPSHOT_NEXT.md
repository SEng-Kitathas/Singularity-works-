# Doctrine Snapshot
_Version: 2026-03-31i_

## Purpose
This file records the currently active doctrine for the workstream.

It has two simultaneous jobs:
1. show the operator which laws, constraints, and methodological deltas are actually active right now
2. stop the model from silently importing abandoned assumptions or stale rules from earlier phases

## Operator / lab meaning
Use this file to preserve the active logic of the lab:
- mode-control state
- quality pressure posture
- search posture
- local doctrine deltas
- current incumbent method
- what is under challenge versus what is load-bearing

This is not the place for every historical idea the project ever touched.
It is a live doctrinal slice.

## Model / control obligations
When this file is updated, the model SHALL:
- identify the active mode-control state
- state which laws are carrying the most weight right now
- name the current incumbent architecture or method
- record what is actively being challenged
- record Sigma-style divergence branches that are still alive
- SHALL NOT confuse historical noise with current doctrine

## Template

### Active mode-control state
- <DISCUSSION / BUILD>
- Why: <trigger or arbitration reason>

### Current governing laws
- <LAW 0 / 1 / 2 / 3 notes>
- <LAW 4 / 5 / Ω posture>
- <LAW Σ posture>

### Current quality / search posture
- Verification pressure: <fill in>
- Cross-disciplinary pressure: <fill in>
- Maximum-attainable pressure: <fill in>
- Divergence / wrong-path pressure: <fill in>

### Current incumbent architecture / method
- <fill in>

### Active constraints
- <technical, procedural, evidence, or operator constraints>

### What is load-bearing right now
- <the assumptions, files, results, or methods currently treated as authoritative enough to build on>

### What is under challenge
- <the assumptions or methods actively being tested, red-teamed, or demotion-pressured>

### Active Sigma branches
- <wrong-path probes, counterexamples, alternates, isomorphisms, adversarial frames still in play>

### What was recently promoted
- <fill in>

### What was recently demoted
- <fill in>

### Doctrine drift watchlist
- <likely failure modes: mode bleed, summary substitution, stale baseline reuse, etc.>

## Update trigger
Update this file whenever doctrine materially changes through:
- promotion
- demotion
- role handoff
- evidence pressure
- architecture shift
- mode transition

## Completion rule
This file is complete for the pass when a future reader can tell what rules are alive now without reading an archaeological dig through old prose.

---
## Provenance tail
- Artifact ID: `08 SHALL_INIT_DOCTRINE_SNAPSHOT_NEXT.md`
- Artifact class: `live_state_doctrine`
- Authority scope: `currently active doctrine and rule surface`
- Default read-next file: `09 SHALL_INIT_REVISIT_LEDGER_NEXT.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `direct update permitted during active pass; record maintenance when semantics materially change`
- This artifact SHALL NOT be treated as authoritative in isolation.
