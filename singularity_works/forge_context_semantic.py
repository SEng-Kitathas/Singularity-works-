from __future__ import annotations

from .forge_context_blocks import (
    BiTemporalBlock,
    ContradictionBlock,
    EpistemicStatus,
    SemanticBlock,
    _encode_contradiction,
    _encode_semantic,
    _now,
)


class ForgeContextSemanticMixin:
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

