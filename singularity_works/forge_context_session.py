from __future__ import annotations

from typing import TYPE_CHECKING

from .forge_context_blocks import (
    BiTemporalBlock,
    EpistemicStatus,
    WitnessBlock,
    _consolidation_gates,
    _encode_semantic,
    _encode_witness,
    _now,
)

if TYPE_CHECKING:
    from .forge_context import ForgeContext


class ForgeContextSessionMixin:
    # ── SBUF — volatile session buffer ───────────────────────────────

    def sbuf_push(
        self,
        session_id: str,
        artifact_id: str,
        gate_id: str,
        status: str,
        severity: str,
        finding_codes: list[str],
        finding_messages: list[str],
        radical_tags: list[str],
        capsule_id: str,
        language: str = "",
        confidence: str = "high",
        valid_from: str | None = None,
    ) -> WitnessBlock:
        """
        Push a raw gate result into SBUF.
        Does NOT touch EPMEM — call consolidate() after a session.
        valid_from: when the vulnerability/observation held (event time).
                    Defaults to now if not provided.
        """
        w = WitnessBlock(
            session_id=session_id,
            artifact_id=artifact_id,
            gate_id=gate_id,
            status=status,
            severity=severity,
            finding_codes=finding_codes,
            finding_messages=finding_messages,
            radical_tags=radical_tags,
            capsule_id=capsule_id,
            language=language,
            confidence=confidence,
            temporal=BiTemporalBlock(
                t_created=_now(),
                valid_from=valid_from or _now(),
            ),
        )
        self.sbuf.push_witness(w)
        return w

    # ── EPMEM — episodic witness ledger ───────────────────────────────

    def epmem_commit(self, witness: WitnessBlock) -> None:
        """Commit a WitnessBlock to durable EPMEM. Append-only."""
        epmem = self._ctx["epmem"]
        epmem.append(_encode_witness(witness))
        # Rolling window: keep last N entries
        max_e = self.CONSOLIDATION_CONFIG["max_epmem_entries"]
        if len(epmem) > max_e:
            self._ctx["epmem"] = epmem[-max_e:]

    def epmem_query(
        self,
        radical_family: str | None = None,
        capsule_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[WitnessBlock]:
        """Query EPMEM by radical family, capsule, or status."""
        results: list[WitnessBlock] = []
        for entry in reversed(self._epmem_blocks()):
            if radical_family and radical_family not in entry.radical_tags:
                continue
            if capsule_id and entry.capsule_id != capsule_id:
                continue
            if status and entry.status != status:
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results


    # ── Consolidation — SBUF → EPMEM → SMEM ──────────────────────────

    def consolidate(self, session_id: str, final_status: str) -> dict:
        """
        Run the consolidation cycle:
        1. Commit all SBUF witnesses to EPMEM
        2. Apply promotion gates
        3. Promote qualifying patterns to SMEM
        4. Detect contradictions against existing SMEM
        5. Clear SBUF (hippocampal reset)
        Returns a summary of what was committed and promoted.
        """
        witnesses = self.sbuf.witnesses()
        if not witnesses:
            return {"committed": 0, "promoted": 0, "contradictions": 0}

        existing_smem = self._smem_blocks()

        committed = 0
        promoted = 0
        contradictions_found = 0
        capsule_hits: dict[str, list[str]] = {}

        for w in witnesses:
            # Always commit to EPMEM — full fidelity witness
            self.epmem_commit(w)
            committed += 1

            # Apply promotion gates
            decision = _consolidation_gates(w, existing_smem, self.CONSOLIDATION_CONFIG)

            if decision == "Contradict":
                # Find the semantic block this contradicts
                for smem_block in existing_smem:
                    if (smem_block.radical_family and
                            any(r in w.radical_tags for r in [smem_block.radical_family]) and
                            smem_block.status == EpistemicStatus.STABLE_SEMANTIC):
                        self.record_contradiction(
                            contradicts_semantic_id=smem_block.semantic_id,
                            contradicting_witness_id=w.witness_id,
                            contradiction_type="evidence_conflict",
                            new_claim=f"Gate {w.gate_id} produced {w.status} — contradicts prior belief",
                        )
                        contradictions_found += 1
                        break

            elif decision == "Promote" and w.status == "fail" and w.finding_codes:
                # Accumulate by capsule for batch promotion
                key = w.capsule_id or w.gate_id
                if key not in capsule_hits:
                    capsule_hits[key] = []
                capsule_hits[key].append(w.witness_id)

        # Batch promote capsules that accumulated enough evidence
        min_support = self.CONSOLIDATION_CONFIG["min_support_for_stable"]
        for capsule_id, witness_ids in capsule_hits.items():
            # Find the radical family from the witnesses
            radical_tags = []
            for w in witnesses:
                if (w.capsule_id or w.gate_id) == capsule_id:
                    radical_tags.extend(w.radical_tags)
            radical_family = radical_tags[0] if radical_tags else "UNKNOWN"

            # Check if already in SMEM
            already = any(
                b.get("capsule_family") == capsule_id and
                b.get("status") not in (EpistemicStatus.CONTRADICTED.value, EpistemicStatus.SUPERSEDED.value)
                for b in self._ctx["smem"]
            )

            if not already:
                # Find the most common finding code
                finding_summary = ", ".join(
                    w.finding_codes[0] for w in witnesses
                    if (w.capsule_id or w.gate_id) == capsule_id and w.finding_codes
                )[:80]
                self.smem_promote(
                    claim=f"Capsule '{capsule_id}' fires reliably ({finding_summary})",
                    claim_type="capsule_prior",
                    radical_family=radical_family,
                    capsule_family=capsule_id,
                    supporting_witness_ids=witness_ids,
                    confidence=min(0.5 + len(witness_ids) * 0.1, 0.9),
                    justification=f"Promoted from {len(witness_ids)} witness(es) in session {session_id}",
                )
                promoted += 1
            else:
                # Strengthen existing belief
                for idx, block in enumerate(self._smem_blocks()):
                    if block.capsule_family == capsule_id:
                        block.support_count += len(witness_ids)
                        block.support_ids.extend(witness_ids)
                        if block.status == EpistemicStatus.HYPOTHESIS and block.support_count >= min_support:
                            block.status = EpistemicStatus.PROVISIONAL_SEMANTIC
                            promoted += 1
                        elif block.status == EpistemicStatus.PROVISIONAL_SEMANTIC and block.support_count >= min_support * 2:
                            block.status = EpistemicStatus.STABLE_SEMANTIC
                        self._ctx["smem"][idx] = _encode_semantic(block)

        # Update legacy genome_priors (backward compat)
        for w in witnesses:
            if w.capsule_id:
                priors = self._ctx["forge"]["genome_priors"]
                if w.capsule_id not in priors:
                    priors[w.capsule_id] = {"fires": 0, "green_after_fix": 0}
                priors[w.capsule_id]["fires"] += 1

        # Clear SBUF (hippocampal reset)
        self.sbuf.clear()

        return {
            "committed": committed,
            "promoted": promoted,
            "contradictions": contradictions_found,
            "session_id": session_id,
            "final_status": final_status,
        }


    # ── Forge session (v3.0 compat + v4.0 consolidation) ─────────────

    def record_forge_session(
        self,
        session_id: str,
        files_analyzed: list[str],
        gate_counts: dict[str, int],
        findings: list[dict],
        genome_capsules_fired: list[str],
        transformation_candidates: list[dict],
        applied_transformations: int,
        final_status: str,
        rounds: int = 0,
        auto_consolidate: bool = True,
    ) -> None:
        """
        Record a complete forge session.
        If auto_consolidate=True, also runs the SBUF → EPMEM consolidation.
        """
        session = {
            "id": session_id,
            "timestamp": _now(),
            "files": files_analyzed,
            "gate_counts": gate_counts,
            "finding_count": len(findings),
            "high_critical": sum(
                1 for f in findings if f.get("severity") in ("critical", "high")
            ),
            "capsules_fired": genome_capsules_fired,
            "candidates": len(transformation_candidates),
            "applied": applied_transformations,
            "status": final_status,
            "dialect_rounds": rounds,
        }
        sessions = self._ctx["forge"]["sessions"]
        sessions.append(session)
        if len(sessions) > self.CONSOLIDATION_CONFIG["max_sessions"]:
            self._ctx["forge"]["sessions"] = sessions[-self.CONSOLIDATION_CONFIG["max_sessions"]:]

        # Push findings to SBUF for consolidation
        for f in findings:
            self.sbuf_push(
                session_id=session_id,
                artifact_id=f.get("artifact_id", session_id),
                gate_id=f.get("gate_id", "unknown"),
                status=f.get("status", "fail"),
                severity=f.get("severity", "medium"),
                finding_codes=f.get("finding_codes", []),
                finding_messages=[f.get("message", "")],
                radical_tags=f.get("radical_tags", []),
                capsule_id=f.get("capsule_id", ""),
                language=f.get("language", ""),
                confidence=f.get("confidence", "high"),
            )

        # Proven axioms
        for tc in transformation_candidates:
            axiom = tc.get("transformation_axiom") or tc.get("axiom")
            if axiom and final_status == "green":
                proven = self._ctx["forge"]["proven_axioms"]
                if axiom not in proven:
                    proven.append(axiom)

        if auto_consolidate:
            self.consolidate(session_id, final_status)

