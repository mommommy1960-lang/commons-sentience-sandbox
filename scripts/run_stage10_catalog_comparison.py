"""
Convenience runner for Stage 10 cross-catalog comparison.

Runs the comparison if both Fermi (Stage 9) and Swift (Stage 10) summary
JSONs are present in their default output locations.  Otherwise prints the
exact missing prerequisite and how to generate it.
"""
from __future__ import annotations
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT  = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.run_stage10_catalog_comparison import main

if __name__ == "__main__":
    sys.exit(main())
