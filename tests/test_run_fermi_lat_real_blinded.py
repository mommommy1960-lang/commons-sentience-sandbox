"""
tests/test_run_fermi_lat_real_blinded.py
=========================================
Tests for run_fermi_lat_real_blinded.py.

Coverage:
  - Pre-condition checks (missing registration, missing source file)
  - Normal blinded run on mock-public-schema CSV
  - Signal keys are correctly blinded
  - Blinded summary written to disk
  - Run manifest written with correct status
  - QC report written
  - Blinded run blocked when QC stopping rule triggers
  - No automatic unblind in any scenario
"""

import csv
import json
import pathlib
import pytest

_REPO_ROOT = pathlib.Path(__file__).parent.parent

from reality_audit.data_analysis.run_fermi_lat_real_blinded import (
    run_fermi_lat_real_blinded,
    BlindedRunError,
    _blind_result,
    _SIGNAL_KEYS,
)
from reality_audit.data_analysis.register_fermi_lat_real_analysis import (
    REGISTRATION,
    register,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_mock_csv(path: pathlib.Path, n_per_grb: int = 10, n_grb: int = 5) -> str:
    """Write a mock CSV matching the strict public schema."""
    import random
    rng = random.Random(99)
    grbs = [
        ("GRB080916C", 4.35),
        ("GRB090902B", 1.822),
        ("GRB090510",  0.903),
        ("GRB130427A", 0.340),
        ("GRB160509A", 1.170),
    ][:n_grb]
    rows = []
    ei = 1
    for grb, z in grbs:
        for _ in range(n_per_grb):
            rows.append({
                "event_id": f"EVT_{ei:04d}",
                "source_id": grb,
                "photon_energy": round(rng.uniform(0.1, 50.0), 4),
                "arrival_time": round(rng.uniform(0.0, 20.0), 4),
                "redshift": z,
            })
            ei += 1
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return str(path)


def _write_registration(path: pathlib.Path) -> str:
    """Write a copy of the frozen registration to a temp path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(REGISTRATION, f, indent=2)
    return str(path)


# ---------------------------------------------------------------------------
# 1. TestBlindResultHelper
# ---------------------------------------------------------------------------

class TestBlindResultHelper:
    def test_signal_keys_replaced(self):
        fake = {
            "observed_slope": 1.23e-5,
            "p_value": 0.001,
            "z_score": 3.1,
            "detection_claimed": True,
            "null_retained": False,
            "n_events": 50,
        }
        blinded = _blind_result(fake)
        for key in _SIGNAL_KEYS:
            assert blinded[key] == "BLINDED", f"{key} not blinded"

    def test_non_signal_keys_preserved(self):
        fake = {"n_events": 50, "p_value": 0.01, "observed_slope": 1e-5,
                "z_score": 2.0, "detection_claimed": False, "null_retained": True}
        blinded = _blind_result(fake)
        assert blinded["n_events"] == 50

    def test_recovery_test_blinded(self):
        fake = {
            "observed_slope": 0.0, "p_value": 0.5,
            "z_score": 0.0, "detection_claimed": False, "null_retained": True,
            "recovery_test": {"p_value": 0.001, "recovered": True, "model": "x"},
        }
        blinded = _blind_result(fake)
        assert blinded["recovery_test"]["p_value"] == "BLINDED"
        assert blinded["recovery_test"]["recovered"] == "BLINDED"
        assert blinded["recovery_test"]["model"] == "x"  # non-signal preserved


# ---------------------------------------------------------------------------
# 2. TestPreconditionChecks
# ---------------------------------------------------------------------------

class TestPreconditionChecks:
    def test_missing_registration_raises(self, tmp_path):
        csv_path = str(_make_mock_csv(tmp_path / "data.csv"))
        with pytest.raises(BlindedRunError, match="Registration file required"):
            run_fermi_lat_real_blinded(
                source_file=csv_path,
                registration_path=str(tmp_path / "nonexistent_reg.json"),
                output_dir=str(tmp_path / "out"),
            )

    def test_missing_source_file_raises(self, tmp_path):
        reg_path = str(_write_registration(tmp_path / "reg.json"))
        with pytest.raises(FileNotFoundError):
            run_fermi_lat_real_blinded(
                source_file=str(tmp_path / "no_such_file.csv"),
                registration_path=reg_path,
                output_dir=str(tmp_path / "out"),
                dry_run_ingest=True,
            )

    def test_unfrozen_registration_raises(self, tmp_path):
        reg = dict(REGISTRATION)
        reg["frozen"] = False
        reg_path = tmp_path / "unfrozen_reg.json"
        with open(reg_path, "w") as f:
            json.dump(reg, f)
        csv_path = _make_mock_csv(tmp_path / "data.csv")
        with pytest.raises(BlindedRunError, match="not marked frozen"):
            run_fermi_lat_real_blinded(
                source_file=str(csv_path),
                registration_path=str(reg_path),
                output_dir=str(tmp_path / "out"),
                dry_run_ingest=True,
            )


# ---------------------------------------------------------------------------
# 3. TestNormalBlindedRun
# ---------------------------------------------------------------------------

class TestNormalBlindedRun:
    def _run(self, tmp_path):
        csv_path = _make_mock_csv(tmp_path / "data.csv")
        reg_path = _write_registration(tmp_path / "reg.json")
        return run_fermi_lat_real_blinded(
            source_file=csv_path,
            registration_path=reg_path,
            output_dir=str(tmp_path / "out"),
            n_permutations=100,
            seed=42,
            dry_run_ingest=True,
        )

    def test_run_ok(self, tmp_path):
        result = self._run(tmp_path)
        assert result["run_ok"] is True

    def test_ingest_complete(self, tmp_path):
        result = self._run(tmp_path)
        assert result["ingest_complete"] is True

    def test_no_stop_reasons(self, tmp_path):
        result = self._run(tmp_path)
        assert result["stop_reasons"] == []

    def test_blinded_summary_written(self, tmp_path):
        result = self._run(tmp_path)
        assert pathlib.Path(result["blinded_summary_path"]).exists()

    def test_run_manifest_written(self, tmp_path):
        result = self._run(tmp_path)
        assert pathlib.Path(result["run_manifest_path"]).exists()

    def test_qc_report_written(self, tmp_path):
        result = self._run(tmp_path)
        assert pathlib.Path(result["qc_report_path"]).exists()

    def test_signal_keys_blinded_in_summary(self, tmp_path):
        result = self._run(tmp_path)
        with open(result["blinded_summary_path"]) as f:
            summary = json.load(f)
        for key in _SIGNAL_KEYS:
            if key in summary:
                assert summary[key] == "BLINDED", (
                    f"Signal key '{key}' not blinded in written summary"
                )

    def test_blinded_true_in_summary(self, tmp_path):
        result = self._run(tmp_path)
        with open(result["blinded_summary_path"]) as f:
            summary = json.load(f)
        assert summary["blinded"] is True

    def test_unblind_permitted_false(self, tmp_path):
        result = self._run(tmp_path)
        with open(result["blinded_summary_path"]) as f:
            summary = json.load(f)
        assert summary["unblind_permitted"] is False

    def test_run_manifest_status_ok(self, tmp_path):
        result = self._run(tmp_path)
        with open(result["run_manifest_path"]) as f:
            manifest = json.load(f)
        assert manifest["status"] == "OK"
        assert manifest["automatic_unblind"] is False

    def test_qc_report_proceed_true(self, tmp_path):
        result = self._run(tmp_path)
        with open(result["qc_report_path"]) as f:
            qc = json.load(f)
        assert qc["proceed_to_analysis"] is True
        assert qc["ingest_complete"] is True


# ---------------------------------------------------------------------------
# 4. TestBlockedRun (insufficient data)
# ---------------------------------------------------------------------------

class TestBlockedRun:
    def _run_insufficient(self, tmp_path):
        """Only 1 event per GRB; well below minimum."""
        csv_path = _make_mock_csv(tmp_path / "tiny.csv", n_per_grb=1, n_grb=2)
        reg_path = _write_registration(tmp_path / "reg.json")
        # dry_run_ingest=False so IngestConfig raises IngestError on stop;
        # but run_fermi_lat_real_blinded catches the stop via returned manifest.
        # Use dry_run_ingest=True here so the function returns a blocked result
        # rather than re-raising IngestError.
        return run_fermi_lat_real_blinded(
            source_file=str(csv_path),
            registration_path=str(reg_path),
            output_dir=str(tmp_path / "out"),
            n_permutations=50,
            seed=42,
            dry_run_ingest=True,
        )

    def test_run_ok_false(self, tmp_path):
        result = self._run_insufficient(tmp_path)
        assert result["run_ok"] is False

    def test_stop_reasons_non_empty(self, tmp_path):
        result = self._run_insufficient(tmp_path)
        assert len(result["stop_reasons"]) > 0

    def test_ingest_complete_false(self, tmp_path):
        result = self._run_insufficient(tmp_path)
        assert result["ingest_complete"] is False

    def test_blinded_summary_shows_blocked(self, tmp_path):
        result = self._run_insufficient(tmp_path)
        with open(result["blinded_summary_path"]) as f:
            summary = json.load(f)
        assert summary["status"] == "BLOCKED"

    def test_run_manifest_shows_blocked(self, tmp_path):
        result = self._run_insufficient(tmp_path)
        with open(result["run_manifest_path"]) as f:
            manifest = json.load(f)
        assert manifest["status"] == "BLOCKED"
        assert manifest["analysis_ran"] is False


# ---------------------------------------------------------------------------
# 5. TestNoAutoUnblind
# ---------------------------------------------------------------------------

class TestNoAutoUnblind:
    """Verify that no automatic unblinding happens under any scenario."""

    def test_normal_run_never_unblinded(self, tmp_path):
        csv_path = _make_mock_csv(tmp_path / "data.csv")
        reg_path = _write_registration(tmp_path / "reg.json")
        result = run_fermi_lat_real_blinded(
            source_file=str(csv_path),
            registration_path=str(reg_path),
            output_dir=str(tmp_path / "out"),
            n_permutations=100,
            seed=42,
            dry_run_ingest=True,
        )
        # Run manifest must say automatic_unblind=False
        with open(result["run_manifest_path"]) as f:
            manifest = json.load(f)
        assert manifest.get("automatic_unblind") is False

    def test_blinded_summary_never_contains_raw_p_value(self, tmp_path):
        csv_path = _make_mock_csv(tmp_path / "data.csv")
        reg_path = _write_registration(tmp_path / "reg.json")
        result = run_fermi_lat_real_blinded(
            source_file=str(csv_path),
            registration_path=str(reg_path),
            output_dir=str(tmp_path / "out"),
            n_permutations=100,
            seed=42,
            dry_run_ingest=True,
        )
        with open(result["blinded_summary_path"]) as f:
            raw_text = f.read()
        # The literal float p-value must not appear as a plain number in the file
        # (it will appear as the string "BLINDED")
        assert '"p_value": "BLINDED"' in raw_text or '"p_value":"BLINDED"' in raw_text
