"""
tests/test_data_analysis_readiness.py
======================================
Tests for the real-data analysis readiness layer.

Covers:
  - ExperimentRegistry + ExperimentSpec
  - NullModelLibrary (all 5 models)
  - SignalInjector (all 4 injectors)
  - Blinder (blind/freeze/unblind lifecycle)
  - ReportWriter (JSON/CSV/Markdown/manifest)
  - mock_cosmic_ray_pipeline (null run + injection run + recovery)
  - mock_timing_pipeline (null run + injection run + recovery)
"""

import math
import os
import tempfile
import pytest

from reality_audit.data_analysis.experiment_registry import (
    ExperimentSpec,
    ExperimentRegistry,
    build_default_registry,
)
from reality_audit.data_analysis.null_models import NullModelLibrary
from reality_audit.data_analysis.signal_injection import SignalInjector
from reality_audit.data_analysis.blinding import Blinder
from reality_audit.data_analysis.reporting import ReportWriter
from reality_audit.data_analysis.mock_cosmic_ray_pipeline import (
    run_cosmic_ray_pipeline,
    dipole_power,
)
from reality_audit.data_analysis.mock_timing_pipeline import (
    run_timing_pipeline,
    timing_slope,
)


# ===========================================================================
# ExperimentRegistry
# ===========================================================================


class TestExperimentSpec:
    def test_create(self):
        spec = ExperimentSpec(
            name="test_exp",
            hypothesis="null is true",
            primary_statistic="mean",
            null_model="isotropic_uniform",
            signal_model="preferred_axis",
        )
        assert spec.name == "test_exp"
        assert spec.blinding_status == "blinded"
        assert spec.is_blinded()

    def test_to_dict_roundtrip(self):
        spec = ExperimentSpec(
            name="roundtrip",
            hypothesis="h",
            primary_statistic="p",
            null_model="no_delay",
            signal_model="timing_delay_linear",
            tags=["a", "b"],
        )
        d = spec.to_dict()
        spec2 = ExperimentSpec.from_dict(d)
        assert spec2.name == "roundtrip"
        assert spec2.tags == ["a", "b"]

    def test_is_blinded_variants(self):
        spec = ExperimentSpec(
            name="x", hypothesis="h", primary_statistic="p",
            null_model="n", signal_model="s",
            blinding_status="open",
        )
        assert not spec.is_blinded()


class TestExperimentRegistry:
    def test_register_and_get(self):
        reg = ExperimentRegistry()
        spec = ExperimentSpec(
            name="exp1", hypothesis="h", primary_statistic="p",
            null_model="n", signal_model="s",
        )
        reg.register(spec)
        assert reg.get("exp1") is spec

    def test_duplicate_raises(self):
        reg = ExperimentRegistry()
        spec = ExperimentSpec(
            name="dup", hypothesis="h", primary_statistic="p",
            null_model="n", signal_model="s",
        )
        reg.register(spec)
        with pytest.raises(ValueError):
            reg.register(spec)

    def test_filter_by_tag(self):
        reg = ExperimentRegistry()
        for i in range(3):
            reg.register(ExperimentSpec(
                name=f"e{i}", hypothesis="h", primary_statistic="p",
                null_model="n", signal_model="s",
                tags=["x"] if i < 2 else ["y"],
            ))
        assert len(reg.filter_by_tag("x")) == 2
        assert len(reg.filter_by_tag("y")) == 1

    def test_update(self):
        reg = ExperimentRegistry()
        reg.register(ExperimentSpec(
            name="upd", hypothesis="h", primary_statistic="p",
            null_model="n", signal_model="s",
        ))
        reg.update("upd", blinding_status="open")
        assert reg.get("upd").blinding_status == "open"

    def test_save_load(self, tmp_path):
        reg = ExperimentRegistry()
        reg.register(ExperimentSpec(
            name="saved", hypothesis="h", primary_statistic="p",
            null_model="n", signal_model="s",
        ))
        path = str(tmp_path / "registry.json")
        reg.save(path)
        reg2 = ExperimentRegistry.load(path)
        assert len(reg2) == 1
        assert reg2.get("saved").hypothesis == "h"

    def test_build_default_registry(self):
        reg = build_default_registry()
        assert len(reg) == 3
        names = [s.name for s in reg.all()]
        assert "cosmic_ray_anisotropy_v1" in names
        assert "astrophysical_timing_delay_v1" in names
        assert "cmb_axis_alignment_v1" in names
        assert all(s.is_blinded() for s in reg.all())

    def test_summary_structure(self):
        reg = build_default_registry()
        summary = reg.summary()
        assert len(summary) == 3
        assert "name" in summary[0]
        assert "primary_statistic" in summary[0]


