from __future__ import annotations
# complexity_justified: substrate omega genome surface
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


def _list() -> list:
    return []


def _dict() -> dict:
    return {}


@dataclass
class GenomeCapsule:
    pattern_id: str
    family: str
    radicals: list[str]
    summary: str
    invariants: list[str] = field(default_factory=_list)
    anti_patterns: list[str | dict] = field(default_factory=_list)
    language_manifestations: dict[str, list[str]] = field(default_factory=_dict)
    emitters: list[str] = field(default_factory=_list)
    transformation_axioms: list[str] = field(default_factory=_list)
    laws: list[str] = field(default_factory=_list)
    capabilities: list[str] = field(default_factory=_list)
    # Isomorph class: the cross-domain structural equivalent family.
    # e.g. "ownership_linearity_capability" — same pattern appearing as
    # Rust borrow checking, linear types, capability systems, RAII etc.
    isomorph_class: str = ""


class RadicalMap:
    """
    SoA-style semantic coordinate system for the genome.
    Radicals are compressed family kernels — the invariant core of a pattern class.
    Capsule entries orbit their parent radical(s).
    Isomorphism: a lookup table where keys are semantic constellations
    and values are lists of pattern stars within those constellations.
    """

    def __init__(self, capsules: list["GenomeCapsule"]) -> None:
        # SoA parallel arrays (indexed by capsule position)
        self.pattern_ids: list[str] = []
        self.radical_sets: list[frozenset] = []
        self.family_ids: list[str] = []
        self.isomorph_classes: list[str] = []
        self.capability_sets: list[frozenset] = []
        # Inverted indices
        self._radical_index: dict[str, list[int]] = {}
        self._isomorph_index: dict[str, list[int]] = {}
        self._family_index: dict[str, list[int]] = {}
        self._cap_index: dict[str, list[int]] = {}
        # Build
        for i, cap in enumerate(capsules):
            self.pattern_ids.append(cap.pattern_id)
            rset = frozenset(cap.radicals)
            cset = frozenset(cap.capabilities)
            self.radical_sets.append(rset)
            self.family_ids.append(cap.family)
            self.isomorph_classes.append(cap.isomorph_class or "")
            self.capability_sets.append(cset)
            for r in rset:
                self._radical_index.setdefault(r, []).append(i)
            if cap.isomorph_class:
                self._isomorph_index.setdefault(cap.isomorph_class, []).append(i)
            self._family_index.setdefault(cap.family, []).append(i)
            for c in cset:
                self._cap_index.setdefault(c, []).append(i)

    def by_radical(self, radical: str) -> list[int]:
        return self._radical_index.get(radical, [])

    def by_isomorph_class(self, cls: str) -> list[int]:
        return self._isomorph_index.get(cls, [])

    def score(self, idx: int, preferred_radicals: set, capabilities: set) -> float:
        """Score a capsule by radical and capability overlap (0.0–1.0)."""
        r_overlap = len(preferred_radicals & self.radical_sets[idx]) / max(len(preferred_radicals), 1)
        c_overlap = len(capabilities & self.capability_sets[idx]) / max(len(capabilities), 1)
        return r_overlap * 0.4 + c_overlap * 0.6

    def ranked_for_task(
        self,
        preferred_radicals: set,
        capabilities: set,
    ) -> list[int]:
        """Return all capsule indices ranked by relevance to this task."""
        scores = {
            i: self.score(i, preferred_radicals, capabilities)
            for i in range(len(self.pattern_ids))
        }
        return sorted(scores, key=lambda i: scores[i], reverse=True)

    def matches(
        self,
        *,
        radicals: set[str] | None = None,
        families: set[str] | None = None,
        language: str | None = None,
        capabilities: set[str] | None = None,
    ) -> bool:
        if radicals and not radicals.intersection(self.radicals):
            return False
        if families and self.family not in families:
            return False
        if language and language not in self.language_manifestations:
            return False
        if capabilities and not capabilities.intersection(self.capabilities):
            return False
        return True


class RadicalMapGenome:
    def __init__(self, capsules: list[GenomeCapsule]) -> None:
        self.capsules = capsules
        self.by_id = {capsule.pattern_id: capsule for capsule in capsules}
        self.radical_map = RadicalMap(capsules)

    @classmethod
    def load(cls, path: str | Path) -> "RadicalMapGenome":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        capsules = [GenomeCapsule(**capsule) for capsule in data["capsules"]]
        return cls(capsules)

    def query(
        self,
        *,
        radicals: list[str] | None = None,
        families: list[str] | None = None,
        language: str | None = None,
        capabilities: list[str] | None = None,
    ) -> list[GenomeCapsule]:
        radical_set = set(radicals or [])
        family_set = set(families or [])
        capability_set = set(capabilities or [])
        matches = [
            capsule for capsule in self.capsules
            if capsule.matches(
                radicals=radical_set if radicals else None,
                families=family_set if families else None,
                language=language,
                capabilities=capability_set if capabilities else None,
            )
        ]
        return sorted(matches, key=lambda item: (item.family, item.pattern_id))

    def bundle_for_task(
        self,
        *,
        language: str,
        capabilities: list[str],
        preferred_radicals: list[str] | None = None,
        budget_weights: "dict[str, float] | None" = None,
    ) -> dict[str, Any]:
        # Use RadicalMap for scored, ranked selection.
        # Capability overlap is the primary filter; radical overlap is a boost.
        # budget_weights: maps capsule_id → calibrated distortion_budget.
        # Capsules from tight-budget families (low budget = high support) get a
        # scoring bonus. This is the integration point for SMEM calibration.
        # Isomorphism: lower budget = higher effective temperature = tighter centroid
        # = more confident capsule = score boost.
        cap_set = set(capabilities)
        rad_set = set(preferred_radicals or [])
        ranked_indices = self.radical_map.ranked_for_task(rad_set, cap_set)
        selected: list[GenomeCapsule] = []
        for idx in ranked_indices:
            cap = self.capsules[idx]
            # Include if any capability overlaps
            if cap_set.intersection(cap.capabilities):
                selected.append(cap)
        # Apply budget-weight re-ordering: capsules from tight-budget families
        # (stable SMEM, high support) float to the top.
        # budget_weights maps capsule_id → calibrated budget (lower = tighter = higher priority).
        if budget_weights:
            def _priority(c: "GenomeCapsule") -> float:
                budget = budget_weights.get(c.pattern_id, 0.20)
                # Lower budget → higher priority (invert and normalize to 0–1)
                return 1.0 - budget
            selected.sort(key=_priority, reverse=True)
        return {
            "language": language,
            "capabilities": capabilities,
            "preferred_radicals": preferred_radicals or [],
            "budget_weights": budget_weights or {},
            "selected_patterns": [
                {
                    "pattern_id": capsule.pattern_id,
                    "family": capsule.family,
                    "radicals": capsule.radicals,
                    "summary": capsule.summary,
                    "emitters": capsule.emitters,
                    "transformation_axioms": capsule.transformation_axioms,
                    "laws": capsule.laws,
                    "capabilities": capsule.capabilities,
                }
                for capsule in selected
            ],
        }
