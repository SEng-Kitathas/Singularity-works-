from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from forge_semantic_delta_replay_v0_1_3 import build_plan, replay_plan, SemanticDeltaPlan, DeltaOperation
from forge_semantic_fact_ir_v0_1_2 import canonical_json

TARGET = ROOT / "investigation" / "vuln_benchmark_quarry_20260902" / "PyGoat"
RUN = ROOT / "investigation" / "sw_forge_reconstruction" / "semantic_delta_replay_pygoat_v0_1_3_20260909"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def git_state():
    def g(args):
        r=subprocess.run(["git","-C",str(TARGET),*args],capture_output=True,text=True,timeout=20)
        return r.stdout.strip() if r.returncode==0 else f"ERR:{r.stderr[-300:]}"
    status=g(["status","--porcelain=v1","--untracked-files=no"])
    return {"head":g(["rev-parse","HEAD"]),"tracked_dirty_lines":len(status.splitlines()) if status else 0}


def main() -> int:
    fixture=load("qualified_delta_fixture_v05",CODE/"run_semantic_snapshot_delta_pygoat_v0_5.py")
    before=git_state()
    baseline=fixture.source_set()
    original=baseline[fixture.URL_PATH]
    comment=dict(baseline); comment[fixture.URL_PATH]=original+"\n# semantic-delta-noop\n"
    route_line="    path('', views.home, name='homepage'),"
    if route_line not in original:
        raise SystemExit("expected qualified PyGoat route fixture absent")
    removed=dict(baseline); removed[fixture.URL_PATH]=original.replace(route_line,"    # homepage route removed by in-memory counterfactual",1)

    old,_=fixture.build_snapshot(baseline,"replay_old")
    comment_snap,_=fixture.build_snapshot(comment,"replay_comment")
    removed_snap,_=fixture.build_snapshot(removed,"replay_removed")

    pc=build_plan(old,comment_snap)
    pc2=build_plan(old,comment_snap)
    pr=build_plan(old,removed_snap)
    reverse=build_plan(removed_snap,old)

    replay_comment=replay_plan(old,pc,target_producer=comment_snap.producer,target_source_texts_by_path=comment)
    replay_removed=replay_plan(old,pr,target_producer=removed_snap.producer,target_source_texts_by_path=removed)
    replay_reverse=replay_plan(removed_snap,reverse,target_producer=old.producer,target_source_texts_by_path=baseline)

    stale_rejected=False
    try:
        replay_plan(comment_snap,pr,target_producer=removed_snap.producer,target_source_texts_by_path=removed)
    except ValueError:
        stale_rejected=True

    tamper_rejected=False
    if pc.operations:
        ops=list(pc.operations); first=ops[0]
        ops[0]=DeltaOperation(first.operation_id,first.action,first.collection,first.key,"0"*64,first.after_sha256,first.value)
        bad=SemanticDeltaPlan(pc.plan_id,pc.base_bundle_id,pc.target_bundle_id,tuple(ops))
        try:
            replay_plan(old,bad,target_producer=comment_snap.producer,target_source_texts_by_path=comment)
        except ValueError:
            tamper_rejected=True

    after=git_state()
    checks={
        "target_clean_before":before["tracked_dirty_lines"]==0,
        "target_clean_after":after["tracked_dirty_lines"]==0,
        "target_head_unchanged":before["head"]==after["head"],
        "comment_plan_deterministic":pc.as_dict()==pc2.as_dict(),
        "comment_replay_exact_bundle_id":replay_comment.bundle_id==comment_snap.bundle_id,
        "comment_replay_exact_serialization":canonical_json(replay_comment.as_dict())==canonical_json(comment_snap.as_dict()),
        "semantic_removal_replay_exact_bundle_id":replay_removed.bundle_id==removed_snap.bundle_id,
        "semantic_removal_replay_exact_serialization":canonical_json(replay_removed.as_dict())==canonical_json(removed_snap.as_dict()),
        "reverse_replay_exact_bundle_id":replay_reverse.bundle_id==old.bundle_id,
        "reverse_replay_exact_serialization":canonical_json(replay_reverse.as_dict())==canonical_json(old.as_dict()),
        "stale_base_rejected":stale_rejected,
        "tampered_precondition_rejected":tamper_rejected,
        "authority_none":pc.delta_authority==pr.delta_authority==reverse.delta_authority=="NONE",
        "operations_nonempty":len(pc.operations)>0 and len(pr.operations)>0 and len(reverse.operations)>0,
    }
    summary={
        "schema":"forge.semantic-delta-replay-pygoat/0.1.3",
        "verdict":"PASS" if all(checks.values()) else "FAIL",
        "checks":checks,
        "pass_count":sum(checks.values()),
        "check_count":len(checks),
        "git":{"before":before,"after":after},
        "snapshots":{"old":old.bundle_id,"comment":comment_snap.bundle_id,"removed":removed_snap.bundle_id},
        "plans":{
            "comment":{"plan_id":pc.plan_id,"operations":len(pc.operations)},
            "removed":{"plan_id":pr.plan_id,"operations":len(pr.operations)},
            "reverse_removed_to_old":{"plan_id":reverse.plan_id,"operations":len(reverse.operations)},
        },
        "artifact_hashes":{
            "replay":hashlib.sha256((CODE/"forge_semantic_delta_replay_v0_1_3.py").read_bytes()).hexdigest(),
            "ir":hashlib.sha256((CODE/"forge_semantic_fact_ir_v0_1_2.py").read_bytes()).hexdigest(),
            "fixture":hashlib.sha256((CODE/"run_semantic_snapshot_delta_pygoat_v0_5.py").read_bytes()).hexdigest(),
        },
        "claim_ceiling":"EXACT_SEMANTIC_BUNDLE_REPLAY_OVER_QUALIFIED_PYGOAT_SNAPSHOTS_ONLY",
        "not_proven":[
            "source-code edit materialization",
            "semantic-preserving refactor equivalence",
            "cross-language transform lowering",
            "merge/conflict algebra for concurrent semantic edits",
            "large multi-repo replay performance",
        ],
    }
    RUN.mkdir(parents=True,exist_ok=True)
    (RUN/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (RUN/"comment_plan.json").write_text(json.dumps(pc.as_dict(),indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    (RUN/"removed_plan.json").write_text(json.dumps(pr.as_dict(),indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    (RUN/"reverse_plan.json").write_text(json.dumps(reverse.as_dict(),indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    manifest=[]
    for p in sorted(RUN.iterdir()):
        if p.is_file() and p.name!="output_manifest.json":
            b=p.read_bytes(); manifest.append({"path":p.name,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)})
    (RUN/"output_manifest.json").write_text(json.dumps({"schema":"forge.semantic-delta-replay-output-manifest/0.1.3","files":manifest,"count":len(manifest)},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0 if summary["verdict"]=="PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
