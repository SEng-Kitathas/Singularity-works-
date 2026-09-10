from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from forge_semantic_delta_replay_v0_1_3 import build_plan, replay_plan
from forge_semantic_delta_materialization_bridge_v0_1 import build_materialization_bridge, bridge_fingerprint
from forge_semantic_materializer_v0_1 import plan_replace_fact_evidence, apply_patch_to_text
from forge_semantic_fact_ir_v0_1_2 import canonical_json
from forge_semantic_snapshot_delta_v0_4 import diff_snapshots, fact_semantic_key

TARGET = ROOT / "investigation" / "vuln_benchmark_quarry_20260902" / "PyGoat"
RUN = ROOT / "investigation" / "sw_forge_reconstruction" / "semantic_delta_materialization_bridge_pygoat_v0_1_20260909"
SANDBOX = RUN / "sandbox" / "PyGoat"


def load(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); assert spec.loader is not None
    sys.modules[name]=mod; spec.loader.exec_module(mod); return mod


def git_state():
    def g(args):
        r=subprocess.run(["git","-C",str(TARGET),*args],capture_output=True,text=True,timeout=20)
        return r.stdout.strip() if r.returncode==0 else f"ERR:{r.stderr[-300:]}"
    status=g(["status","--porcelain=v1","--untracked-files=no"])
    return {"head":g(["rev-parse","HEAD"]),"tracked_dirty_lines":len(status.splitlines()) if status else 0}


def copy_surface(source_texts):
    if SANDBOX.exists(): shutil.rmtree(SANDBOX)
    for logical,text in source_texts.items():
        p=SANDBOX/Path(logical.split('/',1)[1]); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')


def collect_sandbox():
    out={}
    for p in sorted(SANDBOX.rglob('*.py')):
        out[f"PyGoat/{str(p.relative_to(SANDBOX)).replace(chr(92),'/')}"]=p.read_text(encoding='utf-8',errors='replace')
    return out


