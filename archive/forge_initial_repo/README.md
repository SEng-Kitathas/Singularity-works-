# Singularity Works

Initial Forge scaffold for a governed software production and audit platform.

## Current shape

This initial cut focuses on the runtime spine that survived reconciliation:

- intake through `language_front_door`
- evidence capture through `evidence_ledger`
- normalized structural fingerprints through `pattern_ir`
- execution context through `forge_context`
- orchestration through `orchestration`
- judgment/promotion stub through `cil_council`
- CLI entry through `runtime`

## Run

```bash
python -m singularity_works.runtime demo
```

## Test

```bash
pytest
```
