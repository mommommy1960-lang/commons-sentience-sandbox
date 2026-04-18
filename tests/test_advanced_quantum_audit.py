"""Tests for advanced_quantum_audit.py."""

import json
import pytest
from pathlib import Path
from reality_audit.benchmarks.advanced_quantum_double_slit import run_all_conditions
from reality_audit.benchmarks.advanced_quantum_runner import run_advanced_benchmark
from reality_audit.analysis.advanced_quantum_audit import (
    run_advanced_audit,
    _q1_coherent_vs_which_path,
    _q2_visibility_vs_distinguishability,
    _q3_stability,
    _q4_eraser_recovery,
)


@pytest.fixture(scope="module")
def full_results():
    return run_all_conditions(
        n_trials=500, n_bins=40, seed=0, screen_width=20.0,
        eraser_overlap=0.5,
        overlap_values=[1.0, 0.75, 0.5, 0.25, 0.0],
    )


@pytest.fixture(scope="module")
def fake_agg():
    """Minimal aggregate_summary for Q3 testing without running 100 full runs."""
    return {
        "n_repeated_runs": 10,
        "two_slit_coherent": {"fringe_visibility_empirical": {"mean": 0.85, "std": 0.01, "cv": 0.012}},
        "two_slit_which_path": {"fringe_visibility_empirical": {"mean": 0.30, "std": 0.02, "cv": 0.06}},
        "stability_assessment": {
            "coherent_cv": 0.012,
            "which_path_cv": 0.04,
            "stable": True,
            "conditions_separated": True,
        },
    }


class TestQ1:
    def test_pass(self, full_results):
        q1 = _q1_coherent_vs_which_path(full_results)
        assert q1["PASS"] is True

    def test_keys_present(self, full_results):
        q1 = _q1_coherent_vs_which_path(full_results)
        for k in ["v_coherent", "v_which_path", "PASS"]:
            assert k in q1


class TestQ2:
    def test_pass(self, full_results):
        q2 = _q2_visibility_vs_distinguishability(full_results)
        assert q2["PASS"] is True

    def test_monotone(self, full_results):
        q2 = _q2_visibility_vs_distinguishability(full_results)
        assert q2["visibility_monotone_decreasing"] is True

    def test_theoretical_bounds_satisfied(self, full_results):
        q2 = _q2_visibility_vs_distinguishability(full_results)
        assert q2["all_theoretical_complementarity_bounds_satisfied"] is True


class TestQ3:
    def test_pass_with_fake_agg(self, fake_agg):
        q3 = _q3_stability(fake_agg)
        assert q3["PASS"] is True

    def test_keys_present(self, fake_agg):
        q3 = _q3_stability(fake_agg)
        for k in ["cv_coherent", "cv_which_path", "conditions_separated", "PASS"]:
            assert k in q3


class TestQ4:
    def test_pass(self, full_results):
        q4 = _q4_eraser_recovery(full_results)
        assert q4["PASS"] is True

    def test_eraser_closer_to_coherent(self, full_results):
        q4 = _q4_eraser_recovery(full_results)
        assert q4["eraser_closer_to_coherent_than_which_path"] is True


class TestRunAdvancedAudit:
    def test_writes_json_files(self, full_results, fake_agg, tmp_path):
        run_advanced_audit(full_results, fake_agg, output_dir=tmp_path)
        assert (tmp_path / "audit_summary.json").exists()
        assert (tmp_path / "audit_comparison_report.json").exists()

    def test_verdict_string_valid(self, full_results, fake_agg):
        report = run_advanced_audit(full_results, fake_agg)
        assert report["verdict"] in {"AUDIT_PASSED", "AUDIT_FAILED"}

    def test_comparison_report_parseable(self, full_results, fake_agg, tmp_path):
        run_advanced_audit(full_results, fake_agg, output_dir=tmp_path)
        data = json.loads((tmp_path / "audit_comparison_report.json").read_text())
        assert "comparisons" in data
