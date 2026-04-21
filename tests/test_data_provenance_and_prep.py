"""
tests/test_data_provenance_and_prep.py
=====================================
Tests for the data provenance / authenticity layer and the Fermi-LAT data
preparation module.

Test categories
---------------
1. Synthetic fixture is rejected as AUTHENTIC_PUBLIC
2. Provenance sidecar metadata is required for authentic tier
3. Valid sidecar + non-synthetic hash → AUTHENTIC_PUBLIC tier
4. Redshift enrichment — success path
5. Redshift enrichment — insufficient coverage failure path
6. Malformed / unexpected-schema public input
7. Duplicate handling in event data
8. Blinded fields remain blinded after prep + ingest (integration guard)
"""

import json
import pathlib
import shutil
import tempfile
from typing import Any, Dict

import pandas as pd
import pytest

from reality_audit.data_analysis.data_provenance import (
    AuthenticityTier,
    assess_authenticity,
    write_provenance_sidecar,
    _sha256_prefix,
    _is_known_synthetic,
)
from reality_audit.data_analysis.fermi_lat_data_prep import (
    PrepReport,
    prepare_fermi_lat_real_data,
    describe_required_formats,
    MIN_REDSHIFT_SOURCES,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_event_csv(tmp_dir: pathlib.Path, name: str, n_grbs: int = 10) -> pathlib.Path:
    """Write a minimal valid event CSV with n_grbs distinct GRB sources."""
    rows = []
    for i in range(n_grbs):
        grb = f"GRB{10000 + i:05d}A"
        for ev in range(5):
            rows.append(
                {
                    "grb_name": grb,
                    "arrival_time": 100.0 + i * 50 + ev * 0.1,
                    "energy_gev": 0.1 + ev * 0.01,
                }
            )
    path = tmp_dir / name
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _make_metadata_csv(
    tmp_dir: pathlib.Path, name: str = "meta.csv", n_grbs: int = 10, skip_last: int = 0
) -> pathlib.Path:
    rows = [
        {"grb_name": f"GRB{10000 + i:05d}A", "redshift": 0.5 + i * 0.1, "t90_s": 10.0}
        for i in range(n_grbs - skip_last)
    ]
    path = tmp_dir / name
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _write_valid_sidecar(csv_path: pathlib.Path) -> pathlib.Path:
    sidecar_path = write_provenance_sidecar(
        csv_path=str(csv_path),
        source_description="Fermi-LAT GRB event data from FSSC public archive",
        data_origin="Fermi FSSC / HEASARC",
        acquisition_date="2026-04-20",
        source_url="https://fermi.gsfc.nasa.gov/ssc/data/",
        file_format="CSV derived from FITS event file",
        grb_list=["GRB090902B"],
    )
    return pathlib.Path(sidecar_path)


# ---------------------------------------------------------------------------
# Category 1: Synthetic fixture detection
# ---------------------------------------------------------------------------


class TestSyntheticFixtureRejection:
    """Known synthetic fixtures must not be classified as AUTHENTIC_PUBLIC."""

    def test_synthetic_csv_rejected_by_name(self, tmp_path):
        p = tmp_path / "synthetic_fermi_lat_grb_events.csv"
        p.write_text("grb_name,arrival_time,energy_gev\nGRB001,1.0,0.1\n")
        report = assess_authenticity(str(p))
        assert report.authenticity_tier == AuthenticityTier.REHEARSAL

    def test_synthetic_name_marker_detected(self, tmp_path):
        p = tmp_path / "my_synthetic_dataset.csv"
        p.write_text("grb_name,arrival_time,energy_gev\nGRB001,1.0,0.1\n")
        assert _is_known_synthetic(p)

    def test_known_hash_match_yields_rehearsal(self, tmp_path):
        """Copy actual synthetic fixture; hash check must return REHEARSAL."""
        src = pathlib.Path(
            "data/real/synthetic_fermi_lat_grb_events.csv"
        )
        if not src.exists():
            pytest.skip("Synthetic fixture not present in data/real/")
        dest = tmp_path / "disguised_real.csv"
        shutil.copy(src, dest)
        report = assess_authenticity(str(dest))
        assert report.authenticity_tier in (
            AuthenticityTier.REHEARSAL, AuthenticityTier.UNVERIFIED
        ), (
            "A file with known-synthetic SHA-256 must not reach AUTHENTIC_PUBLIC"
        )
        assert not report.eligible_for_scientific_run

    def test_real_test_dataset_not_eligible(self):
        """real_test_dataset.csv is known synthetic; must not be eligible."""
        candidate = pathlib.Path("data/real/real_test_dataset.csv")
        if not candidate.exists():
            pytest.skip("real_test_dataset.csv not present")
        report = assess_authenticity(str(candidate))
        assert not report.eligible_for_scientific_run

    def test_synthetic_fixture_failure_reason_recorded(self, tmp_path):
        p = tmp_path / "synthetic_data.csv"
        p.write_text("grb_name,arrival_time,energy_gev\nGRB001,1.0,0.1\n")
        report = assess_authenticity(str(p))
        assert any("SYNTHETIC" in r.upper() for r in report.failure_reasons)


# ---------------------------------------------------------------------------
# Category 2: Provenance sidecar is required
# ---------------------------------------------------------------------------


class TestProvenanceSidecarRequired:
    """Without a provenance sidecar a file cannot be AUTHENTIC_PUBLIC."""

    def test_no_sidecar_yields_unverified(self, tmp_path):
        p = _make_event_csv(tmp_path, "pubdata.csv")
        report = assess_authenticity(str(p))
        assert report.authenticity_tier == AuthenticityTier.UNVERIFIED

    def test_no_sidecar_not_eligible(self, tmp_path):
        p = _make_event_csv(tmp_path, "pubdata.csv")
        report = assess_authenticity(str(p))
        assert not report.eligible_for_scientific_run

    def test_no_sidecar_failure_reason_recorded(self, tmp_path):
        p = _make_event_csv(tmp_path, "pubdata.csv")
        report = assess_authenticity(str(p))
        assert any("PROVENANCE" in r.upper() for r in report.failure_reasons)

    def test_empty_sidecar_missing_required_fields_yields_unverified(self, tmp_path):
        p = _make_event_csv(tmp_path, "pubdata.csv")
        sidecar = p.with_suffix(".provenance.json")
        sidecar.write_text(json.dumps({"notes": "incomplete"}))
        report = assess_authenticity(str(p))
        assert report.authenticity_tier == AuthenticityTier.UNVERIFIED
        assert len(report.provenance_missing_fields) > 0

    def test_malformed_json_sidecar_yields_unverified(self, tmp_path):
        p = _make_event_csv(tmp_path, "pubdata.csv")
        sidecar = p.with_suffix(".provenance.json")
        sidecar.write_text("{bad json{{")
        report = assess_authenticity(str(p))
        assert report.authenticity_tier == AuthenticityTier.UNVERIFIED

    def test_partial_sidecar_records_which_fields_are_missing(self, tmp_path):
        p = _make_event_csv(tmp_path, "pubdata.csv")
        sidecar = p.with_suffix(".provenance.json")
        sidecar.write_text(json.dumps({"source_description": "x"}))
        report = assess_authenticity(str(p))
        # data_origin and acquisition_date should be flagged missing
        assert any(
            "data_origin" in f or "acquisition_date" in f
            for f in report.provenance_missing_fields
        )


# ---------------------------------------------------------------------------
# Category 3: AUTHENTIC_PUBLIC classification
# ---------------------------------------------------------------------------


class TestAuthenticPublicMode:
    """A file with valid sidecar and non-synthetic content → AUTHENTIC_PUBLIC."""

    def test_valid_sidecar_non_synthetic_yields_authentic(self, tmp_path):
        p = _make_event_csv(tmp_path, "lat_grb_events.csv")
        _write_valid_sidecar(p)
        report = assess_authenticity(str(p))
        assert report.authenticity_tier == AuthenticityTier.AUTHENTIC_PUBLIC

    def test_eligible_for_scientific_run_true(self, tmp_path):
        p = _make_event_csv(tmp_path, "lat_grb_events.csv")
        _write_valid_sidecar(p)
        report = assess_authenticity(str(p))
        assert report.eligible_for_scientific_run is True

    def test_provenance_record_fields_populated(self, tmp_path):
        p = _make_event_csv(tmp_path, "lat_grb_events.csv")
        _write_valid_sidecar(p)
        report = assess_authenticity(str(p))
        assert report.provenance is not None
        assert report.provenance.source_description
        assert report.provenance.acquisition_date
        assert report.provenance.data_origin

    def test_to_dict_serialisable(self, tmp_path):
        p = _make_event_csv(tmp_path, "lat_grb_events.csv")
        _write_valid_sidecar(p)
        report = assess_authenticity(str(p))
        d = report.to_dict()
        # Should be JSON-serialisable
        json.dumps(d)

    def test_missing_file_yields_missing_tier(self, tmp_path):
        report = assess_authenticity(str(tmp_path / "nonexistent.csv"))
        assert report.authenticity_tier == AuthenticityTier.MISSING


# ---------------------------------------------------------------------------
# Category 4: Redshift enrichment — success path
# ---------------------------------------------------------------------------


class TestRedshiftEnrichmentSuccess:
    def test_full_join_produces_correct_output_row_count(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=10)
        meta = _make_metadata_csv(tmp_path, n_grbs=10)
        out = tmp_path / "prepared.csv"
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        assert report.status == "OK"
        assert report.n_events_output == report.n_events_raw
        assert report.n_events_dropped == 0

    def test_output_csv_written(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=10)
        meta = _make_metadata_csv(tmp_path, n_grbs=10)
        out = tmp_path / "prepared.csv"
        prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        assert out.exists()
        df = pd.read_csv(out)
        assert "redshift" in df.columns
        assert df["redshift"].notna().all()

    def test_sources_with_redshift_count_correct(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=10)
        meta = _make_metadata_csv(tmp_path, n_grbs=10)
        out = tmp_path / "prepared.csv"
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        assert report.n_sources_with_redshift == 10

    def test_energy_mev_column_converted_to_gev(self, tmp_path):
        """Event files with energy in MeV should be converted to GeV."""
        rows = [
            {"grb_name": f"GRB{10000 + i:05d}A", "arrival_time": 100.0 + i, "energy_mev": 1000.0}
            for i in range(10)
        ]
        df = pd.DataFrame(rows)
        events = tmp_path / "events_mev.csv"
        df.to_csv(events, index=False)
        meta = _make_metadata_csv(tmp_path, n_grbs=10)
        out = tmp_path / "prepared.csv"
        prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        out_df = pd.read_csv(out)
        assert "energy_gev" in out_df.columns
        assert abs(out_df["energy_gev"].iloc[0] - 1.0) < 1e-9

    def test_optional_metadata_columns_passed_through(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=6)
        meta_rows = [
            {"grb_name": f"GRB{10000 + i:05d}A", "redshift": 0.5 + i * 0.1, "t90_s": 20.0}
            for i in range(6)
        ]
        meta = tmp_path / "meta.csv"
        pd.DataFrame(meta_rows).to_csv(meta, index=False)
        out = tmp_path / "prepared.csv"
        prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        out_df = pd.read_csv(out)
        assert "t90_s" in out_df.columns

    def test_overwrite_false_raises_on_existing_file(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=6)
        meta = _make_metadata_csv(tmp_path, n_grbs=6)
        out = tmp_path / "prepared.csv"
        prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        with pytest.raises(FileExistsError):
            prepare_fermi_lat_real_data(str(events), str(meta), str(out), overwrite=False)

    def test_overwrite_true_replaces_file(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=6)
        meta = _make_metadata_csv(tmp_path, n_grbs=6)
        out = tmp_path / "prepared.csv"
        prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out), overwrite=True)
        assert report.status == "OK"


