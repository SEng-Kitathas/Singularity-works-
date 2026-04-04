"""
Logic Blueprint Engine — Python Lowering Pilot
Version: 2026-04-04 · v1.23

Complete round-trip: Python source → Forge IR (4 layers) → Path walk → Blob emission.

This is not a replacement for the front gate. It is the substrate proof:
can Forge IR represent a real path faithfully enough that a human reading
the blob understands what the code does without reading the code?

Target: SQLi family (chosen because battery gives 100% ground truth).
Designed to generalize — the same path walker works for any sink family.

Architecture:
    lower(code)           → ForgeIR
    walk_paths(ir)        → list[PathState]
    emit_blobs(paths)     → list[Blob]
    analyze(code)         → LBEResult

Forge IR Layers (from spec v0.1):
    Layer 1: Structural  — modules, callables, blocks, graph topology
    Layer 2: Operational — calls, data movement, effects
    Layer 3: Semantic    — trust, taint, ownership, invariants
    Layer 4: Annotation  — roles, suspicion, confidence
"""
from __future__ import annotations

import ast
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


# ── Layer 1: Structural ───────────────────────────────────────────────────

@dataclass
class Symbol:
    symbol_id: str
    name: str
    kind: str           # param | local | import | global | unknown
    declared_type: str = "unknown"
    inferred_type: str = "unknown"
    scope_owner: str = ""
    trust_state: str = "untrusted"      # untrusted | claimed_safe | narrowed | verified
    ownership_state: str = "owned"      # owned | borrowed | external | unknown
    invariant_state: str = "unknown"    # unknown | validated | violated


@dataclass
class Callable:
    callable_id: str
    module_id: str
    kind: str           # function | method | lambda | route_handler
    name: str
    parameters: list[str]
    local_symbols: dict[str, Symbol]
    entry_node_id: str
    exit_node_ids: list[str]
    declared_effects: list[str]
    inferred_effects: list[str]
    parse_confidence: str = "parsed"    # parsed | partial | recovered | unknown
    line: int = 0


@dataclass
class IRNode:
    node_id: str
    node_kind: str      # see node taxonomy below
    callable_id: str
    line: int
    properties: dict[str, Any] = field(default_factory=dict)
    # Node kind taxonomy (from Forge IR spec):
    # Control:   Entry Exit Branch Loop Merge Return ExceptionEdge
    # Source:    QueryArg FormField CookieRead HeaderRead BodyRead
    #            EnvRead ConfigRead DatabaseRead UnknownSource
    # Transform: StringConcat TemplateCompose QueryCompose Encode Decode
    #            Escape Hash WrapperCall UnknownTransform
    # Effect:    QueryExec DatabaseWrite OutboundRequest Redirect
    #            RenderInline CommandExec AuthStateMutation TokenIssue
    #            ResponseBodyWrite UnknownEffect
    # Recovery:  RecoveredPhase UnknownStructuredNode


@dataclass
class IREdge:
    edge_id: str
    edge_kind: str      # ControlFlow | DataFlow | TrustClaim | TrustEarned
                        # Narrowing | WrapperOf | RoleSupports | RoleConflicts
    source_id: str
    target_id: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ForgeIR:
    """Complete 4-layer Forge IR for one artifact."""
    ir_version: str = "0.1"
    source_kind: str = "unknown"
    parse_status: str = "parsed"    # parsed | partial | recovered | opaque
    artifact_id: str = ""

    # Layer 1: Structural
    module_id: str = ""
    callables: list[Callable] = field(default_factory=list)
    nodes: list[IRNode] = field(default_factory=list)
    edges: list[IREdge] = field(default_factory=list)
    import_ids: list[str] = field(default_factory=list)
    unresolved_refs: list[str] = field(default_factory=list)

    # Layer 2: Operational
    sources: list[IRNode] = field(default_factory=list)     # source nodes
    sinks: list[IRNode] = field(default_factory=list)       # effect/sink nodes
    transforms: list[IRNode] = field(default_factory=list)  # transform nodes

    # Layer 3: Semantic
    trust_annotations: list[dict] = field(default_factory=list)
    taint_flows: list[dict] = field(default_factory=list)
    ownership_annotations: list[dict] = field(default_factory=list)
    invariant_annotations: list[dict] = field(default_factory=list)

    # Layer 4: Annotation
    role_hints: list[str] = field(default_factory=list)
    suspicion_markers: list[str] = field(default_factory=list)
    wrapper_theater: bool = False
    analysis_metadata: dict = field(default_factory=dict)

    def node_by_id(self, nid: str) -> IRNode | None:
        return next((n for n in self.nodes if n.node_id == nid), None)


