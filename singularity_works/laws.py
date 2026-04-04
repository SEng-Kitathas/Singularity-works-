from __future__ import annotations
"""Immutable law registry for Singularity Works."""

IMMUTABLE_LAWS = {
    "LAW_0": {
        "name": "Discourse != Implementation",
        "principle": "Spec refinement is not building.",
    },
    "LAW_1": {
        "name": "0-Day Not Someday",
        "principle": "When building: no stubs, no TODOs, no MVPs, no phases.",
    },
    "LAW_2": {
        "name": "Global Trigger Mapping",
        "principle": "Implementation paths inherit LAW_1 rigor.",
    },
    "LAW_3": {
        "name": "Ambiguity Resolution",
        "principle": "Implementation must resolve ambiguity before emission.",
    },
    "LAW_4": {
        "name": "Pedantic Execution",
        "principle": "Verify, do not infer or assume.",
    },
    "LAW_5": {
        "name": "Multi-Disciplinary Research",
        "principle": "Cross-pollinate foundations and first principles.",
    },
    "LAW_OMEGA": {
        "name": "The Golden Law",
        "principle": "Artifacts should maximize invariants, determinism, stability, and evidence quality.",
    },
    "LAW_SIGMA": {
        "name": "Generative Divergence",
        "principle": "Explore alternatives explicitly and challenge assumptions constructively.",
    },
}

BASELINE_AXIOMS = {
    "no_todos": True,
    "no_fixmes": True,
    "no_placeholder_stubs": True,
    "qa_applies_to_forge_itself": True,
    "residual_risk_must_be_explicit": True,
}

SELF_QA_REQUIREMENT_TEXT = (
    "Code must not contain TODO or stub markers. "
    "Resource discipline should be respected. "
    "Dangerous execution primitives should be absent. "
    "Residual risk must be explicit."
)
