from __future__ import annotations
# complexity_justified: interprocedural analysis crosses function boundaries; graph, builder, and local semantic analyzers are separated into dedicated modules.

from typing import Any

from .interprocedural_graph import (
    CallGraph,
    CallSite,
    FunctionNode,
    InitCycle,
    InvariantViolation,
    TaintPath,
)
from .interprocedural_locals import (
    find_incomplete_sanitization,
    find_redos,
    find_timing_attacks,
    find_weak_hash_usage,
)


def analyze(content: str) -> dict[str, Any]:
    """Run the full interprocedural analysis suite on Python content."""
    from .interprocedural_locals import _try_parse

    tree = _try_parse(content)
    results: dict[str, Any] = {
        "taint_paths": [],
        "invariant_violations": [],
        "init_cycles": [],
        "timing_attacks": [],
        "incomplete_sanitization": [],
        "redos": [],
        "weak_hash": [],
    }
    if tree is None:
        return results

    cg = CallGraph()
    cg.build(tree)
    results["taint_paths"] = [
        {"description": p.description(), "confidence": p.confidence,
         "sink_type": p.sink_type, "sink_line": p.sink_line,
         "chain": p.call_chain}
        for p in cg.propagate_taint()
    ]
    results["invariant_violations"] = [
        {"description": v.description, "enforcing": v.enforcing_func,
         "bypass": v.bypass_func, "attr": v.target_attr, "line": v.bypass_line}
        for v in cg.find_invariant_bypasses()
    ]
    results["init_cycles"] = [
        {"description": c.description, "cycle": c.cycle}
        for c in cg.find_init_cycles()
    ]
    results["timing_attacks"] = find_timing_attacks(content)
    results["incomplete_sanitization"] = find_incomplete_sanitization(content)
    results["redos"] = find_redos(content)
    results["weak_hash"] = find_weak_hash_usage(content)
    return results