# ── Layer 3: Path State ───────────────────────────────────────────────────

@dataclass
class PathState:
    """Live semantic state carried by the walker as it traverses a path."""
    path_id: str
    callable_id: str
    current_node_id: str

    # Trust axis
    trust_overall: str = "untrusted"        # untrusted | claimed_safe | narrowed | verified
    trust_claims: list[str] = field(default_factory=list)
    trust_earned: list[str] = field(default_factory=list)
    trust_drops: list[str] = field(default_factory=list)

    # Taint axis
    tainted_symbols: set[str] = field(default_factory=set)
    sanitized_symbols: set[str] = field(default_factory=set)
    sanitization_claims: list[str] = field(default_factory=list)
    sanitization_proofs: list[str] = field(default_factory=list)

    # Symbol state map: name → current trust/taint state
    symbol_states: dict[str, dict] = field(default_factory=dict)

    # Effect accumulation
    effects_reached: list[str] = field(default_factory=list)
    sinks_reached: list[dict] = field(default_factory=list)

    # Source tracking
    entry_sources: list[dict] = field(default_factory=list)
    transform_chain: list[str] = field(default_factory=list)

    # Ambiguity and confidence
    unknowns: list[str] = field(default_factory=list)
    confidence: str = "high-confidence inferred"

    def is_tainted(self, var: str) -> bool:
        return var in self.tainted_symbols and var not in self.sanitized_symbols

    def record_taint(self, var: str, source: str, line: int) -> None:
        self.tainted_symbols.add(var)
        self.entry_sources.append({
            "source": source, "var": var, "line": line,
            "trust": "untrusted", "confidence": "parsed"
        })

    def record_transform(self, kind: str, input_var: str, output_var: str) -> None:
        self.transform_chain.append(f"{kind}({input_var}→{output_var})")
        # Taint propagates through transforms unless sanitization is proven
        if input_var in self.tainted_symbols:
            self.tainted_symbols.add(output_var)

    def record_sink(self, sink_kind: str, var: str, line: int) -> None:
        self.effects_reached.append(sink_kind)
        self.sinks_reached.append({
            "sink_kind": sink_kind, "var": var, "line": line,
            "tainted": self.is_tainted(var),
        })


# ── Blob (emitted artifact) ───────────────────────────────────────────────

@dataclass
class Blob:
    """
    Primary artifact emitted by the LBE at a path terminal or sink boundary.
    Semantic compression of a behavior slice — not a raw trace.
    """
    blob_id: str
    path_id: str
    checkpoint_kind: str    # terminal | sink_boundary | ambiguity_checkpoint
    callable_id: str
    module_id: str

    # Behavior content
    entry_sources: list[dict]
    transform_chain: list[str]
    effects: list[str]
    sinks: list[dict]

    # Trust state
    trust_claims: list[str]
    trust_earned: list[str]
    trust_state: str        # untrusted | claimed_safe | narrowed | verified
    wrapper_theater: bool = False

    # Scores (0.0–1.0)
    risk_score: float = 0.0
    deception_score: float = 0.0
    legitimacy_score: float = 0.0
    ambiguity_score: float = 0.0
    suspicious_clean_score: float = 0.0

    confidence_class: str = "high-confidence inferred"
    verdict: str = ""
    notes: list[str] = field(default_factory=list)
    lineage: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "blob_id": self.blob_id,
            "path_id": self.path_id,
            "checkpoint_kind": self.checkpoint_kind,
            "callable_id": self.callable_id,
            "module_id": self.module_id,
            "entry_sources": self.entry_sources,
            "transform_chain": self.transform_chain,
            "effects": self.effects,
            "sinks": self.sinks,
            "trust_claims": self.trust_claims,
            "trust_earned": self.trust_earned,
            "trust_state": self.trust_state,
            "wrapper_theater": self.wrapper_theater,
            "risk_score": round(self.risk_score, 3),
            "deception_score": round(self.deception_score, 3),
            "legitimacy_score": round(self.legitimacy_score, 3),
            "ambiguity_score": round(self.ambiguity_score, 3),
            "suspicious_clean_score": round(self.suspicious_clean_score, 3),
            "confidence_class": self.confidence_class,
            "verdict": self.verdict,
            "notes": self.notes,
        }


