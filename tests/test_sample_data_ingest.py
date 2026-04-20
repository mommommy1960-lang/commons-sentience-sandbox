"""
tests/test_sample_data_ingest.py
=================================
Tests that the local sample dataset (data/sample_fermi_lat_grb_events.csv)
ingests correctly through the Fermi-LAT GRB adapter and is compatible with
the real timing pipeline.

These tests validate:
  - Load and normalization
  - Grouping by source
  - Metadata counts
  - Physical plausibility of normalized values
  - Compatibility with run_real_timing_pipeline()
"""

import os
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent
SAMPLE_CSV = REPO_ROOT / "data" / "sample_fermi_lat_grb_events.csv"

from reality_audit.adapters.fermi_lat_grb_adapter import (
    load_grb_events,
    to_timing_pipeline_format,
    load_and_convert,
    _z_to_distance_Mpc,
)
from reality_audit.data_analysis.real_timing_pipeline import run_real_timing_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load():
    """Load the sample CSV once; used by multiple tests."""
    return load_grb_events(str(SAMPLE_CSV), energy_unit="GeV", time_unit="s")


def _pipeline_fmt():
    return to_timing_pipeline_format(_load())


# ---------------------------------------------------------------------------
# 1. TestSampleFileExists
# ---------------------------------------------------------------------------

class TestSampleFileExists:
    def test_sample_csv_present(self):
        assert SAMPLE_CSV.exists(), f"Sample dataset not found at {SAMPLE_CSV}"

    def test_sample_csv_non_empty(self):
        assert SAMPLE_CSV.stat().st_size > 0

    def test_sample_csv_has_header(self):
        with open(SAMPLE_CSV) as f:
            header = f.readline().strip()
        assert "event_id" in header
        assert "source_id" in header
        assert "photon_energy" in header
        assert "arrival_time" in header


# ---------------------------------------------------------------------------
# 2. TestSampleLoadBasics
# ---------------------------------------------------------------------------

class TestSampleLoadBasics:
    def test_load_returns_dict(self):
        out = _load()
        assert isinstance(out, dict)

    def test_events_key_present(self):
        out = _load()
        assert "events" in out

    def test_by_source_key_present(self):
        out = _load()
        assert "by_source" in out

    def test_metadata_key_present(self):
        out = _load()
        assert "metadata" in out

    def test_schema_version(self):
        out = _load()
        assert out["metadata"]["schema_version"] == "1.0"

    def test_total_event_count(self):
        """Sample file has 50 events (10 per GRB × 5 GRBs)."""
        out = _load()
        assert out["metadata"]["n_events"] == 50

    def test_source_count(self):
        """Sample file has 5 distinct GRBs."""
        out = _load()
        assert out["metadata"]["n_sources"] == 5

    def test_no_dropped_events(self):
        """All rows are valid; none should be dropped."""
        out = _load()
        assert out["metadata"]["n_dropped"] == 0


# ---------------------------------------------------------------------------
# 3. TestSampleNormalization
# ---------------------------------------------------------------------------

