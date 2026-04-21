"""
tests/test_double_slit_sim.py
==============================
Tests for:
  reality_audit/data_analysis/double_slit_sim.py
  reality_audit/data_analysis/double_slit_benchmark.py
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile

import pytest

from reality_audit.data_analysis.double_slit_sim import (
    run_double_slit_sim,
    write_all_artifacts,
    write_json_report,
    write_csv_data,
    write_markdown_summary,
    _fringe_visibility,
    _compute_intensity,
    _linspace,
    _sample_hits,
)
from reality_audit.data_analysis.double_slit_benchmark import (
    run_benchmark,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _coherent_result(seed: int = 42, **kwargs):
    return run_double_slit_sim(
        coherence=1.0,
        decoherence_strength=0.0,
        measurement_on=False,
        seed=seed,
        **kwargs,
    )


def _decohered_result(strength: float = 0.9, seed: int = 42, **kwargs):
    return run_double_slit_sim(
        coherence=1.0,
        decoherence_strength=strength,
        measurement_on=False,
        seed=seed,
        **kwargs,
    )


def _measured_result(seed: int = 42, **kwargs):
    return run_double_slit_sim(
        coherence=1.0,
        decoherence_strength=0.0,
        measurement_on=True,
        seed=seed,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Physics model unit tests
# ---------------------------------------------------------------------------

class TestFringeVisibility:
    def test_uniform_intensity_zero_visibility(self):
        """Uniform (classical) intensity should give zero visibility."""
        uniform = [1.0] * 100
        assert _fringe_visibility(uniform) == 0.0

    def test_full_contrast_visibility(self):
        """Pattern with I_min=0 should give V=1."""
        pattern = [0.0, 1.0, 0.0, 1.0]
        assert _fringe_visibility(pattern) == pytest.approx(1.0)

    def test_partial_contrast(self):
        pattern = [0.2, 1.0, 0.2, 1.0]
        vis = _fringe_visibility(pattern)
        assert 0.0 < vis < 1.0

    def test_empty_list(self):
        assert _fringe_visibility([]) == 0.0

    def test_single_element(self):
        assert _fringe_visibility([0.5]) == 0.0


class TestLinspace:
    def test_basic(self):
        result = _linspace(0.0, 1.0, 5)
        assert len(result) == 5
        assert result[0] == pytest.approx(0.0)
        assert result[-1] == pytest.approx(1.0)

    def test_single_point(self):
        assert _linspace(3.0, 7.0, 1) == [3.0]


class TestComputeIntensity:
    def test_coherent_centre_peak(self):
        """Centre position (x=0) should have the maximum intensity for alpha=0."""
        positions = _linspace(-1e-3, 1e-3, 201)
        intensities = _compute_intensity(
            positions,
            wavelength=500e-9,
            slit_separation=1e-4,
            slit_width=2e-5,
            screen_distance=1.0,
            alpha=0.0,
        )
        centre_idx = len(positions) // 2
        # Centre should be close to maximum (normalised to 1.0)
        assert intensities[centre_idx] == pytest.approx(1.0, abs=0.05)

    def test_alpha_one_reduces_contrast(self):
        """Full decoherence (alpha=1) should give lower visibility than alpha=0."""
        positions = _linspace(-5e-3, 5e-3, 301)
        i_coherent = _compute_intensity(positions, 500e-9, 1e-4, 2e-5, 1.0, alpha=0.0)
        i_classical = _compute_intensity(positions, 500e-9, 1e-4, 2e-5, 1.0, alpha=1.0)
        vis_c = _fringe_visibility(i_coherent)
        vis_cl = _fringe_visibility(i_classical)
        assert vis_c > vis_cl, "Coherent should have higher visibility than classical"


class TestSampleHits:
    def test_returns_correct_count(self):
        positions = _linspace(-1e-3, 1e-3, 50)
        intensities = [1.0] * 50
        hits = _sample_hits(positions, intensities, 100, seed=0)
        assert len(hits) == 100

    def test_hits_within_range(self):
        positions = _linspace(-1e-3, 1e-3, 50)
        intensities = [1.0] * 50
        hits = _sample_hits(positions, intensities, 200, seed=0)
        # Allow very small margin for sub-bin jitter
        margin = (positions[-1] - positions[0]) / (len(positions) - 1)
        assert all(positions[0] - margin <= h <= positions[-1] + margin for h in hits)


# ---------------------------------------------------------------------------
# Simulation integration tests
# ---------------------------------------------------------------------------

class TestRunDoubleSlitSim:
    def test_result_has_required_keys(self):
        result = _coherent_result()
        for key in [
            "run_id", "timestamp", "parameters", "positions", "intensity",
            "hit_positions", "visibility", "coherence_score",
            "interference_detected", "regime", "notes", "summary_stats",
        ]:
            assert key in result, f"Missing key: {key}"

    def test_coherent_has_high_visibility(self):
        """Fully coherent run should produce strong fringe visibility (> 0.6)."""
        result = _coherent_result()
        assert result["visibility"] > 0.6, (
            f"Expected visibility > 0.6 in coherent case, got {result['visibility']}"
        )

    def test_strong_decoherence_reduces_visibility(self):
        """Strong decoherence (0.9) should give lower visibility than coherent."""
        coherent = _coherent_result()
        decohered = _decohered_result(strength=0.9)
        assert decohered["visibility"] < coherent["visibility"], (
            "Expected decohered visibility < coherent"
        )

    def test_measurement_on_reduces_interference(self):
        """measurement_on=True should give lower visibility than coherent."""
        coherent = _coherent_result()
        measured = _measured_result()
        assert measured["visibility"] < coherent["visibility"], (
            "measurement_on should reduce fringe visibility"
        )

    def test_measurement_on_below_threshold(self):
        """measurement_on should produce visibility < 0.15 (classicalized)."""
        result = _measured_result()
        assert result["visibility"] < 0.15, (
            f"measurement_on should classicalize; got visibility={result['visibility']}"
        )

    def test_measurement_on_regime_label(self):
        result = _measured_result()
        assert result["regime"] == "classicalized"

    def test_coherent_interference_detected(self):
        result = _coherent_result()
        assert result["interference_detected"] is True

    def test_measurement_on_interference_not_detected(self):
        result = _measured_result()
        assert result["interference_detected"] is False

    def test_seeded_runs_reproducible(self):
        """Two runs with the same seed must produce identical visibility."""
        r1 = run_double_slit_sim(seed=99)
        r2 = run_double_slit_sim(seed=99)
        assert r1["visibility"] == pytest.approx(r2["visibility"], abs=1e-9)
        assert r1["positions"] == pytest.approx(r2["positions"], abs=1e-12)
        assert r1["intensity"] == pytest.approx(r2["intensity"], abs=1e-9)

    def test_different_seeds_produce_different_hits(self):
        """Different seeds should produce different hit samples."""
        r1 = run_double_slit_sim(seed=1)
        r2 = run_double_slit_sim(seed=2)
        # It's astronomically unlikely hits are identical
        assert r1["hit_positions"] != r2["hit_positions"]

    def test_positions_length_matches_screen_points(self):
        result = run_double_slit_sim(screen_points=200, seed=0)
        assert len(result["positions"]) == 200
        assert len(result["intensity"]) == 200

    def test_num_particles_respected(self):
        result = run_double_slit_sim(num_particles=123, seed=0)
        assert result["summary_stats"]["num_hits"] == 123

    def test_noise_level_does_not_crash(self):
        result = run_double_slit_sim(noise_level=0.1, seed=7)
        assert 0.0 <= result["visibility"] <= 1.0

    def test_partial_decoherence_intermediate_visibility(self):
        """Partial decoherence (0.5) visibility should be between coherent and classical."""
        coherent = _coherent_result()
        partial = run_double_slit_sim(decoherence_strength=0.5, seed=42)
        fully_decohered = _decohered_result(strength=1.0)
        assert fully_decohered["visibility"] <= partial["visibility"] <= coherent["visibility"]

    def test_parameter_passthrough(self):
        """All input parameters should be preserved in the result."""
        result = run_double_slit_sim(
            wavelength=633e-9,
            slit_separation=2e-4,
            decoherence_strength=0.3,
            measurement_on=False,
            seed=55,
        )
        assert result["parameters"]["wavelength_m"] == pytest.approx(633e-9)
        assert result["parameters"]["slit_separation_m"] == pytest.approx(2e-4)
        assert result["parameters"]["decoherence_strength"] == pytest.approx(0.3)
        assert result["parameters"]["seed"] == 55

    def test_run_id_is_unique(self):
        r1 = run_double_slit_sim(seed=0)
        r2 = run_double_slit_sim(seed=0)
        assert r1["run_id"] != r2["run_id"]

    def test_coherence_zero_acts_like_full_decoherence(self):
        """coherence=0 should produce heavily reduced visibility."""
        result = run_double_slit_sim(coherence=0.0, seed=42)
        assert result["visibility"] < 0.15


# ---------------------------------------------------------------------------
# Artifact output tests
# ---------------------------------------------------------------------------

class TestArtifactOutput:
    def test_json_report_written(self, tmp_path):
        result = _coherent_result()
        out = tmp_path / "report.json"
        write_json_report(result, str(out))
        assert out.exists()
        data = json.loads(out.read_text())
        assert "visibility" in data
        assert "run_id" in data
        assert "WARNING" in data

    def test_csv_written(self, tmp_path):
        result = _coherent_result(screen_points=100)
        out = tmp_path / "intensity.csv"
        write_csv_data(result, str(out))
        assert out.exists()
        lines = out.read_text().splitlines()
        assert lines[0] == "position_m,normalised_intensity"
        assert len(lines) == 101  # header + 100 data rows

    def test_markdown_written(self, tmp_path):
        result = _coherent_result()
        out = tmp_path / "summary.md"
        write_markdown_summary(result, str(out))
        assert out.exists()
        text = out.read_text()
        assert "visibility" in text.lower()
        assert "WARNING" in text or "Warning" in text

    def test_write_all_artifacts_creates_files(self, tmp_path):
        result = _coherent_result()
        paths = write_all_artifacts(result, str(tmp_path), "test_run")
        assert pathlib.Path(paths["json"]).exists()
        assert pathlib.Path(paths["csv"]).exists()
        assert pathlib.Path(paths["markdown"]).exists()

    def test_json_no_protected_signal_keys(self, tmp_path):
        """JSON report must not contain protected signal keys (matching Fermi-LAT conventions)."""
        result = _coherent_result()
        out = tmp_path / "report.json"
        write_json_report(result, str(out))
        text = out.read_text()
        for key in ["observed_slope", "p_value", "z_score", "detection_claimed", "null_retained"]:
            assert key not in text, f"Protected key '{key}' found in double-slit JSON output"


# ---------------------------------------------------------------------------
# Benchmark tests
# ---------------------------------------------------------------------------

class TestDoubleSlit_Benchmark:
    def test_benchmark_all_pass(self):
        """All three benchmark modes should pass with default parameters."""
        report = run_benchmark(seed=42, write_artifacts=False)
        assert report["overall_pass"] is True, (
            f"Benchmark failed: {json.dumps(report, indent=2)}"
        )

    def test_benchmark_has_three_modes(self):
        report = run_benchmark(seed=42, write_artifacts=False)
        assert len(report["modes"]) == 3

    def test_benchmark_mode_names(self):
        report = run_benchmark(seed=42, write_artifacts=False)
        names = {m["name"] for m in report["modes"]}
        assert names == {"coherent_baseline", "partial_decoherence", "measurement_classicalized"}

    def test_coherent_baseline_passes(self):
        report = run_benchmark(seed=42, write_artifacts=False)
        baseline = next(m for m in report["modes"] if m["name"] == "coherent_baseline")
        assert baseline["pass"] is True

    def test_partial_decoherence_passes(self):
        report = run_benchmark(seed=42, write_artifacts=False)
        mode = next(m for m in report["modes"] if m["name"] == "partial_decoherence")
        assert mode["pass"] is True

    def test_measurement_classicalized_passes(self):
        report = run_benchmark(seed=42, write_artifacts=False)
        mode = next(m for m in report["modes"] if m["name"] == "measurement_classicalized")
        assert mode["pass"] is True

    def test_benchmark_artifacts_written(self, tmp_path):
        run_benchmark(seed=42, write_artifacts=True, output_dir=str(tmp_path))
        assert (tmp_path / "double_slit_benchmark_report.json").exists()
        assert (tmp_path / "double_slit_benchmark_report.md").exists()
        assert (tmp_path / "double_slit_benchmark_scores.csv").exists()

    def test_benchmark_deterministic(self):
        """Same seed → same results."""
        r1 = run_benchmark(seed=7, write_artifacts=False)
        r2 = run_benchmark(seed=7, write_artifacts=False)
        for m1, m2 in zip(r1["modes"], r2["modes"]):
            assert m1["visibility_observed"] == pytest.approx(m2["visibility_observed"], abs=1e-9)

    def test_coherent_visibility_higher_than_classicalized(self):
        report = run_benchmark(seed=42, write_artifacts=False)
        coherent_vis = next(m["visibility_observed"] for m in report["modes"] if m["name"] == "coherent_baseline")
        classical_vis = next(m["visibility_observed"] for m in report["modes"] if m["name"] == "measurement_classicalized")
        assert coherent_vis > classical_vis
