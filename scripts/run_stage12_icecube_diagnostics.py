"""Convenience wrapper for Stage 12 IceCube diagnostics runner."""

from __future__ import annotations

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.run_stage12_icecube_diagnostics import main

if __name__ == "__main__":
    sys.exit(main())
