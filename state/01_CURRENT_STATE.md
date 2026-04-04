# Singularity Works — Current State
_Version: v1.19 · 2026-04-03_

## Architecture
- `singularity_works/` — Production Python forge (28 modules, 12,214 lines)
- `configs/seed_genome.json` — 37 capsules, all loading clean
- `examples/` — verify_build, demo runs
- `methodology/` — PCMMAD_LATEST_2026-04-03 (full dual-surface archive)

## Verification state (v1.19)
- compile: True
- good: green | bad: red | bad_rem: green
- security: red | security_rem: green  
- execution: red | execution_rem: green
- self_audit: 920 pass / 4 warn / 0 fail
- **Combined battery: 46/46 FP=0 FN=0**

## v1.19 additions over v1.18
- seed_genome.json schema fixed (two new capsules now load)
- JWT algorithm confusion detection strategy (local_jwt_algorithm_confusion)
- HTTP non-TLS detection strategy (local_http_no_tls)
- Cross-function SSRF taint propagation (fixed-point, 2-hop chains, httpx async, urllib)
- Auth rate limiting monitor (must_rate_limit_auth_endpoint)
- Callback state silent-abstention fix (OAuth absent-state now catches)
- Goroutine docstring self-scan guard

## Active monitor set (9 protocol monitors)
must_establish_session_before_redirect | must_harden_auth_cookies
must_clear_auth_state_on_logout | must_finalize_transaction_after_write  
must_rotate_or_revoke_refresh_token | must_preserve_refresh_token_family_integrity
must_validate_state_token_before_callback_use | must_validate_and_consume_recovery_token
must_rate_limit_auth_endpoint

## Known limits
- SSRF requirement-selection sensitivity on some generic phrasings
- 4 warn files: forge_context.py, genome_gate_factory.py, monitoring.py, recovery.py (architectural, no high/critical)
