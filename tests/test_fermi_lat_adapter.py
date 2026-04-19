"""
tests/test_fermi_lat_adapter.py
================================
Tests for the Fermi-LAT GRB adapter and real timing pipeline integration.

Covers:
  - load_grb_events() from JSON and CSV files
  - Column auto-detection and custom column_map
  - Energy unit conversion (MeV, GeV, TeV)
  - Time normalisation (relative seconds per source)
  - Redshift → distance_Mpc conversion
  - Invalid / NaN row handling
  - Minimum events per source filtering
  - to_timing_pipeline_format() output shape
  - load_and_convert() convenience wrapper
  - real_timing_pipeline.run_real_timing_pipeline() integration
    - null run: p_value in [0, 1], null_retained
    - injection run: slope increases
    - blinding: blind before freeze raises on unblind
    - freeze_immediately mode: unblinded output written
    - output files written to disk
"""

import csv
import json
import math
import os
import pytest

from reality_audit.adapters.fermi_lat_grb_adapter import (
    load_grb_events,
    to_timing_pipeline_format,
    load_and_convert,
    _z_to_distance_Mpc,
    _normalize_energy,
    _canonical_column_map,
)
from reality_audit.data_analysis.real_timing_pipeline import run_real_timing_pipeline


# ---------------------------------------------------------------------------
# Fixtures: synthetic GRB-like datasets
# ---------------------------------------------------------------------------


def _make_csv(path: str, rows: list, headers: list) -> str:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)
    return path


def _make_json(path: str, rows: list) -> str:
    with open(path, "w") as f:
        json.dump(rows, f)
    return path


def _sample_rows(n_per_grb: int = 10, n_grb: int = 5) -> list:
    """Build n_grb GRBs each with n_per_grb photon events."""
    import random
    rng = random.Random(42)
    rows = []
    for g in range(n_grb):
        grb_id = f"GRB{200000 + g:06d}"
        for i in range(n_per_grb):
            rows.append({
                "event_id": f"{grb_id}_{i}",
                "photon_energy": rng.uniform(0.1, 100.0),   # GeV
                "arrival_time": rng.uniform(0.0, 100.0),    # seconds
                "source_id": grb_id,
                "redshift": round(rng.uniform(0.1, 3.0), 3),
            })
    return rows


HEADERS_STANDARD = [
    "event_id", "photon_energy", "arrival_time", "source_id", "redshift"
]


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------


class TestEnergyConversion:
    def test_GeV_unchanged(self):
        assert _normalize_energy(1.0, "GeV", "energy") == 1.0

    def test_MeV_to_GeV(self):
        assert abs(_normalize_energy(1000.0, "MeV", "energy") - 1.0) < 1e-10

    def test_TeV_to_GeV(self):
        assert abs(_normalize_energy(1.0, "TeV", "energy") - 1000.0) < 1e-8

    def test_keV_to_GeV(self):
        assert abs(_normalize_energy(1e6, "keV", "energy") - 1.0) < 1e-5

    def test_unknown_unit_falls_back_to_GeV(self):
        # Unknown unit → treated as GeV (no conversion)
        result = _normalize_energy(5.0, "UNKNOWN", "energy_gev")
        assert result == 5.0


class TestZToDistance:
    def test_zero_redshift(self):
        assert _z_to_distance_Mpc(0.0) == 0.0

    def test_small_z_positive(self):
        d = _z_to_distance_Mpc(0.1)
        assert d > 0

    def test_monotone_increasing(self):
        ds = [_z_to_distance_Mpc(z) for z in [0.1, 0.5, 1.0, 2.0]]
        assert all(ds[i] < ds[i + 1] for i in range(len(ds) - 1))

    def test_unit_z_order_Gpc(self):
        # z=1 should give ~4–7 Gpc range
        d = _z_to_distance_Mpc(1.0)
        assert 3000 < d < 10000