# ── LBE Result ────────────────────────────────────────────────────────────

@dataclass
class LBEResult:
    artifact_id: str
    ir: ForgeIR
    paths: list[PathState]
    blobs: list[Blob]
    elapsed_ms: float

    @property
    def highest_risk_blob(self) -> Blob | None:
        return max(self.blobs, key=lambda b: b.risk_score, default=None)

    @property
    def route_to_lbe_confirmed(self) -> bool:
        return any(b.risk_score > 0.5 for b in self.blobs)

    def summary(self) -> str:
        if not self.blobs:
            return "LBE: no sinks reached — path terminates clean"
        hrb = self.highest_risk_blob
        return (
            f"LBE: {len(self.blobs)} blob(s) emitted | "
            f"max_risk={hrb.risk_score:.2f} | "
            f"verdict={hrb.verdict}"
        )


# ── Python Lowering Pass ──────────────────────────────────────────────────

# Source node indicators
_REQUEST_SOURCES = {
    "args", "form", "json", "data", "values", "cookies", "headers", "files",
    "get_json", "view_args",
}

# Known dangerous sinks → IR node kind
_SINK_MAP = {
    "execute": "QueryExec",
    "executemany": "QueryExec",
    "raw": "QueryExec",
    "system": "CommandExec",
    "popen": "CommandExec",
    "render_template_string": "RenderInline",
    "render": "RenderInline",
    "redirect": "Redirect",
}

# Namespace-qualified sinks: only fire when called on these objects
_NAMESPACED_SINKS = {
    "requests": {"get": "OutboundRequest", "post": "OutboundRequest",
                 "put": "OutboundRequest", "patch": "OutboundRequest",
                 "delete": "OutboundRequest", "request": "OutboundRequest"},
    "httpx":    {"get": "OutboundRequest", "post": "OutboundRequest"},
    "urllib":   {"urlopen": "OutboundRequest"},
    "pickle":   {"loads": "UnknownEffect", "load": "UnknownEffect"},
    "yaml":     {"load": "UnknownEffect"},
    "subprocess": {"run": "CommandExec", "call": "CommandExec",
                   "Popen": "CommandExec", "check_output": "CommandExec"},
    "os":       {"system": "CommandExec", "popen": "CommandExec"},
}

# Transform operations
_TRANSFORM_MAP = {
    "format": "StringConcat",
    "join": "StringConcat",
    "replace": "StringConcat",
    "encode": "Encode",
    "decode": "Decode",
    "escape": "Escape",
    "quote": "Escape",
    "b64encode": "Encode",
    "b64decode": "Decode",
    "loads": "Decode",
    "dumps": "Encode",
}

# Trust-earning signals
_TRUST_EARNED_CALLS = {
    "escape", "quote_plus", "quote", "html.escape",
    "parameterize", "sanitize", "validate",
    "compare_digest", "verify", "check",
    "realpath", "abspath", "normpath",
}

# Trust claim signals (say safe, may not be)
_TRUST_CLAIM_NAMES = {
    "safe_", "_safe", "sanitized_", "_sanitized",
    "clean_", "_clean", "validated_", "_validated",
    "escaped_", "_escaped",
}


def _safe_parse(code: str) -> ast.AST | None:
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def _node_id(prefix: str, line: int, counter: list) -> str:
    counter[0] += 1
    return f"{prefix}-{line}-{counter[0]}"


def _is_request_source(node: ast.Attribute) -> bool:
    """Check if an attribute access is a request input source."""
    return (
        isinstance(node.value, ast.Name)
        and node.value.id == "request"
        and node.attr in _REQUEST_SOURCES
    )


