# Doctrine Snapshot

## Governing Law
**PROBE → DERIVE → EMBODY → VERIFY → RECURSE**

## Forge Pipeline
```
intake.py (classify)
    ↓
probe_loop.py (orchestrate)
    ↓
genome_gates.py (evaluate patterns)
    ↓
remediation.py (generate patches)
    ↓
assurance.py (final status)
```

## Detection Categories

### Known Language Vulnerabilities
- Command Execution (shell_exec, exec, system)
- Dynamic Eval (eval without safeMathEval)
- SQL Injection (string interpolation without parameterization)
- XSS Reflected/Stored (unencoded output)
- CSRF State Change (missing token validation)
- Open Redirect (unvalidated redirect target)
- SSRF (attacker-controlled outbound requests)
- SSTI (template injection)
- Unsafe Deserialization (pickle.loads on user input)
- Predictable Token Generation (MD5-based tokens)
- Fake Safety Wrappers (function allowlist($x) { return $x; })

### Unknown Language Handling
- Novel structured unknown detection (alien blobs)
- Semantic risk markers in unknown languages
- Suspicious unknown representation patterns
- Low-loudness role cues (wave 4)

## Promotion Rules
- Promoted buckets must stay clean (green)
- Pressure buckets may stay amber without blocking
- Unknown but coherent code-like systems → skeptical quarantine, NOT false green

## No-Drift Rules
- No summary-first handling
- No single-source sufficiency
- No silent overwrite
- No promotion without doctrine effect
- No architecture decision outrunning preserved raw evidence

## Codex Omega Laws Active
- Law 0: Discourse ≠ implementation
- Law 1: 0-Day not Someday (no stubs/TODOs in BUILD mode)
- Law 4: Pedantic execution, aerospace-grade verification
- Law Ω: Every artifact at theoretical maximum
- Law Σ: Voice speculative ideas, challenge assumptions