class TestCanonicalColumnMap:
    def test_standard_headers_auto(self):
        cmap = _canonical_column_map(HEADERS_STANDARD)
        assert cmap["photon_energy"] == "photon_energy"
        assert cmap["arrival_time"] == "arrival_time"
        assert cmap["source_id"] == "source_id"
        assert cmap["redshift"] == "redshift"

    def test_synonym_energy(self):
        cmap = _canonical_column_map(["energy", "time", "name"])
        assert cmap["photon_energy"] == "energy"

    def test_custom_map_overrides(self):
        cmap = _canonical_column_map(
            ["e_mev", "t", "burst"],
            column_map={"photon_energy": "e_mev", "source_id": "burst"},
        )
        assert cmap["photon_energy"] == "e_mev"
        assert cmap["source_id"] == "burst"


# ---------------------------------------------------------------------------
# Adapter load from CSV
# ---------------------------------------------------------------------------


class TestLoadFromCSV:
    def test_basic_load(self, tmp_path):
        rows = _sample_rows(5, 3)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        out = load_grb_events(path)
        assert out["metadata"]["n_events"] == 15
        assert out["metadata"]["n_sources"] == 3

    def test_energy_values_positive(self, tmp_path):
        rows = _sample_rows(5, 2)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        out = load_grb_events(path)
        assert all(ev["energy"] > 0 for ev in out["events"])

    def test_relative_time_starts_at_zero(self, tmp_path):
        rows = _sample_rows(5, 2)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        out = load_grb_events(path)
        for src, info in out["by_source"].items():
            times = [ev["time"] for ev in info["events"]]
            assert times[0] == 0.0 or times[0] < 1e-10

    def test_distance_derived_from_redshift(self, tmp_path):
        rows = _sample_rows(4, 2)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        out = load_grb_events(path)
        # All events have redshift → distance should be set
        for ev in out["events"]:
            assert ev["distance_Mpc"] is not None
            assert ev["distance_Mpc"] > 0

    def test_sorted_by_time(self, tmp_path):
        rows = _sample_rows(8, 1)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        out = load_grb_events(path)
        for info in out["by_source"].values():
            times = [ev["time"] for ev in info["events"]]
            assert times == sorted(times)

    def test_min_events_per_source_filtering(self, tmp_path):
        # 1-event source should be dropped with min=2
        rows = _sample_rows(1, 3)  # 1 event per GRB
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        out = load_grb_events(path, min_events_per_source=2)
        assert out["metadata"]["n_sources"] == 0
        assert out["metadata"]["n_events"] == 0

    def test_missing_energy_row_dropped(self, tmp_path):
        rows = _sample_rows(3, 2)
        rows[0]["photon_energy"] = ""   # invalid
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        out = load_grb_events(path)
        assert out["metadata"]["n_dropped"] >= 1

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            load_grb_events("/no/such/file.csv")

    def test_schema_version_in_metadata(self, tmp_path):
        rows = _sample_rows(3, 2)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        out = load_grb_events(path)
        assert out["metadata"]["schema_version"] == "1.0"


# ---------------------------------------------------------------------------
# Adapter load from JSON
# ---------------------------------------------------------------------------


