#!/usr/bin/env python3
"""
scripts/run_stage14_confirmatory_reruns.py
==========================================
Thin wrapper: ensures repo root is on sys.path, then delegates to the
data_analysis module.

Usage
-----
python scripts/run_stage14_confirmatory_reruns.py
python scripts/run_stage14_confirmatory_reruns.py --null-repeats 500 --axis-count 192
"""
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.run_stage14_confirmatory_reruns import main

sys.exit(main())