# ---------------------------------------------------------------------------
# Category 5: Insufficient redshift coverage failure path
# ---------------------------------------------------------------------------


class TestInsufficientRedshiftCoverage:
    def test_partially_missing_redshift_drops_events(self, tmp_path):
        n_grbs = 10
        skip = 7  # only 3 sources will have redshift
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=n_grbs)
        meta = _make_metadata_csv(tmp_path, n_grbs=n_grbs, skip_last=skip)
        out = tmp_path / "prepared.csv"
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        assert report.status == "INSUFFICIENT_REDSHIFT_COVERAGE"
        assert report.n_sources_without_redshift == skip
        assert len(report.missing_redshift_grbs) == skip
        assert report.n_events_dropped > 0

    def test_zero_sources_with_redshift_returns_insufficient(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=5)
        # metadata CSV has no grb_name matches
        meta_rows = [{"grb_name": "GRB_UNKNOWN", "redshift": 0.5}]
        meta = tmp_path / "meta.csv"
        pd.DataFrame(meta_rows).to_csv(meta, index=False)
        out = tmp_path / "prepared.csv"
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        assert report.n_sources_with_redshift == 0
        assert report.status == "INSUFFICIENT_REDSHIFT_COVERAGE"

    def test_missing_redshift_grbs_list_populated(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=8)
        meta = _make_metadata_csv(tmp_path, n_grbs=8, skip_last=4)
        out = tmp_path / "prepared.csv"
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        assert len(report.missing_redshift_grbs) == 4

    def test_redshift_never_fabricated(self, tmp_path):
        """Events with no redshift match must be dropped, never filled."""
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=5)
        meta = _make_metadata_csv(tmp_path, n_grbs=3)  # 2 GRBs got no match
        out = tmp_path / "prepared.csv"
        prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        if out.exists():
            df = pd.read_csv(out)
            assert df["redshift"].notna().all(), (
                "Output file must not contain NaN redshifts — "
                "missing values must be dropped, never fabricated"
            )

    def test_warning_emitted_for_missing_redshifts(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=8)
        meta = _make_metadata_csv(tmp_path, n_grbs=8, skip_last=3)
        out = tmp_path / "prepared.csv"
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        assert any("REDSHIFT_MISSING" in w for w in report.warnings)