def lower(code: str, artifact_id: str = "") -> ForgeIR:
    """
    Lower Python source into Forge IR.
    Layer 1 + 2 + 3 implementation. Layer 4 populated by walk_paths().
    """
    if not artifact_id:
        artifact_id = "M-" + hashlib.sha256(code.encode()).hexdigest()[:8]

    ir = ForgeIR(
        source_kind="python",
        artifact_id=artifact_id,
        module_id=artifact_id,
    )

    tree = _safe_parse(code)
    if tree is None:
        ir.parse_status = "partial"
        ir.analysis_metadata["parse_error"] = "SyntaxError"
        return ir

    counter = [0]

    # Layer 1: Structural — extract callables + imports
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            ir.import_ids.extend(n for n in names if n)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            c_id = f"C-{node.name}-{node.lineno}"
            params = [a.arg for a in node.args.args]

            # Build local symbols
            local_syms: dict[str, Symbol] = {}
            for p in params:
                local_syms[p] = Symbol(
                    symbol_id=f"S-{p}-{node.lineno}",
                    name=p, kind="param",
                    trust_state="untrusted",  # params from caller are untrusted by default
                    scope_owner=c_id,
                )

            # Walk function body to find assignments
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for t in child.targets:
                        if isinstance(t, ast.Name):
                            local_syms[t.id] = Symbol(
                                symbol_id=f"S-{t.id}-{child.lineno}",
                                name=t.id, kind="local",
                                scope_owner=c_id,
                            )

            kind = "function"
            # Check for route decorator
            for deco in node.decorator_list:
                deco_str = ast.unparse(deco) if hasattr(ast, "unparse") else ""
                if any(k in deco_str for k in ("route", "get", "post", "put", "delete", "patch")):
                    kind = "route_handler"

            callable_obj = Callable(
                callable_id=c_id,
                module_id=artifact_id,
                kind=kind,
                name=node.name,
                parameters=params,
                local_symbols=local_syms,
                entry_node_id=f"Entry-{node.lineno}",
                exit_node_ids=[],
                declared_effects=[],
                inferred_effects=[],
                line=node.lineno,
            )
            ir.callables.append(callable_obj)

            # Entry node
            ir.nodes.append(IRNode(
                node_id=f"Entry-{node.lineno}",
                node_kind="Entry",
                callable_id=c_id,
                line=node.lineno,
                properties={"name": node.name, "params": params},
            ))

    # Layer 2: Operational — walk all expressions for sources/transforms/sinks
    for fn_node in ast.walk(tree):
        if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        c_id = f"C-{fn_node.name}-{fn_node.lineno}"

        for child in ast.walk(fn_node):
            # Source nodes: request.args.get(...), request.form[...], etc.
            if isinstance(child, ast.Call):
                # Check for request.args.get() style
                func = child.func
                if (isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Attribute)
                        and _is_request_source(func.value)):
                    n = IRNode(
                        node_id=_node_id("Src", child.lineno, counter),
                        node_kind="QueryArg",
                        callable_id=c_id,
                        line=child.lineno,
                        properties={
                            "source": "request." + func.value.attr,
                            "key": (ast.unparse(child.args[0])
                                   if child.args else "?"),
                        },
                    )
                    ir.nodes.append(n)
                    ir.sources.append(n)

                # Sink detection
                sink_name = ""
                if isinstance(func, ast.Attribute):
                    sink_name = func.attr
                elif isinstance(func, ast.Name):
                    sink_name = func.id

                # Check simple sink map first
                sink_kind = _SINK_MAP.get(sink_name)
                # Then check namespace-qualified sinks
                if sink_kind is None and isinstance(func, ast.Attribute):
                    owner_str = ""
                    if isinstance(func.value, ast.Name):
                        owner_str = func.value.id
                    elif isinstance(func.value, ast.Attribute):
                        owner_str = func.value.attr
                    for ns, ns_sinks in _NAMESPACED_SINKS.items():
                        if ns in owner_str.lower() and sink_name in ns_sinks:
                            sink_kind = ns_sinks[sink_name]
                            break

                if sink_kind is not None:
                    if True:  # structure preserved
                        # Collect args as taint candidates
                        arg_reprs = []
                        for arg in child.args:
                            if hasattr(ast, "unparse"):
                                arg_reprs.append(ast.unparse(arg))
                        n = IRNode(
                            node_id=_node_id("Sink", child.lineno, counter),
                            node_kind=sink_kind,
                            callable_id=c_id,
                            line=child.lineno,
                            properties={
                                "sink_name": sink_name,
                                "args": arg_reprs[:3],
                            },
                        )
                        ir.nodes.append(n)
                        ir.sinks.append(n)

                # Transform detection
                if sink_name in _TRANSFORM_MAP:
                    tn = IRNode(
                        node_id=_node_id("Xfm", child.lineno, counter),
                        node_kind=_TRANSFORM_MAP[sink_name],
                        callable_id=c_id,
                        line=child.lineno,
                        properties={"op": sink_name},
                    )
                    ir.nodes.append(tn)
                    ir.transforms.append(tn)

            # F-string detection: f"...{var}..." → StringConcat + potential QueryCompose
            elif isinstance(child, ast.JoinedStr):
                has_var = any(isinstance(v, ast.FormattedValue)
                             for v in child.values)
                if has_var:
                    tn = IRNode(
                        node_id=_node_id("Xfm", child.lineno, counter),
                        node_kind="StringConcat",
                        callable_id=c_id,
                        line=child.lineno,
                        properties={"op": "f-string", "has_interpolation": True},
                    )
                    ir.nodes.append(tn)
                    ir.transforms.append(tn)

            # % formatting: "SELECT ... %s" % var → QueryCompose
            elif isinstance(child, ast.BinOp) and isinstance(child.op, ast.Mod):
                if isinstance(child.left, ast.Constant) and isinstance(child.left.value, str):
                    tn = IRNode(
                        node_id=_node_id("Xfm", child.lineno, counter),
                        node_kind="QueryCompose",
                        callable_id=c_id,
                        line=child.lineno,
                        properties={"op": "%-format", "template": child.left.value[:60]},
                    )
                    ir.nodes.append(tn)
                    ir.transforms.append(tn)

    # Layer 3: Semantic — annotate trust
    # Check for trust-earning calls
    for c in ast.walk(tree):
        if isinstance(c, ast.Call):
            fname = ""
            if isinstance(c.func, ast.Attribute):
                fname = c.func.attr
            elif isinstance(c.func, ast.Name):
                fname = c.func.id
            if fname in _TRUST_EARNED_CALLS:
                ir.trust_annotations.append({
                    "kind": "earned",
                    "call": fname,
                    "line": c.lineno,
                    "trust_type": "verified_" + fname,
                })

    # Check for trust claims (variable names suggesting safety)
    for fn_node in ast.walk(tree):
        if isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(fn_node):
                if isinstance(child, ast.Assign):
                    for t in child.targets:
                        if isinstance(t, ast.Name):
                            for claim in _TRUST_CLAIM_NAMES:
                                if t.id.startswith(claim) or t.id.endswith(claim.strip("_")):
                                    ir.trust_annotations.append({
                                        "kind": "claim",
                                        "var": t.id,
                                        "line": child.lineno,
                                        "claim_type": "naming_convention_safety",
                                    })

    return ir


