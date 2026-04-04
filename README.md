# Singularity Works — Forge v1.18

Autonomous bug bounty engine with AST-based protocol monitors and multi-round remediation.

## Status: 46/46 Tests Passing ✓

## What This Does

Forge is a vulnerability scanner that:
1. **Ingests** source code (Python, PHP, JavaScript, TypeScript, Java, C#, Ruby)
2. **Detects** 15+ vulnerability classes with zero false positives on known-good code
3. **Generates** automated patches with semantic awareness
4. **Handles** unknown/alien languages with skeptical quarantine (no false green passes)

## Vulnerability Classes Detected

| Class | Description |
|-------|-------------|
| SSRF | Server-side request forgery via attacker-controlled URLs |
| SSTI | Template injection via user-controlled template strings |
| XSS Reflected | Cross-site scripting via unencoded reflected input |
| XSS Stored | Cross-site scripting via unencoded stored input |
| SQLi | SQL injection via string interpolation |
| CSRF | Cross-site request forgery on state-changing operations |
| Command Injection | Shell command execution with user input |
| Open Redirect | Unvalidated redirect targets |
| Unsafe Deserialization | Pickle/Marshal on user-controlled data |
| Predictable Tokens | Weak token generation (MD5-based) |
| Fake Wrappers | Deceptive "safe" functions that don't sanitize |
| NoSQL Injection | MongoDB $where injection |
| Broken Auth | Plaintext password storage/comparison |
| Unknown Language | Alien/novel structured blobs with semantic risk |

## Quick Start

```bash
python run_current_codebase.py
```

## Project Structure

```
forge_sandbox/       # v1.18 working scanner
  intake.py          # Language detection + pattern classification
  probe_loop.py      # Multi-round orchestration
  genome_gates.py    # 30+ pattern detectors
  remediation.py     # Automated patch generation
  assurance.py       # Final status evaluation
  switchboard.py     # Routing logic
  facts.py           # Evidence bus

corpus/              # Test cases
  public/            # DVWA, Juice Shop, NodeGoat samples
  representative/    # Adversarial + synthetic pressure cases

methodology/         # PCMMAD bootstrap (00-93)

state/               # PCMMAD state documents
  NEXT_STEPS.md
  DOCTRINE_SNAPSHOT.md
  CURRENT_STATE.md
  TRACE_MATRIX.md

spec/                # Architecture specs
  CIL_ARCHITECTURE/  # CIL layer reference

archive/             # Historical artifacts
  forge_initial_repo/  # Typed architecture skeleton (not implemented)

results/             # Test run outputs
tests/               # Expectation definitions
docs/                # Session notes + documentation
```

## Laws Active

- **Law Ω**: Every artifact at theoretical maximum
- **Law 1**: 0-Day not Someday (no stubs in BUILD mode)
- **Law 4**: Pedantic execution, aerospace-grade verification

## Version History

| Version | Score | Key Changes |
|---------|-------|-------------|
| v1.9 | ~30/46 | Initial public corpus |
| v1.14 | ~40/46 | Synthetic assault |
| v1.15 | ~42/46 | Alien wave 1 |
| v1.16 | ~44/46 | Alien wave 2 |
| v1.17 | ~45/46 | Alien wave 3 |
| v1.18 | 46/46 | Alien wave 4 + low-loudness |

## Blocking Issues

1. `seed_genome.json` — Schema for two new capsules, not in current dump
2. Logic Blueprint Engine specs — Created in conversation, need embedding

## Author

Rahl (SEng-Kitathas)
rahl@singularity.works
