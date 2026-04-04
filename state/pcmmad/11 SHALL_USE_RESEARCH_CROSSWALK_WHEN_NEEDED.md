# Research Crosswalk
_Version: 2026-03-31i_

## Purpose
Use this instrument when an outside framework, paper, discipline, or method appears relevant but has not yet been translated into local project language.

## Operator / lab meaning
This file exists to prevent prestige import, cargo-cult adoption, and vague "this seems useful" thinking.
A crosswalk forces the operator to state what the foreign concept actually is, what it maps to locally, what it changes, and what must be tested before adoption.

## Model / control obligations
The model SHALL:
- translate outside concepts into local operational language before relying on them
- distinguish direct mapping from analogy, inspiration, and speculation
- state doctrine impact explicitly rather than implying it
- preserve mismatch and friction instead of smoothing it away
- flag when a source is being used as evidence versus merely as heuristic inspiration

The model SHALL NOT:
- import terminology as if it were already integrated
- treat conceptual resemblance as proof of equivalence
- flatten cross-domain differences for rhetorical neatness

## When to use
Use this file when any of the following is true:
- a paper, framework, or outside method is being imported
- a term from another field seems promising but is not yet locally grounded
- a cross-domain isomorphism is suspected
- an external concept may affect doctrine, architecture, workflow, or evaluation

## Template
| Outside concept / source | Source class | Local translation | Mapping type | Claimed benefit | Friction / mismatch | Doctrine effect | Required validation | Action |
|---|---|---|---|---|---|---|---|---|
| <fill in> | <paper/spec/framework/field/etc> | <fill in> | <direct/partial/analogy/speculative> | <fill in> | <fill in> | <fill in> | <fill in> | <adopt/test/hold/reject> |

## Required notes
### Why this mapping is not naive
- <fill in>

### What would falsify the mapping
- <fill in>

### Isomorphisms worth tracking
- <fill in>

### Wrong-path risk
- <fill in>

## Known failure modes this file suppresses
- prestige laundering
- language import without embodiment
- analogy inflation
- untested doctrinal drift

## Update rule
If a mapped concept becomes load-bearing, it SHALL also appear in the doctrine snapshot, trace matrix, or promotion review as appropriate.

## Normative note
Outside concepts SHALL be translated into local operational terms before adoption. Untranslated imports are seeds at best, not doctrine.

---
## Provenance tail
- Artifact ID: `11 SHALL_USE_RESEARCH_CROSSWALK_WHEN_NEEDED.md`
- Artifact class: `research_crosswalk`
- Authority scope: `cross-domain research mapping`
- Default read-next file: `12 SHALL_USE_ZERO_LOSS_EXTRACTION_WHEN_CORPUS_EXISTS.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `append derived artifacts when possible; otherwise replace visibly and regenerate provenance`
- This artifact SHALL NOT be treated as authoritative in isolation.