# ---------------------------------------------------------------------------
# Category 6: Malformed public input
# ---------------------------------------------------------------------------


class TestMalformedInput:
    def test_event_csv_missing_grb_name_column(self, tmp_path):
        p = tmp_path / "bad_events.csv"
        pd.DataFrame({"arrival_time": [1.0], "energy_gev": [0.1]}).to_csv(p, index=False)
        meta = _make_metadata_csv(tmp_path, n_grbs=5)
        out = tmp_path / "out.csv"
        report = prepare_fermi_lat_real_data(str(p), str(meta), str(out))
        assert report.status == "SCHEMA_ERROR"

    def test_event_csv_missing_arrival_time_column(self, tmp_path):
        p = tmp_path / "bad_events.csv"
        pd.DataFrame({"grb_name": ["GRB001"], "energy_gev": [0.1]}).to_csv(p, index=False)
        meta = _make_metadata_csv(tmp_path, n_grbs=5)
        out = tmp_path / "out.csv"
        report = prepare_fermi_lat_real_data(str(p), str(meta), str(out))
        assert report.status == "SCHEMA_ERROR"

    def test_metadata_csv_missing_redshift_column(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=5)
        meta = tmp_path / "meta.csv"
        pd.DataFrame({"grb_name": ["GRB001"], "t90_s": [10.0]}).to_csv(meta, index=False)
        out = tmp_path / "out.csv"
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        assert report.status == "SCHEMA_ERROR"

    def test_nonexistent_event_csv(self, tmp_path):
        meta = _make_metadata_csv(tmp_path, n_grbs=5)
        out = tmp_path / "out.csv"
        report = prepare_fermi_lat_real_data(
            str(tmp_path / "does_not_exist.csv"), str(meta), str(out)
        )
        assert report.status == "SCHEMA_ERROR"

    def test_nonexistent_metadata_csv(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=5)
        out = tmp_path / "out.csv"
        report = prepare_fermi_lat_real_data(
            str(events), str(tmp_path / "no_meta.csv"), str(out)
        )
        assert report.status == "SCHEMA_ERROR"


