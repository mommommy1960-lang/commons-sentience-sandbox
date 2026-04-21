#!/usr/bin/env python3
"""
scripts/run_stage14_confirmatory_comparison.py
===============================================
Thin wrapper: ensures repo root is on sys.path, then delegates to the
data_analysis module.

Usage
-----
python scripts/run_stage14_confirmatory_comparison.py
python scripts/run_stage14_confirmatory_comparison.py \\
    --fermi outputs/stage14_confirmatory/fermi/stage14_confirmatory_fermi_summary.json
"""
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.run_stage14_confirmatory_comparison import main

sys.exit(main())
