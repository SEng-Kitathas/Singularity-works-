# Main/Core ↔ App Development Division Evaluation — Verbatim Main Evaluation

Date received by App: 2026-09-02
Purpose: preserve Main's exact evaluation of the two-strand development topology for App-side design pressure.

--- BEGIN VERBATIM MAIN EVALUATION ---

Mode: DISCUSSION
Role: R4 Convergence Refiner

Yes — as a development division, I think it’s a strong structure, with one important condition: treat it as two development strands of one product, not two products or two permanent architectural kingdoms.

The division is unusually clean because it separates by kind of pressure, not by arbitrary technology boundary.

Main/Core asks: What is Forge actually allowed to mean? It owns canonical semantics, contracts, evidence/currentness, LBE substrate, materialization rules, capability logic, and shared interfaces.

App asks: Can a human actually use this thing under real runtime conditions? It owns recovery, renderer/process isolation, shell, Ergo, SmartCanvas, terminal/HUD behavior, interaction design, operator workflow, and the ugly embodiment failures that only appear once software becomes a product.

That is much better than a simplistic “backend team / frontend team” split. App can pressure Main with reality without becoming authoritative over semantics, while Main can evolve semantics without constantly destabilizing the renderer and UX.

The main advantages are parallelism, blast-radius containment, clearer ownership, and better architecture pressure. App becomes an aggressive consumer of Core interfaces. If App keeps needing to reach behind an interface, the interface is probably wrong. If Main starts implementing renderer-specific concepts to make App happy, Core is probably leaking product concerns. That tension is useful.

The danger is allowing the strands to become culturally or technically independent. The failure modes are predictable: duplicated logic, private App substitutes for Core behavior, Main interfaces designed in a vacuum, huge delayed merges, and “ours vs theirs” ownership. Your base-pair/checkpoint discipline is specifically what makes the division viable.

I’d operate it under five rules:

1. Canonical truth has one owner. App may cache/project/visualize Core semantics, never silently reimplement them.
2. App discoveries flow upstream as requirements and hostile examples, not copied code by default.
3. Qualified Main changes flow downstream early. Don’t let App trail five major Core generations.
4. App promotion flows upstream late. Product embodiment earns qualification before Main absorbs it.
5. Every cross-strand interface has an explicit contract and version/currentness identity. That makes drift visible instead of social.

There’s also a useful asymmetry: Main should generally be more conservative; App should generally be more experimental. App can try strange UX, renderer architecture, workflows, coprocessor ideas, lenses, interaction mechanics, etc. Main only absorbs the generalized mechanism after the App proves it matters. Conversely, Main can strengthen semantic laws without demanding App immediately rebuild itself around every lab experiment.

So I would keep this division.

I would not make it permanent in the sense of “these codebases shall always remain separate.” Think of it as an organizational and qualification topology. The Git topology can eventually converge while the two development roles remain distinct.

That is probably the strongest version of the double-helix idea:

Main evolves what Forge is. App evolves what Forge feels like to operate. Each strand continuously constrains and improves the other.

That’s a very good division for this project.

--- END VERBATIM MAIN EVALUATION ---
