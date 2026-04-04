# Singularity Works — The Forge

Autonomous software security analysis engine built using the PCMMAD (Parallel Concurrent Multi-Model Adversarial Discourse) methodology.

## Current Version: v1.18 (Law Ω Compliant)

**Score: 46/46** — All protocol monitors passing.

### Recent Capabilities (v1.18)
- Cross-function SSRF taint propagation
- JWT algorithm confusion detection  
- HTTP non-TLS monitors
- AST-based protocol analysis across Python, PHP, JavaScript, TypeScript, Ruby, Java, C#

## Structure

```
├── forge_sandbox/       # Core analysis engine
│   ├── genome_gates.py  # Genome-based vulnerability pattern matching
│   ├── intake.py        # File intake and AST parsing
│   ├── remediation.py   # Automated fix generation
│   ├── probe_loop.py    # Continuous analysis loop
│   └── switchboard.py   # Protocol routing
├── corpus/
│   ├── public/          # Known vulnerable samples (DVWA, Juice Shop, etc.)
│   └── representative/  # Synthetic/adversarial test cases
├── methodology/         # PCMMAD bootstrap protocols
├── results/             # Analysis reports
└── tests/               # Regression expectations
```

## Running

```bash
python run_current_codebase.py
```

## Law Ω Compliance

All code artifacts target theoretical maximum quality. No stubs, no TODOs, no MVP shortcuts.

---
*Part of the KarnOS/SYNAPSE/Yggdrasil ecosystem*
