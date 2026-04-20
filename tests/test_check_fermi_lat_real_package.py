"""
tests/test_check_fermi_lat_real_package.py
==========================================
Tests for reality_audit/data_analysis/check_fermi_lat_real_package.py
"""

import csv
import json
import pathlib
import tempfile

import pytest

from reality_audit.data_analysis.check_fermi_lat_real_package import (
    check_real_package,
    _MIN_TOTAL_EVENTS,
    _MIN_SOURCES_WITH_REDSHIFT,
    _MAX_DUPLICATE_FRACTION,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: pathlib.Path, rows, fieldnames=None):
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _make_rows(
    n=40, n_grb=6, arrival_col="time_s", energy_valid=True, with_redshift=True,
    dup_ids=0,
):
    """Generate minimal valid rows."""
    grbs = [f"GRB{i:04d}" for i in range(n_grb)]
    redshifts = [0.5 + i * 0.3 for i in range(n_grb)]
    rows = []
    for i in range(n):
        grb = grbs[i % n_grb]
        idx = grbs.index(grb)
        z = redshifts[idx] if with_redshift else ""
        eid = f"EVT{i:05d}" if i >= dup_ids else "EVT00000"
        rows.append({
            "event_id": eid,
            "grb_name": grb,
            "energy_gev": 1.0 if energy_valid else 9999.0,
            arrival_col: float(i) * 5.0,
            "redshift": z,
            "grb_t90_s": 60.0,
        })
    return rows


# ---------------------------------------------------------------------------
# TestMissingFile
# ---------------------------------------------------------------------------

class TestMissingFile:
    def test_missing_file_returns_reject(self, tmp_path):
        report = check_real_package(str(tmp_path / "nonexistent.csv"), output_path=str(tmp_path / "out.json"))
        assert report["recommendation"] == "REJECT"
        assert "FILE_NOT_FOUND" in report["hard_failures"]

    def test_missing_file_writes_report(self, tmp_path):
        out = tmp_path / "out.json"
        check_real_package(str(tmp_path / "gone.csv"), output_path=str(out))
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["file_found"] is False

    def test_missing_file_message(self, tmp_path):
        report = check_real_package(str(tmp_path / "nope.csv"), output_path=str(tmp_path / "out.json"))
        assert "No real dataset detected" in report["message"]


# ---------------------------------------------------------------------------
# TestSchemaValidation
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_valid_schema_accepted(self, tmp_path):
        rows = _make_rows()
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["schema_valid"] is True
        assert report["missing_columns"] == []

    def test_missing_energy_col_rejected(self, tmp_path):
        rows = _make_rows()
        for r in rows:
            del r["energy_gev"]
        p = tmp_path / "data.csv"
        _write_csv(p, rows, fieldnames=["event_id", "grb_name", "time_s", "redshift", "grb_t90_s"])
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["schema_valid"] is False
        assert report["recommendation"] == "REJECT"

    def test_missing_arrival_time_col_rejected(self, tmp_path):
        rows = [{"event_id": f"E{i}", "grb_name": "GRB0", "energy_gev": 1.0,
                 "redshift": 1.0, "grb_t90_s": 60.0} for i in range(40)]
        p = tmp_path / "data.csv"
        _write_csv(p, rows, fieldnames=["event_id", "grb_name", "energy_gev", "redshift", "grb_t90_s"])
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["schema_valid"] is False
        assert any("arrival_time" in m for m in report["missing_columns"])

    def test_photon_arrival_time_s_alias_accepted(self, tmp_path):
        rows = _make_rows(arrival_col="photon_arrival_time_s")
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["schema_valid"] is True

    def test_arrival_time_s_alias_accepted(self, tmp_path):
        rows = _make_rows(arrival_col="arrival_time_s")
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["schema_valid"] is True

    def test_t_alias_accepted(self, tmp_path):
        rows = _make_rows(arrival_col="t")
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["schema_valid"] is True


# ---------------------------------------------------------------------------
# TestEventCount
# ---------------------------------------------------------------------------

class TestEventCount:
    def test_sufficient_events_accepted(self, tmp_path):
        rows = _make_rows(n=40)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert not any("TOO_FEW" in f for f in report["hard_failures"])

    def test_too_few_events_rejected(self, tmp_path):
        rows = _make_rows(n=10, n_grb=5)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert any("TOO_FEW_EVENTS" in f for f in report["hard_failures"])
        assert report["recommendation"] == "REJECT"

    def test_event_count_reported(self, tmp_path):
        rows = _make_rows(n=55)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["n_events"] == 55


# ---------------------------------------------------------------------------
# TestDuplicates
# ---------------------------------------------------------------------------

