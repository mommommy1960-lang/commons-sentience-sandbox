"""Tests for quantum_benchmark_audit.py."""

import json
import pytest
from pathlib import Path
from reality_audit.benchmarks.quantum_double_slit import run_all_conditions
from reality_audit.analysis.quantum_benchmark_audit import (
    run_quantum_benchmark_audit,
    _q1_audit_coherent_vs_decohered,
    _q2_audit_decoherence_trend,
    _q3_audit_seed_stability,
)


@pytest.fixture(scope="module")
def full_results():
    return run_all_conditions(
        n_trials=500,
        n_bins=40,
        seed=0,
        screen_width=20.0,
        slit_separation=4.0,
        slit_width=1.0,
        wavelength=1.0,
        screen_distance=100.0,
        partial_gammas=[0.0, 0.25, 0.5, 0.75, 1.0],
    )


class TestQ1CoherentVsDecohered:
    def test_pass_for_good_conditions(self, full_results):
        q1 = _q1_audit_coherent_vs_decohered(full_results)
        assert q1["PASS"] is True

    def test_returns_required_keys(self, full_results):
        q1 = _q1_audit_coherent_vs_decohered(full_results)
        for key in ["question", "v_coherent", "v_decohered", "PASS"]:
            assert key in q1

    def test_coherent_visibility_higher_than_decohered(self, full_results):
        q1 = _q1_audit_coherent_vs_decohered(full_results)
        assert q1["v_coherent"] > q1["v_decohered"]


class TestQ2DecoherenceTrend:
    def test_pass_for_good_sweep(self, full_results):
        q2 = _q2_audit_decoherence_trend(full_results)
        assert q2["PASS"] is True

    def test_slope_negative(self, full_results):
        q2 = _q2_audit_decoherence_trend(full_results)
        assert q2["visibility_vs_gamma_slope"] < 0.0

    def test_monotone_true(self, full_results):
        q2 = _q2_audit_decoherence_trend(full_results)
        assert q2["is_monotone_non_increasing"] is True


class TestQ3SeedStability:
    def test_pass_with_small_runs(self):
        q3 = _q3_audit_seed_stability(
            n_trials=500,
            n_bins=40,
            screen_width=20.0,
            seeds=[0, 1, 2],
        )
        assert q3["PASS"] is True

    def test_cv_coherent_below_threshold(self):
        q3 = _q3_audit_seed_stability(n_trials=500, n_bins=40, screen_width=20.0, seeds=[0, 1])
        assert q3["cv_coherent"] < 0.05


class TestRunQuantumBenchmarkAudit:
    def test_overall_pass(self, full_results):
        report = run_quantum_benchmark_audit(
            full_results,
            run_seed_stability=True,
            seed_stability_kwargs={"n_trials": 500, "n_bins": 40, "screen_width": 20.0, "seeds": [0, 1]},
        )
        assert report["overall_PASS"] is True

    def test_verdict_audit_passed(self, full_results):
        report = run_quantum_benchmark_audit(
            full_results,
            run_seed_stability=False,
        )
        # Q3 skipped means PASS=None → overall_PASS should be False only if explicitly failed
        assert "verdict" in report

    def test_writes_json_files(self, full_results, tmp_path):
        run_quantum_benchmark_audit(full_results, output_dir=tmp_path, run_seed_stability=False)
        assert (tmp_path / "audit_summary.json").exists()
        assert (tmp_path / "audit_comparison_report.json").exists()

    def test_audit_summary_parseable(self, full_results, tmp_path):
        run_quantum_benchmark_audit(full_results, output_dir=tmp_path, run_seed_stability=False)
        data = json.loads((tmp_path / "audit_summary.json").read_text())
        assert "verdict" in data

    def test_comparison_report_has_comparisons(self, full_results, tmp_path):
        run_quantum_benchmark_audit(full_results, output_dir=tmp_path, run_seed_stability=False)
        data = json.loads((tmp_path / "audit_comparison_report.json").read_text())
        assert "comparisons" in data
