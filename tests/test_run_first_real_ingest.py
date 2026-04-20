"""
tests/test_run_first_real_ingest.py
====================================
Tests for reality_audit/data_analysis/run_first_real_ingest.py
"""

import csv
import json
import pathlib

import pytest

from reality_audit.data_analysis.run_first_real_ingest import (
    _find_real_candidates,
    run_first_real_ingest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: pathlib.Path, n=40, n_grb=6, arrival_col="time_s"):
    grbs = [f"GRB{i:04d}" for i in range(n_grb)]
    rows = []
    for i in range(n):
        rows.append({
            "event_id": f"EVT{i:05d}",
            "grb_name": grbs[i % n_grb],
            "energy_gev": 1.0 + (i % 10) * 0.5,
            arrival_col: float(i) * 5.0,
            "redshift": 0.5 + (i % n_grb) * 0.3,
            "grb_t90_s": 60.0,
        })
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# TestFindRealCandidates
# ---------------------------------------------------------------------------

class TestFindRealCandidates:
    def test_empty_dir_returns_empty(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        assert _find_real_candidates(d) == []

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        assert _find_real_candidates(tmp_path / "missing") == []

    def test_synthetic_file_excluded(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        (d / "synthetic_fermi_lat_grb_events.csv").write_text("a,b\n1,2\n")
        assert _find_real_candidates(d) == []

    def test_real_file_included(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        f = d / "grb_events.csv"
        f.write_text("a,b\n1,2\n")
        result = _find_real_candidates(d)
        assert len(result) == 1
        assert result[0] == f

    def test_synthetic_excluded_real_included(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        (d / "synthetic_fermi_lat_grb_events.csv").write_text("a,b\n1,2\n")
        real = d / "real_grb_events.csv"
        real.write_text("a,b\n1,2\n")
        result = _find_real_candidates(d)
        assert result == [real]

    def test_uppercase_synthetic_excluded(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        (d / "SYNTHETIC_data.csv").write_text("a,b\n1,2\n")
        assert _find_real_candidates(d) == []


# ---------------------------------------------------------------------------
# TestWaitingState
# ---------------------------------------------------------------------------

class TestWaitingState:
    def test_empty_dir_returns_waiting(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        mfst = tmp_path / "manifest.json"
        result = run_first_real_ingest(
            data_dir=str(d),
            manifest_path=str(mfst),
        )
        assert result["status"] == "WAITING"
        assert result["candidate"] is None

    def test_waiting_manifest_written(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        mfst = tmp_path / "manifest.json"
        run_first_real_ingest(data_dir=str(d), manifest_path=str(mfst))
        assert mfst.exists()
        data = json.loads(mfst.read_text())
        assert data["status"] == "WAITING"

    def test_waiting_message_content(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        mfst = tmp_path / "manifest.json"
        result = run_first_real_ingest(data_dir=str(d), manifest_path=str(mfst))
        assert "No real dataset detected" in result["message"]

    def test_only_synthetic_returns_waiting(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        _write_csv(d / "synthetic_rehearsal.csv")
        mfst = tmp_path / "manifest.json"
        result = run_first_real_ingest(data_dir=str(d), manifest_path=str(mfst))
        assert result["status"] == "WAITING"


# ---------------------------------------------------------------------------
# TestBlockedState
# ---------------------------------------------------------------------------

class TestBlockedState:
    def test_too_few_events_blocked(self, tmp_path):
        """File with < 30 events should be BLOCKED (REJECT from check)."""
        d = tmp_path / "real"
        d.mkdir()
        _write_csv(d / "grb_data.csv", n=5, n_grb=2)
        mfst = tmp_path / "manifest.json"
        result = run_first_real_ingest(data_dir=str(d), manifest_path=str(mfst))
        assert result["status"] == "BLOCKED"
        assert result["check_report"] is not None
        assert result["check_report"]["recommendation"] == "REJECT"

    def test_blocked_manifest_written(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        _write_csv(d / "grb_data.csv", n=5, n_grb=2)
        mfst = tmp_path / "manifest.json"
        run_first_real_ingest(data_dir=str(d), manifest_path=str(mfst))
        data = json.loads(mfst.read_text())
        assert data["status"] == "BLOCKED"

    def test_insufficient_redshift_blocked(self, tmp_path):
        """File with 0 sources having redshift → REJECT."""
        d = tmp_path / "real"
        d.mkdir()
        rows = [
            {"event_id": f"E{i}", "grb_name": f"GRB{i%6:04d}",
             "energy_gev": 1.0, "time_s": float(i),
             "redshift": "", "grb_t90_s": 60.0}
            for i in range(40)
        ]
        p = d / "grb_noredshift.csv"
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        mfst = tmp_path / "manifest.json"
        result = run_first_real_ingest(data_dir=str(d), manifest_path=str(mfst))
        assert result["status"] == "BLOCKED"


# ---------------------------------------------------------------------------
# TestCompleteState
# ---------------------------------------------------------------------------

class TestCompleteState:
    def test_valid_file_completes(self, tmp_path):
        """A file that passes all gates should result in COMPLETE status."""
        reg = pathlib.Path(
            "commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json"
        )
        if not reg.exists():
            pytest.skip("Registration JSON not present")
        d = tmp_path / "real"
        d.mkdir()
        _write_csv(d / "grb_real.csv", n=40, n_grb=6)
        mfst = tmp_path / "manifest.json"
        result = run_first_real_ingest(
            data_dir=str(d),
            registration_path=str(reg),
            manifest_path=str(mfst),
            n_permutations=50,
            seed=0,
        )
        assert result["status"] == "COMPLETE"
        assert result["candidate"] is not None

    def test_complete_manifest_written(self, tmp_path):
        reg = pathlib.Path(
            "commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json"
        )
        if not reg.exists():
            pytest.skip("Registration JSON not present")
        d = tmp_path / "real"
        d.mkdir()
        _write_csv(d / "grb_real.csv", n=40, n_grb=6)
        mfst = tmp_path / "manifest.json"
        run_first_real_ingest(
            data_dir=str(d),
            registration_path=str(reg),
            manifest_path=str(mfst),
            n_permutations=50,
            seed=0,
        )
        data = json.loads(mfst.read_text())
        assert data["status"] == "COMPLETE"
        assert data["blinded_result"] is not None

    def test_no_automatic_unblind(self, tmp_path):
        """Blinded result must never contain raw signal values."""
        reg = pathlib.Path(
            "commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json"
        )
        if not reg.exists():
            pytest.skip("Registration JSON not present")
        d = tmp_path / "real"
        d.mkdir()
        _write_csv(d / "grb_real.csv", n=40, n_grb=6)
        mfst = tmp_path / "manifest.json"
        run_first_real_ingest(
            data_dir=str(d),
            registration_path=str(reg),
            manifest_path=str(mfst),
            n_permutations=50,
            seed=0,
        )
        text = mfst.read_text()
        # Signal keys must not appear as floats / booleans in the written manifest
        import re
        assert not re.search(r'"p_value"\s*:\s*[0-9]', text)
        assert not re.search(r'"z_score"\s*:\s*[0-9\-]', text)

    def test_complete_message_mentions_unblinding(self, tmp_path):
        reg = pathlib.Path(
            "commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json"
        )
        if not reg.exists():
            pytest.skip("Registration JSON not present")
        d = tmp_path / "real"
        d.mkdir()
        _write_csv(d / "grb_real.csv", n=40, n_grb=6)
        mfst = tmp_path / "manifest.json"
        result = run_first_real_ingest(
            data_dir=str(d),
            registration_path=str(reg),
            manifest_path=str(mfst),
            n_permutations=50,
            seed=0,
        )
        assert "unblind" in result["message"].lower()


# ---------------------------------------------------------------------------
# TestManifestStructure
# ---------------------------------------------------------------------------

class TestManifestStructure:
    def test_manifest_has_required_keys(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        mfst = tmp_path / "manifest.json"
        result = run_first_real_ingest(data_dir=str(d), manifest_path=str(mfst))
        required = {"status", "candidate", "check_report", "blinded_result",
                    "manifest_path", "message"}
        for k in required:
            assert k in result, f"Missing key: {k}"

    def test_manifest_path_recorded(self, tmp_path):
        d = tmp_path / "real"
        d.mkdir()
        mfst = tmp_path / "my_manifest.json"
        result = run_first_real_ingest(data_dir=str(d), manifest_path=str(mfst))
        assert result["manifest_path"] == str(mfst)
