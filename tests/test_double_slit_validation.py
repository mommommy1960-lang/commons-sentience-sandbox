"""
test_double_slit_validation.py
==============================
Validation tests for the double-slit diagnostics benchmark runner.

These tests verify expected trend behavior across coherent, decohered,
and measurement modes using tolerant thresholds.
"""

from __future__ import annotations

import json
import os

from reality_audit.data_analysis.double_slit_sim import run_double_slit_sim
from reality_audit.data_analysis.run_double_slit_diagnostics import run_double_slit_diagnostics


def test_coherent_mode_has_interference():
    result = run_double_slit_sim(
        coherence=1.0,
        decoherence_strength=0.0,
        measurement_on=False,
        seed=42,
    )
    assert result["interference_detected"] is True
    assert result["visibility"] > 0.5


def test_decohered_mode_reduces_interference_vs_coherent():
    coherent = run_double_slit_sim(
        coherence=1.0,
        decoherence_strength=0.0,
        measurement_on=False,
        seed=42,
    )
    decohered = run_double_slit_sim(
        coherence=1.0,
        decoherence_strength=0.7,
        measurement_on=False,
        seed=43,
    )
    assert decohered["visibility"] < coherent["visibility"]
    assert decohered["visibility"] < 0.7


def test_measurement_mode_strongly_suppresses_interference():
    coherent = run_double_slit_sim(
        coherence=1.0,
        decoherence_strength=0.0,
        measurement_on=False,
        seed=42,
    )
    measured = run_double_slit_sim(
        coherence=1.0,
        decoherence_strength=0.0,
        measurement_on=True,
        seed=44,
    )
    assert measured["visibility"] < coherent["visibility"]
    assert measured["visibility"] < 0.2
    assert measured["interference_detected"] is False


def test_diagnostics_runner_creates_summary_artifacts(tmp_path):
    out_dir = str(tmp_path / "double_slit_diag")
    result = run_double_slit_diagnostics(
        output_dir=out_dir,
        name="diag_test",
        num_particles=1500,
        screen_points=240,
        seed=101,
    )

    assert os.path.isfile(result["json_path"])
    assert os.path.isfile(result["md_path"])
    assert os.path.isfile(result["manifest_path"])

    # Per-mode artifacts should exist. Plot may be skipped if matplotlib is absent.
    for mode in ("coherent", "decohered", "measurement"):
        mode_dir = os.path.join(out_dir, mode)
        assert os.path.isdir(mode_dir)
        assert os.path.isfile(os.path.join(mode_dir, f"double_slit_{mode}_report.json"))
        assert os.path.isfile(os.path.join(mode_dir, f"double_slit_{mode}_summary.md"))
        assert os.path.isfile(os.path.join(mode_dir, f"double_slit_{mode}_intensity.csv"))


def test_diagnostics_json_contains_expected_fields_and_trends(tmp_path):
    out_dir = str(tmp_path / "double_slit_diag_json")
    result = run_double_slit_diagnostics(
        output_dir=out_dir,
        name="diag_test_json",
        seed=202,
    )

    with open(result["json_path"]) as f:
        payload = json.load(f)

    assert "modes" in payload
    assert "comparisons" in payload
    assert "expectations" in payload
    assert "benchmark_readiness" in payload

    c = payload["modes"]["coherent"]["visibility"]
    d = payload["modes"]["decohered"]["visibility"]
    m = payload["modes"]["measurement"]["visibility"]

    assert c > d
    assert c > m
    assert m < 0.2
    assert payload["comparisons"]["visibility_drop_coherent_to_decohered"] > 0.0
    assert payload["comparisons"]["visibility_drop_coherent_to_measurement"] > 0.0
