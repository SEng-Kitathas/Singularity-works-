from __future__ import annotations

"""Renderer-neutral Forge Workbench frontend model v0.1.

The Workbench is an authority-NONE presentation projection over a canonical frozen
semantic field. It may route attention through lenses/search/selection and present
qualified semantic-delta replay plans. It never mutates source, semantic state,
Git state, or runtime authority.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import shlex
from typing import Any, Mapping

from singularity_works.semantic_field import FrozenSemanticFactBundle, canonical_json


WORKBENCH_SCHEMA = "forge-workbench-model/0.1"
WORKBENCH_STATE_SCHEMA = "forge-workbench-interaction-state/0.1"
DELTA_PREVIEW_SCHEMA = "forge-workbench-semantic-delta-preview/0.1"
SUPPORTED_REPLAY_VERSION = "forge.semantic-delta-replay/0.1.3"
SUPPORTED_LENSES = ("all", "capability", "implementation", "unknown", "evidence")
CURRENTNESS_STATES = ("MATCH", "MISMATCH", "UNKNOWN")
IMPLEMENTATION_KINDS = frozenset(
    {"module", "function", "method", "class", "value", "call", "effect", "record", "source_span"}
)


class WorkbenchModelError(ValueError):
    """Fail-closed invalid frontend projection input."""


@dataclass(frozen=True)
class WorkbenchInteractionState:
    schema: str = WORKBENCH_STATE_SCHEMA
    lens: str = "all"
    query: str = ""
    selected_entity_id: str | None = None

    def __post_init__(self) -> None:
        if self.lens not in SUPPORTED_LENSES:
            raise WorkbenchModelError(f"unsupported lens: {self.lens}")


@dataclass(frozen=True)
class DeltaCollectionCount:
    collection: str
    remove_count: int
    upsert_count: int


@dataclass(frozen=True)
class SemanticDeltaPreview:
    schema: str
    plan_id: str
    version: str
    base_bundle_id: str
    target_bundle_id: str
    delta_authority: str
    operation_count: int
    collection_counts: tuple[DeltaCollectionCount, ...]
    qualification_status: str
    claim_ceiling: str
    checks_passed: int
    checks_total: int
    reverse_replay_evidence: bool
    materialization_enabled: bool
    materialization_reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkbenchNode:
    entity_id: str
    kind: str
    name: str
    source_path: str | None
    fact_count: int
    unknown_count: int
    evidence_statuses: tuple[str, ...]
    assurance_ceilings: tuple[str, ...]
    predicates: tuple[str, ...]
    selected: bool


@dataclass(frozen=True)
class InspectorFact:
    fact_id: str
    predicate: str
    object_json: str
    evidence_status: str
    assurance_ceiling: str
    evidence_ids: tuple[str, ...]
    derivation_from: tuple[str, ...]


@dataclass(frozen=True)
class InspectorEvidence:
    evidence_id: str
    source_id: str
    source_path: str
    start_line: int
    end_line: int
    snippet_sha256: str
    role: str


@dataclass(frozen=True)
class WorkbenchUnknown:
    seam_id: str
    subject_id: str | None
    subject_name: str | None
    question: str
    reason: str
    evidence_ids: tuple[str, ...]
    assurance_ceiling: str
    blocking: bool


@dataclass(frozen=True)
class EvidenceInspector:
    entity_id: str
    kind: str
    name: str
    source_path: str | None
    facts: tuple[InspectorFact, ...]
    evidence: tuple[InspectorEvidence, ...]
    unknowns: tuple[WorkbenchUnknown, ...]


@dataclass(frozen=True)
class CommandAffordance:
    command_id: str
    syntax: str
    enabled: bool
    consequence_scope: str
    reason: str


@dataclass(frozen=True)
class WorkbenchModel:
    schema: str
    source_bundle_id: str
    source_authority: str
    projection_authority: str
    currentness: str
    state: WorkbenchInteractionState
    nodes: tuple[WorkbenchNode, ...]
    total_entity_count: int
    visible_entity_count: int
    unknowns: tuple[WorkbenchUnknown, ...]
    total_unknown_count: int
    inspector: EvidenceInspector | None
    selection_visible: bool
    delta_preview: SemanticDeltaPreview | None
    commands: tuple[CommandAffordance, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @property
    def model_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CommandResult:
    accepted: bool
    state: WorkbenchInteractionState
    ui_intent: str
    message: str
    consequence_scope: str = "READ_ONLY_UI"


def _object_json(value: Any) -> str:
    """Canonical display form; canonical objects are presented, not reinterpreted."""
    return canonical_json(value)


def _source_path(bundle: FrozenSemanticFactBundle, source_id: str | None) -> str | None:
    if source_id is None:
        return None
    source = bundle.sources.get(source_id)
    return source.path if source is not None else None


def _entity_evidence_ids(bundle: FrozenSemanticFactBundle, entity_id: str) -> set[str]:
    entity = bundle.entities[entity_id]
    ids: set[str] = set()
    if entity.evidence_id:
        ids.add(entity.evidence_id)
    for fact in bundle.facts.values():
        if fact.subject_id == entity_id:
            ids.update(fact.evidence_ids)
    for seam in bundle.unknowns.values():
        if seam.subject_id == entity_id:
            ids.update(seam.evidence_ids)
    return ids


def _unknown_rows(bundle: FrozenSemanticFactBundle) -> tuple[WorkbenchUnknown, ...]:
    rows: list[WorkbenchUnknown] = []
    for seam in sorted(bundle.unknowns.values(), key=lambda item: item.seam_id):
        entity = bundle.entities.get(seam.subject_id) if seam.subject_id else None
        rows.append(
            WorkbenchUnknown(
                seam_id=seam.seam_id,
                subject_id=seam.subject_id,
                subject_name=entity.name if entity else None,
                question=seam.question,
                reason=seam.reason,
                evidence_ids=tuple(seam.evidence_ids),
                assurance_ceiling=seam.assurance_ceiling,
                blocking=bool(seam.blocking),
            )
        )
    return tuple(rows)


def _lens_match(
    bundle: FrozenSemanticFactBundle,
    entity_id: str,
    *,
    lens: str,
    unknown_subjects: set[str],
) -> bool:
    entity = bundle.entities[entity_id]
    if lens == "all":
        return True
    if lens == "capability":
        return entity.kind == "capability"
    if lens == "implementation":
        return entity.kind in IMPLEMENTATION_KINDS
    if lens == "unknown":
        return entity_id in unknown_subjects
    if lens == "evidence":
        return bool(_entity_evidence_ids(bundle, entity_id))
    raise WorkbenchModelError(f"unsupported lens: {lens}")


def _query_match(
    bundle: FrozenSemanticFactBundle,
    entity_id: str,
    *,
    query: str,
    facts_by_subject: Mapping[str, tuple[Any, ...]],
    unknowns_by_subject: Mapping[str, tuple[Any, ...]],
) -> bool:
    needle = query.strip().casefold()
    if not needle:
        return True
    entity = bundle.entities[entity_id]
    parts = [entity.entity_id, entity.kind, entity.name, _source_path(bundle, entity.source_id) or ""]
    parts.extend(fact.predicate for fact in facts_by_subject.get(entity_id, ()))
    for seam in unknowns_by_subject.get(entity_id, ()):
        parts.extend((seam.question, seam.reason))
    return needle in "\n".join(parts).casefold()


def _index_subject_rows(bundle: FrozenSemanticFactBundle) -> tuple[dict[str, tuple[Any, ...]], dict[str, tuple[Any, ...]]]:
    facts: dict[str, list[Any]] = {}
    unknowns: dict[str, list[Any]] = {}
    for fact in bundle.facts.values():
        facts.setdefault(fact.subject_id, []).append(fact)
    for seam in bundle.unknowns.values():
        if seam.subject_id is not None:
            unknowns.setdefault(seam.subject_id, []).append(seam)
    return (
        {key: tuple(sorted(values, key=lambda item: item.fact_id)) for key, values in facts.items()},
        {key: tuple(sorted(values, key=lambda item: item.seam_id)) for key, values in unknowns.items()},
    )


def _build_inspector(
    bundle: FrozenSemanticFactBundle,
    entity_id: str,
    *,
    facts_by_subject: Mapping[str, tuple[Any, ...]],
    unknowns_by_subject: Mapping[str, tuple[Any, ...]],
) -> EvidenceInspector:
    if entity_id not in bundle.entities:
        raise WorkbenchModelError(f"selection references unknown entity: {entity_id}")
    entity = bundle.entities[entity_id]
    facts = tuple(
        InspectorFact(
            fact_id=fact.fact_id,
            predicate=fact.predicate,
            object_json=_object_json(fact.object_value),
            evidence_status=fact.evidence_status,
            assurance_ceiling=fact.assurance_ceiling,
            evidence_ids=tuple(fact.evidence_ids),
            derivation_from=tuple(fact.derivation_from),
        )
        for fact in facts_by_subject.get(entity_id, ())
    )
    unknowns = tuple(
        WorkbenchUnknown(
            seam_id=seam.seam_id,
            subject_id=seam.subject_id,
            subject_name=entity.name,
            question=seam.question,
            reason=seam.reason,
            evidence_ids=tuple(seam.evidence_ids),
            assurance_ceiling=seam.assurance_ceiling,
            blocking=bool(seam.blocking),
        )
        for seam in unknowns_by_subject.get(entity_id, ())
    )
    evidence_ids = set(_entity_evidence_ids(bundle, entity_id))
    evidence_rows: list[InspectorEvidence] = []
    for evidence_id in sorted(evidence_ids):
        evidence = bundle.evidence.get(evidence_id)
        if evidence is None:
            raise WorkbenchModelError(f"entity evidence missing from frozen bundle: {evidence_id}")
        source = bundle.sources.get(evidence.source_id)
        if source is None:
            raise WorkbenchModelError(f"evidence source missing from frozen bundle: {evidence.source_id}")
        evidence_rows.append(
            InspectorEvidence(
                evidence_id=evidence.evidence_id,
                source_id=evidence.source_id,
                source_path=source.path,
                start_line=evidence.start_line,
                end_line=evidence.end_line,
                snippet_sha256=evidence.snippet_sha256,
                role=evidence.role,
            )
        )
    return EvidenceInspector(
        entity_id=entity.entity_id,
        kind=entity.kind,
        name=entity.name,
        source_path=_source_path(bundle, entity.source_id),
        facts=facts,
        evidence=tuple(evidence_rows),
        unknowns=unknowns,
    )


def _named_plan_ids(summary: Mapping[str, Any]) -> set[str]:
    plan_ids: set[str] = set()
    plans = summary.get("plans", {})
    if not isinstance(plans, Mapping):
        return plan_ids
    for value in plans.values():
        if isinstance(value, Mapping) and isinstance(value.get("plan_id"), str):
            plan_ids.add(value["plan_id"])
    return plan_ids


def build_delta_preview(
    plan: Mapping[str, Any],
    qualification_summary: Mapping[str, Any] | None = None,
) -> SemanticDeltaPreview:
    """Validate a serialized Core replay plan and project a read-only UI summary."""
    required = {"version", "plan_id", "base_bundle_id", "target_bundle_id", "delta_authority", "operations"}
    missing = sorted(required - set(plan))
    if missing:
        raise WorkbenchModelError(f"semantic delta plan missing keys: {', '.join(missing)}")
    if plan["version"] != SUPPORTED_REPLAY_VERSION:
        raise WorkbenchModelError(f"unsupported semantic replay version: {plan['version']}")
    if plan["delta_authority"] != "NONE":
        raise WorkbenchModelError("semantic delta plan authority must remain NONE")
    for key in ("plan_id", "base_bundle_id", "target_bundle_id"):
        if not isinstance(plan[key], str) or not plan[key]:
            raise WorkbenchModelError(f"semantic delta plan {key} must be a non-empty string")

    operations = plan["operations"]
    if not isinstance(operations, list):
        raise WorkbenchModelError("semantic delta operations must be a list")
    operation_ids: set[str] = set()
    counts: dict[str, dict[str, int]] = {}
    for operation in operations:
        if not isinstance(operation, Mapping):
            raise WorkbenchModelError("semantic delta operation must be an object")
        action = operation.get("action")
        collection = operation.get("collection")
        operation_id = operation.get("operation_id")
        key = operation.get("key")
        if action not in {"REMOVE", "UPSERT"}:
            raise WorkbenchModelError(f"unsupported semantic delta action: {action}")
        if not isinstance(collection, str) or not collection:
            raise WorkbenchModelError("semantic delta operation collection must be non-empty")
        if not isinstance(key, str) or not key:
            raise WorkbenchModelError("semantic delta operation key must be non-empty")
        if not isinstance(operation_id, str) or not operation_id:
            raise WorkbenchModelError("semantic delta operation_id must be non-empty")
        if operation_id in operation_ids:
            raise WorkbenchModelError(f"duplicate semantic delta operation_id: {operation_id}")
        operation_ids.add(operation_id)
        bucket = counts.setdefault(collection, {"REMOVE": 0, "UPSERT": 0})
        bucket[action] += 1
        if action == "REMOVE" and operation.get("value") is not None:
            raise WorkbenchModelError("REMOVE operation must not carry a value")
        if action == "UPSERT" and operation.get("value") is None:
            raise WorkbenchModelError("UPSERT operation must carry a value")

    qualification_status = "UNVERIFIED"
    claim_ceiling = "UNQUALIFIED_REPLAY_PREVIEW_ONLY"
    checks_passed = 0
    checks_total = 0
    reverse_evidence = False
    if qualification_summary is not None:
        checks = qualification_summary.get("checks")
        if not isinstance(checks, Mapping):
            raise WorkbenchModelError("qualification summary checks must be an object")
        checks_total = int(qualification_summary.get("check_count", len(checks)))
        checks_passed = int(qualification_summary.get("pass_count", sum(bool(v) for v in checks.values())))
        all_named_checks = bool(checks) and all(value is True for value in checks.values())
        plan_named = plan["plan_id"] in _named_plan_ids(qualification_summary)
        passed = (
            qualification_summary.get("verdict") == "PASS"
            and all_named_checks
            and checks_passed == checks_total
            and checks_total == len(checks)
            and plan_named
            and isinstance(qualification_summary.get("claim_ceiling"), str)
            and bool(qualification_summary.get("claim_ceiling"))
        )
        if passed:
            qualification_status = "QUALIFIED_BOUNDED"
            claim_ceiling = str(qualification_summary["claim_ceiling"])
        else:
            qualification_status = "UNQUALIFIED"
            claim_ceiling = str(qualification_summary.get("claim_ceiling") or "UNQUALIFIED_REPLAY_PREVIEW_ONLY")
        reverse_evidence = bool(
            checks.get("reverse_replay_exact_bundle_id") is True
            and checks.get("reverse_replay_exact_serialization") is True
        )

    collection_counts = tuple(
        DeltaCollectionCount(
            collection=collection,
            remove_count=values["REMOVE"],
            upsert_count=values["UPSERT"],
        )
        for collection, values in sorted(counts.items())
    )
    return SemanticDeltaPreview(
        schema=DELTA_PREVIEW_SCHEMA,
        plan_id=str(plan["plan_id"]),
        version=str(plan["version"]),
        base_bundle_id=str(plan["base_bundle_id"]),
        target_bundle_id=str(plan["target_bundle_id"]),
        delta_authority="NONE",
        operation_count=len(operations),
        collection_counts=collection_counts,
        qualification_status=qualification_status,
        claim_ceiling=claim_ceiling,
        checks_passed=checks_passed,
        checks_total=checks_total,
        reverse_replay_evidence=reverse_evidence,
        materialization_enabled=False,
        materialization_reason=(
            "Core exact bundle replay is presentation evidence only; source edit materialization is not earned."
        ),
    )


def _command_affordances(delta_preview: SemanticDeltaPreview | None) -> tuple[CommandAffordance, ...]:
    replay_ready = bool(delta_preview and delta_preview.qualification_status == "QUALIFIED_BOUNDED")
    reverse_ready = bool(replay_ready and delta_preview and delta_preview.reverse_replay_evidence)
    return (
        CommandAffordance("home", "home", True, "READ_ONLY_UI", "Reset lens, query and selection."),
        CommandAffordance("clear", "clear", True, "READ_ONLY_UI", "Clear selection and search."),
        CommandAffordance("lens", "lens <all|capability|implementation|unknown|evidence>", True, "READ_ONLY_UI", "Route attention through a mechanical lens."),
        CommandAffordance("select", "select <entity-id>", True, "READ_ONLY_UI", "Inspect an existing canonical entity."),
        CommandAffordance("find", "find <text>", True, "READ_ONLY_UI", "Filter existing presentation strings."),
        CommandAffordance("preview-delta", "preview-delta", replay_ready, "READ_ONLY_UI", "Show qualified bundle replay preview." if replay_ready else "No qualified replay plan is bound."),
        CommandAffordance("reverse-preview", "reverse-preview", reverse_ready, "READ_ONLY_UI", "Show reverse replay evidence." if reverse_ready else "No qualified reverse replay evidence is bound."),
        CommandAffordance("materialize", "materialize", False, "DISABLED", "EXACT_BUNDLE_REPLAY != SOURCE_EDIT_MATERIALIZATION."),
    )


def build_workbench_model(
    bundle: FrozenSemanticFactBundle,
    *,
    currentness: str = "UNKNOWN",
    state: WorkbenchInteractionState | None = None,
    delta_plan: Mapping[str, Any] | None = None,
    delta_qualification_summary: Mapping[str, Any] | None = None,
) -> WorkbenchModel:
    """Build deterministic frontend state without minting semantic authority."""
    if not isinstance(bundle, FrozenSemanticFactBundle):
        raise WorkbenchModelError("Workbench requires a FrozenSemanticFactBundle")
    if bundle.target_execution:
        raise WorkbenchModelError("Workbench refuses executed-target semantic bundles")
    if bundle.authority != "NONE":
        raise WorkbenchModelError("canonical frontend consumer expects bundle authority NONE")
    if currentness not in CURRENTNESS_STATES:
        raise WorkbenchModelError(f"unsupported currentness: {currentness}")
    state = state or WorkbenchInteractionState()
    if state.selected_entity_id is not None and state.selected_entity_id not in bundle.entities:
        raise WorkbenchModelError(f"selection references unknown entity: {state.selected_entity_id}")

    facts_by_subject, unknowns_by_subject = _index_subject_rows(bundle)
    unknown_subjects = set(unknowns_by_subject)
    visible_ids = [
        entity_id
        for entity_id in bundle.entities
        if _lens_match(bundle, entity_id, lens=state.lens, unknown_subjects=unknown_subjects)
        and _query_match(
            bundle,
            entity_id,
            query=state.query,
            facts_by_subject=facts_by_subject,
            unknowns_by_subject=unknowns_by_subject,
        )
    ]
    visible_ids.sort(
        key=lambda entity_id: (
            bundle.entities[entity_id].kind,
            bundle.entities[entity_id].name.casefold(),
            entity_id,
        )
    )

    nodes: list[WorkbenchNode] = []
    for entity_id in visible_ids:
        entity = bundle.entities[entity_id]
        facts = facts_by_subject.get(entity_id, ())
        unknowns = unknowns_by_subject.get(entity_id, ())
        nodes.append(
            WorkbenchNode(
                entity_id=entity.entity_id,
                kind=entity.kind,
                name=entity.name,
                source_path=_source_path(bundle, entity.source_id),
                fact_count=len(facts),
                unknown_count=len(unknowns),
                evidence_statuses=tuple(sorted({fact.evidence_status for fact in facts})),
                assurance_ceilings=tuple(sorted({fact.assurance_ceiling for fact in facts})),
                predicates=tuple(sorted({fact.predicate for fact in facts})),
                selected=entity_id == state.selected_entity_id,
            )
        )

    inspector = None
    if state.selected_entity_id is not None:
        inspector = _build_inspector(
            bundle,
            state.selected_entity_id,
            facts_by_subject=facts_by_subject,
            unknowns_by_subject=unknowns_by_subject,
        )

    delta_preview = None
    if delta_plan is not None:
        delta_preview = build_delta_preview(delta_plan, delta_qualification_summary)
    elif delta_qualification_summary is not None:
        raise WorkbenchModelError("delta qualification summary supplied without a delta plan")

    all_unknowns = _unknown_rows(bundle)
    return WorkbenchModel(
        schema=WORKBENCH_SCHEMA,
        source_bundle_id=bundle.bundle_id,
        source_authority=bundle.authority,
        projection_authority="NONE",
        currentness=currentness,
        state=state,
        nodes=tuple(nodes),
        total_entity_count=len(bundle.entities),
        visible_entity_count=len(nodes),
        unknowns=all_unknowns,
        total_unknown_count=len(all_unknowns),
        inspector=inspector,
        selection_visible=bool(state.selected_entity_id is not None and state.selected_entity_id in set(visible_ids)),
        delta_preview=delta_preview,
        commands=_command_affordances(delta_preview),
    )


def apply_readonly_command(
    state: WorkbenchInteractionState,
    command: str,
    *,
    bundle: FrozenSemanticFactBundle,
    delta_preview: SemanticDeltaPreview | None = None,
) -> CommandResult:
    """Apply only presentation-state commands; never dispatch external effects."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        return CommandResult(False, state, "NONE", f"command parse error: {exc}")
    if not tokens:
        return CommandResult(False, state, "NONE", "empty command")

    name = tokens[0].casefold()
    if name == "home" and len(tokens) == 1:
        return CommandResult(True, WorkbenchInteractionState(), "RESET_VIEW", "Workbench view reset.")
    if name == "clear" and len(tokens) == 1:
        return CommandResult(
            True,
            WorkbenchInteractionState(lens=state.lens, query="", selected_entity_id=None),
            "CLEAR_FILTER_SELECTION",
            "Search and selection cleared.",
        )
    if name == "lens" and len(tokens) == 2:
        lens = tokens[1].casefold()
        if lens not in SUPPORTED_LENSES:
            return CommandResult(False, state, "NONE", f"unsupported lens: {lens}")
        return CommandResult(
            True,
            WorkbenchInteractionState(lens=lens, query=state.query, selected_entity_id=state.selected_entity_id),
            "SET_LENS",
            f"Lens set to {lens}.",
        )
    if name == "select" and len(tokens) == 2:
        entity_id = tokens[1]
        if entity_id not in bundle.entities:
            return CommandResult(False, state, "NONE", f"unknown entity: {entity_id}")
        return CommandResult(
            True,
            WorkbenchInteractionState(lens=state.lens, query=state.query, selected_entity_id=entity_id),
            "SELECT_ENTITY",
            f"Selected {entity_id}.",
        )
    if name == "find" and len(tokens) >= 2:
        query = " ".join(tokens[1:]).strip()
        return CommandResult(
            True,
            WorkbenchInteractionState(lens=state.lens, query=query, selected_entity_id=state.selected_entity_id),
            "SET_QUERY",
            f"Search set to {query!r}.",
        )
    if name == "preview-delta" and len(tokens) == 1:
        if delta_preview is None or delta_preview.qualification_status != "QUALIFIED_BOUNDED":
            return CommandResult(False, state, "NONE", "no qualified semantic delta preview is bound")
        return CommandResult(True, state, "SHOW_DELTA_PREVIEW", f"Preview {delta_preview.plan_id}.")
    if name == "reverse-preview" and len(tokens) == 1:
        if (
            delta_preview is None
            or delta_preview.qualification_status != "QUALIFIED_BOUNDED"
            or not delta_preview.reverse_replay_evidence
        ):
            return CommandResult(False, state, "NONE", "no qualified reverse replay evidence is bound")
        return CommandResult(True, state, "SHOW_REVERSE_REPLAY_EVIDENCE", "Show bounded reverse replay evidence.")
    if name == "materialize":
        return CommandResult(
            False,
            state,
            "NONE",
            "materialize disabled: EXACT_BUNDLE_REPLAY != SOURCE_EDIT_MATERIALIZATION",
            consequence_scope="DISABLED",
        )
    return CommandResult(False, state, "NONE", f"unsupported read-only command: {name}")