class TestDuplicates:
    def test_no_duplicates_accepted(self, tmp_path):
        rows = _make_rows(n=40, dup_ids=0)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["duplicate_fraction"] == 0.0
        assert not any("DUPLICATE" in f for f in report["hard_failures"])

    def test_high_duplicate_fraction_rejected(self, tmp_path):
        # All event_ids the same → dup fraction ≈ 1.0
        rows = [{"event_id": "EVT00000", "grb_name": f"GRB{i%6:04d}",
                 "energy_gev": 1.0, "time_s": float(i),
                 "redshift": 1.0, "grb_t90_s": 60.0} for i in range(40)]
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert any("DUPLICATE_FRACTION_EXCEEDED" in f for f in report["hard_failures"])
        assert report["recommendation"] == "REJECT"

    def test_duplicate_fraction_value(self, tmp_path):
        rows = _make_rows(n=40, dup_ids=0)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert isinstance(report["duplicate_fraction"], float)


# ---------------------------------------------------------------------------
# TestRedshiftCoverage
# ---------------------------------------------------------------------------

class TestRedshiftCoverage:
    def test_sufficient_redshift_accepted(self, tmp_path):
        rows = _make_rows(n=40, n_grb=6, with_redshift=True)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert not any("REDSHIFT" in f for f in report["hard_failures"])
        assert report["n_sources_with_redshift"] >= 5

    def test_missing_redshift_rejected(self, tmp_path):
        rows = _make_rows(n=40, n_grb=6, with_redshift=False)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert any("INSUFFICIENT_REDSHIFT_COVERAGE" in f for f in report["hard_failures"])
        assert report["recommendation"] == "REJECT"

    def test_n_missing_redshift_count(self, tmp_path):
        rows = _make_rows(n=40, n_grb=6, with_redshift=False)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["n_missing_redshift"] == 40


# ---------------------------------------------------------------------------
# TestEnergyWarning
# ---------------------------------------------------------------------------

class TestEnergyWarning:
    def test_implausible_energy_triggers_warning(self, tmp_path):
        rows = _make_rows(n=40, energy_valid=False)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert any("ENERGY_OUT_OF_RANGE" in w for w in report["warnings"])
        # Warning only → not a hard failure
        assert not any("ENERGY_OUT_OF_RANGE" in f for f in report["hard_failures"])

    def test_implausible_energy_gives_accept_with_warnings(self, tmp_path):
        rows = _make_rows(n=40, energy_valid=False)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["recommendation"] == "ACCEPT_WITH_WARNINGS"


# ---------------------------------------------------------------------------
# TestRecommendation
# ---------------------------------------------------------------------------

class TestRecommendation:
    def test_clean_file_accept_for_blinded_run(self, tmp_path):
        rows = _make_rows(n=40, n_grb=6)
        p = tmp_path / "data.csv"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(tmp_path / "out.json"))
        assert report["recommendation"] == "ACCEPT_FOR_BLINDED_RUN"
        assert report["hard_failures"] == []
        assert report["warnings"] == []

    def test_synthetic_file_passes(self, tmp_path):
        """The rehearsal CSV must still pass the check."""
        synthetic = pathlib.Path("data/real/synthetic_fermi_lat_grb_events.csv")
        if not synthetic.exists():
            pytest.skip("synthetic CSV not present in workspace")
        report = check_real_package(str(synthetic), output_path=str(tmp_path / "out.json"))
        assert report["recommendation"] in ("ACCEPT_FOR_BLINDED_RUN", "ACCEPT_WITH_WARNINGS")
        assert report["hard_failures"] == []


# ---------------------------------------------------------------------------
# TestOutputFile
# ---------------------------------------------------------------------------

class TestOutputFile:
    def test_output_json_written(self, tmp_path):
        rows = _make_rows(n=40)
        p = tmp_path / "data.csv"
        out = tmp_path / "check_report.json"
        _write_csv(p, rows)
        check_real_package(str(p), output_path=str(out))
        assert out.exists()
        data = json.loads(out.read_text())
        assert "recommendation" in data

    def test_output_contains_all_keys(self, tmp_path):
        rows = _make_rows(n=40)
        p = tmp_path / "data.csv"
        out = tmp_path / "check_report.json"
        _write_csv(p, rows)
        report = check_real_package(str(p), output_path=str(out))
        required_keys = {
            "n_events", "n_sources", "n_sources_with_redshift",
            "n_missing_redshift", "duplicate_fraction", "schema_valid",
            "missing_columns", "warnings", "hard_failures", "recommendation",
        }
        for k in required_keys:
            assert k in report, f"Missing key: {k}"
