"""Tests for reality_audit/analysis/metric_calibration.py"""
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import pytest

from reality_audit.analysis.metric_calibration import (
    STATUS_TRUSTED_ABSOLUTE,
    STATUS_TRUSTED_COMPARATIVE,
    STATUS_UNSTABLE_CONFOUNDED,
    STATUS_EXPERIMENTAL,
    _METRIC_CATALOGUE,
    build_calibration_report,
    write_calibration_report,
    run_metric_calibration,
)


# ---------------------------------------------------------------------------
# Catalogue shape tests
# ---------------------------------------------------------------------------

class TestCatalogue:
    def test_all_required_metrics_present(self):
        names = {e["metric"] for e in _METRIC_CATALOGUE}
        required = {
            "path_smoothness", "avg_control_effort", "audit_bandwidth",
            "stability_score", "mean_position_error", "convergence_turn",
            "quantization_artifact_score", "observer_dependence_score",
            "anisotropy_score", "hidden_measured_gap_raw",
            "hidden_measured_gap_path_normalised",
            "observation_schedule_sensitivity",
        }
        assert required.issubset(names)

    def test_every_entry_has_required_keys(self):
        required_keys = {
            "metric", "status", "meaning", "evidence",
            "confounds", "caveats", "encoding_sensitive", "governance_sensitive",
        }
        for entry in _METRIC_CATALOGUE:
            missing = required_keys - entry.keys()
            assert not missing, f"Metric {entry['metric']} missing keys: {missing}"

    def test_all_statuses_are_valid(self):
        valid = {
            STATUS_TRUSTED_ABSOLUTE, STATUS_TRUSTED_COMPARATIVE,
            STATUS_UNSTABLE_CONFOUNDED, STATUS_EXPERIMENTAL,
        }
        for entry in _METRIC_CATALOGUE:
            assert entry["status"] in valid, (
                f"Metric {entry['metric']} has unknown status {entry['status']!r}"
            )

    def test_path_smoothness_is_trusted_absolute(self):
        entry = next(e for e in _METRIC_CATALOGUE if e["metric"] == "path_smoothness")
        assert entry["status"] == STATUS_TRUSTED_ABSOLUTE

    def test_observer_dependence_score_is_unstable(self):
        entry = next(e for e in _METRIC_CATALOGUE if e["metric"] == "observer_dependence_score")
        assert entry["status"] == STATUS_UNSTABLE_CONFOUNDED

    def test_observation_schedule_sensitivity_is_experimental(self):
        entry = next(e for e in _METRIC_CATALOGUE if e["metric"] == "observation_schedule_sensitivity")
        assert entry["status"] == STATUS_EXPERIMENTAL

    def test_anisotropy_is_encoding_sensitive(self):
        entry = next(e for e in _METRIC_CATALOGUE if e["metric"] == "anisotropy_score")
        assert entry["encoding_sensitive"] is True

    def test_path_smoothness_not_encoding_sensitive(self):
        entry = next(e for e in _METRIC_CATALOGUE if e["metric"] == "path_smoothness")
        assert entry["encoding_sensitive"] is False

    def test_avg_control_effort_governance_sensitive(self):
        entry = next(e for e in _METRIC_CATALOGUE if e["metric"] == "avg_control_effort")
        assert entry["governance_sensitive"] is True

    def test_evidence_lists_not_empty_for_validated_metrics(self):
        for entry in _METRIC_CATALOGUE:
            if entry["status"] in (STATUS_TRUSTED_ABSOLUTE, STATUS_TRUSTED_COMPARATIVE):
                assert len(entry["evidence"]) >= 1, (
                    f"Metric {entry['metric']} has no evidence entries"
                )


# ---------------------------------------------------------------------------
# build_calibration_report
# ---------------------------------------------------------------------------

