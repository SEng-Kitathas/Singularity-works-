from __future__ import annotations

from .cil_council import operator_brief
from .facts import inferred, observed
from .forge_context import ForgeContext
from .language_front_door import detect_language
from .models import EvaluationResult, IntakeArtifact
from .pattern_ir import fingerprint


def intake_artifact(path: str, content: str) -> IntakeArtifact:
    language = detect_language(path, content)
    fp = fingerprint(language, content)
    return IntakeArtifact(path=path, content=content, language=language, fingerprint=fp)


def evaluate_artifact(context: ForgeContext, path: str, content: str) -> EvaluationResult:
    artifact = intake_artifact(path, content)

    evidence = [
        observed(
            claim="artifact ingested",
            source=path,
            rationale="file content received by front door",
            language=artifact.language,
        ),
        observed(
            claim="fingerprint computed",
            source=path,
            rationale="normalized structural digest created",
            digest=artifact.fingerprint.digest,
        ),
    ]

    accepted = artifact.language != "unknown"
    accepted_because = []
    unresolved_because = []

    if accepted:
        accepted_because.append(f"recognized language: {artifact.language}")
    else:
        unresolved_because.append("language could not be classified")

    if len(artifact.fingerprint.normalized_lines) < 2:
        unresolved_because.append("artifact too small for meaningful structural judgment")
    else:
        accepted_because.append("artifact has sufficient normalized structure for baseline analysis")

    score = 0.95 if accepted and not unresolved_because else 0.55 if accepted else 0.15
    result = EvaluationResult(
        accepted=accepted,
        score=score,
        accepted_because=accepted_because,
        unresolved_because=unresolved_because,
        evidence=evidence,
    )
    result.operator_brief = operator_brief(result)
    for item in result.operator_brief:
        context.evidence_ledger.append(inferred(item, source=path, rationale="operator brief projection"))
    context.evidence_ledger.extend(evidence)
    return result
