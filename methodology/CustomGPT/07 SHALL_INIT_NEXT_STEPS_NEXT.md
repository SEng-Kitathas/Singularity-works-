# Next Steps
_Version: 2026-03-31k_

## Purpose
This file is the forward work queue for the active workstream.

It has two simultaneous jobs:
1. give the operator a clean execution horizon
2. stop the model from hiding uncertainty inside vague “we should probably” language

## Operator / lab meaning
Use this file to separate:
- what must happen now
- what can happen later
- what is blocked on evidence
- what is blocked on embodiment or verification
- what may need demotion, replay, or reversal

This file is not a wish list.
It is the shaped frontier of work.

## Model / control obligations
When updating this file, the model SHALL:
- turn vague intentions into discrete actions
- separate evidence waits from build waits
- note demotion / replay candidates explicitly instead of burying them
- keep items ordered by dependency or load-bearing impact
- SHALL NOT use this file to launder unfounded confidence

## Recommended entry format
Each action SHOULD name:
- the action
- why it matters
- the dependency or trigger
- what “done” looks like

## Template

### Immediate
| Priority | Action | Why it matters | Dependency / trigger | Done when |
|---|---|---|---|---|
| P0 | <fill in> | <fill in> | <fill in> | <fill in> |

### Near-term
| Priority | Action | Why it matters | Dependency / trigger | Done when |
|---|---|---|---|---|
| P1 | <fill in> | <fill in> | <fill in> | <fill in> |

### Waiting on evidence
| Evidence needed | Why blocked | Source or acquisition path | Earliest revisit trigger |
|---|---|---|---|
| <fill in> | <fill in> | <fill in> | <fill in> |

### Waiting on embodiment / verification
| Pending embodiment or check | Why blocked | Dependency | Done when |
|---|---|---|---|
| <fill in> | <fill in> | <fill in> | <fill in> |

### Demotion / replay candidates
| Candidate | Why it may need replay or demotion | What would decide it | Current status |
|---|---|---|---|
| <fill in> | <fill in> | <fill in> | <fill in> |

## Queue hygiene rule
If an item cannot be acted on, moved, or checked, it SHOULD migrate to the right blocked bucket instead of pretending to be active work.

## Completion rule
This file is complete for the pass when the next work interval can begin without inventing a plan from scratch.

---
## Provenance tail
- Artifact ID: `07 SHALL_INIT_NEXT_STEPS_NEXT.md`
- Artifact class: `live_state_next_steps`
- Authority scope: `next-action queue and work ordering`
- Default read-next file: `08 SHALL_INIT_DOCTRINE_SNAPSHOT_NEXT.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `direct update permitted during active pass; record maintenance when semantics materially change`
- This artifact SHALL NOT be treated as authoritative in isolation.
