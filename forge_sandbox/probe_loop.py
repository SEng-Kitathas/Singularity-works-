
from .intake import classify
from .facts import Fact, FactBus
from .switchboard import run_switchboard
from .genome_gates import evaluate as evaluate_gates
from .assurance import evaluate_assurance
from .remediation import plan_remediation, reassess_obligations

def probe_once(filename, code):
    intake = classify(code)
    bus = FactBus()
    for finding in intake["findings"]:
        bus.publish(Fact(kind="finding", payload={"finding": finding, "summary": finding, "code": code}))
    switch = run_switchboard(bus.as_dicts())
    subject = {"filename": filename, "code": code, "language": intake["language"], "front_door_mode": intake["front_door_mode"], "trace_links":[{"source":"intake","target":"pipeline"}]}
    gates = evaluate_gates(subject)
    assurance = evaluate_assurance(gates)
    pipeline_results=[]
    current_patch_state = code
    current_remaining = list(assurance["assurance_rollup"]["residual"])
    for cand in switch["candidates"]:
        plan = plan_remediation(current_patch_state, cand["axiom"], intake["language"])
        current_patch_state = plan["proposed_patch"]
        current_remaining = reassess_obligations(current_remaining, plan)
        disposition = "promoted_for_review" if current_remaining != assurance["assurance_rollup"]["residual"] else "degraded"
        pipeline_results.append({
            "axiom": cand["axiom"],
            "disposition": disposition,
            "promotion_safe": False,
            "review_required": True,
            "pre_obligations": list(assurance["assurance_rollup"]["residual"]),
            "post_obligations": list(current_remaining),
            "remediation_plan": plan,
        })
    return {
        "file": filename,
        "intake": intake,
        "switchboard": switch,
        "gates": gates,
        "assurance": assurance,
        "pipeline_results": pipeline_results,
        "patched_code": current_patch_state,
        "summary": {
            "language": intake["language"],
            "findings": intake["findings"],
            "semantic_markers": intake["semantic_markers"],
            "candidate_count": len(switch["candidates"]),
            "assurance_status": assurance["assurance_rollup"]["status"],
            "promoted_for_review_count": sum(1 for r in pipeline_results if r["disposition"]=="promoted_for_review"),
            "degraded_count": sum(1 for r in pipeline_results if r["disposition"]=="degraded"),
            "residual_obligations": sorted(set([o for r in pipeline_results for o in r.get("post_obligations", [])])),
        }
    }

def probe_loop(filename, code, max_rounds=3):
    rounds=[]
    current_code=code
    for i in range(max_rounds):
        result=probe_once(filename, current_code)
        result["round"]=i+1
        rounds.append(result)
        next_code=result["patched_code"]
        if next_code == current_code:
            break
        current_code=next_code
    return {"file": filename, "rounds": rounds, "final_summary": rounds[-1]["summary"], "final_code": current_code}
