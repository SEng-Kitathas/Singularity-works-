from pathlib import Path

from singularity_works.forge_context import ForgeContext
from singularity_works.orchestration import evaluate_artifact
from singularity_works.pattern_ir import normalize_source


def test_normalization_removes_comments_and_blank_lines():
    result = normalize_source(
        '''
        # comment
        def add(a, b):   # inline
            return a + b
        '''
    )
    assert result == ("def add(a, b):", "return a + b")


def test_demo_style_evaluation_creates_evidence(tmp_path: Path):
    context = ForgeContext(workspace=tmp_path, run_id="smoke")
    result = evaluate_artifact(context, "demo.py", "def add(a,b):\n    return a+b\n")
    assert result.accepted is True
    assert context.evidence_path.exists()
