
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from singularity_works.runtime import demo_run

if __name__ == '__main__':
    demo_run(ROOT, good=True, show_hud=True)
