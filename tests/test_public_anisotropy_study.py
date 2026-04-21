"""
test_public_anisotropy_study.py
================================
Tests for the Stage 7 public-data anisotropy analysis track.

All tests use small synthetic datasets and are fully deterministic when seeded.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.public_event_catalogs import (
    load_public_catalog,
    describe_catalog_coverage,
    _normalize_records,
    _read_csv_or_tsv,
    _real_data_dir,
    SCHEMA_FIELDS,
)
from reality_audit.data_analysis.public_anisotropy_study import (
    run_public_anisotropy_study,
    scan_trial_axes,
    write_public_study_artifacts,
    _build_48_axes,
)
from reality_audit.data_analysis.public_anisotropy_benchmark import run_benchmark


# ===========================================================================
# Fixtures
# ===========================================================================

def _make_isotropic_events(n=50, seed=7):
    """Generate small synthetic isotropic events directly (no file I/O)."""
    import random, math
    rng = random.Random(seed)
    events = []
    for i in range(n):
        cos_dec = rng.uniform(-1.0, 1.0)
        dec = math.degrees(math.asin(cos_dec))
        ra  = rng.uniform(0.0, 360.0)
        events.append({
            "event_id":    f"tst_{i:04d}",
            "energy":      math.exp(rng.uniform(math.log(0.1), math.log(100.0))),
            "arrival_time": rng.uniform(58000.0, 59000.0),
            "ra":          ra,
            "dec":         dec,
            "instrument":  "TEST",
            "epoch":       "2019",
            "_b_proxy":    abs(dec),
            "_parse_warnings": [],
        })
    return events


def _make_preferred_axis_events(n=50, seed=7, strength=0.8):
    """Generate events pulled toward RA=45, Dec=30."""
    import random, math
    events = _make_isotropic_events(n=n, seed=seed)
    rng = random.Random(seed + 1000)
    for e in events:
        if rng.random() < strength:
            t = rng.uniform(0.0, 1.0)
            e["ra"]  = e["ra"]  * (1 - t) + 45.0 * t
            e["dec"] = e["dec"] * (1 - t) + 30.0 * t
            e["_b_proxy"] = abs(e["dec"])
    return events


# ===========================================================================
# Tests: public_event_catalogs.py
# ===========================================================================

class TestLoadSyntheticCatalog:
    def test_synthetic_isotropic_returns_list(self):
        events = load_public_catalog("synthetic_isotropic")
        assert isinstance(events, list)
        assert len(events) > 0

    def test_synthetic_isotropic_schema(self):
        events = load_public_catalog("synthetic_isotropic")
        first  = events[0]
        for field in SCHEMA_FIELDS:
            assert field in first, f"Missing field: {field}"

    def test_synthetic_isotropic_ra_range(self):
        events = load_public_catalog("synthetic_isotropic")
        ras = [e["ra"] for e in events if e.get("ra") is not None]
        assert all(0.0 <= r <= 360.0 for r in ras), "RA out of range"

    def test_synthetic_isotropic_dec_range(self):
        events = load_public_catalog("synthetic_isotropic")
        decs = [e["dec"] for e in events if e.get("dec") is not None]
        assert all(-90.0 <= d <= 90.0 for d in decs), "Dec out of range"

    def test_synthetic_preferred_axis_returns_list(self):
        events = load_public_catalog("synthetic_preferred_axis")
        assert len(events) > 0

    def test_synthetic_preferred_axis_schema(self):
        events = load_public_catalog("synthetic_preferred_axis")
        assert all(field in events[0] for field in SCHEMA_FIELDS)

    def test_normalize_records_alias_mapping(self):
        """Column aliases like 'ra_deg' should map to 'ra'."""
        raw = [{"ra_deg": "45.0", "dej2000": "-10.5",
                "trigger_mjd": "58500.0", "name": "GRB001",
                "fluence": "1e-7"}]
        normed = _normalize_records(raw, source_name="test")
        assert normed[0]["ra"] == pytest.approx(45.0)
        assert normed[0]["dec"] == pytest.approx(-10.5)
        assert normed[0]["arrival_time"] == pytest.approx(58500.0)
        assert normed[0]["event_id"] == "GRB001"
        assert normed[0]["energy"] == pytest.approx(1e-7)

    def test_normalize_records_fallback_event_id(self):
        raw = [{"ra": "10.0", "dec": "5.0"}]
        normed = _normalize_records(raw, source_name="mysource")
        assert normed[0]["event_id"].startswith("mysource_")

    def test_manual_ingest_from_csv(self, tmp_path):
        """Writing a CSV and loading it via load_public_catalog path argument."""
        csv_path = tmp_path / "test_catalog.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["event_id", "ra", "dec",
                                               "energy", "arrival_time",
                                               "instrument", "epoch"])
            w.writeheader()
            for i in range(10):
                import math, random
                rng = random.Random(i)
                cos_dec = rng.uniform(-1.0, 1.0)
                w.writerow({
                    "event_id": f"e{i:03d}",
                    "ra": rng.uniform(0, 360),
                    "dec": math.degrees(math.asin(cos_dec)),
                    "energy": rng.uniform(0.1, 100.0),
                    "arrival_time": rng.uniform(58000, 59000),
                    "instrument": "TEST",
                    "epoch": "2020",
                })
        events = load_public_catalog(str(csv_path))
        assert len(events) == 10
        assert all(e.get("ra") is not None for e in events)


class TestDescribeCatalogCoverage:
    def test_returns_required_keys(self):
        events = load_public_catalog("synthetic_isotropic")
        cov = describe_catalog_coverage(events)
        for key in ["event_count", "available_fields", "missingness",
                    "ra_dec_coverage", "time_span_mjd", "instrument_labels"]:
            assert key in cov

    def test_event_count_matches(self):
        events = load_public_catalog("synthetic_isotropic")
        cov = describe_catalog_coverage(events)
        assert cov["event_count"] == len(events)

    def test_empty_catalog(self):
        cov = describe_catalog_coverage([])
        assert cov["event_count"] == 0

    def test_missingness_zero_for_complete_data(self):
        events = load_public_catalog("synthetic_isotropic")
        cov = describe_catalog_coverage(events)
        # energy and arrival_time should be present for synthetic data
        assert cov["missingness"]["ra"] == 0.0
        assert cov["missingness"]["dec"] == 0.0


# ===========================================================================
# Tests: scan_trial_axes
# ===========================================================================

class TestScanTrialAxes:
    def test_axes_count_48(self):
        axes = _build_48_axes()
        assert len(axes) == 48

    def test_all_axes_unit_length(self):
        for ax in _build_48_axes():
            length = math.sqrt(sum(a ** 2 for a in ax))
            assert abs(length - 1.0) < 1e-10

    def test_scan_returns_required_keys(self):
        events = _make_isotropic_events(n=50, seed=1)
        result = scan_trial_axes(events, num_axes=48, seed=0)
        for key in ["best_score", "best_axis_index", "best_axis_xyz",
                    "all_scores", "num_axes"]:
            assert key in result

    def test_scan_scores_nonnegative(self):
        events = _make_isotropic_events(n=50, seed=1)
        result = scan_trial_axes(events, num_axes=48)
        assert all(s >= 0.0 for s in result["all_scores"])

    def test_scan_best_score_matches_all_scores(self):
        events = _make_isotropic_events(n=50, seed=1)
        result = scan_trial_axes(events, num_axes=48)
        assert result["best_score"] == max(result["all_scores"])

    def test_scan_empty_events(self):
        result = scan_trial_axes([], num_axes=48)
        assert result["best_score"] == 0.0
        assert result["all_scores"] == []

    def test_preferred_axis_score_higher_than_isotropic(self):
        iso  = _make_isotropic_events(n=100, seed=42)
        pref = _make_preferred_axis_events(n=100, seed=42, strength=0.9)
        iso_score  = scan_trial_axes(iso,  num_axes=48)["best_score"]
        pref_score = scan_trial_axes(pref, num_axes=48)["best_score"]
        assert pref_score > iso_score, (
            f"Expected preferred-axis score {pref_score:.4f} > "
            f"isotropic score {iso_score:.4f}"
        )


# ===========================================================================
# Tests: run_public_anisotropy_study
# ===========================================================================

class TestRunPublicAnisotropyStudy:
    def test_returns_required_keys(self):
        events  = _make_isotropic_events(n=50, seed=0)
        results = run_public_anisotropy_study(events, null_repeats=10, seed=0)
        for key in ["event_count", "anisotropy", "preferred_axis", "axis_scan",
                    "energy_time_correlation", "cluster_score", "null_comparison",
                    "signal_evaluation", "run_metadata"]:
            assert key in results, f"Missing key: {key}"

    def test_event_count_matches_input(self):
        events  = _make_isotropic_events(n=60, seed=3)
        results = run_public_anisotropy_study(events, null_repeats=5, seed=3)
        assert results["event_count"] == 60

    def test_seeded_reproducibility(self):
        events = _make_isotropic_events(n=50, seed=5)
        r1 = run_public_anisotropy_study(events, null_repeats=10, seed=99)
        r2 = run_public_anisotropy_study(events, null_repeats=10, seed=99)
        assert r1["preferred_axis"]["score"] == r2["preferred_axis"]["score"]
        assert r1["null_comparison"]["axis_percentile"] == \
               r2["null_comparison"]["axis_percentile"]

    def test_different_seeds_may_differ(self):
        events = _make_isotropic_events(n=50, seed=5)
        r1 = run_public_anisotropy_study(events, null_repeats=20, seed=1)
        r2 = run_public_anisotropy_study(events, null_repeats=20, seed=9999)
        # Null percentiles depend on RNG; they should generally differ
        # (not guaranteed for every seed, but almost certain)
        # We just check they run without error:
        assert "signal_evaluation" in r1
        assert "signal_evaluation" in r2

    def test_preferred_axis_injection_raises_percentile(self):
        """Injected preferred-axis should score higher than isotropic baseline."""
        iso  = _make_isotropic_events(n=100, seed=42)
        pref = _make_preferred_axis_events(n=100, seed=42, strength=0.9)
        r_iso  = run_public_anisotropy_study(iso,  null_repeats=30, seed=0)
        r_pref = run_public_anisotropy_study(pref, null_repeats=30, seed=0)
        assert (r_pref["null_comparison"]["axis_percentile"] >
                r_iso["null_comparison"]["axis_percentile"]), (
            "Expected preferred-axis percentile to exceed isotropic baseline"
        )

    def test_signal_evaluation_keys(self):
        events  = _make_isotropic_events(n=30, seed=1)
        results = run_public_anisotropy_study(events, null_repeats=5, seed=1)
        sig = results["signal_evaluation"]
        assert "tier" in sig
        assert "max_percentile" in sig
        assert "per_metric_percentiles" in sig
        assert "caveat" in sig

    def test_tier_valid_values(self):
        from reality_audit.data_analysis.simulation_signature_analysis import (
            TIER_NONE, TIER_WEAK, TIER_MODERATE, TIER_STRONG
        )
        events  = _make_isotropic_events(n=30, seed=2)
        results = run_public_anisotropy_study(events, null_repeats=5, seed=2)
        assert results["signal_evaluation"]["tier"] in (
            TIER_NONE, TIER_WEAK, TIER_MODERATE, TIER_STRONG
        )

    def test_config_overrides_null_repeats(self):
        events  = _make_isotropic_events(n=30, seed=0)
        results = run_public_anisotropy_study(
            events, null_repeats=99, seed=0, config={"null_repeats": 7}
        )
        assert results["null_comparison"]["null_repeats"] == 7


# ===========================================================================
# Tests: write_public_study_artifacts
# ===========================================================================

class TestWritePublicStudyArtifacts:
    def test_artifacts_created(self, tmp_path):
        events  = _make_isotropic_events(n=40, seed=10)
        results = run_public_anisotropy_study(events, null_repeats=5, seed=10)
        manifest = write_public_study_artifacts(
            results=results, events=events, null_events_example=None,
            output_dir=str(tmp_path), name="test_run",
            plots_enabled=False, catalog_name="test_cat",
        )
        assert os.path.exists(manifest["json_summary"])
        assert os.path.exists(manifest["csv_summary"])
        assert os.path.exists(manifest["md_summary"])
        assert os.path.exists(manifest["manifest"])

    def test_json_has_required_structure(self, tmp_path):
        events  = _make_isotropic_events(n=40, seed=11)
        results = run_public_anisotropy_study(events, null_repeats=5, seed=11)
        manifest = write_public_study_artifacts(
            results=results, events=events, null_events_example=None,
            output_dir=str(tmp_path), name="test_run",
            plots_enabled=False, catalog_name="test_cat",
        )
        with open(manifest["json_summary"]) as f:
            payload = json.load(f)
        assert "results" in payload
        assert "coverage" in payload
        assert payload["catalog"] == "test_cat"

    def test_csv_row_written(self, tmp_path):
        events  = _make_isotropic_events(n=30, seed=12)
        results = run_public_anisotropy_study(events, null_repeats=5, seed=12)
        manifest = write_public_study_artifacts(
            results=results, events=events, null_events_example=None,
            output_dir=str(tmp_path), name="test_run",
            plots_enabled=False, catalog_name="test_cat",
        )
        with open(manifest["csv_summary"]) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert rows[0]["name"] == "test_run"

    def test_plots_skipped_gracefully(self, tmp_path):
        """Should not crash when plots_enabled=False."""
        events  = _make_isotropic_events(n=20, seed=13)
        results = run_public_anisotropy_study(events, null_repeats=3, seed=13)
        manifest = write_public_study_artifacts(
            results=results, events=events, null_events_example=None,
            output_dir=str(tmp_path), name="no_plots",
            plots_enabled=False,
        )
        assert "sky_plot" not in manifest


# ===========================================================================
# Tests: benchmark
# ===========================================================================

class TestPublicAnisotropyBenchmark:
    def test_benchmark_isotropic_scenario_passes(self, tmp_path, monkeypatch):
        """Run only the isotropic baseline scenario inline."""
        events  = _make_isotropic_events(n=60, seed=42)
        results = run_public_anisotropy_study(events, null_repeats=30, seed=42)
        axis_pct = results["null_comparison"]["axis_percentile"]
        assert axis_pct < 0.90, (
            f"Isotropic baseline axis_percentile={axis_pct:.4f} should be < 0.90"
        )

    def test_benchmark_preferred_axis_scenario_passes(self):
        """Run preferred-axis recovery inline."""
        pref    = _make_preferred_axis_events(n=80, seed=42, strength=0.9)
        results = run_public_anisotropy_study(pref, null_repeats=30, seed=42)
        axis_pct = results["null_comparison"]["axis_percentile"]
        assert axis_pct > 0.50, (
            f"Preferred-axis recovery axis_percentile={axis_pct:.4f} should be > 0.50"
        )

    def test_full_benchmark_runs(self, tmp_path, monkeypatch):
        """run_benchmark() completes without exception."""
        # Redirect output to tmp_path to avoid polluting outputs/
        import reality_audit.data_analysis.public_anisotropy_benchmark as bm_module
        monkeypatch.setattr(
            bm_module, "_OUTPUT_BASE", str(tmp_path / "bm_out")
        )
        results = run_benchmark(plots=False)
        # At least the two synthetic scenarios should run
        names = [r["scenario"] for r in results]
        assert "synthetic_isotropic_baseline" in names
        assert "synthetic_preferred_axis_recovery" in names


# ===========================================================================
# Tests: convenience script
# ===========================================================================

class TestConvenienceScript:
    def test_script_runs(self, capsys):
        """scripts/run_public_anisotropy_examples.py main() runs without crash."""
        import scripts.run_public_anisotropy_examples as script_mod
        script_mod.main()
        captured = capsys.readouterr()
        assert "Name" in captured.out or "synth" in captured.out.lower()
