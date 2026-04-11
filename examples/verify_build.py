from __future__ import annotations
from pathlib import Path
import json
import compileall
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from singularity_works.runtime import demo_run
from singularity_works.evidence_ledger import EvidenceLedger
from singularity_works.enforcement import EnforcementEngine
from singularity_works.gates import syntax_gate, simplification_gate
from singularity_works.genome import RadicalMapGenome
from singularity_works.genome_gate_factory import genome_gates_from_bundle
from singularity_works.laws import SELF_QA_REQUIREMENT_TEXT

def self_audit(root: Path) -> dict:
    # Self-audit uses genome-derived gates — the forge audits itself with the same
    # gates it applies outward. Genome is loaded from the project configs.
    genome_path = root / "configs" / "seed_genome.json"
    genome = RadicalMapGenome.load(genome_path) if genome_path.exists() else None
    # All capsules are relevant for self-audit — select with broad capabilities
    bundle = genome.bundle_for_task(
        language="python",
        capabilities=["resource_safety", "trust_boundary_hardening", "code_completeness", "law_enforcement"],
        preferred_radicals=["TRUST", "RESOURCE", "CLEAN"],
    ) if genome else {"selected_patterns": []}
    genome_gates = genome_gates_from_bundle(bundle, genome) if genome else []

    def make_engine() -> EnforcementEngine:
        eng = EnforcementEngine()
        eng.register(syntax_gate())
        eng.register(simplification_gate())
        for g in genome_gates:
            eng.register(g)
        return eng
    package = root / 'singularity_works'
    files = sorted(package.glob('*.py'))
    results = []
    for path in files:
        content = path.read_text(encoding='utf-8')
        subject = {
            'artifact_id': f'self:{path.name}',
            'requirement_id': 'REQ-SELF-QA',
            'requirement_text': SELF_QA_REQUIREMENT_TEXT,
            'content': content,
            'family': 'function_module',
            'radicals': ['TRUST', 'RESOURCE'],
        }
        summary = make_engine().run(subject)
        results.append({'file': path.name, 'counts': summary.counts, 'residuals': summary.open_residuals})
    totals = {'pass': 0, 'warn': 0, 'fail': 0, 'residual': 0}
    for item in results:
        for k, v in item['counts'].items():
            totals[k] = totals.get(k, 0) + v
    failing_files = [r['file'] for r in results if r['counts'].get('fail', 0) > 0]
    warning_files = [r['file'] for r in results if r['counts'].get('warn', 0) > 0]
    return {'totals': totals, 'failing_files': failing_files, 'warning_files': warning_files, 'results': results}

