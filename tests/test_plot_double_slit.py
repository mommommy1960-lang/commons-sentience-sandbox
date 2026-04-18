"""
tests/test_plot_double_slit.py — Tests for double-slit plot generation.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from reality_audit.analysis.plot_double_slit import generate_all_double_slit_figures
from reality_audit.benchmarks.double_slit import run_all_conditions


class TestGenerateAllDoubleSlit:
    def test_returns_four_files(self, tmp_path):
        results = run_all_conditions(n_trials=500, n_bins=50, seed=0)
        figs_dir = tmp_path / "figures"
        written = generate_all_double_slit_figures(
            figures_dir=figs_dir,
            results=results,
        )
        assert len(written) == 4

    def test_all_four_files_exist(self, tmp_path):
        results = run_all_conditions(n_trials=500, n_bins=50, seed=0)
        figs_dir = tmp_path / "figures"
        written = generate_all_double_slit_figures(figures_dir=figs_dir, results=results)
        for p in written:
            assert p.exists(), f"Figure not written: {p}"

    def test_expected_file_names(self, tmp_path):
        results = run_all_conditions(n_trials=500, n_bins=50, seed=0)
        figs_dir = tmp_path / "figures"
        written = generate_all_double_slit_figures(figures_dir=figs_dir, results=results)
        names = {p.name for p in written}
        assert "one_slit_distribution.png" in names
        assert "two_slit_distribution.png" in names
        assert "two_slit_measured_distribution.png" in names
        assert "overlay_comparison.png" in names

    def test_figures_have_nonzero_size(self, tmp_path):
        results = run_all_conditions(n_trials=500, n_bins=50, seed=0)
        figs_dir = tmp_path / "figures"
        written = generate_all_double_slit_figures(figures_dir=figs_dir, results=results)
        for p in written:
            assert p.stat().st_size > 1000, f"Figure too small: {p}"

    def test_figures_are_png(self, tmp_path):
        results = run_all_conditions(n_trials=500, n_bins=50, seed=0)
        figs_dir = tmp_path / "figures"
        written = generate_all_double_slit_figures(figures_dir=figs_dir, results=results)
        for p in written:
            assert p.suffix == ".png"

    def test_synthetic_fallback_with_no_results(self, tmp_path):
        """Should produce figures even when no results dict is provided and no file exists."""
        figs_dir = tmp_path / "figures"
        results_dir = tmp_path / "nonexistent"
        written = generate_all_double_slit_figures(
            results_dir=results_dir,
            figures_dir=figs_dir,
        )
        assert len(written) == 4
        for p in written:
            assert p.exists()
