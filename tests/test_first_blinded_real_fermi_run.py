"""
tests/test_first_blinded_real_fermi_run.py
==========================================
Tests for:
  reality_audit/data_analysis/milestone_report.py
  reality_audit/data_analysis/first_blinded_real_fermi_run.py
"""

import csv
import json
import pathlib

import pytest

from reality_audit.data_analysis.milestone_report import (
    generate_milestone_report,
    _blinding_status,
    _qc_gate_summary,
    _ingest_summary,
    _PROTECTED_KEYS,
)
from reality_audit.data_analysis.first_blinded_real_fermi_run import (
    first_blinded_real_fermi_run,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REG_PATH = pathlib.Path(
    "commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json"
)


def _write_csv(path: pathlib.Path, n=40, n_grb=6):
    grbs = [f"GRB{i:04d}" for i in range(n_grb)]
    rows = [
        {
            "event_id": f"E{i:05d}",
            "grb_name": grbs[i % n_grb],
            "energy_gev": 1.0 + (i % 10) * 0.3,
            "time_s": float(i) * 4.5,
            "redshift": 0.5 + (i % n_grb) * 0.25,
            "grb_t90_s": 60.0,
        }
        for i in range(n)
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _write_blinded_summary(path: pathlib.Path, leaked: bool = False):
    data = {
        "blinded": True,
        "unblind_permitted": False,
        "n_events_analysed": 40,
        "n_sources_analysed": 6,
        "primary_statistic": "timing_slope_s_per_GeV_per_Mpc",
        "observed_slope": 0.001 if leaked else "BLINDED",
        "p_value": 0.05 if leaked else "BLINDED",
        "z_score": 1.5 if leaked else "BLINDED",
        "detection_claimed": True if leaked else "BLINDED",
        "null_retained": False if leaked else "BLINDED",
        "n_permutations": 500,
        "seed": 42,
        "unblind_requires": ["explicit_human_approval"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _write_qc_report(path: pathlib.Path):
    data = {
        "n_events": 40,
        "n_sources": 6,
        "n_dropped_by_adapter": 0,
        "n_warnings": 0,
        "stopping_rules_triggered": [],
        "ingest_complete": True,
        "proceed_to_analysis": True,
        "source_file": "data/real/test.csv",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _write_ingest_manifest(path: pathlib.Path):
    data = {
        "status": "OK",
        "metadata": {
            "n_events": 40,
            "n_dropped": 0,
            "n_sources": 6,
            "n_sources_with_redshift": 6,
        },
        "dropped_events": {"reasons": []},
        "warnings": [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _write_first_ingest_manifest(path: pathlib.Path, status="COMPLETE"):
    data = {
        "status": status,
        "candidate": "data/real/test.csv",
        "check_report": {
            "schema_valid": True,
            "recommendation": "ACCEPT_FOR_BLINDED_RUN",
            "hard_failures": [],
            "warnings": [],
        },
        "blinded_result": {"run_ok": True},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# TestMilestoneReport — blinding_status helper
# ---------------------------------------------------------------------------

class TestBlindingStatusHelper:
    def test_blinded_keys_confirmed(self, tmp_path):
        blinded = {
            "blinded": True,
            "unblind_permitted": False,
            "observed_slope": "BLINDED",
            "p_value": "BLINDED",
            "z_score": "BLINDED",
            "detection_claimed": "BLINDED",
            "null_retained": "BLINDED",
        }
        result = _blinding_status(blinded)
        assert result["signal_keys_confirmed_blinded"] is True
        assert result["leaked_keys"] == []

    def test_leaked_keys_detected(self):
        blinded = {
            "blinded": True,
            "unblind_permitted": False,
            "observed_slope": 0.001,  # leaked
            "p_value": "BLINDED",
            "z_score": "BLINDED",
            "detection_claimed": "BLINDED",
            "null_retained": "BLINDED",
        }
        result = _blinding_status(blinded)
        assert result["signal_keys_confirmed_blinded"] is False
        assert "observed_slope" in result["leaked_keys"]

    def test_none_input_returns_not_available(self):
        result = _blinding_status(None)
        assert result["available"] is False
        assert result["blinding_enforced"] is False


# ---------------------------------------------------------------------------
# TestMilestoneReport — QC and ingest helpers
# ---------------------------------------------------------------------------

class TestQcAndIngestHelpers:
    def test_qc_gate_summary_none(self):
        result = _qc_gate_summary(None)
        assert result["available"] is False

    def test_qc_gate_summary_populates(self):
        qc = {"n_events": 50, "n_sources": 7, "n_dropped_by_adapter": 0,
              "n_warnings": 0, "stopping_rules_triggered": [], "ingest_complete": True,
              "proceed_to_analysis": True, "source_file": "data/real/test.csv"}
        result = _qc_gate_summary(qc)
        assert result["available"] is True
        assert result["n_events"] == 50

    def test_ingest_summary_none(self):
        result = _ingest_summary(None)
        assert result["available"] is False

    def test_ingest_summary_populates(self):
        ingest = {"status": "OK", "metadata": {"n_events": 40, "n_dropped": 0,
                  "n_sources": 6, "n_sources_with_redshift": 6},
                  "dropped_events": {"reasons": []}, "warnings": []}
        result = _ingest_summary(ingest)
        assert result["available"] is True
        assert result["n_events"] == 40


# ---------------------------------------------------------------------------
# TestGenerateMilestoneReport
# ---------------------------------------------------------------------------

class TestGenerateMilestoneReport:
    def test_output_file_written(self, tmp_path):
        bs = tmp_path / "blinded_summary.json"
        qc = tmp_path / "qc.json"
        im = tmp_path / "ingest.json"
        mfst = tmp_path / "manifest.json"
        out = tmp_path / "milestone.json"
        _write_blinded_summary(bs)
        _write_qc_report(qc)
        _write_ingest_manifest(im)
        _write_first_ingest_manifest(mfst)
        generate_milestone_report(
            manifest_path=str(mfst),
            qc_report_path=str(qc),
            blinded_summary_path=str(bs),
            ingest_manifest_path=str(im),
            output_path=str(out),
        )
        assert out.exists()

    def test_unblinding_status_field(self, tmp_path):
        bs = tmp_path / "bs.json"; qc = tmp_path / "qc.json"
        im = tmp_path / "im.json"; mfst = tmp_path / "mfst.json"
        out = tmp_path / "out.json"
        _write_blinded_summary(bs); _write_qc_report(qc)
        _write_ingest_manifest(im); _write_first_ingest_manifest(mfst)
        r = generate_milestone_report(str(mfst), str(qc), str(bs), str(im), str(out))
        assert r["unblinding_status"] == "UNBLINDING NOT PERFORMED"

    def test_scientific_claim_field(self, tmp_path):
        bs = tmp_path / "bs.json"; qc = tmp_path / "qc.json"
        im = tmp_path / "im.json"; mfst = tmp_path / "mfst.json"
        out = tmp_path / "out.json"
        _write_blinded_summary(bs); _write_qc_report(qc)
        _write_ingest_manifest(im); _write_first_ingest_manifest(mfst)
        r = generate_milestone_report(str(mfst), str(qc), str(bs), str(im), str(out))
        assert "NO SCIENTIFIC CLAIM" in r["scientific_claim_status"]

    def test_blinding_confirmed_in_report(self, tmp_path):
        bs = tmp_path / "bs.json"; qc = tmp_path / "qc.json"
        im = tmp_path / "im.json"; mfst = tmp_path / "mfst.json"
        out = tmp_path / "out.json"
        _write_blinded_summary(bs); _write_qc_report(qc)
        _write_ingest_manifest(im); _write_first_ingest_manifest(mfst)
        r = generate_milestone_report(str(mfst), str(qc), str(bs), str(im), str(out))
        assert r["blinding"]["signal_keys_confirmed_blinded"] is True
        assert r["blinding"]["unblind_permitted"] is False

    def test_report_contains_required_keys(self, tmp_path):
        bs = tmp_path / "bs.json"; qc = tmp_path / "qc.json"
        im = tmp_path / "im.json"; mfst = tmp_path / "mfst.json"
        out = tmp_path / "out.json"
        _write_blinded_summary(bs); _write_qc_report(qc)
        _write_ingest_manifest(im); _write_first_ingest_manifest(mfst)
        r = generate_milestone_report(str(mfst), str(qc), str(bs), str(im), str(out))
        for k in ("milestone", "unblinding_status", "run_timestamp", "commit_hash",
                  "pipeline_status", "dataset", "ingestion", "qc_gates", "blinding",
                  "artifact_paths"):
            assert k in r, f"Missing key: {k}"

    def test_leaked_keys_detected_in_report(self, tmp_path):
        bs = tmp_path / "bs.json"; qc = tmp_path / "qc.json"
        im = tmp_path / "im.json"; mfst = tmp_path / "mfst.json"
        out = tmp_path / "out.json"
        _write_blinded_summary(bs, leaked=True)  # observed_slope = 0.001
        _write_qc_report(qc); _write_ingest_manifest(im)
        _write_first_ingest_manifest(mfst)
        r = generate_milestone_report(str(mfst), str(qc), str(bs), str(im), str(out))
        assert r["blinding"]["signal_keys_confirmed_blinded"] is False
        assert len(r["blinding"]["leaked_keys"]) > 0

    def test_missing_inputs_handled_gracefully(self, tmp_path):
        out = tmp_path / "out.json"
        r = generate_milestone_report(
            manifest_path=str(tmp_path / "missing.json"),
            qc_report_path=str(tmp_path / "missing_qc.json"),
            blinded_summary_path=str(tmp_path / "missing_bs.json"),
            ingest_manifest_path=str(tmp_path / "missing_im.json"),
            output_path=str(out),
        )
        assert r["pipeline_status"] == "UNKNOWN"
        assert out.exists()


# ---------------------------------------------------------------------------
# TestFirstBlindedRealFermiRun — waiting/blocked states
# ---------------------------------------------------------------------------

class TestFirstBlindedRealFermiRunWaiting:
    def test_empty_dir_waiting(self, tmp_path):
        d = tmp_path / "real"; d.mkdir()
        mfst = tmp_path / "manifest.json"
        ms = tmp_path / "milestone.json"
        result = first_blinded_real_fermi_run(
            data_dir=str(d),
            manifest_path=str(mfst),
            milestone_report_path=str(ms),
        )
        assert result["overall_status"] == "WAITING"

    def test_only_synthetic_waiting(self, tmp_path):
        d = tmp_path / "real"; d.mkdir()
        _write_csv(d / "synthetic_rehearsal.csv")
        mfst = tmp_path / "manifest.json"
        ms = tmp_path / "milestone.json"
        result = first_blinded_real_fermi_run(
            data_dir=str(d),
            manifest_path=str(mfst),
            milestone_report_path=str(ms),
        )
        assert result["overall_status"] == "WAITING"

    def test_too_few_events_blocked(self, tmp_path):
        d = tmp_path / "real"; d.mkdir()
        _write_csv(d / "grb_data.csv", n=5, n_grb=2)
        mfst = tmp_path / "manifest.json"
        ms = tmp_path / "milestone.json"
        result = first_blinded_real_fermi_run(
            data_dir=str(d),
            manifest_path=str(mfst),
            milestone_report_path=str(ms),
        )
        assert result["overall_status"] == "BLOCKED"


class TestFirstBlindedRealFermiRunComplete:
    def test_valid_file_complete(self, tmp_path):
        if not _REG_PATH.exists():
            pytest.skip("Registration JSON not present")
        d = tmp_path / "real"; d.mkdir()
        _write_csv(d / "grb_real.csv", n=40, n_grb=6)
        mfst = tmp_path / "manifest.json"
        ms = tmp_path / "milestone.json"
        result = first_blinded_real_fermi_run(
            data_dir=str(d),
            registration_path=str(_REG_PATH),
            manifest_path=str(mfst),
            milestone_report_path=str(ms),
            n_permutations=50,
            seed=0,
        )
        assert result["overall_status"] == "COMPLETE"

    def test_milestone_report_written(self, tmp_path):
        if not _REG_PATH.exists():
            pytest.skip("Registration JSON not present")
        d = tmp_path / "real"; d.mkdir()
        _write_csv(d / "grb_real.csv", n=40, n_grb=6)
        mfst = tmp_path / "manifest.json"
        ms = tmp_path / "milestone.json"
        first_blinded_real_fermi_run(
            data_dir=str(d),
            registration_path=str(_REG_PATH),
            manifest_path=str(mfst),
            milestone_report_path=str(ms),
            n_permutations=50,
            seed=0,
        )
        assert ms.exists()
        data = json.loads(ms.read_text())
        assert data["unblinding_status"] == "UNBLINDING NOT PERFORMED"

    def test_complete_blinding_confirmed(self, tmp_path):
        if not _REG_PATH.exists():
            pytest.skip("Registration JSON not present")
        d = tmp_path / "real"; d.mkdir()
        _write_csv(d / "grb_real.csv", n=40, n_grb=6)
        mfst = tmp_path / "manifest.json"
        ms = tmp_path / "milestone.json"
        result = first_blinded_real_fermi_run(
            data_dir=str(d),
            registration_path=str(_REG_PATH),
            manifest_path=str(mfst),
            milestone_report_path=str(ms),
            n_permutations=50,
            seed=0,
        )
        blinding = result["milestone_report"]["blinding"]
        assert blinding["blinding_enforced"] is True
        assert blinding["signal_keys_confirmed_blinded"] is True
        assert blinding["unblind_permitted"] is False

    def test_no_protected_values_in_milestone_json(self, tmp_path):
        if not _REG_PATH.exists():
            pytest.skip("Registration JSON not present")
        import re
        d = tmp_path / "real"; d.mkdir()
        _write_csv(d / "grb_real.csv", n=40, n_grb=6)
        mfst = tmp_path / "manifest.json"
        ms = tmp_path / "milestone.json"
        first_blinded_real_fermi_run(
            data_dir=str(d),
            registration_path=str(_REG_PATH),
            manifest_path=str(mfst),
            milestone_report_path=str(ms),
            n_permutations=50,
            seed=0,
        )
        text = ms.read_text()
        assert not re.search(r'"p_value"\s*:\s*[0-9]', text)
        assert not re.search(r'"z_score"\s*:\s*[0-9\-]', text)
        assert not re.search(r'"observed_slope"\s*:\s*[0-9\-]', text)
