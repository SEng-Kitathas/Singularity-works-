"""
Singularity Works — LBE Blueprint
The cartographic layer over the Universal Structural Reasoner.

DESIGN INTENT
─────────────
The Universal Reasoner maps the territory from first principles.
The Blueprint is the map artifact — a navigable, color-coded flowchart
of what the code DOES: sources, transforms, sinks, trust crossings,
obligations, and the exact minimum replacement to turn red paths green.

THREE COLORS, ONE PRINCIPLE
───────────────────────────
  RED    — tainted flow reaches dangerous sink without earned trust
  YELLOW — tainted flow with naming claims but no earned trust (wrapper theater)
  GREEN  — validated path — trust earned before sink boundary
  PURPLE — structural obligation violated (no taint flow, invariant broken)
  GRAY   — clean discharge — trust earned, path is safe

MINIMUM REPLACEMENT
───────────────────
For every red/yellow path, the Blueprint annotates the exact node
where a validation would turn the path green, and what that fix looks like.
This is the surgical cut point — the minimum code that needs replacement.

Rule: minimum replacement = the last transform before the sink
  (or the sink itself if no transforms exist).
This is the node closest to the effect surface where sanitization
can be inserted. Replace exactly that, and nothing else, and the
path becomes green.

OUTPUT
──────
  Blueprint.to_mermaid()     → Mermaid flowchart string (renderable)
  Blueprint.to_summary()     → human-readable text summary
  Blueprint.to_dict()        → serializable for MCP / HUD consumption
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from singularity_works.lbe_universal import UniversalIR, UTaintFlow, UObligation
    from singularity_works.lbe_pilot import LBEResult, PathState, Blob


# ── Path colors ───────────────────────────────────────────────────────────────

class PathColor:
    RED    = "red"       # tainted → dangerous sink, no earned trust
    YELLOW = "yellow"    # tainted → sink, CLAIMED but not EARNED trust
    GREEN  = "green"     # validated path — trust earned
    PURPLE = "purple"    # structural obligation violated
    GRAY   = "gray"      # clean discharge / non-security path


# ── Blueprint data model ──────────────────────────────────────────────────────

@dataclass
class BPNode:
    """A node in the Blueprint graph."""
    node_id: str
    label: str
    kind: str        # source | transform | sink | validation | claim | obligation | callable
    color: str       # PathColor value
    line: int = 0
    detail: str = ""


@dataclass
class BPEdge:
    """A directed edge in the Blueprint graph."""
    from_id: str
    to_id: str
    label: str       # "tainted" | "validated" | "claimed" | "unchecked" | "calls"
    color: str       # PathColor value


@dataclass
class MinimumReplacement:
    """The surgical cut point that turns a red path green."""
    target_node_id: str
    target_label: str
    line: int
    what_to_do: str         # "add validation before this call" etc.
    safe_alternative: str   # concrete suggestion
    turns_path: str         # "green" if fixed


@dataclass
class BPFlow:
    """A complete source→sink flow with color and fix annotation."""
    flow_id: str
    color: str
    source_label: str
    sink_label: str
    sink_kind: str
    transform_labels: list[str]
    trust_claims: list[str]
    trust_earned: list[str]
    risk_score: float
    minimum_replacement: MinimumReplacement | None
    verdict: str
    is_obligation: bool = False


@dataclass
class Blueprint:
    """
    The complete map of what an artifact does.
    Produced by analyze_blueprint() over any LBE result.
    """
    artifact_id: str
    language: str
    parse_confidence: str

    # Graph structure
    nodes: list[BPNode] = field(default_factory=list)
    edges: list[BPEdge] = field(default_factory=list)

    # Semantic flows (colored)
    flows: list[BPFlow] = field(default_factory=list)

    # High-level summary
    callable_names: list[str] = field(default_factory=list)
    source_kinds: list[str] = field(default_factory=list)
    sink_kinds: list[str] = field(default_factory=list)
    obligation_kinds: list[str] = field(default_factory=list)

    # Risk surface at a glance
    risk_surface: dict[str, float] = field(default_factory=dict)  # sink_kind → max_risk
    red_paths: int = 0
    yellow_paths: int = 0
    green_paths: int = 0
    purple_paths: int = 0

    def to_mermaid(self) -> str:
        """
        Render as a color-coded Mermaid flowchart.
        Red edges = dangerous untrusted paths.
        Yellow edges = wrapper theater.
        Green edges = validated.
        Purple = obligation violations.
        ★ marker on minimum replacement node.
        """
        lines = ["flowchart TD"]

        # Node definitions
        _seen: set[str] = set()
        for n in self.nodes:
            if n.node_id in _seen:
                continue
            _seen.add(n.node_id)
            safe_label = _mermaid_escape(n.label[:55])
            shape = _mermaid_shape(n.kind)
            lines.append(f"    {n.node_id}{shape[0]}\"{safe_label}\"{shape[1]}:::{n.kind}_{n.color}")

        # Blank line
        lines.append("")

        # Edge definitions
        for e in self.edges:
            safe_label = _mermaid_escape(e.label[:30])
            lines.append(f"    {e.from_id} -->|\"{safe_label}\"| {e.to_id}")

        # Blank line
        lines.append("")

        # Class definitions (color scheme)
        lines += [
            "    %% ── Color scheme ─────────────────────────────────────────",
            "    classDef source_red      fill:#ff6b6b,stroke:#cc0000,color:#fff",
            "    classDef source_green    fill:#51cf66,stroke:#2f9e44,color:#fff",
            "    classDef source_gray     fill:#adb5bd,stroke:#868e96,color:#fff",
            "    classDef transform_red   fill:#ffd43b,stroke:#e67700,color:#222",
            "    classDef transform_yellow fill:#ffa94d,stroke:#e67700,color:#222",
            "    classDef transform_green  fill:#8ce99a,stroke:#2f9e44,color:#222",
            "    classDef transform_gray   fill:#dee2e6,stroke:#adb5bd,color:#222",
            "    classDef sink_red        fill:#c92a2a,stroke:#7f1d1d,color:#fff,font-weight:bold",
            "    classDef sink_yellow     fill:#e67700,stroke:#7c3300,color:#fff",
            "    classDef sink_green      fill:#2f9e44,stroke:#1a5928,color:#fff",
            "    classDef sink_gray       fill:#495057,stroke:#343a40,color:#fff",
            "    classDef validation_green fill:#12b886,stroke:#087f5b,color:#fff",
            "    classDef validation_gray  fill:#12b886,stroke:#087f5b,color:#fff",
            "    classDef claim_yellow    fill:#fab005,stroke:#7c6000,color:#222",
            "    classDef obligation_purple fill:#ae3ec9,stroke:#6741d9,color:#fff",
            "    classDef callable_gray   fill:#e9ecef,stroke:#ced4da,color:#333",
        ]

        # Add min-replacement annotations as comments
        for flow in self.flows:
            if flow.minimum_replacement:
                mr = flow.minimum_replacement
                lines.append(
                    f"    %% ★ MIN-REPLACE [{mr.target_node_id}]: {mr.what_to_do[:60]}"
                )

        return "\n".join(lines)

    def to_summary(self) -> str:
        """Human-readable behavioral summary."""
        parts = [
            f"Blueprint: {self.artifact_id}",
            f"Language:  {self.language} (confidence: {self.parse_confidence})",
            f"",
            f"Callables: {', '.join(self.callable_names) or 'none detected'}",
            f"Sources:   {', '.join(self.source_kinds) or 'none detected'}",
            f"Sinks:     {', '.join(self.sink_kinds) or 'none detected'}",
            f"",
            f"Path summary:",
            f"  RED    (tainted → dangerous): {self.red_paths}",
            f"  YELLOW (wrapper theater):      {self.yellow_paths}",
            f"  GREEN  (validated):            {self.green_paths}",
            f"  PURPLE (obligation violated):  {self.purple_paths}",
        ]
        for flow in self.flows:
            if flow.color in (PathColor.RED, PathColor.YELLOW):
                parts.append(f"")
            if flow.color == PathColor.RED:
                parts.append(f"  ● RED: {flow.verdict}")
                if flow.minimum_replacement:
                    mr = flow.minimum_replacement
                    parts.append(f"    ★ Fix at line {mr.line}: {mr.what_to_do}")
                    parts.append(f"      → {mr.safe_alternative}")
            elif flow.color == PathColor.YELLOW:
                parts.append(f"  ● YELLOW (wrapper theater): {flow.verdict}")
                if flow.minimum_replacement:
                    mr = flow.minimum_replacement
                    parts.append(f"    ★ Fix: {mr.what_to_do}")
            elif flow.color == PathColor.PURPLE:
                parts.append(f"  ● PURPLE: {flow.verdict}")
        if self.obligation_kinds:
            parts.append(f"")
            parts.append(f"Unfulfilled obligations: {', '.join(self.obligation_kinds)}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "artifact_id":     self.artifact_id,
            "language":        self.language,
            "parse_confidence":self.parse_confidence,
            "callable_names":  self.callable_names,
            "source_kinds":    self.source_kinds,
            "sink_kinds":      self.sink_kinds,
            "risk_surface":    self.risk_surface,
            "red_paths":       self.red_paths,
            "yellow_paths":    self.yellow_paths,
            "green_paths":     self.green_paths,
            "purple_paths":    self.purple_paths,
            "obligation_kinds":self.obligation_kinds,
            "flows": [
                {
                    "flow_id":     f.flow_id,
                    "color":       f.color,
                    "source":      f.source_label,
                    "sink":        f.sink_label,
                    "sink_kind":   f.sink_kind,
                    "transforms":  f.transform_labels,
                    "risk_score":  f.risk_score,
                    "verdict":     f.verdict,
                    "minimum_replacement": {
                        "line":             f.minimum_replacement.line,
                        "target":           f.minimum_replacement.target_label,
                        "what_to_do":       f.minimum_replacement.what_to_do,
                        "safe_alternative": f.minimum_replacement.safe_alternative,
                    } if f.minimum_replacement else None,
                }
                for f in self.flows
            ],
            "mermaid": self.to_mermaid(),
        }


# ── Blueprint construction from UniversalIR + blobs ──────────────────────────

def build_blueprint(
    ir: "UniversalIR",
    flows: "list[UTaintFlow]",
    blobs: list[dict],
    artifact_id: str = "",
) -> Blueprint:
    """
    Build Blueprint from UniversalIR + taint flows + blob outputs.
    Called by analyze_blueprint() — the main entry point.
    """
    bp = Blueprint(
        artifact_id=artifact_id,
        language=ir.language_guess,
        parse_confidence=ir.parse_confidence,
    )

    node_ctr = [0]

    def nid(prefix: str) -> str:
        node_ctr[0] += 1
        return f"{prefix}{node_ctr[0]}"

    # ── Callable nodes (gray — structural skeleton) ───────────────────────────
    # Extract from IR sources/sinks line numbers to infer callables
    # (UniversalIR doesn't track callables directly — reconstruct from pattern)
    callable_matches = re.findall(
        r'(?:def|fn|func|function|public\s+\w+|void|int)\s+(\w+)\s*\(',
        "\n".join([s.text for s in ir.sources + ir.sinks] if ir.sources or ir.sinks else []),
    )
    bp.callable_names = list(dict.fromkeys(callable_matches))[:10]

    # ── Source nodes ──────────────────────────────────────────────────────────
    src_nodes: dict[int, str] = {}  # line → node_id
    for src in ir.sources:
        n_id = nid("SRC")
        src_nodes[src.line] = n_id
        color = PathColor.RED if not ir.validations else PathColor.GRAY
        bp.nodes.append(BPNode(
            node_id=n_id,
            label=f"⬇ {src.label[:45]}",
            kind="source",
            color=color,
            line=src.line,
            detail=src.text[:80],
        ))
        if src.label not in bp.source_kinds:
            bp.source_kinds.append(src.label)

    # ── Validation nodes ──────────────────────────────────────────────────────
    val_nodes: dict[int, str] = {}
    for val in ir.validations:
        n_id = nid("VAL")
        val_nodes[val.line] = n_id
        bp.nodes.append(BPNode(
            node_id=n_id,
            label=f"✓ {val.label[:45]}",
            kind="validation",
            color=PathColor.GREEN,
            line=val.line,
        ))

    # ── Trust claim nodes ─────────────────────────────────────────────────────
    clm_nodes: dict[int, str] = {}
    for clm in ir.claims:
        n_id = nid("CLM")
        clm_nodes[clm.line] = n_id
        bp.nodes.append(BPNode(
            node_id=n_id,
            label=f"⚠ {clm.text[:45]}",
            kind="claim",
            color=PathColor.YELLOW,
            line=clm.line,
        ))

    # ── Transform nodes ───────────────────────────────────────────────────────
    xfm_nodes: dict[int, str] = {}
    for xfm in ir.transforms:
        n_id = nid("XFM")
        xfm_nodes[xfm.line] = n_id
        # Color depends on whether we have validations
        color = PathColor.RED if not ir.validations else PathColor.GRAY
        bp.nodes.append(BPNode(
            node_id=n_id,
            label=f"⟳ {xfm.label[:45]}",
            kind="transform",
            color=color,
            line=xfm.line,
        ))

    # ── Sink nodes + flows ────────────────────────────────────────────────────
    snk_nodes: dict[int, str] = {}
    for blob in blobs:
        for sink_rec in blob.get("sinks", []):
            snk_line = sink_rec.get("line", 0)
            if snk_line in snk_nodes:
                continue

            sink_kind = sink_rec.get("sink_kind", "Unknown")
            tainted = sink_rec.get("tainted", False)
            has_claims = bool(blob.get("trust_claims"))
            has_earned = bool(blob.get("trust_earned"))

            if tainted and not has_earned:
                color = PathColor.YELLOW if has_claims else PathColor.RED
            else:
                color = PathColor.GREEN

            n_id = nid("SNK")
            snk_nodes[snk_line] = n_id
            label = f"{'⛔' if color==PathColor.RED else '⚡' if color==PathColor.YELLOW else '✅'} {sink_kind}"
            bp.nodes.append(BPNode(
                node_id=n_id,
                label=label,
                kind="sink",
                color=color,
                line=snk_line,
                detail=blob.get("verdict", "")[:80],
            ))

            if sink_kind not in bp.sink_kinds:
                bp.sink_kinds.append(sink_kind)
            bp.risk_surface[sink_kind] = max(
                bp.risk_surface.get(sink_kind, 0.0),
                blob.get("risk_score", 0.0)
            )

    # ── Obligation nodes ──────────────────────────────────────────────────────
    obl_nodes: dict[str, str] = {}
    for obl in ir.obligations:
        if obl.fulfillment_found:
            continue
        n_id = nid("OBL")
        obl_nodes[obl.kind] = n_id
        bp.nodes.append(BPNode(
            node_id=n_id,
            label=f"⚑ OBLIGATION: {obl.kind[:40]}",
            kind="obligation",
            color=PathColor.PURPLE,
            line=obl.acquisition_line,
            detail=obl.description[:100],
        ))
        bp.obligation_kinds.append(obl.kind)

    # ── Build edges from flows ────────────────────────────────────────────────
    for flow in flows:
        src_line = flow.source_node.line
        snk_line = flow.sink_node.line
        has_earned = bool(flow.earned_trust)
        has_claims = bool(flow.claims)

        if src_line in src_nodes and snk_line in snk_nodes:
            src_id = src_nodes[src_line]
            snk_id = snk_nodes[snk_line]

            # Determine edge path color
            if has_earned:
                edge_color = PathColor.GREEN
                edge_label = "validated"
            elif has_claims:
                edge_color = PathColor.YELLOW
                edge_label = "claimed (unverified)"
            else:
                edge_color = PathColor.RED
                edge_label = "tainted"

            # Check for transforms between source and sink
            prev_id = src_id
            for xfm in sorted(flow.transforms, key=lambda t: t.line):
                if xfm.line in xfm_nodes:
                    x_id = xfm_nodes[xfm.line]
                    bp.edges.append(BPEdge(prev_id, x_id, edge_label, edge_color))
                    prev_id = x_id

            # Check for validations between source and sink
            for val_line, val_id in sorted(val_nodes.items()):
                if src_line < val_line < snk_line:
                    bp.edges.append(BPEdge(prev_id, val_id, "validates", PathColor.GREEN))
                    prev_id = val_id
                    edge_color = PathColor.GREEN
                    edge_label = "validated"

            bp.edges.append(BPEdge(prev_id, snk_id, edge_label, edge_color))

    # ── Build BPFlow objects ──────────────────────────────────────────────────
    flow_id_ctr = [0]
    for blob in blobs:
        flow_id_ctr[0] += 1
        sink_recs = blob.get("sinks", [])
        if not sink_recs:
            continue

        sink_rec = sink_recs[0]
        tainted = sink_rec.get("tainted", False)
        has_claims = bool(blob.get("trust_claims"))
        has_earned = bool(blob.get("trust_earned"))

        if tainted and not has_earned:
            color = PathColor.YELLOW if has_claims else PathColor.RED
        else:
            color = PathColor.GREEN

        # Minimum replacement logic
        mr = None
        sink_kind = sink_rec.get("sink_kind", "Unknown")
        sink_line = sink_rec.get("line", 0)
        if color in (PathColor.RED, PathColor.YELLOW):
            transforms = blob.get("transform_chain", [])
            # Min replacement = last transform if present, else the sink itself
            if transforms:
                last_transform = transforms[-1]
                mr = MinimumReplacement(
                    target_node_id=_find_xfm_node(xfm_nodes, last_transform),
                    target_label=last_transform,
                    line=_extract_line(last_transform),
                    what_to_do=_suggest_fix_transform(last_transform, sink_kind),
                    safe_alternative=_suggest_safe_alternative(sink_kind, transforms),
                    turns_path=PathColor.GREEN,
                )
            else:
                mr = MinimumReplacement(
                    target_node_id=snk_nodes.get(sink_line, "SNK?"),
                    target_label=sink_kind,
                    line=sink_line,
                    what_to_do=f"add validation before {sink_kind} call",
                    safe_alternative=_suggest_safe_alternative(sink_kind, []),
                    turns_path=PathColor.GREEN,
                )

        sources = blob.get("entry_sources", [])
        bp_flow = BPFlow(
            flow_id=f"F{flow_id_ctr[0]:04d}",
            color=color,
            source_label=sources[0]["source"] if sources else "?",
            sink_label=sink_rec.get("var", sink_kind)[:50],
            sink_kind=sink_kind,
            transform_labels=blob.get("transform_chain", [])[:4],
            trust_claims=blob.get("trust_claims", []),
            trust_earned=blob.get("trust_earned", []),
            risk_score=blob.get("risk_score", 0.0),
            minimum_replacement=mr,
            verdict=blob.get("verdict", ""),
        )
        bp.flows.append(bp_flow)

        if color == PathColor.RED:    bp.red_paths += 1
        elif color == PathColor.YELLOW: bp.yellow_paths += 1
        elif color == PathColor.GREEN:  bp.green_paths += 1

    # Obligation flows
    for obl in ir.obligations:
        if obl.fulfillment_found:
            continue
        flow_id_ctr[0] += 1
        obl_map = {
            "VALIDATE_BEFORE_USE":     ("QueryExec",  0.85),
            "CONSTANT_TIME_COMPARE":   ("TimingOracle",0.82),
            "COMMIT_AFTER_WRITE":      ("QueryExec",  0.75),
            "SESSION_BEFORE_REDIRECT": ("Redirect",   0.80),
            "TOKEN_REVOKE_BEFORE_ROTATE":("TokenIssue",0.78),
            "GOROUTINE_CANCELLATION":  ("GoroutineLeak",0.80),
            "NO_REUSE_AFTER_FREE":     ("MemorySafety",0.92),
            "SAFE_MEMORY_ARITHMETIC":  ("IntegerOverflow",0.85),
            "PROTOTYPE_GUARD":         ("PrototypePollution",0.88),
            "CSPRNG_FOR_SECRETS":      ("WeakRandomness",0.88),
            "CSRF_TOKEN_IN_CALLBACK":  ("AuthStateMutation",0.82),
            "TOKEN_EXPIRY_AFTER_RESET":("TokenIssue", 0.78),
        }
        sk, risk = obl_map.get(obl.kind, ("Unknown", 0.75))
        mr = MinimumReplacement(
            target_node_id=obl_nodes.get(obl.kind, "OBL?"),
            target_label=obl.kind,
            line=obl.acquisition_line,
            what_to_do=_obligation_fix(obl.kind),
            safe_alternative=_obligation_safe_alt(obl.kind),
            turns_path=PathColor.GREEN,
        )
        bp.flows.append(BPFlow(
            flow_id=f"F{flow_id_ctr[0]:04d}",
            color=PathColor.PURPLE,
            source_label="structural",
            sink_label=obl.kind,
            sink_kind=sk,
            transform_labels=[],
            trust_claims=[],
            trust_earned=[],
            risk_score=risk,
            minimum_replacement=mr,
            verdict=f"OBLIGATION VIOLATED: {obl.description[:70]}",
            is_obligation=True,
        ))
        bp.purple_paths += 1

    return bp


# ── Blueprint from Python LBE paths ──────────────────────────────────────────

def build_blueprint_from_lbe(
    lbe_result: "LBEResult",
    artifact_id: str = "",
) -> Blueprint:
    """
    Build Blueprint from a Python-AST LBE result (lbe_pilot.LBEResult).
    Converts PathState + Blob objects into Blueprint nodes and flows.
    """
    from singularity_works.lbe_universal import (
        UniversalIR, UNode, UTaintFlow, UObligation, lower_universal, walk_universal
    )

    # Build a minimal UniversalIR from the Python LBE IR to reuse build_blueprint
    # We use the ForgeIR from lbe_pilot as the authoritative source
    ir = lbe_result.ir
    code = ir.content if hasattr(ir, 'content') else ""

    # Convert Python ForgeIR to UniversalIR-compatible structure
    uni_ir = lower_universal(code, artifact_id)
    uni_ir.language_guess = "python"
    uni_ir.parse_confidence = "parsed"  # Python AST = certain

    blobs = [b.to_dict() for b in lbe_result.blobs]
    flows = walk_universal(uni_ir, code)

    return build_blueprint(uni_ir, flows, blobs, artifact_id)


# ── Main entry point ──────────────────────────────────────────────────────────

def analyze_blueprint(code: str, artifact_id: str = "") -> Blueprint:
    """
    Complete pipeline: code → UniversalIR → flows → blobs → Blueprint.
    This is the top-level LBE entry point that produces the map.
    """
    from singularity_works.lbe_universal import lower_universal, walk_universal, emit_universal_blobs

    if not artifact_id:
        artifact_id = "A-" + hashlib.sha256(code.encode()).hexdigest()[:8]

    ir = lower_universal(code, artifact_id)
    flows = walk_universal(ir, code)
    blobs = emit_universal_blobs(ir, flows, artifact_id)

    return build_blueprint(ir, flows, blobs, artifact_id)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mermaid_escape(s: str) -> str:
    """Escape characters that break Mermaid syntax."""
    return (s.replace('"', "'")
             .replace('<', '&lt;')
             .replace('>', '&gt;')
             .replace('{', '[')
             .replace('}', ']')
             .replace('(', '[')
             .replace(')', ']'))


def _mermaid_shape(kind: str) -> tuple[str, str]:
    """Return Mermaid node shape open/close brackets for a kind."""
    shapes = {
        "source":     ("[/", "\\]"),   # parallelogram
        "sink":       ("[(", ")]"),    # stadium
        "transform":  ("[", "]"),      # rectangle
        "validation": ("([", "])"),    # rounded rectangle
        "claim":      ("{", "}"),      # diamond
        "obligation": ("{{", "}}"),    # hexagon
        "callable":   ("[[", "]]"),    # subroutine
    }
    return shapes.get(kind, ("[", "]"))


def _extract_line(transform_label: str) -> int:
    """Extract line number from 'TransformKind@L42' labels."""
    m = re.search(r'@L(\d+)', transform_label)
    return int(m.group(1)) if m else 0


def _find_xfm_node(xfm_nodes: dict[int, str], transform_label: str) -> str:
    line = _extract_line(transform_label)
    return xfm_nodes.get(line, "XFM?")


def _suggest_fix_transform(transform_label: str, sink_kind: str) -> str:
    """Suggest what to replace at the transform node."""
    if "Concat" in transform_label or "Compose" in transform_label or "f-string" in transform_label:
        if "Query" in sink_kind or "SQL" in sink_kind:
            return "replace string composition with parameterized query placeholder"
        return "replace string interpolation with safe encoding/escaping"
    if "Decode" in transform_label:
        return "validate decoded content against schema before passing to sink"
    if "Format" in transform_label:
        return "use named format with allowlist rather than raw interpolation"
    return f"add validation/sanitization before {sink_kind}"


def _suggest_safe_alternative(sink_kind: str, transforms: list[str]) -> str:
    """Concrete safe alternative suggestion for the sink."""
    alts = {
        "QueryExec":         'Use parameterized query: execute("SELECT ... WHERE x = %s", (val,))',
        "CommandExec":       "Use allowlist check before subprocess.run(); avoid shell=True",
        "OutboundRequest":   "Validate hostname against allowlist before requests.get()",
        "RenderInline":      "Use render_template() with Jinja2 autoescape, not Template(f-string)",
        "LDAPQuery":         "Use LDAP escape_filter_chars() before building search filter",
        "XPathExec":         "Use parameterized XPath or escape xpath.escape() before query",
        "UnknownEffect":     "Validate and sanitize input before passing to this call",
        "DynamicDispatch":   "Use allowlist dict instead of getattr(module, user_input)",
        "ReflectionExec":    "Use explicit class registry; never pass user input to Class.forName()",
        "AuthStateMutation": "Verify current_user.id == resource.owner_id before mutation",
        "FileWrite":         "Normalize path with os.path.realpath() and verify prefix",
    }
    return alts.get(sink_kind, f"Add validation gate before {sink_kind} call")


def _obligation_fix(kind: str) -> str:
    fixes = {
        "GOROUTINE_CANCELLATION":    "add context.Context parameter and select ctx.Done() case",
        "NO_REUSE_AFTER_FREE":       "remove the unsafe dereference after drop(); use Arc/Rc instead",
        "SAFE_MEMORY_ARITHMETIC":    "use __builtin_umul_overflow() or check for SIZE_MAX/UINT_MAX before malloc",
        "PROTOTYPE_GUARD":           "add: if (key === '__proto__' || key === 'constructor') continue;",
        "CONSTANT_TIME_COMPARE":     "replace == with hmac.compare_digest(a, b)",
        "COMMIT_AFTER_WRITE":        "add db.session.commit() or use transaction context manager",
        "SESSION_BEFORE_REDIRECT":   "call login_user() or session[...] = before redirect()",
        "CSRF_TOKEN_IN_CALLBACK":    "validate request.args.get('state') == session['oauth_state']",
        "TOKEN_EXPIRY_AFTER_RESET":  "delete or mark token as used after set_password() completes",
        "TOKEN_REVOKE_BEFORE_ROTATE":"call revoke(old_token) before issuing create_refresh_token()",
        "CSPRNG_FOR_SECRETS":        "replace random.random() with secrets.token_urlsafe(32)",
        "VALIDATE_BEFORE_USE":       "add input validation before the dangerous sink call",
    }
    return fixes.get(kind, f"discharge the {kind} obligation before the acquisition point exits scope")


def _obligation_safe_alt(kind: str) -> str:
    alts = {
        "GOROUTINE_CANCELLATION": (
            "func fetchData(ctx context.Context, url string) string { ... "
            "select { case <-ctx.Done(): return '' } }"
        ),
        "NO_REUSE_AFTER_FREE":       "let val = Arc::new(data); // use Arc<T> instead of raw ptr after drop",
        "SAFE_MEMORY_ARITHMETIC":    "size_t total; if (__builtin_umul_overflow(count, elem_size, &total)) abort();",
        "PROTOTYPE_GUARD": (
            "Use hasOwnProperty + prototype key check. "
            "See OWASP prototype pollution prevention guide."
        ),
        "CONSTANT_TIME_COMPARE":     "return hmac.compare_digest(expected.encode(), candidate.encode())",
        "COMMIT_AFTER_WRITE":        "with db.session.begin(): db.add(user)  # auto-commits on exit",
        "CSRF_TOKEN_IN_CALLBACK":    "if request.args.get('state') != session.pop('oauth_state', None): abort(403)",
        "CSPRNG_FOR_SECRETS":        "token = secrets.token_urlsafe(32)",
    }
    return alts.get(kind, "See security documentation for safe discharge pattern")
