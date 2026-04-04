# LAB COMPARISON PROTOCOL — PCMMAD

## PURPOSE
Provide a standard method for comparing outputs from parallel Labs without collapsing them into narrative preference.

## REQUIRED INPUTS
Each Lab comparison SHALL reference:
- authority base identifier
- session header
- target
- stop boundary
- output artifact type
- current state label
- summary of what became more real
- summary of what remains thin

## COMPARISON AXES
All Labs SHALL be compared on:

1. EMBODIMENT
- Did the Lab produce a real artifact?
- What is the artifact state label?

2. TARGET ADHERENCE
- Did the Lab stay on the declared target?
- Did it violate stop boundaries?

3. AUTHORITY INTEGRITY
- Did it mutate outside its authority base?
- Did it preserve sealed vs mutable distinctions?

4. DRIFT / CONFLICT PROFILE
- What drift events occurred?
- Were they surfaced explicitly?

5. FAILURE DISCOVERY
- What did this Lab detect that others missed?
- What false closure did it prevent?

6. OPERATOR VALUE
- What artifact or finding is worth promoting?

## OUTPUT FORMAT
Use:

[LAB COMPARISON]
- Lab ID:
- Target:
- Artifact type:
- State label:
- Strongest contribution:
- Weakest point:
- Drift events:
- Promotion candidate:
- Merge candidate:
- Kill candidate:

## DECISION OUTCOMES
A comparison SHALL terminate in one or more of:
- PROMOTE
- MERGE
- HOLD
- KILL

No vague “good ideas” bucket is allowed.

## RULE
Compare artifacts and authority surfaces first.
Narrative elegance is secondary.

---
## Provenance tail
- Artifact ID: `LAB_COMPARISON_PROTOCOL.md`
- Artifact class: `lab_comparison_protocol`
- Authority scope: `parallel-lab comparison and convergence discipline`
- Default read-next file: `ARTIFACT_PROMOTION_AND_SCORING.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `visible replacement + version bump + provenance regeneration`
- This artifact SHALL NOT be treated as authoritative in isolation.
