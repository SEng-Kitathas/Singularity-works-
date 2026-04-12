from __future__ import annotations

from typing import TYPE_CHECKING

from .forge_context_blocks import (
    BiTemporalBlock,
    ContradictionBlock,
    EpistemicStatus,
    SemanticBlock,
    WitnessBlock,
    _consolidation_gates,
    _decode_contradiction,
    _encode_contradiction,
    _encode_semantic,
    _encode_witness,
    _now,
)

if TYPE_CHECKING:
    from .forge_context import ForgeContext


class ForgeContextMemoryMixin:
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

    # ── SMEM — semantic memory ────────────────────────────────────────

    def smem_promote(
        self,
        claim: str,
        claim_type: str,
        radical_family: str,
        capsule_family: str,
        supporting_witness_ids: list[str],
        confidence: float = 0.7,
        justification: str = "",
    ) -> SemanticBlock:
        """
        Promote a pattern to SMEM. Starts at HYPOTHESIS; caller can
        call smem_advance() to move through the epistemic states.
        """
        block = SemanticBlock(
            claim=claim,
            claim_type=claim_type,
            radical_family=radical_family,
            capsule_family=capsule_family,
            status=EpistemicStatus.HYPOTHESIS,
            confidence=confidence,
            support_count=len(supporting_witness_ids),
            support_ids=supporting_witness_ids,
            temporal=BiTemporalBlock(valid_from=_now()),
            promotion_justification=justification,
        )
        self._ctx["smem"].append(_encode_semantic(block))
        return block

    def smem_advance(self, semantic_id: str, new_status: EpistemicStatus, justification: str = "") -> bool:
        """Advance a SMEM block to the next epistemic state."""
        for idx, block in enumerate(self._smem_blocks()):
            if block.semantic_id == semantic_id:
                block.promote(new_status, justification)
                self._ctx["smem"][idx] = _encode_semantic(block)
                return True
        return False

    def smem_query(
        self,
        radical_family: str | None = None,
        status: EpistemicStatus | None = None,
        limit: int = 20,
    ) -> list[SemanticBlock]:
        """Query SMEM by radical family and/or epistemic status."""
        results: list[SemanticBlock] = []
        active_statuses = {
            EpistemicStatus.STABLE_SEMANTIC,
            EpistemicStatus.PROVISIONAL_SEMANTIC,
            EpistemicStatus.HYPOTHESIS,
        }
        for block in self._smem_blocks():
            if block.status not in active_statuses:
                continue
            if radical_family and block.radical_family != radical_family:
                continue
            if status and block.status != status:
                continue
            results.append(block)
            if len(results) >= limit:
                break
        return results

    def smem_get_priors(self) -> dict[str, dict]:
        """
        Return stable SMEM beliefs as genome priors with calibrated distortion budgets.

        Distortion budget calibration (isomorphism: arXiv 2509.24431 temperature→gap):
          High support density → tighter centroid → lower budget
          High confidence spread → looser centroid → higher budget
        """
        import math as _math
        priors: dict[str, dict] = {}

        # Calibrate per radical family
        family_groups: dict[str, list[SemanticBlock]] = {}
        for block in self._smem_blocks():
            if block.status in (
                EpistemicStatus.STABLE_SEMANTIC,
                EpistemicStatus.PROVISIONAL_SEMANTIC,
            ):
                fam = block.radical_family or "UNKNOWN"
                family_groups.setdefault(fam, []).append(block)

        calibrated: dict[str, float] = {}
        for fam, blocks in family_groups.items():
            supports = [b.support_count or 1 for b in blocks]
            confs = [b.confidence or 0.5 for b in blocks]
            avg_sup = sum(supports) / len(supports)
            mean_c = sum(confs) / len(confs)
            std_dev = (_math.sqrt(sum((c - mean_c) ** 2 for c in confs) / len(confs))
                       if len(confs) > 1 else 0.0)
            density_factor = 1.0 / (1.0 + _math.log1p(avg_sup / 5.0))
            spread_factor = 1.0 + std_dev * 0.5
            calibrated[fam] = max(0.05, min(0.50, 0.20 * density_factor * spread_factor))

        for block in self._smem_blocks():
            if block.status in (
                EpistemicStatus.STABLE_SEMANTIC,
                EpistemicStatus.PROVISIONAL_SEMANTIC,
            ):
                cid = block.capsule_family
                if cid:
                    fam = block.radical_family or "UNKNOWN"
                    priors[cid] = {
                        "fires": block.support_count or 1,
                        "confidence": block.confidence or 0.5,
                        "status": block.status.value,
                        "claim": block.claim,
                        "radical_family": fam,
                        "distortion_budget": calibrated.get(fam, 0.20),
                    }

        for cid, data in self._ctx["forge"]["genome_priors"].items():
            if cid not in priors:
                priors[cid] = {
                    "fires": data.get("fires", 0), "confidence": 0.5,
                    "status": "legacy", "distortion_budget": 0.20,
                }
        return priors

    def record_contradiction(
        self,
        contradicts_semantic_id: str,
        contradicting_witness_id: str,
        contradiction_type: str,
        new_claim: str = "",
    ) -> ContradictionBlock:
        """
        Record a contradiction.
        Invalidates the targeted SemanticBlock using Zep's mechanism:
        sets valid_until of old belief = valid_from of new evidence.
        """
        contradicts_claim = ""
        for idx, block in enumerate(self._smem_blocks()):
            if block.semantic_id == contradicts_semantic_id:
                contradicts_claim = block.claim
                block.temporal.expire()
                block.status = EpistemicStatus.CONTRADICTED
                block.contradiction_count += 1
                self._ctx["smem"][idx] = _encode_semantic(block)
                break

        cb = ContradictionBlock(
            contradicts_semantic_id=contradicts_semantic_id,
            contradicts_claim=contradicts_claim,
            contradicting_witness_id=contradicting_witness_id,
            new_claim=new_claim,
            contradiction_type=contradiction_type,
        )
        self._ctx["contradictions"].append(_encode_contradiction(cb))
        return cb

    # ── Contradiction Graph queries (TM-006) ─────────────────────────
    # The flat contradiction list acts as an adjacency list:
    # each ContradictionBlock encodes one directed edge (contradicted → contradicting).
    # These methods provide the same query interface as the Rust ContradictionGraph,
    # enabling drop-in replacement once a proper DiGraph is warranted.

    def contradiction_active_roots(self) -> list[SemanticBlock]:
        """
        Return SMEM blocks that have no incoming contradiction edges AND are not
        contradicted. These represent the current worldview — what CIL believes now.
        Mirrors Rust ContradictionGraph.active_roots().
        """
        contradicted_ids = {c.contradicts_semantic_id for c in self._contradiction_blocks()}
        return [
            b for b in self._smem_blocks()
            if b.semantic_id not in contradicted_ids
            and b.status != EpistemicStatus.CONTRADICTED
        ]

    def contradiction_chain(self, semantic_id: str) -> list[ContradictionBlock]:
        """
        Return all contradictions reachable from a given semantic_id
        (full refutation ancestry via DFS over the contradiction list).
        Mirrors Rust ContradictionGraph.contradiction_chain().
        """
        visited: set[str] = set()
        result: list[ContradictionBlock] = []
        queue = [semantic_id]
        contradictions = self._contradiction_blocks()
        while queue:
            sid = queue.pop()
            if sid in visited:
                continue
            visited.add(sid)
            for c in contradictions:
                if c.contradicts_semantic_id == sid:
                    result.append(c)
                    for b in self._smem_blocks():
                        if b.semantic_id == c.contradicting_witness_id:
                            queue.append(b.semantic_id)
        return result

    def contradiction_summary(self) -> dict:
        """
        Return a summary suitable for the compile_context Retrieval Compiler.
        Mirrors Rust ContradictionGraph.summary().
        """
        contradictions = self._contradiction_blocks()
        smem = self._smem_blocks()
        active_roots = self.contradiction_active_roots()
        contradicted = [b for b in smem if b.status == EpistemicStatus.CONTRADICTED]
        return {
            "total_beliefs": len(smem),
            "active_beliefs": len(active_roots),
            "contradicted_beliefs": len(contradicted),
            "contradiction_edges": len(contradictions),
            "summary": (
                f"ContradictionGraph: {len(active_roots)}/{len(smem)} active beliefs "
                f"| {len(contradictions)} contradiction edges"
            ),
        }

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

    # ── Retrieval Compiler ────────────────────────────────────────────

    def compile_context(
        self,
        radical_hints: list[str] | None = None,
        max_witnesses: int = 10,
        max_semantic: int = 15,
        include_contradictions: bool = True,
    ) -> str:
        """
        Task-conditioned context packet.
        Assembles: recent witnesses, stable SMEM beliefs, open contradictions.
        This is what gets injected into the model context — not raw storage.

        Isomorphism: the Retrieval Compiler in CIL Layer 5E.
        """
        parts: list[str] = []

        # 1. Stable SMEM beliefs (project knowledge)
        stable = [
            b for b in self._ctx["smem"]
            if b.get("status") in (
                EpistemicStatus.STABLE_SEMANTIC.value,
                EpistemicStatus.PROVISIONAL_SEMANTIC.value,
            )
        ]
        if radical_hints:
            stable = [
                b for b in stable
                if b.radical_family in radical_hints
            ]
        if stable:
            parts.append("## Project Semantic Memory (Stable Beliefs)")
            for b in stable[:max_semantic]:
                status_tag = "✓ STABLE" if b.status == EpistemicStatus.STABLE_SEMANTIC else "~ PROVISIONAL"
                parts.append(
                    f"  [{status_tag}] {b.claim} "
                    f"(family={b.radical_family or '?'}, "
                    f"confidence={b.confidence:.2f}, "
                    f"support={b.support_count})"
                )

        # 2. Recent EPMEM witnesses (what the forge has actually seen)
        recent_epmem = list(reversed(self._epmem_blocks()))[:max_witnesses]
        if recent_epmem:
            parts.append("\n## Recent Episodic Witnesses (Gate Results)")
            for e in recent_epmem:
                codes = ", ".join(e.finding_codes)
                parts.append(
                    f"  [{e.status.upper() if e.status else '?'}] {e.gate_id or '?'} "
                    f"| codes: {codes or 'none'} "
                    f"| capsule: {e.capsule_id or '?'} "
                    f"| lang: {e.language or '?'}"
                )

        # 3. Open contradictions (unresolved tensions)
        if include_contradictions and self._ctx["contradictions"]:
            # Use graph query for active-roots view (TM-006)
            c_summary = self.contradiction_summary()
            parts.append(f"## Contradiction Graph\n  {c_summary['summary']}")
            if c_summary["contradicted_beliefs"] > 0:
                parts.append(f"  ({c_summary['contradicted_beliefs']} beliefs currently contradicted)")
            recent_contradictions = self._contradiction_blocks()[-5:]
            parts.append("\n## Open Contradictions (Unresolved)")
            for c in recent_contradictions:
                parts.append(
                    f"  [CONTRADICTION] {c.contradiction_type or '?'}: "
                    f"'{c.contradicts_claim[:80]}'"
                )

        # 4. Top genome priors
        priors = self.smem_get_priors()
        top = sorted(priors.items(), key=lambda x: x[1].get("fires", 0), reverse=True)[:8]
        if top:
            parts.append("\n## Genome Priors (Project-Specific Capsule Weights)")
            for cid, data in top:
                parts.append(
                    f"  {cid}: fires={data.get('fires',0)} "
                    f"confidence={data.get('confidence',0):.2f}"
                )

        return "\n".join(parts) if parts else "(no prior context for this project)"

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