if __name__ == '__main__':
    base = ROOT
    ledger = EvidenceLedger(base / 'evidence.jsonl')
    ledger.reset()
    compile_ok = compileall.compile_dir(str(base / 'singularity_works'), quiet=1, force=True)
    good = demo_run(base, good=True, show_hud=False)
    bad = demo_run(base, good=False, show_hud=False)
    bad_remediated = demo_run(base, good=False, show_hud=False, apply_transformations=True)
    security = demo_run(base, show_hud=False, scenario="security")
    security_remediated = demo_run(base, show_hud=False, apply_transformations=True, scenario="security")
    execution = demo_run(base, show_hud=False, scenario="execution")
    execution_remediated = demo_run(base, show_hud=False, apply_transformations=True, scenario="execution")
    self_report = self_audit(base)
    self_totals = self_report.get('totals', {})
    self_verification = {
        'passed': self_totals.get('fail', 0) == 0,
        'clean': self_totals.get('fail', 0) == 0 and self_totals.get('warn', 0) == 0,
        'fail_count': self_totals.get('fail', 0),
        'warn_count': self_totals.get('warn', 0),
        'failing_files': self_report.get('failing_files', []),
        'warning_files': self_report.get('warning_files', []),
    }
    report = {
        'compile_ok': compile_ok,
        'good_assurance': good['assurance']['status'],
        'bad_assurance': bad['assurance']['status'],
        'good_gate_counts': good['gate_counts'],
        'bad_gate_counts': bad['gate_counts'],
        'good_session_rollup': good['session_rollup'],
        'bad_session_rollup': bad['session_rollup'],
        'good_primary_claim': good['primary_claim_rollup'],
        'bad_primary_claim': bad['primary_claim_rollup'],
        'good_recursive_audit': good['recursive_audit'],
        'bad_recursive_audit': bad['recursive_audit'],
        'security_assurance': security['assurance']['status'],
        'security_gate_counts': security['gate_counts'],
        'security_recursive_audit': security['recursive_audit'],
        'security_remediated_assurance': security_remediated['assurance']['status'],
        'security_remediated_gate_counts': security_remediated['gate_counts'],
        'security_remediated_recursive_audit': security_remediated['recursive_audit'],
        'execution_assurance': execution['assurance']['status'],
        'execution_gate_counts': execution['gate_counts'],
        'execution_recursive_audit': execution['recursive_audit'],
        'execution_remediated_assurance': execution_remediated['assurance']['status'],
        'execution_remediated_gate_counts': execution_remediated['gate_counts'],
        'execution_remediated_recursive_audit': execution_remediated['recursive_audit'],
        'bad_remediated_assurance': bad_remediated['assurance']['status'],
        'bad_remediated_gate_counts': bad_remediated['gate_counts'],
        'bad_remediated_recursive_audit': bad_remediated['recursive_audit'],
        'bad_remediated_transformations': len(bad_remediated.get('applied_transformations', [])),
        'security_remediated_transformations': len(security_remediated.get('applied_transformations', [])),
        'execution_remediated_transformations': len(execution_remediated.get('applied_transformations', [])),
        'good_claim_count': len(good['requirement_rollup']['claim_rollups']),
        'bad_claim_count': len(bad['requirement_rollup']['claim_rollups']),
        'good_transformations': len(good.get('transformation_plan', [])),
        'bad_transformations': len(bad.get('transformation_plan', [])),
        'self_audit': self_report,
        'self_verification': self_verification,
        'expected': {'compile_ok': True, 'good_assurance': 'green', 'bad_assurance': 'red', 'bad_remediated_assurance': 'green', 'security_assurance': 'red', 'security_remediated_assurance': 'green', 'execution_assurance': 'red', 'execution_remediated_assurance': 'green', 'self_verification_passed': True}
    }
    (base / 'build_verification_summary.json').write_text(json.dumps(report, indent=2))
    md = []
    md.append('# Singularity Works Build Verification Report v0.8')
    md.append('')
    md.append(f"- compile_ok: **{compile_ok}**")
    md.append(f"- good_assurance: **{good['assurance']['status']}**")
    md.append(f"- bad_assurance: **{bad['assurance']['status']}**")
    md.append(f"- good_gate_counts: `{good['gate_counts']}`")
    md.append(f"- bad_gate_counts: `{bad['gate_counts']}`")
    md.append(f"- good_recursive_audit: `{good['recursive_audit']}`")
    md.append(f"- bad_recursive_audit: `{bad['recursive_audit']}`")
    md.append(f"- good_claim_count: **{len(good['requirement_rollup']['claim_rollups'])}**")
    md.append(f"- bad_claim_count: **{len(bad['requirement_rollup']['claim_rollups'])}**")
    md.append(f"- self_audit_totals: `{self_report['totals']}`")
    md.append(f"- self_verification_passed: **{self_verification['passed']}**")
    md.append(f"- self_verification_clean: **{self_verification['clean']}**")
    md.append(f"- self_audit_failing_files: `{self_report['failing_files']}`")
    md.append(f"- self_audit_warning_files: `{self_report['warning_files']}`")
    md.append('')
    md.append('## Recursive self-check')
    md.append('- Good path should have no naivety flags and green assurance.')
    md.append('- Bad path should produce real gate/monitor failures and red assurance.')
    md.append('- The forge should also QA its own Python modules each pass.')
    (base / 'BUILD_VERIFICATION_REPORT_v0_7.md').write_text(chr(10).join(md))
    print(json.dumps(report, indent=2))