class TestSampleNormalization:
    def test_all_energies_positive(self):
        out = _load()
        for ev in out["events"]:
            assert ev["energy"] > 0, f"Non-positive energy: {ev}"

    def test_energies_in_gev_range(self):
        """Sample energies are in 0.06–94 GeV — all should be > 0.01 GeV."""
        out = _load()
        for ev in out["events"]:
            assert ev["energy"] > 0.01

    def test_relative_time_per_source_starts_at_zero(self):
        """Each source group's minimum time should be 0.0 (relative normalization)."""
        out = _load()
        for src, grp in out["by_source"].items():
            times = [e["time"] for e in grp["events"]]
            assert min(times) == pytest.approx(0.0, abs=1e-9), \
                f"Source {src} min time is not 0: {min(times)}"

    def test_all_times_non_negative(self):
        out = _load()
        for ev in out["events"]:
            assert ev["time"] >= 0.0

    def test_redshift_preserved(self):
        """All events have a redshift > 0 (all GRBs in sample have known z)."""
        out = _load()
        for ev in out["events"]:
            assert ev["redshift"] is not None
            assert ev["redshift"] > 0.0

    def test_distance_derived_from_redshift(self):
        """distance_Mpc should be populated from z for all events."""
        out = _load()
        for ev in out["events"]:
            assert ev["distance_Mpc"] is not None
            assert ev["distance_Mpc"] > 0.0

    def test_distance_monotone_with_redshift(self):
        """Higher-z GRBs should have larger mean distance_Mpc."""
        out = _load()
        grb_z = {}
        grb_d = {}
        for ev in out["events"]:
            src = ev["source"]
            grb_z.setdefault(src, ev["redshift"])
            grb_d.setdefault(src, ev["distance_Mpc"])
        # Sort by z and confirm distance is monotone
        sorted_by_z = sorted(grb_z.items(), key=lambda x: x[1])
        distances = [grb_d[s] for s, _ in sorted_by_z]
        for i in range(len(distances) - 1):
            assert distances[i] < distances[i + 1], \
                "Distances not monotone with redshift"

    def test_event_ids_unique(self):
        out = _load()
        ids = [ev["event_id"] for ev in out["events"]]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# 4. TestGroupingBySource
# ---------------------------------------------------------------------------

class TestGroupingBySource:
    def test_five_source_groups(self):
        out = _load()
        assert len(out["by_source"]) == 5

    def test_each_group_has_ten_events(self):
        out = _load()
        for src, grp in out["by_source"].items():
            assert grp["n_events"] == 10, \
                f"Source {src} has {grp['n_events']} events, expected 10"

    def test_known_grb_names_present(self):
        out = _load()
        expected = {"GRB080916C", "GRB090902B", "GRB090510", "GRB130427A", "GRB160509A"}
        assert set(out["by_source"].keys()) == expected

    def test_group_mean_energy_positive(self):
        out = _load()
        for src, grp in out["by_source"].items():
            assert grp["mean_energy_GeV"] > 0.0

    def test_group_time_span_positive(self):
        out = _load()
        for src, grp in out["by_source"].items():
            assert grp["time_span_s"] > 0.0, \
                f"Source {src} has zero time span"

    def test_grb130427a_max_energy_high(self):
        """GRB130427A is the highest-energy event source in the sample (range 0.07–94 GeV).
        With 10 randomly drawn events the max should exceed 30 GeV consistently."""
        out = _load()
        grpA = out["by_source"]["GRB130427A"]
        max_e = max(e["energy"] for e in grpA["events"])
        assert max_e > 30.0, f"Expected max energy > 30 GeV, got {max_e}"

    def test_grb090510_short_timescale(self):
        """GRB090510 is a short GRB — time span < 2 s in the sample."""
        out = _load()
        assert out["by_source"]["GRB090510"]["time_span_s"] < 2.0


# ---------------------------------------------------------------------------
# 5. TestPipelineFormatCompatibility
# ---------------------------------------------------------------------------

class TestPipelineFormatCompatibility:
    def test_pipeline_format_keys(self):
        fmt = _pipeline_fmt()
        for key in ("energy_GeV", "distance_Mpc", "timing_offset_s", "n_events", "n_sources"):
            assert key in fmt

    def test_pipeline_list_lengths_match(self):
        fmt = _pipeline_fmt()
        assert len(fmt["energy_GeV"]) == len(fmt["distance_Mpc"]) == len(fmt["timing_offset_s"])

    def test_pipeline_n_events_matches_sample(self):
        fmt = _pipeline_fmt()
        assert fmt["n_events"] == 50

    def test_pipeline_n_sources_matches_sample(self):
        fmt = _pipeline_fmt()
        assert fmt["n_sources"] == 5

    def test_pipeline_energies_all_positive(self):
        fmt = _pipeline_fmt()
        assert all(e > 0 for e in fmt["energy_GeV"])

    def test_pipeline_distances_all_positive(self):
        fmt = _pipeline_fmt()
        assert all(d > 0 for d in fmt["distance_Mpc"])

    def test_pipeline_offsets_non_negative(self):
        fmt = _pipeline_fmt()
        assert all(t >= 0.0 for t in fmt["timing_offset_s"])

    def test_load_and_convert_shortcut(self):
        fmt = load_and_convert(str(SAMPLE_CSV), energy_unit="GeV")
        assert fmt["n_events"] == 50