# ── Path Walker ───────────────────────────────────────────────────────────

def walk_paths(ir: ForgeIR, code: str) -> list[PathState]:
    """
    Walk paths from sources to sinks, carrying PathState.

    For the pilot: one path per callable that has both sources and sinks.
    The full implementation will use bounded graph traversal.
    """
    paths: list[PathState] = []
    path_counter = [0]

    # Build a per-callable view
    callable_sources: dict[str, list[IRNode]] = {}
    callable_sinks: dict[str, list[IRNode]] = {}
    callable_transforms: dict[str, list[IRNode]] = {}

    for n in ir.sources:
        callable_sources.setdefault(n.callable_id, []).append(n)
    for n in ir.sinks:
        callable_sinks.setdefault(n.callable_id, []).append(n)
    for n in ir.transforms:
        callable_transforms.setdefault(n.callable_id, []).append(n)

    # Taint propagation via AST assignment chain
    taint_map = _build_taint_map(code)

    for callable_obj in ir.callables:
        c_id = callable_obj.callable_id
        sources = callable_sources.get(c_id, [])
        sinks = callable_sinks.get(c_id, [])

        if not sinks:
            continue  # no effect surface — no path of interest

        path_counter[0] += 1
        ps = PathState(
            path_id=f"P-{path_counter[0]}",
            callable_id=c_id,
            current_node_id=callable_obj.entry_node_id,
        )

        # Record entry sources from IR source nodes
        for src in sources:
            key = src.properties.get("key", "?")
            source_label = src.properties.get("source", "request")
            ps.record_taint(key, f"{source_label}.{key}", src.line)

        # Seed taint from taint_map's __request__ entries (variables assigned from request)
        # This bridges the gap between source-node key strings and actual variable names
        for req_var in taint_map.get("__request__", []):
            if req_var not in ps.tainted_symbols:
                ps.tainted_symbols.add(req_var)
                # Record as entry source if not already present
                already = any(s.get("var") == req_var for s in ps.entry_sources)
                if not already:
                    ps.entry_sources.append({
                        "source": "request", "var": req_var,
                        "line": sources[0].line if sources else 0,
                        "trust": "untrusted", "confidence": "parsed",
                    })

        # Propagate taint through assignment chains
        changed = True
        while changed:
            changed = False
            for tainted_var, derived_vars in taint_map.items():
                if tainted_var in ps.tainted_symbols:
                    for dv in derived_vars:
                        if dv not in ps.tainted_symbols:
                            ps.tainted_symbols.add(dv)
                            ps.transform_chain.append(f"assign({tainted_var}→{dv})")
                            changed = True

        # Record transforms in call order
        for xfm in sorted(callable_transforms.get(c_id, []), key=lambda n: n.line):
            kind = xfm.node_kind
            ps.transform_chain.append(f"{kind}@L{xfm.line}")

        # Check trust annotations in this callable's scope
        for ann in ir.trust_annotations:
            if ann.get("kind") == "earned":
                earned_call = ann.get("call", "")
                ps.trust_earned.append(f"verified_{earned_call}")
                # Mark the relevant symbol as sanitized if it's tainted
                # (conservative: only mark as sanitized if it's the only tainted var)
                if len(ps.tainted_symbols) == 1:
                    var = next(iter(ps.tainted_symbols))
                    ps.sanitized_symbols.add(var)
                    ps.sanitization_proofs.append(earned_call)

            elif ann.get("kind") == "claim":
                var = ann.get("var", "")
                ps.trust_claims.append(f"naming_convention:{var}")

        # Determine overall trust state
        if ps.trust_earned:
            ps.trust_overall = "narrowed"
        elif ps.trust_claims:
            ps.trust_overall = "claimed_safe"
        elif ps.tainted_symbols:
            ps.trust_overall = "untrusted"
        else:
            ps.trust_overall = "untrusted"  # no sources → conservative

        # Walk to sinks
        for sink in sorted(sinks, key=lambda n: n.line):
            # Determine which variables reach this sink
            sink_args = sink.properties.get("args", [])
            reaches_tainted = any(
                any(t in arg for t in ps.tainted_symbols)
                for arg in sink_args
            )
            # Also check if f-string or % format is in the transform chain
            # and sinks are DB queries — classic SQLi path
            has_string_compose = any(
                k in ps.transform_chain
                for k in ("StringConcat", "QueryCompose")
                if any(k in t for t in ps.transform_chain)
            )
            reaches_tainted = reaches_tainted or (
                sink.node_kind == "QueryExec" and
                any("Concat" in t or "Compose" in t or "f-string" in t
                    for t in ps.transform_chain)
            )

            taint_var = (
                next(iter(ps.tainted_symbols), "?")
                if reaches_tainted else "?"
            )
            ps.record_sink(sink.node_kind, taint_var, sink.line)

        if ps.sinks_reached:
            paths.append(ps)

    return paths


