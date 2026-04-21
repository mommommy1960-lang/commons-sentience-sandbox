"""
tests/test_fermi_lat_public_ingest.py
======================================
Tests for the fermi_lat_public_ingest module.

Validates:
  - Schema validation
  - Energy-unit consistency check
  - Timestamp consistency check
  - Duplicate detection
  - Redshift coverage check
  - Outlier flagging
  - Stopping rules
  - Manifest output
  - Safe stop on missing file
  - Dry-run mode bypass
  - Full pipeline format compatibility
"""

import csv
import json
import os
import pathlib
import pytest
import tempfile

from reality_audit.adapters.fermi_lat_public_ingest import (
    IngestConfig,
    IngestError,
    ingest_public_file,
    _check_energy_units,
    _check_timestamps,
    _check_duplicates,
    _check_redshift_coverage,
    _check_outlier_energies,
    _check_schema,
)

REPO_ROOT = pathlib.Path(__file__).parent.parent
SAMPLE_CSV = REPO_ROOT / "data" / "sample_fermi_lat_grb_events.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: pathlib.Path, rows: list, extra_cols: list = None) -> None:
    headers = ["event_id", "source_id", "photon_energy", "arrival_time", "redshift"]
    if extra_cols:
        headers += extra_cols
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)


def _sample_rows(n_per_src=10, n_src=5, seed=77) -> list:
    import random
    rng = random.Random(seed)
    grbs = [(f"GRB{i:03d}", round(rng.uniform(0.1, 3.0), 3)) for i in range(n_src)]
    rows = []
    ei = 1
    for grb, z in grbs:
        for j in range(n_per_src):
            rows.append({
                "event_id": f"EVT_{ei:04d}",
                "source_id": grb,
                "photon_energy": round(rng.uniform(0.1, 20.0), 4),
                "arrival_time": round(rng.uniform(0.0, 100.0), 3),
                "redshift": z,
            })
            ei += 1
    return rows


# ---------------------------------------------------------------------------
# TestMissingFile
# ---------------------------------------------------------------------------

class TestMissingFile:
    def test_missing_file_raises_file_not_found(self, tmp_path):
        cfg = IngestConfig(source_file=str(tmp_path / "nonexistent.csv"), dry_run=True)
        with pytest.raises(FileNotFoundError):
            ingest_public_file(cfg)


# ---------------------------------------------------------------------------
# TestSampleFileIngest
# ---------------------------------------------------------------------------