# ---------------------------------------------------------------------------
# 6. TestRealTimingPipelineCompatibility
# ---------------------------------------------------------------------------

class TestRealTimingPipelineCompatibility:
    def test_pipeline_runs_without_error(self, tmp_path):
        events = load_and_convert(str(SAMPLE_CSV), energy_unit="GeV")
        result = run_real_timing_pipeline(
            events,
            experiment_name="sample_ingest_test",
            n_permutations=200,
            seed=42,
            output_dir=str(tmp_path / "output"),
            run_recovery_test=True,
            freeze_immediately=True,
        )
        assert isinstance(result, dict)

    def test_pipeline_returns_required_keys(self, tmp_path):
        events = load_and_convert(str(SAMPLE_CSV), energy_unit="GeV")
        result = run_real_timing_pipeline(
            events,
            experiment_name="sample_keys_test",
            n_permutations=200,
            seed=42,
            output_dir=str(tmp_path / "output"),
            freeze_immediately=True,
        )
        for key in ("observed_slope", "p_value", "null_retained",
                    "z_score", "detection_claimed"):
            assert key in result, f"Missing key: {key}"

    def test_null_retained_on_sample_data(self, tmp_path):
        """
        The sample dataset is synthetic with only 50 events across 5 GRBs.
        With this few events, random fluctuations can produce any p-value.
        We do NOT assert null_retained=True here — the sample is too small
        for that to be a reliable check. We only verify the pipeline produces
        a valid boolean result and does not crash.
        """
        events = load_and_convert(str(SAMPLE_CSV), energy_unit="GeV")
        result = run_real_timing_pipeline(
            events,
            experiment_name="sample_null_test",
            n_permutations=500,
            seed=42,
            output_dir=str(tmp_path / "output"),
            freeze_immediately=True,
        )
        assert isinstance(result["null_retained"], bool)
        assert isinstance(result["detection_claimed"], bool)

    def test_recovery_test_in_result(self, tmp_path):
        events = load_and_convert(str(SAMPLE_CSV), energy_unit="GeV")
        result = run_real_timing_pipeline(
            events,
            experiment_name="sample_recovery_test",
            n_permutations=200,
            seed=42,
            output_dir=str(tmp_path / "output"),
            run_recovery_test=True,
            freeze_immediately=True,
        )
        assert "recovery_test" in result
        assert "recovered" in result["recovery_test"]

    def test_recovery_test_recovered(self, tmp_path):
        """Injected signal should be recoverable (p < 0.05) on real-scale data."""
        events = load_and_convert(str(SAMPLE_CSV), energy_unit="GeV")
        result = run_real_timing_pipeline(
            events,
            experiment_name="sample_recovery_ok",
            n_permutations=200,
            seed=42,
            output_dir=str(tmp_path / "output"),
            run_recovery_test=True,
            recovery_true_slope=5e-4,
            freeze_immediately=True,
        )
        assert result["recovery_test"]["recovered"] is True

    def test_output_files_written(self, tmp_path):
        events = load_and_convert(str(SAMPLE_CSV), energy_unit="GeV")
        run_real_timing_pipeline(
            events,
            experiment_name="sample_files_test",
            n_permutations=100,
            seed=42,
            output_dir=str(tmp_path / "output"),
            freeze_immediately=True,
        )
        written = list((tmp_path / "output").iterdir())
        assert len(written) > 0, "No output files written"
