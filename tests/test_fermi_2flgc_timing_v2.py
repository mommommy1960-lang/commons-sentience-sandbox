import importlib.util
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fermi_v2", ROOT / "scripts/run_fermi_2flgc_timing_v2.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_official_catalog_reproduces_published_counts():
    catalog = MODULE.read_catalog(MODULE.CATALOG)
    original = [row for row in catalog.values() if row["time"] < "2018-08-04"]
    assert len(original) == 186
    assert sum(int(row["lle_bbbd_sig_detected"] or 0) == 1 for row in original) == 91
    assert sum(float(row["su_tsinput"] or 0) > 0 for row in original) == 169


def test_centered_rank_correlation_sign_and_scale():
    x = MODULE.centered_ranks(np.array([1.0, 2.0, 3.0]))
    y = MODULE.centered_ranks(np.array([10.0, 20.0, 30.0]))
    assert MODULE.correlation(x, y) == 1.0
    assert MODULE.correlation(x, y[::-1]) == -1.0


def test_frozen_configuration_prevents_automatic_promotion():
    import json

    config = json.loads(MODULE.CONFIG.read_text())
    assert config["status"] == "FROZEN_BEFORE_EVENT_CONTENT_INSPECTION"
    assert config["null"]["catalogs"] >= 100000
    assert config["trial_control"]["primary_tests"] == 1
    assert "No anomaly claim" in config["promotion_gate"]
