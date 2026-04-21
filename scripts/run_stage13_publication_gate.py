"""
Convenience wrapper — runs the Stage 13 publication gate on default paths.

Usage
-----
    python scripts/run_stage13_publication_gate.py
    python scripts/run_stage13_publication_gate.py --help
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.run_stage13_publication_gate import main

if __name__ == "__main__":
    sys.exit(main())