def _truncate(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return "…"
    return text[: width - 1] + "…"


def render_workbench_text(model: WorkbenchModel, *, width: int = 100, node_limit: int = 12) -> str:
    """Cheap first-class fallback renderer for the exact Workbench model."""
    width = max(60, min(int(width), 180))
    node_limit = max(1, int(node_limit))
    lines: list[str] = []

    def add(text: str = "") -> None:
        lines.append(_truncate(text, width))

    add("FORGE // WORKBENCH")
    add(f"BUNDLE {model.source_bundle_id}  CURRENTNESS {model.currentness}")
    add(f"FIELD AUTHORITY {model.source_authority}  PROJECTION AUTHORITY {model.projection_authority}")
    add(f"LENS {model.state.lens}  QUERY {model.state.query or '—'}  ENTITIES {model.visible_entity_count}/{model.total_entity_count}  UNKNOWN {model.total_unknown_count}")
    add("─" * width)
    if model.delta_preview is not None:
        delta = model.delta_preview
        add(
            f"DELTA {delta.qualification_status}  {delta.base_bundle_id} -> {delta.target_bundle_id}  OPS {delta.operation_count}"
        )
        add(f"CLAIM {delta.claim_ceiling}")
        add(f"MATERIALIZE DISABLED  {delta.materialization_reason}")
        add("─" * width)

    add("MAP / ENTITY LIST")
    if not model.nodes:
        add("(no entities match the current lens/search)")
    for node in model.nodes[:node_limit]:
        marker = ">" if node.selected else " "
        source = f"  {node.source_path}" if node.source_path else ""
        add(f"{marker} [{node.kind}] {node.name}  facts={node.fact_count} unknown={node.unknown_count}{source}")
    if len(model.nodes) > node_limit:
        add(f"… {len(model.nodes) - node_limit} more nodes retained in model")

    add("─" * width)
    add("EVIDENCE INSPECTOR")
    if model.inspector is None:
        add("(no selection)")
    else:
        inspector = model.inspector
        add(f"{inspector.entity_id}  [{inspector.kind}] {inspector.name}")
        for fact in inspector.facts:
            add(
                f"FACT {fact.evidence_status} {fact.predicate} = {fact.object_json}  ceiling={fact.assurance_ceiling}"
            )
        for evidence in inspector.evidence:
            add(
                f"EVIDENCE {evidence.evidence_id}  {evidence.source_path}:{evidence.start_line}-{evidence.end_line}  sha={evidence.snippet_sha256[:12]}"
            )
        for unknown in inspector.unknowns:
            add(f"UNKNOWN {'BLOCKING ' if unknown.blocking else ''}{unknown.question} — {unknown.reason}")

    add("─" * width)
    add("COMMANDS")
    enabled = [item.syntax for item in model.commands if item.enabled]
    disabled = [item.syntax for item in model.commands if not item.enabled]
    add("enabled: " + " · ".join(enabled))
    add("disabled: " + " · ".join(disabled))
    return "\n".join(lines) + "\n"
