import os
import sys

# Ensure the repo root is importable so `from avora_backend import ...` works
# regardless of the CWD pytest is launched from.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
