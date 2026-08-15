import sys
import os
from pathlib import Path

backend_dir = Path(__file__).parent / "avora backend"
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

import runpy
runpy.run_path(str(backend_dir / "main.py"), run_name="__main__")
