# Trace Matrix
_Version: 2026-03-31i_

## Purpose
This file is the load-bearing trace surface for claims, artifacts, and decisions.

It has two simultaneous jobs:
1. give the operator a compact map from claim to evidence to embodiment to verification
2. stop the model from promoting conclusions whose lineage cannot be traced

## Operator / lab meaning
Use this file for anything that has become important enough to matter structurally:
- a claim
- a design choice
- a method decision
- an implementation artifact
- a promoted doctrine element
- a benchmark or experiment result

If it is carrying weight, it should be traceable.

## Model / control obligations
When something becomes load-bearing, the model SHOULD add it here with:
- upstream evidence
- the embodiment or derived artifact
- the verification path
- current status
- confidence or decision posture
- demotion trigger if known

The model SHALL NOT treat fluent lineage stories as substitutes for actual traceability.

## Template

| Artifact / Claim | Upstream evidence | Derivation / interpretation step | Embodiment | Verification | Status | Confidence / posture | Demotion trigger | Notes |
|---|---|---|---|---|---|---|---|---|
| <fill in> | <fill in> | <fill in> | <fill in> | <fill in> | <provisional / promoted / load-bearing / demoted> | <fill in> | <fill in> | <fill in> |

## Inclusion rule
Anything treated as load-bearing SHOULD appear here.
If it does not appear here, it is probably relying on memory, momentum, or hand-waving.

## Completion rule
This file is complete for the pass when the project's important claims and artifacts can be traced instead of merely remembered.

---
## Provenance tail
- Artifact ID: `10 SHALL_INIT_TRACE_MATRIX_NEXT.md`
- Artifact class: `live_state_trace`
- Authority scope: `claim-to-artifact traceability`
- Default read-next file: `10A SHALL_INIT_LIVE_SHADOW_NEXT.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `direct update permitted during active pass; record maintenance when semantics materially change`
- This artifact SHALL NOT be treated as authoritative in isolation.