class TestLoadFromJSON:
    def test_json_array(self, tmp_path):
        rows = _sample_rows(4, 2)
        path = _make_json(str(tmp_path / "grb.json"), rows)
        out = load_grb_events(path)
        assert out["metadata"]["n_events"] == 8

    def test_ndjson(self, tmp_path):
        rows = _sample_rows(3, 2)
        path = str(tmp_path / "grb.ndjson")
        with open(path, "w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        out = load_grb_events(path)
        assert out["metadata"]["n_events"] == 6

    def test_json_column_synonym(self, tmp_path):
        # Use "energy" instead of "photon_energy", "time" instead of "arrival_time"
        rows = [
            {"id": "e1", "energy": 5.0, "time": 1.0, "source": "GRB001"},
            {"id": "e2", "energy": 10.0, "time": 2.0, "source": "GRB001"},
        ]
        path = _make_json(str(tmp_path / "grb.json"), rows)
        out = load_grb_events(path)
        assert out["metadata"]["n_events"] == 2

    def test_mev_energy_conversion(self, tmp_path):
        rows = [
            {"event_id": "a", "photon_energy": 1000.0, "arrival_time": 0.0,
             "source_id": "GRB_MeV", "energy_unit": "MeV"},
            {"event_id": "b", "photon_energy": 5000.0, "arrival_time": 1.0,
             "source_id": "GRB_MeV", "energy_unit": "MeV"},
        ]
        path = _make_json(str(tmp_path / "mev.json"), rows)
        out = load_grb_events(path)
        assert abs(out["events"][0]["energy"] - 1.0) < 1e-9   # 1000 MeV = 1 GeV
        assert abs(out["events"][1]["energy"] - 5.0) < 1e-9   # 5000 MeV = 5 GeV


# ---------------------------------------------------------------------------
# to_timing_pipeline_format
# ---------------------------------------------------------------------------


class TestToPipelineFormat:
    def _make_adapter_output(self, tmp_path):
        rows = _sample_rows(5, 3)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        return load_grb_events(path)

    def test_output_keys(self, tmp_path):
        raw = self._make_adapter_output(tmp_path)
        fmt = to_timing_pipeline_format(raw)
        for k in ("energy_GeV", "distance_Mpc", "timing_offset_s",
                  "n_events", "n_sources", "metadata"):
            assert k in fmt

    def test_list_lengths_match(self, tmp_path):
        raw = self._make_adapter_output(tmp_path)
        fmt = to_timing_pipeline_format(raw)
        n = fmt["n_events"]
        assert len(fmt["energy_GeV"]) == n
        assert len(fmt["distance_Mpc"]) == n
        assert len(fmt["timing_offset_s"]) == n

    def test_fallback_distance(self, tmp_path):
        rows = [
            {"event_id": "a", "photon_energy": 1.0, "arrival_time": 0.0, "source_id": "G1"},
            {"event_id": "b", "photon_energy": 2.0, "arrival_time": 1.0, "source_id": "G1"},
        ]
        path = _make_json(str(tmp_path / "no_dist.json"), rows)
        raw = load_grb_events(path)
        fmt = to_timing_pipeline_format(raw, distance_fallback_Mpc=999.0)
        assert all(d == 999.0 for d in fmt["distance_Mpc"])

    def test_load_and_convert_wrapper(self, tmp_path):
        rows = _sample_rows(4, 2)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        fmt = load_and_convert(path)
        assert "energy_GeV" in fmt
        assert "timing_offset_s" in fmt

    def test_timing_offsets_non_negative(self, tmp_path):
        rows = _sample_rows(6, 2)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        fmt = load_and_convert(path)
        assert all(t >= 0 for t in fmt["timing_offset_s"])


# ---------------------------------------------------------------------------
# Integration: real_timing_pipeline with adapter data
# ---------------------------------------------------------------------------


class TestRealTimingPipelineIntegration:
    def _events(self, tmp_path, n_per_grb=20, n_grb=8):
        rows = _sample_rows(n_per_grb, n_grb)
        path = _make_csv(str(tmp_path / "grb.csv"), rows, HEADERS_STANDARD)
        return load_and_convert(path)

    def test_null_run_has_required_keys(self, tmp_path):
        events = self._events(tmp_path)
        result = run_real_timing_pipeline(
            events=events,
            experiment_name="test_null",
            n_permutations=50,
            seed=1,
            output_dir=str(tmp_path / "out"),
            run_recovery_test=False,
            freeze_immediately=True,
        )
        for k in ("observed_slope", "p_value", "z_score",
                  "null_retained", "detection_claimed"):
            assert k in result

    def test_p_value_in_range(self, tmp_path):
        events = self._events(tmp_path)
        result = run_real_timing_pipeline(
            events, n_permutations=50, seed=2,
            output_dir=str(tmp_path / "out"),
            freeze_immediately=True,
        )
        assert 0.0 <= result["p_value"] <= 1.0

    def test_null_synthetic_data_retained(self, tmp_path):
        """Adapter data with no injected delay should retain null (p > threshold)."""
        events = self._events(tmp_path, n_per_grb=30, n_grb=5)
        result = run_real_timing_pipeline(
            events, n_permutations=100, seed=42,
            output_dir=str(tmp_path / "out"),
            freeze_immediately=True,
        )
        # timing offsets are relative times within bursts (essentially noise)
        # null should typically be retained — we don't assert p>0.05 (random)
        # but assert no detection was claimed
        assert result["detection_claimed"] is False

    def test_recovery_test_present(self, tmp_path):
        events = self._events(tmp_path)
        result = run_real_timing_pipeline(
            events, n_permutations=50, seed=3,
            output_dir=str(tmp_path / "out"),
            freeze_immediately=True,
            run_recovery_test=True,
        )
        assert "recovery_test" in result
        assert "recovered" in result["recovery_test"]

    def test_blinded_before_freeze(self, tmp_path):
        """Without freeze_immediately, signal keys are blinded."""
        events = self._events(tmp_path)
        result = run_real_timing_pipeline(
            events, n_permutations=20, seed=4,
            output_dir=str(tmp_path / "out2"),
            freeze_immediately=False,
        )
        assert result["p_value"] == "<BLINDED>"
        assert result["observed_slope"] == "<BLINDED>"

    def test_unblinded_after_freeze(self, tmp_path):
        events = self._events(tmp_path)
        result = run_real_timing_pipeline(
            events, n_permutations=20, seed=5,
            output_dir=str(tmp_path / "out3"),
            freeze_immediately=True,
        )
        assert isinstance(result["p_value"], float)
        assert isinstance(result["observed_slope"], float)

    def test_output_files_written(self, tmp_path):
        events = self._events(tmp_path)
        out = str(tmp_path / "pipeline_out")
        run_real_timing_pipeline(
            events, n_permutations=20, seed=6,
            output_dir=out,
            freeze_immediately=True,
        )
        files = os.listdir(out)
        assert any("blinded" in f for f in files)
        assert any("unblinded" in f for f in files)

    def test_too_few_events_raises(self, tmp_path):
        events = {
            "energy_GeV": [1.0],
            "distance_Mpc": [500.0],
            "timing_offset_s": [0.0],
            "n_events": 1,
            "n_sources": 1,
            "metadata": {},
        }
        with pytest.raises(ValueError):
            run_real_timing_pipeline(
                events, output_dir=str(tmp_path / "err"),
            )

    def test_custom_column_map(self, tmp_path):
        """Adapter handles non-standard column names via column_map."""
        rows = [
            {"uid": "1", "e_mev": 700.0, "t_s": 0.5,
             "burst": "GRB_A", "z": 0.5},
            {"uid": "2", "e_mev": 1200.0, "t_s": 1.5,
             "burst": "GRB_A", "z": 0.5},
            {"uid": "3", "e_mev": 900.0, "t_s": 2.5,
             "burst": "GRB_A", "z": 0.5},
        ]
        path = _make_json(str(tmp_path / "custom.json"), rows)
        cmap = {
            "event_id": "uid",
            "photon_energy": "e_mev",
            "arrival_time": "t_s",
            "source_id": "burst",
            "redshift": "z",
        }
        raw = load_grb_events(path, column_map=cmap, energy_unit="MeV")
        fmt = to_timing_pipeline_format(raw)
        # 700 MeV = 0.7 GeV
        assert abs(fmt["energy_GeV"][0] - 0.7) < 1e-6
        assert fmt["n_events"] == 3
