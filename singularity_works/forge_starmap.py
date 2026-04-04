"""
Singularity Works — Forge StarMap
Adapter: StarMap Cognitive Geometry → Security Evidence Synthesis

Source corpus parsed and synthesized:
  starmap.py                  — 6-D domain seeds, Fiedler, build_graph, delta, cosine_sim
  starmap.pyc (richer)        — domain_vector, coevidence_affinity, curvature_penalty
  starmap_engine.py           — integrity/interference/fiedler/curvature metrics
  STARMAP-v1_0-COGNITIVE-GEOMETRY.md — Star/Edge/CSR/PropagationEngine/PathFinding
  PART2-StarMap-Trust.md      — Tension metric T(c1,c2), T1-T4 classifier, N0-N4 states
  NEAL-CORE-v19-SOAOA         — Demiurge/Galaxy/Constellation (Rust target)
  Starmap.pdf                 — Vamana/GalacticMemory/SpMV kernel
  StarMap_Research.pdf        — KBH theory, Shannon entropy, bandwidth wall

Adaptation Strategy
-------------------
starmap_engine.py requires: embed_fn(text) → np.ndarray
Forge has no embed_fn. Forge DOES have:
  - Capsule families with semantic positions
  - Gate results with falsified/discharged/residual signal
  - LBE blob taint flows with source→sink structure

Resolution: Use starmap.py's 6-D domain seed vectors as proxy embeddings.
  capsule_family → domain → 6-D vector
No neural model required. The radical/family taxonomy IS the geometry.

Isomorphisms Captured
---------------------
  StarMap Central Star      ↔  Forge failing capsule (gravity well)
  Gravitational Cascade     ↔  Cross-family risk amplification
  Cross-Domain Forcing      ↔  auth fail → check crypto + IDOR
  Fiedler λ₂ = 0            ↔  Isolated bug (not architectural)
  Fiedler λ₂ high           ↔  Systemic vulnerability pattern
  Trust Tier T1-T4          ↔  Forge green / amber / red
  Tension metric            ↔  Blob deception_score (claimed vs earned)
  Interference              ↔  Contradictory findings
  Curvature                 ↔  Risk surface shape (concentrated vs diffuse)
  SpMV A_{t+1} = σ(W·A_t)  ↔  Cross-family cascade propagation
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# ── 6-D Domain Seeds (starmap.py canonical MSPEC-C v3.3.9) -------------------
#
# 7 orthogonal knowledge axes in 6-D space.
# Normalized on load (same as starmap.py VEC dict).

_RAW_SEEDS = {
    "Physical Sciences":      [1.0, 0.1, 0.1, 0.0, 0.0, 0.0],
    "Engineering":            [0.9, 0.2, 0.1, 0.0, 0.0, 0.0],
    "Computational Sciences": [0.8, 0.3, 0.1, 0.0, 0.0, 0.0],
    "Ethics & Morality":      [0.0, 0.0, 0.1, 1.0, 0.8, 0.0],
    "Law & Jurisprudence":    [0.0, 0.0, 0.0, 0.2, 1.0, 0.1],
    "Safety & Risk":          [0.1, 0.2, 0.0, 0.5, 0.5, 0.9],
    "Default":                [0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
}


def _norm(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / (n + 1e-12)


_DOMAIN_VECS: dict[str, np.ndarray] = {
    k: _norm(np.array(v, dtype=float)) for k, v in _RAW_SEEDS.items()
}


# ── Capsule Family → Domain Mapping -------------------------------------------

_FAMILY_DOMAIN: dict[str, str] = {
    "query_integrity":           "Engineering",
    "injection":                 "Engineering",
    "network_safety":            "Engineering",
    "trust_boundary_validation": "Engineering",
    "execution_safety":          "Physical Sciences",
    "concurrency":               "Physical Sciences",
    "numeric_integrity":         "Physical Sciences",
    "temporal_integrity":        "Physical Sciences",
    "resource_scope":            "Physical Sciences",
    "crypto_safety":             "Computational Sciences",
    "state_protocol":            "Computational Sciences",
    "structural_integrity":      "Computational Sciences",
    "state_safety":              "Computational Sciences",
    "logic":                     "Computational Sciences",
    "auth":                      "Law & Jurisprudence",
    "access_control":            "Law & Jurisprudence",
    "authorization":             "Law & Jurisprudence",
    "tls_enforcement":           "Safety & Risk",
    "law_compliance":            "Safety & Risk",
    "memory":                    "Safety & Risk",
}

_DEFAULT_DOMAIN = "Safety & Risk"


def _family_vec(family: str) -> np.ndarray:
    domain = _FAMILY_DOMAIN.get(family, _DEFAULT_DOMAIN)
    return _DOMAIN_VECS[domain]


# ── Data model ----------------------------------------------------------------

@dataclass
class EvidenceNode:
    node_id: str
    label: str
    vec: np.ndarray
    weight: float
    family: str = ""
    kind: str = ""     # finding | discharge | residual | blob_sink


@dataclass
class StarMapMetrics:
    integrity: float = 0.0
    interference: float = 0.0
    fiedler_value: float = 0.0
    curvature: float = 0.0
    central_finding: str = ""
    cross_domain_count: int = 0
    trust_tier: str = "T4"
    tension_max: float = 0.0
    node_count: int = 0
    domains_present: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "integrity":          round(self.integrity, 4),
            "interference":       round(self.interference, 4),
            "fiedler_value":      round(self.fiedler_value, 4),
            "curvature":          round(self.curvature, 4),
            "central_finding":    self.central_finding,
            "cross_domain_count": self.cross_domain_count,
            "trust_tier":         self.trust_tier,
            "tension_max":        round(self.tension_max, 4),
            "node_count":         self.node_count,
            "domains_present":    self.domains_present,
        }

    @property
    def is_systemic(self) -> bool:
        return self.fiedler_value > 0.3

    @property
    def is_isolated(self) -> bool:
        return self.fiedler_value < 0.05

    @property
    def risk_amplifier(self) -> float:
        """
        Geometric risk multiplier for LBE blob scoring.
        Replaces hand-tuned multipliers in lbe_pilot.py _score_risk().
        """
        amp = (1.0 + self.fiedler_value) * (0.5 + self.integrity)
        amp *= (1.0 - 0.3 * self.interference)
        amp *= (1.0 + 0.1 * self.cross_domain_count)
        return round(min(2.5, max(0.1, amp)), 3)


# ── ForgeStarMap --------------------------------------------------------------

class ForgeStarMap:
    """
    Forge-native StarMap adapter.

    Builds an evidence graph from gate results or LBE blobs,
    computes geometric consensus metrics in the 6-D domain proxy space.
    """

    def __init__(self) -> None:
        self.nodes: list[EvidenceNode] = []
        self._counter = 0

    # -- Construction --

    @classmethod
    def from_gate_summary(cls, gate_summary, assurance) -> "ForgeStarMap":
        sm = cls()
        if gate_summary is None:
            return sm

        assurance_dict = assurance.to_dict() if assurance else {}
        falsified = set(assurance_dict.get("falsified", []))

        for gr in gate_summary.results:
            family = _extract_family(gr.gate_id)
            if gr.status == "fail":
                weight = 0.9
                kind = "finding"
            elif gr.status == "warn":
                weight = 0.6
                kind = "finding"
            elif gr.status == "pass":
                weight = 0.2
                kind = "discharge"
            else:
                weight = 0.1
                kind = "discharge"

            if any(gr.gate_id in f for f in falsified):
                weight = min(1.0, weight * 1.5)

            sm._add(gr.gate_id, family, weight, kind)

        # Infra residual exclusion (monitor_seed is noise)
        _INFRA = {"monitor_seed_generation"}
        for r in assurance_dict.get("residual", []):
            if r not in _INFRA:
                sm._add(f"residual:{r}", "Safety & Risk", 0.5, "residual")

        return sm

    @classmethod
    def from_blobs(cls, blobs) -> "ForgeStarMap":
        sm = cls()
        for blob in blobs:
            for sink in blob.sinks_reached:
                fam = _sink_to_family(sink.get("sink_kind", "UnknownEffect"))
                sm._add(
                    f"{sink.get('sink_kind')}@{blob.callable_id}",
                    fam, blob.risk_score, "blob_sink"
                )
                if blob.wrapper_theater:
                    sm._add(
                        f"wrapper_theater:{blob.callable_id}",
                        "trust_boundary_validation",
                        blob.deception_score, "finding"
                    )
        return sm

    @classmethod
    def from_combined(cls, gate_summary, assurance, blobs=None) -> "ForgeStarMap":
        sm = cls.from_gate_summary(gate_summary, assurance)
        if blobs:
            for n in cls.from_blobs(blobs).nodes:
                sm.nodes.append(n)
        return sm

    def _add(self, label: str, family: str, weight: float, kind: str) -> None:
        self._counter += 1
        v = _family_vec(family) * weight
        self.nodes.append(EvidenceNode(
            node_id=f"N{self._counter:04d}",
            label=label,
            vec=_norm(v) if np.linalg.norm(v) > 1e-8 else v,
            weight=weight,
            family=family,
            kind=kind,
        ))

    # -- Analysis --

    def analyze(self) -> StarMapMetrics:
        """
        Compute geometric metrics on evidence graph.
        Implements starmap_engine.StarmapEngine.build_topology() logic
        over forge evidence nodes in 6-D domain proxy space.
        """
        findings = [n for n in self.nodes if n.kind in ("finding", "blob_sink", "residual")]
        if len(findings) < 2:
            # No security findings — clean artifact. Don't fall back to discharge nodes
            # (discharges are noise for Fiedler/interference computation).
            return StarMapMetrics(node_count=len(self.nodes), trust_tier="T1")

        vecs = np.stack([n.vec for n in findings])

        # Consensus (Central Star — the gravity well of evidence)
        consensus = _norm(np.mean(vecs, axis=0))
        dists = np.array([float(np.linalg.norm(consensus - v)) for v in vecs])

        integrity    = 1.0 / (1.0 + float(np.mean(dists)))
        interference = _interference(vecs)
        fiedler      = _fiedler(vecs)
        curvature    = float(np.var(dists))
        tension_max  = _max_tension(vecs)

        central_finding = findings[int(np.argmin(dists))].label
        domains = list({_FAMILY_DOMAIN.get(n.family, _DEFAULT_DOMAIN) for n in findings})
        cross_domain = max(0, len(domains) - 1)
        tier = _trust_tier(integrity, interference, fiedler, tension_max)

        return StarMapMetrics(
            integrity=round(integrity, 4),
            interference=round(interference, 4),
            fiedler_value=round(fiedler, 4),
            curvature=round(curvature, 4),
            central_finding=central_finding,
            cross_domain_count=cross_domain,
            trust_tier=tier,
            tension_max=round(tension_max, 4),
            node_count=len(findings),
            domains_present=domains,
        )

    def propagate(self, central_family: str, depth: int = 3) -> dict:
        """
        Gravitational cascade from a failing family.
        Implements PropagationEngine.focus() from STARMAP-v1_0.
        SpMV analog: A_{t+1} = σ(W·A_t - δ)
        """
        decay, floor, bonus = 0.3, 0.01, 1.2  # cross-domain bonus (reduced from 1.5 to prevent saturation)
        acts = {central_family: 1.0}
        all_fams = list(_FAMILY_DOMAIN.keys())

        for _ in range(depth):
            new_acts = dict(acts)
            for src, src_a in acts.items():
                if src_a < floor:
                    continue
                sv = _family_vec(src)
                sd = _FAMILY_DOMAIN.get(src, _DEFAULT_DOMAIN)
                for tgt in all_fams:
                    if tgt == src:
                        continue
                    tv = _family_vec(tgt)
                    td = _FAMILY_DOMAIN.get(tgt, _DEFAULT_DOMAIN)
                    w = max(0.0, float(np.dot(sv, tv) /
                            (np.linalg.norm(sv) * np.linalg.norm(tv) + 1e-12)))
                    transfer = src_a * w * (1.0 - decay)
                    if sd != td:
                        transfer *= bonus  # cross-domain forcing
                    new_acts[tgt] = min(1.0, new_acts.get(tgt, 0.0) + transfer)
            acts = new_acts

        return {k: round(v, 4) for k, v in
                sorted(acts.items(), key=lambda x: x[1], reverse=True)
                if v > floor}

    def cascade_risk(self) -> dict:
        """Cascade from all failing families simultaneously → systemic risk map."""
        failing = {n.family for n in self.nodes if n.kind == "finding"}
        if not failing:
            return {}
        combined: dict[str, float] = {}
        for fam in failing:
            for k, v in self.propagate(fam, depth=2).items():
                combined[k] = min(1.0, combined.get(k, 0.0) + v)
        return {k: round(v, 4) for k, v in
                sorted(combined.items(), key=lambda x: x[1], reverse=True)}


# ── Geometric primitives (from starmap_engine.py) ----------------------------

def _interference(vecs: np.ndarray) -> float:
    n = len(vecs)
    if n <= 1:
        return 0.0
    total, count = 0.0, 0
    for i in range(n):
        for j in range(i + 1, n):
            ni, nj = np.linalg.norm(vecs[i]), np.linalg.norm(vecs[j])
            if ni > 0 and nj > 0:
                total += 1.0 - float(np.dot(vecs[i], vecs[j]) / (ni * nj))
                count += 1
    return total / count if count else 0.0


def _fiedler(vecs: np.ndarray) -> float:
    n = len(vecs)
    if n <= 1:
        return 0.0
    W = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                ni, nj = np.linalg.norm(vecs[i]), np.linalg.norm(vecs[j])
                if ni > 0 and nj > 0:
                    W[i, j] = max(0.0, float(np.dot(vecs[i], vecs[j]) / (ni * nj)))
    L = np.diag(W.sum(axis=1)) - W
    try:
        ev = np.sort(np.linalg.eigvalsh(L))
        return float(ev[1]) if len(ev) > 1 else 0.0
    except np.linalg.LinAlgError:
        return 0.0


def _max_tension(vecs: np.ndarray) -> float:
    """Max pairwise T(c1,c2) = 1 - cosine_sim (PART2-StarMap-Trust §7.3)."""
    n, mx = len(vecs), 0.0
    for i in range(n):
        for j in range(i + 1, n):
            ni, nj = np.linalg.norm(vecs[i]), np.linalg.norm(vecs[j])
            if ni > 0 and nj > 0:
                mx = max(mx, 1.0 - float(np.dot(vecs[i], vecs[j]) / (ni * nj)))
    return mx


def _trust_tier(integrity: float, interference: float,
                fiedler: float, tension: float) -> str:
    """
    T1-T4 classifier from PART2-StarMap-Trust §4.2.1.
    Forge mapping: T1=green-confirmed / T4=red-speculative.
    """
    if integrity >= 0.75 and interference < 0.25 and fiedler < 0.3 and tension < 0.30:
        return "T1"
    if integrity >= 0.55 and interference < 0.45 and fiedler < 0.55 and tension < 0.50:
        return "T2"
    if integrity >= 0.35 and interference < 0.65 and tension < 0.70:
        return "T3"
    return "T4"


# ── Helpers -------------------------------------------------------------------

def _extract_family(gate_id: str) -> str:
    lower = gate_id.lower().replace("-", "_")
    for fam in _FAMILY_DOMAIN:
        if fam.replace("_", "") in lower.replace("_", ""):
            return fam
    if ":" in gate_id:
        for part in gate_id.split(":")[1:]:
            if "." in part:
                fam = part.split(".")[0]
                if fam in _FAMILY_DOMAIN:
                    return fam
    return "Safety & Risk"


def _sink_to_family(sink_kind: str) -> str:
    return {
        "QueryExec":         "query_integrity",
        "CommandExec":       "execution_safety",
        "OutboundRequest":   "network_safety",
        "RenderInline":      "trust_boundary_validation",
        "Redirect":          "auth",
        "DatabaseWrite":     "query_integrity",
        "AuthStateMutation": "auth",
        "TokenIssue":        "auth",
    }.get(sink_kind, "Safety & Risk")


# ── coevidence_affinity (from starmap.pyc) ------------------------------------

def coevidence_affinity(finding_families: list, epsilon: float = 0.75) -> float:
    """
    Adapted from starmap.pyc coevidence_affinity(domains_for_hypotheses, epsilon=0.75).
    Measures how mutually reinforcing a set of finding families are.
    """
    if not finding_families:
        return 0.0
    centroids = []
    for families in finding_families:
        if not families:
            continue
        c = _norm(np.mean([_family_vec(f) for f in families], axis=0))
        centroids.append(c)
    if len(centroids) < 2:
        return 0.0
    n = len(centroids)
    A = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = float(np.linalg.norm(centroids[i] - centroids[j]))
            if 0.0 < d <= epsilon:
                A[i, j] = A[j, i] = 1.0 / d
    edges = A[A > 0]
    return float(np.mean(edges)) if len(edges) else 0.0


# ── curvature_penalty (from starmap.pyc) --------------------------------------

def curvature_penalty(domain_vectors: list) -> float:
    """
    Adapted from starmap.pyc curvature_penalty(domain_vectors).
    High curvature = risk diffuse across domains = higher ambiguity.
    """
    if len(domain_vectors) < 2:
        return 0.0
    vecs = np.stack(domain_vectors)
    centroid = _norm(np.mean(vecs, axis=0))
    dists = [float(np.linalg.norm(centroid - v)) for v in vecs]
    return float(np.var(dists))


# ── Quick-access helper -------------------------------------------------------

def analyze_result(result) -> StarMapMetrics:
    """One-call: OrchestrationResult → StarMapMetrics."""
    sm = ForgeStarMap.from_gate_summary(result.gate_summary, result.assurance)
    return sm.analyze()
