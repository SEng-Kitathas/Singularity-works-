from __future__ import annotations
# complexity_justified: universal semantic IR — substrate omega
# Every artifact regardless of source language is normalized into this IR.
# Python: full AST fidelity. Other languages: structural heuristics with
# explicit confidence annotation. Gates reason over IR, not raw syntax.
# Isomorphism: Code Property Graph merged with state-machine / trust-boundary
# topology. The forge sees structure, not text.

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Semantic graph primitives
# ---------------------------------------------------------------------------

@dataclass
class SemanticNode:
    node_id: str
    node_type: str      # FUNCTION | CALL | ASSIGN | CONTROL | CLASS | IMPORT | LITERAL
    name: str | None
    line: int
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticEdge:
    edge_type: str      # CONTROL_FLOW | DATA_FLOW | CALL | TRUST | RESOURCE | TEMPORAL
    source_id: str
    target_id: str
    properties: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# State machine (typestate / protocol state)
# ---------------------------------------------------------------------------

@dataclass
class StateNode:
    name: str
    is_terminal: bool = False
    is_error: bool = False
    is_forbidden: bool = False


@dataclass
class StateTransition:
    from_state: str
    to_state: str
    trigger: str


@dataclass
class StateMachine:
    """Tracks lifecycle of a named resource or protocol through a function."""
    tracked: str                    # variable / resource name
    states: list[StateNode] = field(default_factory=list)
    transitions: list[StateTransition] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Trust boundary
# ---------------------------------------------------------------------------

@dataclass
class TrustBoundary:
    """
    A directed taint record: source → [transforms] → sink.

    boundary_type classifies the sink surface.
    confidence reflects analysis depth: high=AST, medium=heuristic, low=regex.

    Directionality fields (populated when source is known):
      source_line:  line where taint enters the program (e.g. request.args.get)
      source_type:  USER_INPUT | ENV | FILE | NETWORK | DB_RESULT | UNKNOWN
      transforms:   intermediate lines where taint is modified before the sink
                    (e.g. format string construction, concatenation)

    A boundary with source_line=0 is a legacy/heuristic record — sink is known
    but source was not traced.  The forge treats these as lower-confidence.
    """
    boundary_type: str      # DB_QUERY | SHELL | TLS | EVAL_EXEC | FILE | NETWORK
    sink_name: str
    sink_line: int
    tainted_input: str | None = None    # what reaches the sink
    validated: bool = False
    confidence: str = "high"
    # Directed chain (source → transforms → sink)
    source_line: int = 0                # 0 = unknown / not traced
    source_type: str = "UNKNOWN"        # USER_INPUT | ENV | FILE | NETWORK | DB_RESULT
    transforms: list[int] = None        # intermediate transform line numbers

    def __post_init__(self) -> None:
        if self.transforms is None:
            self.transforms = []

    def is_directed(self) -> bool:
        """True if source was successfully traced — not just sink-only."""
        return self.source_line > 0

    def chain_length(self) -> int:
        """Number of hops: 1 = source→sink directly, 2 = source→transform→sink, etc."""
        return 1 + len(self.transforms)

    def to_chain_dict(self) -> dict:
        """Serialize the directed chain for FactBus publication."""
        return {
            "source_line":  self.source_line,
            "source_type":  self.source_type,
            "transforms":   list(self.transforms),
            "sink_line":    self.sink_line,
            "sink_name":    self.sink_name,
            "boundary_type": self.boundary_type,
            "hops":         self.chain_length(),
            "directed":     self.is_directed(),
        }


# ---------------------------------------------------------------------------
# Source → Sink taint flow
# ---------------------------------------------------------------------------

@dataclass
class SourceSinkFlow:
    flow_id: str
    source_type: str    # USER_INPUT | ENV | FILE | NETWORK | DB_RESULT
    source_line: int
    sink_type: str      # DB_QUERY | SHELL | EVAL | FILE_WRITE | NETWORK_OUT
    sink_line: int
    sanitized: bool = False


# ---------------------------------------------------------------------------
# Resource protocol violations
# ---------------------------------------------------------------------------

@dataclass
class ResourceViolation:
    resource: str
    violation: str      # LEAKED | USE_AFTER_RELEASE | PREMATURE_RELEASE | DOUBLE_RELEASE
    acquire_line: int
    violation_line: int


# ---------------------------------------------------------------------------
# Temporal / concurrency hazards
# ---------------------------------------------------------------------------

@dataclass
class TemporalGap:
    gap_type: str       # TOCTOU | ASYNC_ATOMICITY | RACE_WINDOW
    check_line: int
    act_line: int
    description: str


# ---------------------------------------------------------------------------
# Universal Semantic IR
# ---------------------------------------------------------------------------

@dataclass
class UniversalSemanticIR:
    """
    The forge's language-agnostic semantic substrate.
    Built once per artifact; consumed by all gates, recovery, the switchboard,
    and the genome matcher.

    For Python:      full AST fidelity (confidence='high')
    Other languages: structural heuristics (confidence='medium'/'low')

    The raw content is always available via .content for fallback.
    """
    artifact_id: str
    language: str
    content: str
    confidence: str = "high"    # how reliable the semantic extraction is

    # Graph primitives (populated for Python; sparse for other languages)
    nodes: list[SemanticNode] = field(default_factory=list)
    edges: list[SemanticEdge] = field(default_factory=list)

    # Semantic structures
    trust_boundaries: list[TrustBoundary] = field(default_factory=list)
    source_sink_flows: list[SourceSinkFlow] = field(default_factory=list)
    resource_violations: list[ResourceViolation] = field(default_factory=list)
    state_machines: list[StateMachine] = field(default_factory=list)
    temporal_gaps: list[TemporalGap] = field(default_factory=list)

    # Structural fingerprint — language-agnostic boolean features
    has_async: bool = False
    has_unsafe_blocks: bool = False
    has_dynamic_exec: bool = False
    has_db_calls: bool = False
    has_network_calls: bool = False
    has_file_io: bool = False
    has_shell_calls: bool = False
    has_tls_calls: bool = False
    has_mutable_defaults: bool = False
    has_recursive_calls: bool = False

    # Vocabulary for radical-based matching
    semantic_tokens: set[str] = field(default_factory=set)
    function_names: list[str] = field(default_factory=list)
    import_names: list[str] = field(default_factory=list)
    # Dangerous calls detected (eval, exec, subprocess, os.system …)
    dangerous_calls: list[str] = field(default_factory=list)

    def dominant_radical(self) -> str | None:
        """Infer the highest-priority radical from structural features."""
        if self.has_db_calls:
            return "QUERY"
        if self.has_dynamic_exec or self.has_shell_calls:
            return "TRUST"
        if self.has_tls_calls:
            return "VERIFY"
        if self.has_file_io:
            return "RESOURCE"
        if self.has_async:
            return "STATE"
        return None

    def has_any_trust_boundary(self) -> bool:
        return bool(self.trust_boundaries)

    def unvalidated_boundaries(self) -> list[TrustBoundary]:
        return [b for b in self.trust_boundaries if not b.validated]