# ---------------------------------------------------------------------------
# Category 7: Duplicate handling
# ---------------------------------------------------------------------------


class TestDuplicateHandling:
    def test_exact_duplicate_events_preserved_for_pipeline(self, tmp_path):
        """
        The prep module does NOT deduplicate events — that is the job of the
        QC gate.  Duplicates must be preserved in the output so that the QC
        gate can enforce the duplicate fraction threshold.
        """
        rows = [
            {"grb_name": "GRB10000A", "arrival_time": 100.0, "energy_gev": 0.1},
            {"grb_name": "GRB10000A", "arrival_time": 100.0, "energy_gev": 0.1},
        ]
        events = tmp_path / "dup_events.csv"
        pd.DataFrame(rows).to_csv(events, index=False)
        meta_rows = [{"grb_name": "GRB10000A", "redshift": 0.5}]
        meta = tmp_path / "meta.csv"
        pd.DataFrame(meta_rows).to_csv(meta, index=False)
        out = tmp_path / "prepared.csv"
        prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        df = pd.read_csv(out)
        assert len(df) == 2, "Duplicate rows must be preserved for QC gate inspection"

    def test_duplicate_grb_in_metadata_does_not_duplicate_events(self, tmp_path):
        """Duplicate grb_name in metadata CSV must be de-duplicated before join."""
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=5)
        meta_rows = (
            [{"grb_name": f"GRB{10000 + i:05d}A", "redshift": 0.5 + i * 0.1} for i in range(5)]
            + [{"grb_name": "GRB10000A", "redshift": 0.9}]  # duplicate
        )
        meta = tmp_path / "meta.csv"
        pd.DataFrame(meta_rows).to_csv(meta, index=False)
        out = tmp_path / "prepared.csv"
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        df = pd.read_csv(out)
        # Row count should equal 5 GRBs × 5 events each = 25
        assert len(df) == 25