# ===========================================================================
# NullModelLibrary
# ===========================================================================


class TestNullModels:
    def test_isotropic_uniform_count(self):
        data = NullModelLibrary.isotropic_uniform(100, seed=1)
        assert data["n_events"] == 100
        assert len(data["theta_rad"]) == 100
        assert len(data["phi_rad"]) == 100

    def test_isotropic_uniform_range(self):
        data = NullModelLibrary.isotropic_uniform(500, seed=2)
        for t in data["theta_rad"]:
            assert 0.0 <= t <= math.pi
        for p in data["phi_rad"]:
            assert 0.0 <= p < 2 * math.pi

    def test_isotropic_uniform_reproducible(self):
        d1 = NullModelLibrary.isotropic_uniform(50, seed=99)
        d2 = NullModelLibrary.isotropic_uniform(50, seed=99)
        assert d1["theta_rad"] == d2["theta_rad"]

    def test_no_delay_count(self):
        data = NullModelLibrary.no_delay(200, seed=3)
        assert data["n_events"] == 200
        assert len(data["timing_offset_s"]) == 200

    def test_no_delay_noise_magnitude(self):
        data = NullModelLibrary.no_delay(1000, seed=4)
        mean = sum(data["timing_offset_s"]) / 1000
        assert abs(mean) < 0.01  # should be near zero

    def test_symmetric_no_preferred_axis(self):
        data = NullModelLibrary.symmetric_no_preferred_axis(seed=5, l_max=4)
        assert data["model"] == "symmetric_no_preferred_axis"
        assert "(1, 0)" in data["alm_real"] or "(1, 0)" in str(data["alm_real"])

    def test_white_noise_background(self):
        data = NullModelLibrary.white_noise_background(300, seed=6, sigma=2.0)
        assert data["n_samples"] == 300
        assert len(data["samples"]) == 300

    def test_bandwidth_flat(self):
        data = NullModelLibrary.bandwidth_flat(64, seed=7)
        assert data["n_bins"] == 64
        assert all(c >= 0 for c in data["counts"])

    def test_available_keys(self):
        keys = NullModelLibrary.available()
        assert "isotropic_uniform" in keys
        assert "no_delay" in keys

    def test_get_dispatch(self):
        data = NullModelLibrary.get("white_noise_background", n_samples=10, seed=1)
        assert len(data["samples"]) == 10

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError):
            NullModelLibrary.get("nonexistent_model")


# ===========================================================================
# SignalInjector
# ===========================================================================


