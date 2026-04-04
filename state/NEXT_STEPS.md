# Forge: Next Steps

## Current State
- v1.18 codebase: 46/46 tests passing
- Working vulnerability scanner for SSRF, SSTI, XSS, SQLi, CSRF, command injection, open redirect, unsafe deserialization, predictable tokens, fake wrapper theater, alien/unknown language patterns
- PCMMAD methodology integrated
- SOP state docs now in state/

## Immediate Actions

### 1. BLOCKING: seed_genome.json
The genome capsule schema file for two new capsules was not in this dump.
Source: Previous ChatGPT session, not in these zips.
Action: Locate or recreate from prior session transcripts.

### 2. Architecture Decision: forge_initial_repo vs v1.18
Two codebases exist:
- v1.18 (`forge_sandbox/`): Working scanner, ~1500 lines, all detection logic
- `forge_initial_repo` (`archive/`): Cleaner typed architecture, ~450 lines, NO detection logic

Decision needed: Refactor v1.18 into forge_initial_repo architecture, or continue v1.18?
Recommendation: Continue v1.18 for now — it works. Refactor can be v2.0 scope.

### 3. Logic Blueprint Engine Specs
Specs created in conversation but not yet embedded:
- Logic Blueprint Engine Spec v0.1
- Forge IR Spec v0.1
- Logic Blueprint Blob Schema Spec v0.1
- Logic Blueprint Path State Field Spec v0.1

Action: Locate these specs and add to spec/ directory.

### 4. CIL Integration
CIL architecture docs now in spec/CIL_ARCHITECTURE/
Next: Map which CIL seams need Forge integration (CIL-007 cilfsd, CIL-021 council, CIL-017 TAINT)

## Deferred

- Repository-scale exemplar mining
- Grammar inference / geometric parser recovery
- Flow-augmented structural representation
- Abstract interpretation gates

## Version History
| Version | Date | Score | Notes |
|---------|------|-------|-------|
| v1.9 | 2026-03 | ~30/46 | Initial public corpus |
| v1.14 | 2026-03 | ~40/46 | Synthetic assault |
| v1.15 | 2026-04 | ~42/46 | Alien wave 1 |
| v1.16 | 2026-04 | ~44/46 | Alien wave 2 |
| v1.17 | 2026-04 | ~45/46 | Alien wave 3 |
| v1.18 | 2026-04 | 46/46 | Alien wave 4 + low-loudness |