# ---------------------------------------------------------------------------
# Category 8: Blinded fields remain blinded (integration guard)
# ---------------------------------------------------------------------------


class TestBlindedFieldsProtected:
    """
    After data prep, the protected signal keys must never appear in the
    prep report or in the columns of the output CSV.
    """

    _PROTECTED_KEYS = {
        "observed_slope",
        "p_value",
        "z_score",
        "detection_claimed",
        "null_retained",
    }

    def test_prep_report_contains_no_signal_keys(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=6)
        meta = _make_metadata_csv(tmp_path, n_grbs=6)
        out = tmp_path / "prepared.csv"
        report = prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        report_dict = report.to_dict()
        for key in self._PROTECTED_KEYS:
            assert key not in report_dict, (
                f"Protected signal key '{key}' must not appear in PrepReport"
            )

    def test_output_csv_contains_no_signal_keys(self, tmp_path):
        events = _make_event_csv(tmp_path, "events.csv", n_grbs=6)
        meta = _make_metadata_csv(tmp_path, n_grbs=6)
        out = tmp_path / "prepared.csv"
        prepare_fermi_lat_real_data(str(events), str(meta), str(out))
        df = pd.read_csv(out)
        for key in self._PROTECTED_KEYS:
            assert key not in df.columns, (
                f"Protected signal key '{key}' must not appear in output CSV columns"
            )

    def test_authenticity_report_contains_no_signal_keys(self, tmp_path):
        p = _make_event_csv(tmp_path, "lat_grb_events.csv")
        _write_valid_sidecar(p)
        report = assess_authenticity(str(p))
        report_dict = report.to_dict()
        for key in self._PROTECTED_KEYS:
            assert key not in report_dict, (
                f"Protected signal key '{key}' must not appear in AuthenticityReport"
            )


# ---------------------------------------------------------------------------
# Utility: describe_required_formats
# ---------------------------------------------------------------------------


class TestDescribeRequiredFormats:
    def test_returns_dict_with_expected_keys(self):
        fmt = describe_required_formats()
        assert "event_csv_required_columns" in fmt
        assert "metadata_csv_required_columns" in fmt
        assert "notes" in fmt

    def test_notes_mention_no_fabrication(self):
        fmt = describe_required_formats()
        assert "NEVER" in fmt["notes"] or "never" in fmt["notes"].lower()