class TestSignalInjector:
    def test_preferred_axis_preserves_count(self):
        null = NullModelLibrary.isotropic_uniform(100, seed=0)
        injected = SignalInjector.preferred_axis(null, injection_strength=0.3)
        assert len(injected["theta_rad"]) == 100

    def test_preferred_axis_injection_metadata(self):
        null = NullModelLibrary.isotropic_uniform(50, seed=0)
        injected = SignalInjector.preferred_axis(null, injection_strength=0.2)
        assert injected["injection"]["type"] == "preferred_axis"
        assert injected["injection"]["injection_strength"] == 0.2

    def test_preferred_axis_invalid_strength(self):
        null = NullModelLibrary.isotropic_uniform(50, seed=0)
        with pytest.raises(ValueError):
            SignalInjector.preferred_axis(null, injection_strength=1.5)

    def test_anisotropy_injection_boosts_alm(self):
        null = NullModelLibrary.symmetric_no_preferred_axis(seed=0, l_max=4)
        key = str((2, 0))
        before = float(null["alm_real"].get(key, 0.0))
        injected = SignalInjector.anisotropy_injection(null, injection_strength=5.0)
        after = float(injected["alm_real"][key])
        assert after > before

    def test_timing_delay_adds_slope(self):
        null = NullModelLibrary.no_delay(200, seed=0)
        injected = SignalInjector.timing_delay_linear(
            null, delay_slope=0.01, injection_strength=1.0
        )
        raw_offsets = null["timing_offset_s"]
        new_offsets = injected["timing_offset_s"]
        assert any(
            abs(new_offsets[i] - raw_offsets[i]) > 1e-6 for i in range(200)
        )

    def test_bandwidth_anomaly_increases_counts(self):
        null = NullModelLibrary.bandwidth_flat(100, seed=0, baseline=1.0)
        injected = SignalInjector.bandwidth_anomaly(
            null, anomaly_bin_start=0, anomaly_bin_end=10,
            excess_fraction=0.5, injection_strength=1.0,
        )
        for i in range(10):
            assert injected["counts"][i] > null["counts"][i] * 0.99

    def test_inject_dispatch(self):
        null = NullModelLibrary.bandwidth_flat(50, seed=0)
        data = SignalInjector.inject("bandwidth_anomaly", null, excess_fraction=0.1)
        assert "injection" in data

    def test_inject_unknown_raises(self):
        null = NullModelLibrary.white_noise_background(10, seed=0)
        with pytest.raises(KeyError):
            SignalInjector.inject("bad_key", null)


# ===========================================================================
# Blinder
# ===========================================================================


class TestBlinder:
    def test_blind_hides_keys(self):
        blinder = Blinder(blind_keys=["p_value", "z_score"])
        results = {"p_value": 0.001, "z_score": 3.5, "n_events": 100}
        blinded = blinder.blind(results)
        assert blinded["p_value"] == "<BLINDED>"
        assert blinded["z_score"] == "<BLINDED>"
        assert blinded["n_events"] == 100

    def test_unblind_requires_freeze(self):
        blinder = Blinder(blind_keys=["p_value"])
        with pytest.raises(RuntimeError):
            blinder.unblind({"p_value": 0.001})

    def test_unblind_after_freeze(self):
        blinder = Blinder(blind_keys=["p_value"])
        results = {"p_value": 0.001, "n_events": 100}
        blinder.freeze(reason="test")
        unblinded = blinder.unblind(results)
        assert unblinded["p_value"] == 0.001
        assert unblinded["_blinding_status"] == "unblinded"

    def test_audit_trail_grows(self):
        blinder = Blinder(blind_keys=["x"])
        blinder.blind({"x": 1})
        blinder.freeze()
        blinder.unblind({"x": 1})
        trail = blinder.audit_trail()
        events = [e["event"] for e in trail]
        assert "blind" in events
        assert "freeze" in events
        assert "unblind" in events

    def test_save_blinded_writes_file(self, tmp_path):
        blinder = Blinder(blind_keys=["secret"])
        path = str(tmp_path / "blinded.json")
        blinder.save_blinded({"secret": 42, "public": 1}, path)
        import json
        with open(path) as f:
            data = json.load(f)
        # save_blinded writes the blinded dict directly (flat, not nested in "results")
        assert data["secret"] == "<BLINDED>"
        assert data["public"] == 1

    def test_save_unblinded_requires_freeze(self, tmp_path):
        blinder = Blinder(blind_keys=["secret"])
        path = str(tmp_path / "unblinded.json")
        with pytest.raises(RuntimeError):
            blinder.save_unblinded({"secret": 42}, path)

    def test_summary_structure(self):
        blinder = Blinder(blind_keys=["x"], experiment_name="test")
        s = blinder.summary()
        assert s["experiment_name"] == "test"
        assert s["frozen"] is False


