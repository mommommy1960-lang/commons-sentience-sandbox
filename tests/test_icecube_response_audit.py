import json
import math
from pathlib import Path

from reality_audit.data_analysis.icecube_response_audit import (
    audit_legacy_three_year_csv,
    exact_binomial_lower_tail,
    legacy_hemisphere_sensitivity,
    response_model_readiness,
    south_pole_zenith_to_declination_deg,
    summarize_official_data_json,
)

from scripts.run_icecube_official_mc_response import _git_blob_sha1, _holm_adjust


def test_current_legacy_37_event_csv_is_quarantined_by_provenance_audit():
    result = audit_legacy_three_year_csv("data/real/icecube_hese_events.csv")
    assert not result.trusted_for_scientific_inference
    assert result.status == "UNTRUSTED_LEGACY_INPUT"
    # Multiple published track-event anchors disagree with this file.
    assert len(result.mismatches) >= 5


def test_south_pole_zenith_declination_conversion():
    assert math.isclose(south_pole_zenith_to_declination_deg(0.0), -90.0)
    assert math.isclose(south_pole_zenith_to_declination_deg(math.pi / 2), 0.0)
    assert math.isclose(south_pole_zenith_to_declination_deg(math.pi), 90.0)


def test_official_json_summary_is_observed_sample_not_exposure(tmp_path: Path):
    fixture = {
        "recoDepositedEnergy": [100000.0, 120000.0, 80000.0, 20000.0],
        "recoZenith": [0.2, 2.0, 2.5, 2.7],
    }
    path = tmp_path / "HESE_data.json"
    path.write_text(json.dumps(fixture))
    summary = summarize_official_data_json(str(path), emin_gev=60000.0)
    assert summary["event_count"] == 3
    assert summary["north"] == 2
    assert summary["south"] == 1
    assert summary["interpretation"] == "observed_sample_only_not_detector_acceptance"


def test_legacy_imbalance_is_sensitive_to_acceptance_assumption():
    rows = legacy_hemisphere_sensitivity(10, 37)
    by_p = {row["assumed_north_acceptance"]: row["p_north_le_k"] for row in rows}
    assert by_p[0.50] < 0.01
    assert by_p[0.40] > 0.05
    assert by_p[0.35] > 0.19


def test_exact_binomial_known_value():
    assert math.isclose(
        exact_binomial_lower_tail(10, 37, 0.5),
        0.003816039301455021,
        rel_tol=1e-12,
    )


def test_response_model_refuses_missing_mc_files(tmp_path: Path):
    readiness = response_model_readiness(str(tmp_path))
    assert not readiness["ready"]
    assert readiness["quality_tier"] == "NO_RESPONSE_MODEL"
    assert len(readiness["missing_files"]) == 3


def test_git_blob_sha_matches_git_object_convention(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_bytes(b"hello\n")
    assert _git_blob_sha1(path) == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_holm_adjustment_is_monotone_and_family_wise():
    adjusted = _holm_adjust({"a": 0.01, "b": 0.04, "c": 0.2})
    assert adjusted == {"a": 0.03, "b": 0.08, "c": 0.2}