def main() -> int:
    RUN.mkdir(parents=True,exist_ok=True)
    fixture=load('qualified_delta_fixture_bridge',CODE/'run_semantic_snapshot_delta_pygoat_v0_5.py')
    before=git_state(); baseline=fixture.source_set(); original=baseline[fixture.URL_PATH]
    route_line="    path('', views.home, name='homepage'),"
    replacement_line="    # homepage route removed by in-memory counterfactual"
    if route_line not in original: raise SystemExit('qualified homepage route fixture absent')
    target_sources=dict(baseline); target_sources[fixture.URL_PATH]=original.replace(route_line,replacement_line,1)

    base,_=fixture.build_snapshot(baseline,'bridge_base')
    target,_=fixture.build_snapshot(target_sources,'bridge_target')
    semantic_plan=build_plan(base,target)
    bridge=build_materialization_bridge(base,target,semantic_plan)
    bridge2=build_materialization_bridge(base,target,semantic_plan)
    if len(bridge.removed_anchors)!=1: raise RuntimeError(f'expected one removed semantic anchor, got {len(bridge.removed_anchors)}')
    anchor=bridge.removed_anchors[0]

    # Explicit lowering policy: this fixture maps removal of the homepage route relation
    # to replacement of its exact evidence line with the exact target counterfactual line.
    source_text=baseline[anchor.source_path]
    old_bytes=source_text.encode('utf-8')[anchor.evidence_start_byte:anchor.evidence_end_byte]
    old_text=old_bytes.decode('utf-8')
    indentation=old_text[:len(old_text)-len(old_text.lstrip(' \t'))]
    newline='\r\n' if old_text.endswith('\r\n') else '\n' if old_text.endswith('\n') else ''
    lowering_text=f"{indentation}{replacement_line.strip()}{newline}"
    patch=plan_replace_fact_evidence(base,baseline,fact_id=anchor.fact_id,new_text=lowering_text,intended_operation=f"semantic_plan:{semantic_plan.plan_id}:remove:{anchor.semantic_key}")
    patch2=plan_replace_fact_evidence(base,baseline,fact_id=anchor.fact_id,new_text=lowering_text,intended_operation=f"semantic_plan:{semantic_plan.plan_id}:remove:{anchor.semantic_key}")

    stale_patch_rejected=False
    try: apply_patch_to_text(patch,source_text+'# drift')
    except ValueError: stale_patch_rejected=True

    copy_surface(baseline)
    sandbox_file=SANDBOX/Path(anchor.source_path.split('/',1)[1]); pre_text=sandbox_file.read_text(encoding='utf-8')
    post_text,apply_receipt=apply_patch_to_text(patch,pre_text); sandbox_file.write_text(post_text,encoding='utf-8')
    post_sources=collect_sandbox(); observed,_=fixture.build_snapshot(post_sources,'bridge_observed')
    observed_delta=diff_snapshots(base,observed)
    replay_target=replay_plan(base,semantic_plan,target_producer=target.producer,target_source_texts_by_path=target_sources)

    inverse=patch.inverse(); rollback_text,rollback_receipt=apply_patch_to_text(inverse,sandbox_file.read_text(encoding='utf-8')); sandbox_file.write_text(rollback_text,encoding='utf-8')
    rollback_sources=collect_sandbox(); rollback,_=fixture.build_snapshot(rollback_sources,'bridge_rollback')
    after=git_state()

    checks={
      'target_clean_before':before['tracked_dirty_lines']==0,
      'target_clean_after':after['tracked_dirty_lines']==0,
      'target_head_unchanged':before['head']==after['head'],
      'semantic_plan_authority_none':semantic_plan.delta_authority=='NONE',
      'bridge_authority_none':bridge.bridge_authority=='NONE',
      'bridge_deterministic':bridge.as_dict()==bridge2.as_dict(),
      'bridge_fingerprint_deterministic':bridge_fingerprint(bridge)==bridge_fingerprint(bridge2),
      'one_removed_semantic_key':len(bridge.removed_semantic_keys)==1,
      'no_added_semantic_keys':len(bridge.added_semantic_keys)==0,
      'no_ambiguous_semantic_keys':len(bridge.ambiguous_semantic_keys)==0,
      'no_multiplicity_changes':bridge.multiplicity_change_count==0,
      'one_exact_removed_anchor':len(bridge.removed_anchors)==1,
      'anchor_semantic_key_matches_patch':patch.intended_semantic_key==anchor.semantic_key,
      'anchor_fact_matches_patch':patch.intended_fact_id==anchor.fact_id,
      'anchor_source_matches_patch':patch.source_path==anchor.source_path and patch.expected_source_sha256==anchor.source_sha256,
      'anchor_evidence_matches_patch':patch.start_byte==anchor.evidence_start_byte and patch.end_byte==anchor.evidence_end_byte and patch.expected_snippet_sha256==anchor.evidence_snippet_sha256,
      'patch_plan_deterministic':patch==patch2,
      'patch_authority_none':patch.materializer_authority=='NONE',
      'stale_patch_rejected':stale_patch_rejected,
      'materialized_source_exact_target':post_sources==target_sources,
      'materialized_snapshot_exact_target':observed.bundle_id==target.bundle_id and canonical_json(observed.as_dict())==canonical_json(target.as_dict()),
      'replay_snapshot_exact_target':replay_target.bundle_id==target.bundle_id and canonical_json(replay_target.as_dict())==canonical_json(target.as_dict()),
      'materialized_and_replay_targets_identical':canonical_json(observed.as_dict())==canonical_json(replay_target.as_dict()),
      'observed_removed_keys_equal_bridge':tuple(observed_delta.removed_semantic_keys)==bridge.removed_semantic_keys,
      'observed_added_keys_equal_bridge':tuple(observed_delta.added_semantic_keys)==bridge.added_semantic_keys,
      'rollback_source_exact':rollback_sources==baseline,
      'rollback_snapshot_exact':rollback.bundle_id==base.bundle_id and canonical_json(rollback.as_dict())==canonical_json(base.as_dict()),
      'sandbox_only_mutation':before==after,
    }
    summary={
      'schema':'forge.semantic-delta-materialization-bridge-pygoat/0.1',
      'verdict':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'pass_count':sum(checks.values()),'check_count':len(checks),
      'git':{'before':before,'after':after},
      'semantic_plan':{'plan_id':semantic_plan.plan_id,'operations':len(semantic_plan.operations),'base_bundle_id':semantic_plan.base_bundle_id,'target_bundle_id':semantic_plan.target_bundle_id},
      'bridge':bridge.as_dict(),'bridge_fingerprint':bridge_fingerprint(bridge),
      'patch':patch.as_dict(),'apply_receipt':apply_receipt,'rollback_receipt':rollback_receipt,
      'observed_delta':observed_delta.as_dict(),
      'artifact_hashes':{
        'bridge':hashlib.sha256((CODE/'forge_semantic_delta_materialization_bridge_v0_1.py').read_bytes()).hexdigest(),
        'replay':hashlib.sha256((CODE/'forge_semantic_delta_replay_v0_1_3.py').read_bytes()).hexdigest(),
        'materializer':hashlib.sha256((CODE/'forge_semantic_materializer_v0_1.py').read_bytes()).hexdigest(),
      },
      'claim_ceiling':'EXACT_REMOVAL_DELTA_TO_EVIDENCE_PATCH_BRIDGE_ON_QUALIFIED_PYGOAT_ROUTE_ONLY',
      'not_proven':['automatic source lowering from arbitrary semantics','semantic additions/substitutions','multi-file transaction planning','cross-language lowering','concurrent edit merge','public Core API promotion']
    }
    (RUN/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (RUN/'semantic_plan.json').write_text(json.dumps(semantic_plan.as_dict(),indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8')
    (RUN/'bridge_plan.json').write_text(json.dumps(bridge.as_dict(),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (RUN/'patch_plan.json').write_text(json.dumps(patch.as_dict(),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    files=[]
    for p in sorted(RUN.iterdir()):
        if p.is_file() and p.name!='output_manifest.json':
            b=p.read_bytes(); files.append({'path':p.name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
    (RUN/'output_manifest.json').write_text(json.dumps({'schema':'forge.semantic-delta-materialization-bridge-output-manifest/0.1','files':files,'count':len(files)},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0 if summary['verdict']=='PASS' else 2

if __name__=='__main__': raise SystemExit(main())