# ===========================================================================
# ReportWriter
# ===========================================================================


class TestReportWriter:
    def test_write_json_summary(self, tmp_path):
        writer = ReportWriter(str(tmp_path), "test_exp")
        results = {"metric": 1.23, "n": 100}
        path = writer.write_json_summary(results, blinded=False)
        assert os.path.exists(path)
        import json
        with open(path) as f:
            data = json.load(f)
        assert data["experiment"] == "test_exp"

    def test_write_csv_row(self, tmp_path):
        writer = ReportWriter(str(tmp_path), "exp")
        writer.write_csv_row({"a": 1, "b": 2.5})
        writer.write_csv_row({"a": 2, "b": 3.5})
        csv_path = os.path.join(str(tmp_path), "exp_results.csv")
        with open(csv_path) as f:
            lines = f.readlines()
        assert len(lines) == 3  # header + 2 rows

    def test_write_markdown_summary(self, tmp_path):
        writer = ReportWriter(str(tmp_path), "exp")
        results = {"p_value": "<BLINDED>", "n": 100}
        path = writer.write_markdown_summary(results, blinded=True)
        content = open(path).read()
        assert "BLINDED" in content
        assert "exp" in content

    def test_write_manifest(self, tmp_path):
        writer = ReportWriter(str(tmp_path), "exp")
        writer.write_json_summary({"x": 1})
        manifest_path = writer.write_manifest()
        import json
        with open(manifest_path) as f:
            data = json.load(f)
        assert "files" in data

    def test_write_all(self, tmp_path):
        writer = ReportWriter(str(tmp_path), "exp")
        blinded = {"p_value": "<BLINDED>", "n": 50}
        unblinded = {"p_value": 0.05, "n": 50}
        paths = writer.write_all(
            blinded, unblinded, csv_row={"run": 1, "p": 0.05}
        )
        assert "blinded_json" in paths
        assert "unblinded_json" in paths
        assert "csv" in paths
        assert "manifest" in paths


# ===========================================================================
# mock_cosmic_ray_pipeline
# ===========================================================================


class TestMockCosmicRayPipeline:
    def test_null_run_returns_dict(self, tmp_path):
        result = run_cosmic_ray_pipeline(
            n_events=200, inject_signal=False, n_permutations=50,
            seed=42, output_dir=str(tmp_path / "cr"),
        )
        assert "observed_dipole_power" in result
        assert "p_value" in result
        assert result["status"] == "mock_dry_run"

    def test_null_run_p_value_range(self, tmp_path):
        result = run_cosmic_ray_pipeline(
            n_events=300, inject_signal=False, n_permutations=100,
            seed=7, output_dir=str(tmp_path / "cr_null"),
        )
        assert 0.0 <= result["p_value"] <= 1.0

    def test_injection_increases_dipole(self, tmp_path):
        null_result = run_cosmic_ray_pipeline(
            n_events=500, inject_signal=False, n_permutations=50,
            seed=1, output_dir=str(tmp_path / "cr_null2"),
        )
        inj_result = run_cosmic_ray_pipeline(
            n_events=500, inject_signal=True, injection_strength=0.5,
            n_permutations=50, seed=1,
            output_dir=str(tmp_path / "cr_inj"),
        )
        assert inj_result["observed_dipole_power"] > null_result["observed_dipole_power"]

    def test_recovery_test_present(self, tmp_path):
        result = run_cosmic_ray_pipeline(
            n_events=400, inject_signal=False, n_permutations=50,
            seed=99, output_dir=str(tmp_path / "cr_rec"),
            run_recovery_test=True,
        )
        assert "recovery_test" in result
        assert "p_value" in result["recovery_test"]

    def test_strong_injection_increases_dipole(self, tmp_path):
        """Strong injection must produce larger dipole power than null."""
        null = run_cosmic_ray_pipeline(
            n_events=600, inject_signal=False, n_permutations=100,
            seed=42, output_dir=str(tmp_path / "cr_strong_null"),
        )
        inj = run_cosmic_ray_pipeline(
            n_events=600, inject_signal=True, injection_strength=0.9,
            n_permutations=100, seed=42,
            output_dir=str(tmp_path / "cr_strong_inj"),
        )
        # With 0.9 injection strength the observed dipole power must exceed null
        assert inj["observed_dipole_power"] > null["observed_dipole_power"]

    def test_output_files_written(self, tmp_path):
        out = str(tmp_path / "cr_files")
        run_cosmic_ray_pipeline(
            n_events=100, n_permutations=20, seed=0,
            output_dir=out,
        )
        files = os.listdir(out)
        assert any("blinded" in f for f in files)
        assert any("unblinded" in f for f in files)

    def test_dipole_power_isotropic(self):
        """Dipole power of a truly uniform sample should be small."""
        from reality_audit.data_analysis.null_models import NullModelLibrary
        data = NullModelLibrary.isotropic_uniform(5000, seed=11)
        power = dipole_power(data["theta_rad"], data["phi_rad"])
        # Expected ~ 3/N = 0.0006; allow up to 10x
        assert power < 0.006


