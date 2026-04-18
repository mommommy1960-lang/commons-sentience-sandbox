"""Tests for plot_advanced_quantum.py."""

import pytest
from pathlib import Path
from reality_audit.benchmarks.advanced_quantum_double_slit import run_all_conditions
from reality_audit.analysis.plot_advanced_quantum import (
    plot_single_condition,
    plot_overlap_sweep,
    plot_visibility_vs_distinguishability,
    plot_hundred_run_stability,
    plot_advanced_quantum,
)


@pytest.fixture(scope="module")
def small_results():
    return run_all_conditions(
        n_trials=100, n_bins=20, seed=0, screen_width=10.0,
        eraser_overlap=0.5, overlap_values=[1.0, 0.5, 0.0],
    )


@pytest.fixture(scope="module")
def fake_agg():
    return {
        "two_slit_coherent": {"fringe_visibility_empirical": {"mean": 0.85, "std": 0.01}},
        "two_slit_which_path": {"fringe_visibility_empirical": {"mean": 0.30, "std": 0.02}},
        "n_repeated_runs": 10,
    }


class TestPlotSingleCondition:
    def test_creates_file(self, small_results, tmp_path):
        out = tmp_path / "one_slit.png"
        plot_single_condition(small_results["one_slit"], "One slit", out)
        assert out.exists()

    def test_file_nonempty(self, small_results, tmp_path):
        out = tmp_path / "coherent.png"
        plot_single_condition(small_results["two_slit_coherent"], "Coherent", out)
        assert out.stat().st_size > 500


class TestPlotOverlapSweep:
    def test_creates_file(self, small_results, tmp_path):
        out = tmp_path / "sweep.png"
        plot_overlap_sweep(small_results["overlap_sweep"], out)
        assert out.exists()

    def test_empty_no_error(self, tmp_path):
        out = tmp_path / "empty.png"
        plot_overlap_sweep([], out)
        assert not out.exists()


class TestPlotVisibilityVsDistinguishability:
    def test_creates_file(self, small_results, tmp_path):
        out = tmp_path / "vd.png"
        probs_wp = small_results["two_slit_which_path"]["probability_profile"]
        probs_c = small_results["two_slit_coherent"]["probability_profile"]
        plot_visibility_vs_distinguishability(small_results["overlap_sweep"], probs_wp, probs_c, out)
        assert out.exists()


class TestPlotHundredRunStability:
    def test_creates_file(self, fake_agg, tmp_path):
        out = tmp_path / "stability.png"
        plot_hundred_run_stability(fake_agg, out)
        assert out.exists()


class TestPlotAdvancedQuantum:
    def test_returns_list(self, small_results, fake_agg, tmp_path):
        paths = plot_advanced_quantum(small_results, aggregate_summary=fake_agg, output_dir=tmp_path)
        assert isinstance(paths, list)

    def test_all_exist(self, small_results, fake_agg, tmp_path):
        paths = plot_advanced_quantum(small_results, aggregate_summary=fake_agg, output_dir=tmp_path)
        for p in paths:
            assert Path(p).exists()

    def test_expected_filenames(self, small_results, fake_agg, tmp_path):
        paths = plot_advanced_quantum(small_results, aggregate_summary=fake_agg, output_dir=tmp_path)
        names = {Path(p).name for p in paths}
        for fn in ["one_slit_distribution.png", "two_slit_coherent_distribution.png",
                   "overlap_sweep.png", "visibility_vs_distinguishability.png"]:
            assert fn in names