def _build_taint_map(code: str) -> dict[str, list[str]]:
    """
    Build a simple assignment-chain taint map.
    var_a = request.args.get('x')  → taint_map['x'] or taint_map['var_a'] = [...]
    var_b = f"...{var_a}..."       → if var_a tainted, var_b tainted
    """
    tree = _safe_parse(code)
    if tree is None:
        return {}

    # Map: var_name → list of vars derived from it
    derives: dict[str, list[str]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
            continue

        lhs = node.targets[0].id
        rhs = node.value

        # Find vars referenced in rhs
        rhs_vars = [n.id for n in ast.walk(rhs) if isinstance(n, ast.Name)]

        # If rhs contains request access, mark lhs as taint source
        rhs_str = ast.unparse(rhs) if hasattr(ast, "unparse") else ""
        if "request." in rhs_str:
            derives.setdefault("__request__", []).append(lhs)

        # If rhs references any variable, propagate taint
        for rv in rhs_vars:
            if rv != lhs:
                derives.setdefault(rv, []).append(lhs)

    return derives


# ── Blob Emitter ──────────────────────────────────────────────────────────

def emit_blobs(ir: ForgeIR, paths: list[PathState], starmap_metrics=None) -> list[Blob]:
    """Emit blobs at each sink boundary in each path."""
    blobs: list[Blob] = []
    blob_counter = [0]

    for ps in paths:
        for sink_rec in ps.sinks_reached:
            blob_counter[0] += 1
            sink_kind = sink_rec["sink_kind"]
            tainted = sink_rec["tainted"]
            sink_line = sink_rec.get("line", 0)

            # Score computation
            risk = _score_risk(sink_kind, tainted, ps)

            # StarMap geometric amplifier: apply systemic risk modifier
            # Uses Fiedler connectivity + evidence coherence + cross-domain signals
            # Replaces hand-tuned multipliers with geometric evidence synthesis
            if starmap_metrics is not None:
                amp = starmap_metrics.risk_amplifier
                risk = round(min(1.0, risk * amp), 3)
            deception = _score_deception(ps)
            # StarMap interference augments deception (contradictory evidence = higher deception signal)
            if starmap_metrics is not None and starmap_metrics.interference > 0:
                deception = round(min(1.0, deception + starmap_metrics.interference * 0.3), 3)
            legitimacy = _score_legitimacy(ps)
            ambiguity = _score_ambiguity(ps)
            # StarMap curvature augments ambiguity (diffuse findings = harder to localize)
            if starmap_metrics is not None and starmap_metrics.curvature > 0:
                ambiguity = round(min(1.0, ambiguity + starmap_metrics.curvature * 2.0), 3)
            suspicious_clean = _score_suspicious_clean(risk, ps)

            # Confidence class
            if risk > 0.7:
                confidence = "high-confidence inferred"
            elif risk > 0.4:
                confidence = "plausible"
            else:
                confidence = "high-confidence inferred"

            # Verdict
            verdict = _derive_verdict(sink_kind, tainted, ps, risk)

            blob = Blob(
                blob_id=f"B-{blob_counter[0]:04d}",
                path_id=ps.path_id,
                checkpoint_kind="sink_boundary",
                callable_id=ps.callable_id,
                module_id=ir.module_id,
                entry_sources=ps.entry_sources,
                transform_chain=ps.transform_chain,
                effects=[sink_kind],
                sinks=[sink_rec],
                trust_claims=ps.trust_claims,
                trust_earned=ps.trust_earned,
                trust_state=ps.trust_overall,
                wrapper_theater=bool(ps.trust_claims and not ps.trust_earned),
                risk_score=risk,
                deception_score=deception,
                legitimacy_score=legitimacy,
                ambiguity_score=ambiguity,
                suspicious_clean_score=suspicious_clean,
                confidence_class=confidence,
                verdict=verdict,
                notes=_build_notes(sink_kind, tainted, ps),
            )
            blobs.append(blob)

    return blobs


def _score_risk(sink_kind: str, tainted: bool, ps: PathState) -> float:
    base = {
        "QueryExec": 0.9,
        "CommandExec": 0.95,
        "RenderInline": 0.85,
        "OutboundRequest": 0.75,
        "Redirect": 0.70,
        "DatabaseWrite": 0.80,
        "AuthStateMutation": 0.85,
        "TokenIssue": 0.75,
        "UnknownEffect": 0.60,
    }.get(sink_kind, 0.5)

    if not tainted:
        base *= 0.2  # Not tainted — not currently exploitable via this path
    if ps.trust_earned:
        base *= 0.15  # Verified sanitization present
    # Note: trust_claims WITHOUT trust_earned = wrapper theater
    # Do NOT reduce risk for unearned claims — that would reward deception
    if "QueryCompose" in str(ps.transform_chain):
        base = min(1.0, base * 1.1)
    if "StringConcat" in str(ps.transform_chain) and sink_kind == "QueryExec":
        base = min(1.0, base * 1.1)
    # Parameterized query: tainted but no string composition → much lower risk
    # The taint reaches the query but as a bound parameter, not as string concat
    if sink_kind == "QueryExec" and tainted and not any(
        k in str(ps.transform_chain) for k in ("Concat", "Compose", "f-string")
    ):
        base *= 0.15  # Parameterized binding — taint is contained

    return round(min(1.0, base), 3)


def _score_deception(ps: PathState) -> float:
    """How much does the path use safety claims not backed by evidence?"""
    if ps.trust_claims and not ps.trust_earned:
        return 0.8
    if ps.trust_claims and ps.trust_earned:
        return 0.2
    return 0.0


def _score_legitimacy(ps: PathState) -> float:
    """How much earned trust evidence exists?"""
    if ps.trust_earned:
        return min(1.0, len(ps.trust_earned) * 0.4)
    if ps.sanitization_proofs:
        return min(1.0, len(ps.sanitization_proofs) * 0.3)
    return 0.0


def _score_ambiguity(ps: PathState) -> float:
    if ps.unknowns:
        return min(1.0, len(ps.unknowns) * 0.25)
    return 0.0


def _score_suspicious_clean(risk: float, ps: PathState) -> float:
    """Suspicious-clean: high effect surface but implausibly low risk signal."""
    if risk < 0.2 and ps.sinks_reached and not ps.tainted_symbols:
        return 0.6
    return 0.0


def _derive_verdict(sink_kind: str, tainted: bool, ps: PathState, risk: float) -> str:
    if not tainted:
        return f"Path reaches {sink_kind} — no taint flow detected on this path"
    if ps.trust_earned:
        return f"Path reaches {sink_kind} with taint — sanitization verified ({ps.trust_earned[0]})"
    if ps.trust_claims:
        return f"Path reaches {sink_kind} with taint — safety CLAIMED but not EARNED (wrapper theater risk)"
    if sink_kind == "QueryExec":
        return "TAINTED INPUT REACHES SQL SINK — SQL injection path confirmed"
    if sink_kind == "CommandExec":
        return "TAINTED INPUT REACHES COMMAND SINK — command injection path confirmed"
    if sink_kind == "RenderInline":
        return "TAINTED INPUT REACHES RENDER SINK — template injection path confirmed"
    return f"TAINTED INPUT REACHES {sink_kind} — {risk:.0%} risk"


def _build_notes(sink_kind: str, tainted: bool, ps: PathState) -> list[str]:
    notes = []
    if tainted and not ps.trust_earned:
        notes.append(
            f"Tainted symbols: {sorted(ps.tainted_symbols)!r} "
            f"reach {sink_kind} without verified sanitization"
        )
    if ps.transform_chain:
        notes.append(f"Transform chain: {' → '.join(ps.transform_chain[:6])}")
    if ps.trust_claims and not ps.trust_earned:
        notes.append(
            f"Trust claims present but unverified: {ps.trust_claims[:2]}"
        )
    return notes


# ── Main Entry Point ──────────────────────────────────────────────────────

def analyze(code: str, artifact_id: str = "", starmap_metrics=None) -> LBEResult:
    """
    Complete LBE analysis round-trip.
    Returns LBEResult with IR, paths, blobs, and timing.
    """
    t0 = time.perf_counter()

    if not artifact_id:
        artifact_id = "A-" + hashlib.sha256(code.encode()).hexdigest()[:8]

    ir = lower(code, artifact_id)
    paths = walk_paths(ir, code)
    blobs = emit_blobs(ir, paths, starmap_metrics=starmap_metrics)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return LBEResult(
        artifact_id=artifact_id,
        ir=ir,
        paths=paths,
        blobs=blobs,
        elapsed_ms=elapsed_ms,
    )
