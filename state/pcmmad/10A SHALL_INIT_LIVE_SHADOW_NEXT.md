# LIVE SHADOW — Singularity Works Forge

## Thread Identity
- Thread: Singularity Works primary build session 2026-04-03
- Last Updated: 2026-04-03 (end of session)
- Mode: BUILD
- Dominant Objective: Forge at v1.19, both repos on GitHub, PCMMAD instantiated. Next session: P0 fixes then IDOR.

## Active User Intent
- Forge and TQ2 ternary weights are the active priorities
- OS (KarnOS/SYNAPSE) paused until ternary weights have a functional plan
- Both GitHub repos now live and correct
- PCMMAD instantiated with forge-specific state

## Current Authoritative State
- v1.19 committed + pushed @ SEng-Kitathas/Singularity-works-
- 28 modules, 12,214 lines, 37 capsules, 36 strategies, 12 monitor runners
- 46/46 FP=0 FN=0, self_audit=920/4/0
- AI-Research repo at SEng-Kitathas/AI-Research-and-development: 508 files + CURRENT_STATE_2026-04-03.md
- PAT used this session: revoke github_pat_11BZO36HQ... before next session

## Active Constraints
- No second-order expansion before P0 fixes (forge_context.py + auth_rate_limit battery)
- Battery must hold at 46/46 (or 49/49 after rate-limit cases) before v1.20 commit
- Deletion rule: kill or mark dead at least one element per session
- Behavioral reliability pass deferred — not before v1.20

## Decisions Locked In
- TQ2 canonical substrate, not GODSPEC/quaternion lines (ancestral material)
- Real forge is singularity_works/ (12,214 lines), not forge_sandbox (846 lines)
- Repo structure: singularity_works/, examples/, configs/, methodology/, state/, corpus/, spec/
- Cross-function SSRF taint: fixed-point, WITH tracking, FP suppression on allowlist — CANON
- 9 auth/session protocol monitors — CANON
- seed_genome capsule schema: detection_strategy inside anti_patterns[0] not top-level — CANON

## Open Loops
- forge_context.py sections/parts NameError bug — P0 fix needed
- auth_rate_limit: 3 battery cases needed before claiming monitor works
- IDOR ownership monitor: next march target
- PAT needs revocation
- Good_service_issue_only FP: known, low priority
- SSRF requirement-selection sensitivity: documented, not fixed

## Immediate Next Step
Session start: `git clone <repo>`, read this shadow, confirm v1.19 state, then fix forge_context.py sections/parts, add 3 auth_rate_limit cases, run 49/49, commit v1.20.

## Last 10 Turn Reinforcement Window
1. Received PCMMAD_LATEST_2026-04-03_fresh.zip — read, evaluated, installed into repos
2. Forge dump + geometric_inference.zip received — TQ2 corpus substantially intact (surprise)
3. GitHome_Action_Protocol.mht extracted — today's build session, not ternary weights
4. Sacrificial Claude thread read — pushed wrong 846-line arch to repo
5. PAT + repo URL provided — cloned both repos
6. seed_genome.json schema fixed — 37 capsules load, blocked v1.19 cleared
7. 46/46 battery run confirmed FP=0 FN=0 at 1.2s
8. v1.19 committed + pushed to Singularity-works- repo
9. singularity_works/ replaced forge_sandbox/ — real arch installed
10. AI-Research repo confirmed 508 files, CURRENT_STATE added, pushed

## Delta Since Previous Shadow
- Session started fresh (no prior shadow existed for this session)
- Both repos now correctly populated for first time
- v1.19 is the first clean tagged version in GitHub
- PCMMAD_REPAIRED instantiated with forge state (this document)
