"""
Singularity Works — Forge StarMap
Version: 2026-04-04

StarMap cognitive geometry adapted for Forge evidence synthesis.

Isomorphisms from the canonical specs:
  - Security domain families → StarMap knowledge domains
  - Gate results → Evidence snippets with embedding vectors
  - Fiedler λ₂ → Evidence coherence (high = all gates agree, low = fragmented)
  - Tension T(c₁, c₂) → Conflict between security claims in the same artifact
  - Trust tier (T1-T4) → Escalation routing (T1/T2 = clean, T3/T4 = LBE)
  - Gravitational cascade → Taint propagation from source to sink
  - Cross-domain forcing → Detecting when one security failure implies another
  - Integrity metric → Coherence around consensus verdict
  - Interference metric → Pairwise contradiction between gate results
  - Curvature metric → Variance in evidence space (ambiguity signal)

Canonical 6-D Security Domain Seed Vectors:
  Dim 0: Injection surface (SQL, cmd, template, LDAP, XPath)
  Dim 1: Trust boundary (auth, CSRF, JWT, rate-limit, session)
  Dim 2: Data integrity (validation, sanitization, encoding, parameterization)
  Dim 3: Resource management (file ops, connections, memory, lifecycle)
  Dim 4: Cryptographic soundness (hashing, TLS, CSPRNG, HMAC)
  Dim 5: Access control (ownership, RBAC, IDOR, privilege)

Mathematical formalism (from NEAL-CORE v17.0 / PART2-StarMap-Trust.md):
  Tension:   T(c₁, c₂) = w_cos·T_cos + w_dist·T_dist + w_act·T_act
  Propagation: A_{t+1} = σ(W·A_t − δ)
  Coherence:   Fiedler λ₂ of Laplacian L = D − W
  Trust Tier:  T1(β≥0.90, consensus≥7/8) → T4(speculative)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from singularity_works.enforcement import GateRunSummary
    from singularity_works.assurance import AssuranceRollup


# ── Canonical Security Domain Seeds (6-D normalized) ─────────────────────
# Designed so that injection↔trust_boundary are close,
# crypto↔access_control are close, and resource_mgmt is orthogonal.
# Mirroring starmap.py's _SEEDS structure applied to security families.

_SECURITY_SEEDS: dict[str, np.ndarray] = {
    "injection":         np.array([1.0, 0.6, 0.3, 0.0, 0.0, 0.1], dtype=float),
    "trust_boundary":    np.array([0.8, 1.0, 0.4, 0.0, 0.1, 0.2], dtype=float),
    "data_integrity":    np.array([0.4, 0.3, 1.0, 0.2, 0.3, 0.0], dtype=float),
    "resource_mgmt":     np.array([0.0, 0.0, 0.2, 1.0, 0.1, 0.0], dtype=float),
    "cryptographic":     np.array([0.1, 0.2, 0.3, 0.1, 1.0, 0.5], dtype=float),
    "access_control":    np.array([0.1, 0.3, 0.0, 0.0, 0.4, 1.0], dtype=float),
    "default":           np.array([0.3, 0.3, 0.3, 0.3, 0.3, 0.3], dtype=float),
}

# Gate family → security domain mapping
_FAMILY_TO_DOMAIN: dict[str, str] = {
    "injection":              "injection",
    "query_integrity":        "injection",
    "execution_safety":       "injection",
    "network_safety":         "trust_boundary",
    "auth":                   "trust_boundary",
    "tls_enforcement":        "trust_boundary",
    "state_protocol":         "trust_boundary",
    "crypto":                 "cryptographic",
    "access_control":         "access_control",
    "concurrency":            "resource_mgmt",
    "memory":                 "resource_mgmt",
    "temporal_safety":        "resource_mgmt",
    "state_safety":           "resource_mgmt",
    "logic":                  "data_integrity",
    "state":                  "data_integrity",
    "static":                 "default",
}


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / (n + 1e-12)


# Normalized canonical vectors
_DOMAIN_VEC: dict[str, np.ndarray] = {
    k: _normalize(v) for k, v in _SECURITY_SEEDS.items()
}


def domain_vector(family: str) -> np.ndarray:
    """Return the canonical 6-D seed vector for a gate family."""
    domain = _FAMILY_TO_DOMAIN.get(family, "default")
    return _DOMAIN_VEC.get(domain, _DOMAIN_VEC["default"])


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na <= 0 or nb <= 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ── Gate Evidence Node ────────────────────────────────────────────────────

@dataclass
class GateEvidence:
    """
    A gate result projected into the 6-D security domain space.
    Analogous to a StarMap 'Star' node.
    """
    gate_id: str
    family: str
    status: str         # pass | warn | fail
    confidence: str     # low | moderate | high | certain
    severity: str       # info | medium | high | critical
    finding_count: int
    residual_count: int

    # Derived
    vec: np.ndarray = field(default_factory=lambda: np.zeros(6))
    activation: float = 0.0   # 0.0 = dark, 1.0 = fully active
    domain: str = "default"

    def __post_init__(self):
        self.domain = _FAMILY_TO_DOMAIN.get(self.family, "default")
        self.vec = self._embed()
        self.activation = self._initial_activation()

    def _embed(self) -> np.ndarray:
        """
        Project this gate result into the 6-D security domain space.
        Base = canonical domain seed, modulated by status/confidence/severity.
        """
        base = domain_vector(self.family).copy()

        # Status modulation: fail amplifies the relevant dimension
        status_weight = {"pass": 0.3, "warn": 0.6, "fail": 1.0}.get(self.status, 0.5)
        severity_weight = {
            "info": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0
        }.get(self.severity, 0.5)
        confidence_weight = {
            "low": 0.3, "moderate": 0.6, "high": 0.85, "certain": 1.0
        }.get(self.confidence, 0.5)

        # Scale the domain seed by security signal strength
        modulated = base * (status_weight * 0.5 + severity_weight * 0.3 + confidence_weight * 0.2)
        return _normalize(modulated)

    def _initial_activation(self) -> float:
        """Initial activation: fail = 1.0 (gravity well), pass = 0.2."""
        return {"fail": 1.0, "warn": 0.6, "pass": 0.2}.get(self.status, 0.3)


# ── Forge Topology ────────────────────────────────────────────────────────

@dataclass
class ForgeTopology:
    """
    The complete StarMap geometry for one forge run.

    Metrics (from starmap_engine.py + NEAL-CORE v17.0):
      integrity:     Coherence around consensus verdict (higher = more agreement)
      interference:  Pairwise conflict energy (lower = less contradiction)
      fiedler_value: λ₂ algebraic connectivity (higher = better connected evidence)
      curvature:     Variance in evidence space (higher = more ambiguous)
      max_tension:   Highest pairwise T(c₁, c₂) — feeds trust tier classifier

    Trust tier (from PART2-StarMap-Trust.md §4.2):
      T1 (Verified):   High integrity + high Fiedler + low tension + low interference
      T2 (Confident):  Moderate thresholds
      T3 (Tentative):  Low thresholds — route to LBE recommended
      T4 (Speculative): Default — route to LBE mandatory
    """
    # Gate evidence nodes
    nodes: list[GateEvidence]

    # Core StarMap metrics
    integrity: float        # 0.0-1.0 (higher = coherent)
    interference: float     # 0.0-1.0 (lower = no conflict)
    fiedler_value: float    # λ₂ ≥ 0 (higher = better connected)
    curvature: float        # variance in distance space
    max_tension: float      # worst pairwise T(c₁, c₂)

    # Consensus
    consensus_node: GateEvidence | None   # gate closest to geometric consensus
    consensus_status: str                  # dominant status verdict

    # Trust tier (from NEAL-CORE v17.0 T1-T4 classifier)
    trust_tier: str         # T1 | T2 | T3 | T4
    terminal_state: str     # N0 | N1 | N2 | N3 | N4

    # Tension matrix (gate_id pairs → tension score)
    tension_matrix: dict[tuple[str, str], float]

    # Cross-domain insights: gate families that should escalate together
    cross_domain_links: list[tuple[str, str, float]]  # (domain_a, domain_b, similarity)

    # Propagated activation after cascade
    activated_domains: dict[str, float]   # domain → final activation after decay

    def to_dict(self) -> dict:
        return {
            "integrity": round(self.integrity, 4),
            "interference": round(self.interference, 4),
            "fiedler_value": round(self.fiedler_value, 4),
            "curvature": round(self.curvature, 4),
            "max_tension": round(self.max_tension, 4),
            "consensus_status": self.consensus_status,
            "trust_tier": self.trust_tier,
            "terminal_state": self.terminal_state,
            "node_count": len(self.nodes),
            "cross_domain_links": [
                {"domain_a": a, "domain_b": b, "similarity": round(s, 3)}
                for a, b, s in self.cross_domain_links[:5]
            ],
            "activated_domains": {
                k: round(v, 3) for k, v in self.activated_domains.items()
            },
        }


# ── Tension Metric (NEAL-CORE v17.0 §7.3) ────────────────────────────────

# Tension weights (from PART2-StarMap-Trust.md)
_W_COS = 0.50
_W_ACT = 0.20
# Note: we substitute graph distance (structural) with family alignment distance
_W_FAM = 0.30

def compute_tension(a: GateEvidence, b: GateEvidence) -> float:
    """
    T(c₁, c₂) = w_cos·T_cos + w_fam·T_fam + w_act·T_act

    T_cos: cosine distance between embedding vectors
    T_fam: are these from conflicting domain families?
    T_act: absolute activation difference
    """
    t_cos = 1.0 - cosine_sim(a.vec, b.vec)

    # Family-level tension: same domain = low, different domains = higher
    # "injection" and "access_control" failing together = medium tension (cross-domain)
    same_domain = (a.domain == b.domain)
    t_fam = 0.0 if same_domain else 0.5

    # Both failing = high tension only if they contradict (one says sanitized, other says not)
    # Simple proxy: if both are fail, tension is lower (corroborating)
    # If one is pass and one is fail, tension is higher (contradictory)
    if a.status != b.status:
        t_fam = min(1.0, t_fam + 0.3)

    t_act = abs(a.activation - b.activation)

    return _W_COS * t_cos + _W_FAM * t_fam + _W_ACT * t_act


# ── Activation Propagation (STARMAP-v1_0 §4) ─────────────────────────────

_DECAY_RATE = 0.3      # Per-hop decay (starmap.py canonical: 0.3)
_NOISE_FLOOR = 0.01    # Below this = dark
_CROSS_DOMAIN_BONUS = 1.5
_MAX_DEPTH = 5

def propagate_activation(
    nodes: list[GateEvidence],
    adjacency: np.ndarray,
) -> dict[str, float]:
    """
    A_{t+1} = σ(W·A_t − δ)

    Double-buffer propagation from starmap.py / STARMAP-v1_0 PropagationEngine.
    Returns final activation per security domain after max_depth steps.
    """
    n = len(nodes)
    if n == 0:
        return {}

    # Initialize activation vector
    a_current = np.array([node.activation for node in nodes], dtype=float)
    a_next = np.zeros(n, dtype=float)

    for depth in range(_MAX_DEPTH):
        for j in range(n):
            incoming = 0.0
            for i in range(n):
                if adjacency[i, j] > 0 and a_current[i] > _NOISE_FLOOR:
                    weight = adjacency[i, j]
                    transfer = a_current[i] * weight * (1.0 - _DECAY_RATE)
                    # Cross-domain bonus
                    if nodes[i].domain != nodes[j].domain:
                        transfer *= _CROSS_DOMAIN_BONUS
                    incoming += transfer
            a_next[j] = min(1.0, a_current[j] + incoming)

        # Apply decay globally
        a_current = a_next * (1.0 - _DECAY_RATE * 0.5)
        a_next = np.zeros(n, dtype=float)

        if np.all(a_current < _NOISE_FLOOR):
            break

    # Aggregate by domain
    domain_activations: dict[str, float] = {}
    for i, node in enumerate(nodes):
        if a_current[i] > _NOISE_FLOOR:
            prev = domain_activations.get(node.domain, 0.0)
            domain_activations[node.domain] = min(1.0, prev + a_current[i])

    return domain_activations


# ── Adjacency Graph from Gate Results ─────────────────────────────────────

def _build_adjacency(nodes: list[GateEvidence], epsilon: float = 0.75) -> np.ndarray:
    """
    Build weighted adjacency from cosine similarity threshold.
    Edge weight = 1/distance if distance ≤ epsilon.
    Direct port from starmap.py build_graph().
    """
    n = len(nodes)
    A = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_sim(nodes[i].vec, nodes[j].vec)
            dist = 1.0 - sim  # cosine distance
            if dist <= (1.0 - epsilon) and dist > 0.0:
                w = 1.0 / (dist + 1e-9)
                A[i, j] = w
                A[j, i] = w
    return A


# ── Fiedler Value (starmap.py fiedler_value) ──────────────────────────────

def fiedler_value(A: np.ndarray) -> float:
    """
    λ₂ of the graph Laplacian L = D − A.
    High λ₂ = well-connected evidence graph.
    λ₂ = 0 means disconnected components (fragmented findings).
    """
    D = np.diag(np.sum(A, axis=1))
    L = D - A
    try:
        ev = np.linalg.eigvalsh(L)
        ev.sort()
        return float(ev[1]) if len(ev) > 1 else 0.0
    except np.linalg.LinAlgError:
        return 0.0


# ── Coevidence Affinity (from pyc: coevidence_affinity) ──────────────────

def coevidence_affinity(groups: list[list[GateEvidence]], epsilon: float = 0.75) -> float:
    """
    How much do multiple hypothesis groups agree geometrically?
    From starmap_cpython-311.pyc coevidence_affinity signature.
    Returns mean pairwise similarity across group centroids.
    """
    if len(groups) < 2:
        return 1.0

    centroids = []
    for group in groups:
        if group:
            vecs = np.stack([n.vec for n in group])
            centroid = _normalize(np.mean(vecs, axis=0))
            centroids.append(centroid)

    if len(centroids) < 2:
        return 1.0

    sims = []
    for i in range(len(centroids)):
        for j in range(i + 1, len(centroids)):
            sims.append(cosine_sim(centroids[i], centroids[j]))

    return float(np.mean(sims))


# ── Curvature Penalty (from pyc: curvature_penalty) ───────────────────────

def curvature_penalty(domain_vecs: list[np.ndarray]) -> float:
    """
    κ(d): variance in the evidence space distances from the consensus.
    High curvature = high ambiguity = route to LBE.
    From starmap_cpython-311.pyc curvature_penalty.
    """
    if len(domain_vecs) < 2:
        return 0.0
    consensus = _normalize(np.mean(np.stack(domain_vecs), axis=0))
    dists = [float(np.linalg.norm(v - consensus)) for v in domain_vecs]
    return float(np.var(dists))


# ── Trust Tier Classifier (NEAL-CORE v17.0 §4.2) ─────────────────────────

def classify_trust_tier(
    integrity: float,
    interference: float,
    fiedler: float,
    max_tension: float,
    assurance_status: str,
    fail_count: int,
) -> tuple[str, str]:
    """
    Classify trust tier T1-T4 and terminal state N0-N4.

    From PART2-StarMap-Trust.md §4.2 + §5.2.

    Key insight: Fiedler=0 on a GREEN result means the gates all trivially pass
    with no conflict to resolve — the graph has no tension edges by design.
    Fiedler matters only when the result is ambiguous (mixed signals).
    Similarly, tension on green-pass-only gate pairs is benign domain diversity,
    not actual security conflict. Tension is only used as a downgrade signal
    when fail_count > 0 (there IS a conflict).

    T1 (Verified) → N4 (Approved):
      integrity ≥ 0.65 AND interference < 0.35 AND status=green AND fail=0

    T2 (Confident) → N4 (Approved):
      integrity ≥ 0.55 AND interference < 0.50 AND status=green AND fail=0

    T3 (Tentative) → N2 (Degraded):
      fail=0 AND status in green/amber
      (lower confidence, but no hard failures)

    T4 (Speculative) → N0/N1/N2/N3:
      fail > 0 or hard conflict signals present
    """
    if fail_count == 0 and assurance_status == "green":
        if integrity >= 0.65 and interference < 0.35:
            return "T1", "N4"
        if integrity >= 0.55 and interference < 0.50:
            return "T2", "N4"
        # Green but weaker coherence — still tentative pass
        return "T3", "N4"

    if fail_count == 0 and assurance_status in ("amber",):
        if integrity >= 0.40 and interference < 0.60:
            return "T3", "N2"

    # Fail present — N-state determined by signal type
    # N0: integrity collapse (contradictory evidence of safety)
    if integrity < 0.15 and fail_count > 0:
        return "T4", "N0"

    # N1: high tension + fail (CHE critical analog — dangerous combination)
    if max_tension >= 0.85 and fail_count > 0:
        return "T4", "N1"

    # N3: deadlock (high interference, no clear verdict)
    if interference >= 0.70 and fail_count == 0:
        return "T4", "N3"

    # Default fail path
    return "T4", "N2"


# ── Cross-Domain Forcing (STARMAP-v1_0 §6) ────────────────────────────────

def find_cross_domain_links(
    nodes: list[GateEvidence],
    min_similarity: float = 0.3,
) -> list[tuple[str, str, float]]:
    """
    Find cross-domain connections — where a finding in one security
    family has structural implications for another.

    "Cross-Disciplinary Forcing: deliberately bridges disparate fields."
    — STARMAP-v1_0 EXECUTIVE SUMMARY

    Examples of valid cross-domain forcing in security:
      - injection failure ↔ access_control failure → privilege escalation
      - trust_boundary failure ↔ cryptographic failure → auth bypass chain
    """
    links: list[tuple[str, str, float]] = []

    # Group by domain
    domain_groups: dict[str, list[GateEvidence]] = {}
    for node in nodes:
        domain_groups.setdefault(node.domain, []).append(node)

    domains = list(domain_groups.keys())
    for i in range(len(domains)):
        for j in range(i + 1, len(domains)):
            da, db = domains[i], domains[j]
            if da == db:
                continue

            # Compute centroid similarity across domains
            vecs_a = np.stack([n.vec for n in domain_groups[da]])
            vecs_b = np.stack([n.vec for n in domain_groups[db]])
            centroid_a = _normalize(np.mean(vecs_a, axis=0))
            centroid_b = _normalize(np.mean(vecs_b, axis=0))
            sim = cosine_sim(centroid_a, centroid_b)

            if sim >= min_similarity:
                links.append((da, db, sim))

    links.sort(key=lambda x: x[2], reverse=True)
    return links


# ── Main Topology Builder ─────────────────────────────────────────────────

def build_evidence_topology(
    gate_summary: "GateRunSummary",
    assurance: "AssuranceRollup",
    audit: dict,
) -> ForgeTopology:
    """
    Build the complete StarMap geometry for a forge gate run.

    Adapted from StarmapEngine.build_topology() in starmap_engine.py,
    applied to gate results instead of web search snippets.

    Parameters:
        gate_summary: GateRunSummary from orc.run()
        assurance:    AssuranceRollup from orc.run()
        audit:        recursive_audit dict from orc.run()

    Returns:
        ForgeTopology with all StarMap metrics computed.
    """
    gate_results = getattr(gate_summary, "results", [])
    gate_counts = audit.get("gate_counts", {})
    fail_count = gate_counts.get("fail", 0)

    # Infrastructure residuals to exclude (same filter as escalation gate)
    _INFRA = frozenset({"monitor_seed_generation", "monitor_seed_gen"})
    _INFRA_WARN = frozenset({"runtime.monitor_seed", "runtime.monitor_seed_gen"})

    # ── Build evidence nodes ──────────────────────────────────────────────
    nodes: list[GateEvidence] = []

    for gr in gate_results:
        gate_id = gr.gate_id
        status = gr.status

        # Skip infra-only warns
        if status == "warn" and gate_id in _INFRA_WARN:
            continue

        # Infer family from gate_id (e.g., "genome:query_integrity.parameterized_queries:...")
        parts = gate_id.split(":")
        family = "static"
        if len(parts) >= 2:
            # gate_id = "genome:family.specific:..."
            family_part = parts[1] if len(parts) > 1 else parts[0]
            family = family_part.split(".")[0]

        findings = getattr(gr, "findings", [])
        residuals = getattr(gr, "residual_obligations", [])
        semantic_residuals = [r for r in residuals if r not in _INFRA]

        severity = "info"
        if status == "fail":
            severity = "high"
            if any("injection" in str(f).lower() or "injection" in family for f in findings):
                severity = "critical"
        elif status == "warn":
            severity = "medium"

        nodes.append(GateEvidence(
            gate_id=gate_id,
            family=family,
            status=status,
            confidence="high" if status in ("pass", "fail") else "moderate",
            severity=severity,
            finding_count=len(findings),
            residual_count=len(semantic_residuals),
        ))

    if not nodes:
        # Degenerate case — no gate results at all
        return ForgeTopology(
            nodes=[],
            integrity=0.0,
            interference=0.0,
            fiedler_value=0.0,
            curvature=0.0,
            max_tension=0.0,
            consensus_node=None,
            consensus_status="unknown",
            trust_tier="T4",
            terminal_state="N2",
            tension_matrix={},
            cross_domain_links=[],
            activated_domains={},
        )

    vecs = np.stack([n.vec for n in nodes])
    n = len(nodes)

    # ── Consensus (geometric mean) ────────────────────────────────────────
    consensus_vec = _normalize(np.mean(vecs, axis=0))
    dists = [float(np.linalg.norm(consensus_vec - v)) for v in vecs]

    # ── Integrity (coherence around consensus) ────────────────────────────
    integrity = float(1.0 / (1.0 + np.mean(dists)))

    # ── Interference (pairwise conflict energy) ───────────────────────────
    interference = 0.0
    pair_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_sim(nodes[i].vec, nodes[j].vec)
            interference += 1.0 - sim
            pair_count += 1
    if pair_count > 0:
        interference /= pair_count

    # ── Fiedler λ₂ ───────────────────────────────────────────────────────
    A = _build_adjacency(nodes, epsilon=0.65)
    fiedler = fiedler_value(A)

    # ── Curvature ─────────────────────────────────────────────────────────
    curvature = curvature_penalty([n.vec for n in nodes])

    # ── Tension matrix ────────────────────────────────────────────────────
    tension_matrix: dict[tuple[str, str], float] = {}
    max_tension = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            t = compute_tension(nodes[i], nodes[j])
            tension_matrix[(nodes[i].gate_id, nodes[j].gate_id)] = t
            if t > max_tension:
                max_tension = t

    # ── Consensus node (closest to consensus vector) ──────────────────────
    closest_idx = int(np.argmin(dists))
    consensus_node = nodes[closest_idx]

    # ── Consensus status (dominant verdict) ──────────────────────────────
    status_counts = {"fail": 0, "warn": 0, "pass": 0}
    for nd in nodes:
        status_counts[nd.status] = status_counts.get(nd.status, 0) + 1

    if status_counts["fail"] > 0:
        consensus_status = "red"
    elif status_counts["warn"] > 0:
        consensus_status = "amber"
    else:
        consensus_status = "green"

    # ── Activation propagation ────────────────────────────────────────────
    activated_domains = propagate_activation(nodes, A)

    # ── Cross-domain links ────────────────────────────────────────────────
    # Only show links where at least one domain has a failing gate
    failing_domains = {n.domain for n in nodes if n.status == "fail"}
    all_links = find_cross_domain_links(nodes)
    cross_domain_links = [
        (da, db, sim) for da, db, sim in all_links
        if da in failing_domains or db in failing_domains
    ]

    # ── Trust tier ────────────────────────────────────────────────────────
    trust_tier, terminal_state = classify_trust_tier(
        integrity=integrity,
        interference=interference,
        fiedler=fiedler,
        max_tension=max_tension,
        assurance_status=assurance.status,
        fail_count=fail_count,
    )

    return ForgeTopology(
        nodes=nodes,
        integrity=integrity,
        interference=interference,
        fiedler_value=fiedler,
        curvature=curvature,
        max_tension=max_tension,
        consensus_node=consensus_node,
        consensus_status=consensus_status,
        trust_tier=trust_tier,
        terminal_state=terminal_state,
        tension_matrix=tension_matrix,
        cross_domain_links=cross_domain_links,
        activated_domains=activated_domains,
    )