# ===========================================================================
# mock_timing_pipeline
# ===========================================================================


class TestMockTimingPipeline:
    def test_null_run_returns_dict(self, tmp_path):
        result = run_timing_pipeline(
            n_events=200, inject_signal=False, n_permutations=50,
            seed=42, output_dir=str(tmp_path / "td"),
        )
        assert "observed_slope" in result
        assert "p_value" in result
        assert result["status"] == "mock_dry_run"

    def test_null_slope_near_zero(self, tmp_path):
        """Null slope should be close to zero (no injected delay)."""
        result = run_timing_pipeline(
            n_events=500, inject_signal=False, n_permutations=100,
            seed=5, output_dir=str(tmp_path / "td_null"),
        )
        assert abs(result["observed_slope"]) < 0.01

    def test_injection_increases_slope(self, tmp_path):
        null = run_timing_pipeline(
            n_events=500, inject_signal=False, n_permutations=50,
            seed=2, output_dir=str(tmp_path / "td_null2"),
        )
        inj = run_timing_pipeline(
            n_events=500, inject_signal=True, injection_strength=1.0,
            true_delay_slope=0.01,
            n_permutations=50, seed=2,
            output_dir=str(tmp_path / "td_inj"),
        )
        assert abs(inj["observed_slope"]) > abs(null["observed_slope"])

    def test_p_value_range(self, tmp_path):
        result = run_timing_pipeline(
            n_events=200, n_permutations=50, seed=3,
            output_dir=str(tmp_path / "td_p"),
        )
        assert 0.0 <= result["p_value"] <= 1.0

    def test_recovery_test_present(self, tmp_path):
        result = run_timing_pipeline(
            n_events=300, n_permutations=50, seed=8,
            output_dir=str(tmp_path / "td_rec"),
            run_recovery_test=True,
        )
        assert "recovery_test" in result
        assert "recovered" in result["recovery_test"]

    def test_output_files_written(self, tmp_path):
        out = str(tmp_path / "td_files")
        run_timing_pipeline(
            n_events=100, n_permutations=20, seed=0,
            output_dir=out,
        )
        files = os.listdir(out)
        assert any("blinded" in f for f in files)
        assert any("unblinded" in f for f in files)

    def test_timing_slope_zero_for_no_delay(self):
        from reality_audit.data_analysis.null_models import NullModelLibrary
        data = NullModelLibrary.no_delay(1000, seed=10)
        slope = timing_slope(
            data["energy_GeV"], data["distance_Mpc"], data["timing_offset_s"]
        )
        assert abs(slope) < 1e-3  # noise-only slope should be tiny
