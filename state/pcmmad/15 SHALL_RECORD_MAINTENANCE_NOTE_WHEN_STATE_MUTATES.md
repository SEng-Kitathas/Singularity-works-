# Maintenance Note — Singularity Works Forge
_Version: 2026-04-03 · v1.19_

## Session: 2026-04-03 — Full recovery + v1.19 push

### What changed
1. **seed_genome.json schema fixed** — two capsules (crypto.no_jwt_algo_confusion, network.no_http_cleartext) had detection_strategy at top level. Correct schema places it inside anti_patterns[0].dict. Now 37/37 load without TypeError.
2. **forge_sandbox/ replaced** — sacrificial Claude had pushed 846-line wrong architecture. Replaced with real singularity_works/ (12,214 lines, 28 modules). This is a breaking structural change to the repo.
3. **methodology/ updated** — PCMMAD_LATEST_2026-04-03 installed (adds 10A/10B/10C shadow pair, 06A failure recovery, forge execution SOP patch, parallel lab protocols).
4. **v1.19 committed and tagged** — all v1.19 changes from previous session now in GitHub.
5. **PCMMAD state surfaces instantiated** — all 7 state documents written with forge-specific content.
6. **AI-Research repo CURRENT_STATE added** — TQ2 experimental state documented from recovered session data.

### Self-audit count change
- Previous recorded: 864 pass / 4 warn (v1.18 ChatGPT package)
- Current: **920 pass / 4 warn / 0 fail** (v1.19 our build)
- Delta of +56 passes: new capsules loading (2 previously broken), plus v1.19 additions

### Known debt inherited
- forge_context.py sections/parts NameError: NOT fixed this session. P0 for next session.
- auth_rate_limit battery: monitor registered but 0 test cases. P0 for next session.
- good_service_issue_only FP: known, not addressed.
- SSRF requirement-selection sensitivity: documented, not addressed.

### PAT note
PAT github_pat_11BZO36HQ... used this session. Must be revoked before next session opens.

### Deletion rule compliance
Deleted: forge_sandbox/ (wrong 846-line architecture). Archived forge_initial_repo in archive/ directory (different unfinished architecture from different session). Both tombstoned.

### Next session entry point
1. Clone repo fresh with new PAT
2. Read 10A LIVE_SHADOW
3. Fix forge_context.py sections/parts
4. Add 3 auth_rate_limit battery cases
5. Run 49/49 battery
6. Commit v1.20
