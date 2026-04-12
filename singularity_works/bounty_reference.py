from __future__ import annotations
from typing import Any

from .bounty_reference_data import _CVSS_MAP, _CWE_MAP


def _cvss_for_finding(finding_code: str, gate_family: str) -> dict[str, Any]:
    """Look up CVSS data by finding code or gate family."""
    code_lower = finding_code.lower().replace("-", "_")
    family_lower = gate_family.lower().replace("-", "_")
    for key, data in _CVSS_MAP.items():
        if key in code_lower or key in family_lower:
            return data.__dict__.copy()
    return _CVSS_MAP["_default"].__dict__.copy()


def _cwe_for(code_or_family: str) -> str:
    slug = code_or_family.lower().replace("-", "_")
    for key, cwe in _CWE_MAP.items():
        if key in slug:
            return cwe
    return "CWE-693: Protection Mechanism Failure"
