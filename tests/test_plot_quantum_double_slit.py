"""Tests for plot_quantum_double_slit.py."""

import pytest
from pathlib import Path
from reality_audit.benchmarks.quantum_double_slit import run_all_conditions
from reality_audit.analysis.plot_quantum_double_slit import (
    plot_single_condition,
    plot_decoherence_sweep,
    plot_overlay_comparison,
    plot_visibility_vs_gamma,
    plot_quantum_double_slit,
)


@pytest.fixture(scope="module")
def small_results():
    return run_all_conditions(
        n_trials=100,
        n_bins=20,
        seed=0,
        screen_width=10.0,
        slit_separation=4.0,
        slit_width=1.0,
        wavelength=1.0,
        screen_distance=100.0,
        partial_gammas=[0.0, 0.5, 1.0],
    )


class TestPlotSingleCondition:
    def test_creates_file(self, small_results, tmp_path):
        out = tmp_path / "one_slit.png"
        plot_single_condition(small_results["one_slit"], "One slit", out)
        assert out.exists()

    def test_file_nonempty(self, small_results, tmp_path):
        out = tmp_path / "coherent.png"
        plot_single_condition(small_results["two_slit_coherent"], "Coherent", out)
        assert out.stat().st_size > 1000


class TestPlotDecoherenceSweep:
    def test_creates_file(self, small_results, tmp_path):
        out = tmp_path / "sweep.png"
        plot_decoherence_sweep(small_results["decoherence_sweep"], out)
        assert out.exists()

    def test_empty_sweep_no_error(self, tmp_path):
        out = tmp_path / "empty_sweep.png"
        plot_decoherence_sweep([], out)
        assert not out.exists()


class TestPlotOverlayComparison:
    def test_creates_file(self, small_results, tmp_path):
        out = tmp_path / "overlay.png"
        plot_overlay_comparison(small_results, out)
        assert out.exists()


class TestPlotVisibilityVsGamma:
    def test_creates_file(self, small_results, tmp_path):
        out = tmp_path / "vis_gamma.png"
        plot_visibility_vs_gamma(small_results["decoherence_sweep"], out)
        assert out.exists()

    def test_empty_sweep_no_error(self, tmp_path):
        out = tmp_path / "empty_vis.png"
        plot_visibility_vs_gamma([], out)
        assert not out.exists()


class TestPlotQuantumDoubleSlit:
    def test_returns_list_of_paths(self, small_results, tmp_path):
        paths = plot_quantum_double_slit(small_results, output_dir=tmp_path)
        assert isinstance(paths, list)
        assert len(paths) >= 4

    def test_all_paths_exist(self, small_results, tmp_path):
        paths = plot_quantum_double_slit(small_results, output_dir=tmp_path)
        for p in paths:
            assert Path(p).exists(), f"Missing: {p}"

    def test_expected_filenames(self, small_results, tmp_path):
        paths = plot_quantum_double_slit(small_results, output_dir=tmp_path)
        names = {Path(p).name for p in paths}
        for expected in [
            "one_slit_distribution.png",
            "two_slit_coherent_distribution.png",
            "two_slit_decohered_distribution.png",
            "overlay_comparison.png",
        ]:
            assert expected in names, f"Missing: {expected}"