class TestSampleFileIngest:
    def test_sample_csv_ingests_ok(self, tmp_path):
        cfg = IngestConfig(
            source_file=str(SAMPLE_CSV),
            output_dir=str(tmp_path),
            dry_run=True,
        )
        result = ingest_public_file(cfg)
        assert result["stopped"] is False

    def test_result_keys_present(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        for key in ("raw", "pipeline_fmt", "manifest", "stopped", "stop_reasons", "manifest_path"):
            assert key in result

    def test_manifest_written(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        assert pathlib.Path(result["manifest_path"]).exists()

    def test_manifest_has_required_keys(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        m = result["manifest"]
        for key in ("ingest_timestamp", "source_file", "metadata", "warnings",
                    "stopping_rules_triggered", "stopped", "status"):
            assert key in m, f"Missing manifest key: {key}"

    def test_manifest_n_events(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        assert result["manifest"]["n_events_after_qc"] == 50

    def test_pipeline_fmt_present(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        fmt = result["pipeline_fmt"]
        assert "energy_GeV" in fmt
        assert "distance_Mpc" in fmt
        assert "timing_offset_s" in fmt


# ---------------------------------------------------------------------------
# TestStoppingRules
# ---------------------------------------------------------------------------

class TestStoppingRules:
    def test_too_few_total_events_stops(self, tmp_path):
        """If min_total_events > actual, ingest should stop."""
        cfg = IngestConfig(
            source_file=str(SAMPLE_CSV),
            output_dir=str(tmp_path),
            min_total_events=10000,   # impossible to satisfy
        )
        # dry_run=False so IngestError should be raised
        with pytest.raises(IngestError, match="too_few_total_events"):
            ingest_public_file(cfg)

    def test_too_few_events_dry_run_does_not_raise(self, tmp_path):
        """Dry run should record stop but not raise."""
        cfg = IngestConfig(
            source_file=str(SAMPLE_CSV),
            output_dir=str(tmp_path),
            min_total_events=10000,
            dry_run=True,
        )
        result = ingest_public_file(cfg)
        assert result["stopped"] is True
        assert "too_few_total_events" in result["stop_reasons"]

    def test_duplicate_ids_stops(self, tmp_path):
        """Duplicate event IDs should trigger stop."""
        rows = _sample_rows(n_per_src=10, n_src=5)
        # Introduce 10% duplicates (5 dups out of 50 rows >> 0.1%)
        rows[:5] = [dict(r, event_id="EVT_0001") for r in rows[:5]]
        path = tmp_path / "dup.csv"
        _write_csv(path, rows)
        cfg = IngestConfig(source_file=str(path), output_dir=str(tmp_path))
        with pytest.raises(IngestError, match="duplicate_ids"):
            ingest_public_file(cfg)

    def test_too_few_redshift_stops(self, tmp_path):
        """Fewer GRBs with redshift than required should stop."""
        rows = _sample_rows(n_per_src=10, n_src=3)  # only 3 sources
        path = tmp_path / "few_src.csv"
        _write_csv(path, rows)
        cfg = IngestConfig(
            source_file=str(path),
            output_dir=str(tmp_path),
            min_sources_with_redshift=5,  # need 5 but only 3 sources
        )
        with pytest.raises(IngestError, match="redshift_coverage"):
            ingest_public_file(cfg)


# ---------------------------------------------------------------------------
# TestQCChecks
# ---------------------------------------------------------------------------

class TestQCChecks:
    def _make_raw_stub(self, energies, times_per_source=None, redshifts=None,
                       n_src=3, events_with_z=True):
        """Build a minimal raw adapter output dict for unit-testing QC functions."""
        events = []
        by_source = {}
        for i in range(n_src):
            src = f"GRB{i:03d}"
            src_evs = []
            for j, e in enumerate(energies):
                t = (times_per_source or [j * 1.0] * len(energies))[j]
                z = (redshifts[i] if redshifts else 0.5) if events_with_z else None
                ev = {"event_id": f"EVT_{i}_{j}", "energy": e, "time": t,
                      "source": src, "redshift": z, "distance_Mpc": 1000.0}
                events.append(ev)
                src_evs.append(ev)
            by_source[src] = {
                "events": src_evs,
                "n_events": len(src_evs),
                "mean_energy_GeV": sum(energies) / len(energies),
                "time_span_s": max(times_per_source or [j for j in range(len(energies))]),
            }
        return {
            "events": events,
            "by_source": by_source,
            "metadata": {
                "n_events": len(events),
                "n_sources": n_src,
                "n_dropped": 0,
                "energy_unit_in": "GeV",
                "schema_version": "1.0",
            },
        }

    def test_energy_implausible_large(self):
        raw = self._make_raw_stub([1e7])  # 10 million GeV — implausible
        warnings = _check_energy_units(raw)
        assert any("implausibly large" in w for w in warnings)

    def test_energy_implausible_small(self):
        raw = self._make_raw_stub([1e-8])  # essentially 0 GeV
        warnings = _check_energy_units(raw)
        assert any("implausibly small" in w for w in warnings)

    def test_energy_normal_no_warning(self):
        raw = self._make_raw_stub([0.5, 1.0, 5.0, 10.0])
        warnings = _check_energy_units(raw)
        assert len(warnings) == 0

    def test_timestamp_large_span_warns(self):
        raw = self._make_raw_stub([1.0], times_per_source=[0.0])
        # Manually set a large time_span
        for src in raw["by_source"].values():
            src["time_span_s"] = 172800  # 2 days
        warnings = _check_timestamps(raw)
        assert any("86400" in w or "1 day" in w for w in warnings)

    def test_timestamp_normal_no_warning(self):
        raw = self._make_raw_stub([1.0, 2.0], times_per_source=[0.0, 50.0])
        warnings = _check_timestamps(raw)
        assert len(warnings) == 0

    def test_duplicate_check_triggered(self):
        raw = self._make_raw_stub([1.0, 2.0], n_src=1)
        # inject duplicates
        for ev in raw["events"][1:]:
            ev["event_id"] = raw["events"][0]["event_id"]
        warnings = _check_duplicates(raw, max_fraction=0.001)
        assert any("Duplicate" in w for w in warnings)

    def test_duplicate_check_clean(self):
        raw = self._make_raw_stub([1.0, 2.0, 3.0])
        warnings = _check_duplicates(raw, max_fraction=0.001)
        assert len(warnings) == 0

    def test_redshift_coverage_ok(self):
        raw = self._make_raw_stub([1.0], n_src=5, events_with_z=True)
        warnings = _check_redshift_coverage(raw, min_sources=5)
        assert len(warnings) == 0

    def test_redshift_coverage_insufficient(self):
        raw = self._make_raw_stub([1.0], n_src=3, events_with_z=True)
        warnings = _check_redshift_coverage(raw, min_sources=5)
        assert any("STOPPING" in w for w in warnings)

    def test_outlier_flag(self):
        # One massive outlier
        energies = [0.1] * 20 + [1e5]
        raw = self._make_raw_stub(energies)
        warnings = _check_outlier_energies(raw)
        assert any("outlier" in w for w in warnings)

    def test_no_outlier_flag_normal(self):
        raw = self._make_raw_stub([0.1, 0.5, 1.0, 2.0, 5.0, 10.0])
        warnings = _check_outlier_energies(raw)
        assert len(warnings) == 0


# ---------------------------------------------------------------------------
# TestManifestContent
# ---------------------------------------------------------------------------

class TestManifestContent:
    def test_manifest_dry_run_flag(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        assert result["manifest"]["dry_run"] is True

    def test_manifest_by_source_summary(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        summary = result["manifest"]["by_source_summary"]
        assert len(summary) == 5
        for src, s in summary.items():
            assert "n_events" in s
            assert "mean_energy_GeV" in s
            assert "has_redshift" in s

    def test_manifest_status_ok_on_clean_ingest(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        assert result["manifest"]["status"] == "OK"

    def test_manifest_status_stopped_on_failing_ingest(self, tmp_path):
        cfg = IngestConfig(
            source_file=str(SAMPLE_CSV),
            output_dir=str(tmp_path),
            min_total_events=10000,
            dry_run=True,
        )
        result = ingest_public_file(cfg)
        # dry_run=True so it doesn't raise, but manifest should say STOPPED
        assert result["manifest"]["stopped"] is True


# ---------------------------------------------------------------------------
# TestPipelineFormatFromIngest
# ---------------------------------------------------------------------------

class TestPipelineFormatFromIngest:
    def test_pipeline_fmt_lengths_consistent(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        fmt = result["pipeline_fmt"]
        assert len(fmt["energy_GeV"]) == len(fmt["distance_Mpc"]) == len(fmt["timing_offset_s"])

    def test_pipeline_fmt_all_energies_positive(self, tmp_path):
        cfg = IngestConfig(source_file=str(SAMPLE_CSV), output_dir=str(tmp_path), dry_run=True)
        result = ingest_public_file(cfg)
        assert all(e > 0 for e in result["pipeline_fmt"]["energy_GeV"])