class TestBuildCalibrationReport:
    def test_returns_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            records = build_calibration_report(output_root=Path(tmpdir))
        assert isinstance(records, list)

    def test_one_record_per_catalogue_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            records = build_calibration_report(output_root=Path(tmpdir))
        assert len(records) == len(_METRIC_CATALOGUE)

    def test_each_record_has_sandbox_variability_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            records = build_calibration_report(output_root=Path(tmpdir))
        for r in records:
            assert "sandbox_variability" in r

    def test_enrichment_from_variability_report(self, tmp_path):
        """If sandbox_variability_report.json is present, it should enrich records."""
        var_report = {
            "variability": [
                {"metrics": {"path_smoothness": "stochastic_but_usable"}}
            ]
        }
        (tmp_path / "sandbox_variability_report.json").write_text(
            json.dumps(var_report)
        )
        records = build_calibration_report(output_root=tmp_path)
        ps = next(r for r in records if r["metric"] == "path_smoothness")
        assert ps["sandbox_variability"] == "stochastic_but_usable"

    def test_enrichment_from_encoding_report(self, tmp_path):
        """If encoding_robustness_report.json is present, encoding_sensitive should update."""
        enc_report = {
            "metrics": {
                "path_smoothness": {"verdict": "ENCODING-SENSITIVE", "spread_pct": 99.0}
            }
        }
        (tmp_path / "encoding_robustness_report.json").write_text(
            json.dumps(enc_report)
        )
        records = build_calibration_report(output_root=tmp_path)
        ps = next(r for r in records if r["metric"] == "path_smoothness")
        assert ps["encoding_sensitive"] is True  # overridden from live data

    def test_missing_reports_handled_gracefully(self, tmp_path):
        """No crash if neither variability nor encoding reports exist."""
        records = build_calibration_report(output_root=tmp_path)
        assert len(records) == len(_METRIC_CATALOGUE)


# ---------------------------------------------------------------------------
# write_calibration_report
# ---------------------------------------------------------------------------

class TestWriteCalibrationReport:
    def test_json_written(self, tmp_path):
        records = build_calibration_report(output_root=tmp_path)
        path = write_calibration_report(records, output_root=tmp_path)
        assert path.exists()

    def test_json_is_valid(self, tmp_path):
        records = build_calibration_report(output_root=tmp_path)
        write_calibration_report(records, output_root=tmp_path)
        with open(tmp_path / "metric_calibration_report.json") as fh:
            data = json.load(fh)
        assert "metrics" in data
        assert len(data["metrics"]) == len(_METRIC_CATALOGUE)

    def test_csv_written(self, tmp_path):
        records = build_calibration_report(output_root=tmp_path)
        write_calibration_report(records, output_root=tmp_path)
        assert (tmp_path / "metric_calibration_summary.csv").exists()

    def test_csv_has_correct_columns(self, tmp_path):
        records = build_calibration_report(output_root=tmp_path)
        write_calibration_report(records, output_root=tmp_path)
        with open(tmp_path / "metric_calibration_summary.csv", newline="") as fh:
            reader = csv.DictReader(fh)
            cols = reader.fieldnames
        assert "metric" in cols
        assert "status" in cols
        assert "encoding_sensitive" in cols

    def test_csv_row_count(self, tmp_path):
        records = build_calibration_report(output_root=tmp_path)
        write_calibration_report(records, output_root=tmp_path)
        with open(tmp_path / "metric_calibration_summary.csv", newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == len(_METRIC_CATALOGUE)


# ---------------------------------------------------------------------------
# run_metric_calibration
# ---------------------------------------------------------------------------

class TestRunMetricCalibration:
    def test_returns_dict_with_expected_keys(self, tmp_path):
        result = run_metric_calibration(output_root=tmp_path)
        assert "records" in result
        assert "report_path" in result
        assert "counts" in result

    def test_counts_cover_all_statuses(self, tmp_path):
        result = run_metric_calibration(output_root=tmp_path)
        counts = result["counts"]
        assert sum(counts.values()) == len(_METRIC_CATALOGUE)

    def test_report_path_exists(self, tmp_path):
        result = run_metric_calibration(output_root=tmp_path)
        assert Path(result["report_path"]).exists()

    def test_at_least_one_trusted_absolute(self, tmp_path):
        result = run_metric_calibration(output_root=tmp_path)
        assert result["counts"].get(STATUS_TRUSTED_ABSOLUTE, 0) >= 1

    def test_at_least_one_unstable(self, tmp_path):
        result = run_metric_calibration(output_root=tmp_path)
        assert result["counts"].get(STATUS_UNSTABLE_CONFOUNDED, 0) >= 1
