"""
tests/test_simulation_signature_analysis.py
===========================================
Tests for the simulation-signature analysis pipeline.

All tests are deterministic (seeded) and lightweight.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from typing import List, Dict, Any

import pytest

from reality_audit.data_analysis.example_event_data import generate_example_event_dataset
from reality_audit.data_analysis.simulation_signature_analysis import (
    ANOMALY_CLUSTERED,
    ANOMALY_ENERGY_DELAY,
    ANOMALY_PREFERRED_AXIS,
    TIER_NONE,
    analyze_event_dataset,
    evaluate_signal_strength,
    generate_null_events,
    inject_synthetic_anomaly,
    load_event_dataset,
    standardize_events,
    write_analysis_artifacts,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def small_events() -> List[Dict[str, Any]]:
    """50 standardized example events, seeded."""
    raw = generate_example_event_dataset(n=50, seed=99)
    return standardize_events(raw)


@pytest.fixture
def csv_file(tmp_path) -> str:
    """Write a tiny CSV and return its path."""
    path = str(tmp_path / "test_events.csv")
    rows = generate_example_event_dataset(n=30, seed=7)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


@pytest.fixture
def json_file(tmp_path) -> str:
    """Write a tiny JSON event list and return its path."""
    path = str(tmp_path / "test_events.json")
    rows = generate_example_event_dataset(n=20, seed=8)
    with open(path, "w") as f:
        json.dump(rows, f)
    return path


# ---------------------------------------------------------------------------
# 1. Dataset loading
# ---------------------------------------------------------------------------

class TestLoadEventDataset:
    def test_loads_csv(self, csv_file):
        records = load_event_dataset(csv_file)
        assert isinstance(records, list)
        assert len(records) == 30

    def test_loads_json_list(self, json_file):
        records = load_event_dataset(json_file)
        assert isinstance(records, list)
        assert len(records) == 20

    def test_loads_json_wrapped(self, tmp_path):
        path = str(tmp_path / "wrapped.json")
        rows = generate_example_event_dataset(n=10, seed=1)
        with open(path, "w") as f:
            json.dump({"events": rows}, f)
        records = load_event_dataset(path)
        assert len(records) == 10

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_event_dataset("/nonexistent/path/file.csv")

    def test_unsupported_extension_raises(self, tmp_path):
        path = str(tmp_path / "file.parquet")
        path_obj = open(path, "w")
        path_obj.close()
        with pytest.raises(ValueError):
            load_event_dataset(path)


# ---------------------------------------------------------------------------
# 2. Standardization
# ---------------------------------------------------------------------------

class TestStandardizeEvents:
    def test_produces_consistent_schema(self, small_events):
        for ev in small_events:
            assert "event_id" in ev
            assert "energy" in ev
            assert "arrival_time" in ev

    def test_assigns_event_id_if_missing(self):
        raw = [{"energy": "1.0", "ra": "10.0", "dec": "5.0"}]
        std = standardize_events(raw)
        assert std[0]["event_id"].startswith("evt_")

    def test_coerces_numeric_fields(self):
        raw = [{"event_id": "x", "energy": "3.14", "ra": "100.0", "dec": "-10.0",
                "arrival_time": "58500.0"}]
        std = standardize_events(raw)
        assert isinstance(std[0]["energy"], float)
        assert isinstance(std[0]["arrival_time"], float)

    def test_handles_non_coercible_gracefully(self):
        raw = [{"event_id": "x", "energy": "not_a_number"}]
        std = standardize_events(raw)
        assert std[0]["energy"] is None
        assert len(std[0]["_parse_warnings"]) > 0

    def test_adds_b_proxy(self, small_events):
        for ev in small_events:
            if ev.get("dec") is not None:
                assert "_b_proxy" in ev


# ---------------------------------------------------------------------------
# 3. Null generation
# ---------------------------------------------------------------------------

class TestGenerateNullEvents:
    def test_preserves_record_count(self, small_events):
        null = generate_null_events(small_events, mode="isotropic", seed=42)
        assert len(null) == len(small_events)

    def test_shuffled_time_count(self, small_events):
        null = generate_null_events(small_events, mode="shuffled_time", seed=42)
        assert len(null) == len(small_events)

    def test_isotropic_tags_records(self, small_events):
        null = generate_null_events(small_events, mode="isotropic", seed=1)
        assert all(r["_null_model"] == "isotropic" for r in null)

    def test_shuffled_time_has_valid_ra(self, small_events):
        null = generate_null_events(small_events, mode="shuffled_time", seed=2)
        ras = [r["ra"] for r in null if r.get("ra") is not None]
        assert len(ras) > 0

    def test_seeded_reproducibility(self, small_events):
        n1 = generate_null_events(small_events, mode="isotropic", seed=7)
        n2 = generate_null_events(small_events, mode="isotropic", seed=7)
        assert [r["ra"] for r in n1] == [r["ra"] for r in n2]

    def test_different_seeds_differ(self, small_events):
        n1 = generate_null_events(small_events, mode="isotropic", seed=7)
        n2 = generate_null_events(small_events, mode="isotropic", seed=8)
        ras1 = [r["ra"] for r in n1]
        ras2 = [r["ra"] for r in n2]
        assert ras1 != ras2


# ---------------------------------------------------------------------------
# 4. Preferred-axis injection changes anisotropy score
# ---------------------------------------------------------------------------

class TestPreferredAxisInjection:
    def test_injection_elevates_axis_score(self):
        raw = generate_example_event_dataset(n=200, seed=42)
        base = standardize_events(raw)

        injected = inject_synthetic_anomaly(
            base, anomaly_type=ANOMALY_PREFERRED_AXIS, strength=0.8, seed=42
        )

        from reality_audit.data_analysis.simulation_signature_analysis import (
            _preferred_axis_score,
        )
        base_ras  = [e["ra"]  for e in base     if e.get("ra")  is not None]
        base_decs = [e["dec"] for e in base     if e.get("dec") is not None]
        inj_ras   = [e["ra"]  for e in injected if e.get("ra")  is not None]
        inj_decs  = [e["dec"] for e in injected if e.get("dec") is not None]

        base_score = _preferred_axis_score(base_ras, base_decs)
        inj_score  = _preferred_axis_score(inj_ras,  inj_decs)
        assert inj_score > base_score, (
            f"Injected axis score {inj_score:.4f} should exceed base {base_score:.4f}"
        )

    def test_injection_tags_metadata(self):
        raw = generate_example_event_dataset(n=50, seed=1)
        events = standardize_events(raw)
        injected = inject_synthetic_anomaly(events, ANOMALY_PREFERRED_AXIS, 0.5, seed=1)
        assert any(e.get("_injected_anomaly") == ANOMALY_PREFERRED_AXIS for e in injected)


# ---------------------------------------------------------------------------
# 5. Energy-delay injection changes energy-time metric
# ---------------------------------------------------------------------------

class TestEnergyDelayInjection:
    def test_injection_changes_pearson_r(self):
        raw = generate_example_event_dataset(n=200, seed=42)
        base = standardize_events(raw)

        injected = inject_synthetic_anomaly(
            base, anomaly_type=ANOMALY_ENERGY_DELAY, strength=0.8, seed=42
        )

        from reality_audit.data_analysis.simulation_signature_analysis import _pearson_r
        b_e = [e["energy"] for e in base if e.get("energy") and e.get("arrival_time")]
        b_t = [e["arrival_time"] for e in base if e.get("energy") and e.get("arrival_time")]
        i_e = [e["energy"] for e in injected if e.get("energy") and e.get("arrival_time")]
        i_t = [e["arrival_time"] for e in injected if e.get("energy") and e.get("arrival_time")]

        r_base = abs(_pearson_r(b_e, b_t) or 0.0)
        r_inj  = abs(_pearson_r(i_e, i_t) or 0.0)
        assert r_inj > r_base, (
            f"Injected |r| {r_inj:.4f} should exceed base |r| {r_base:.4f}"
        )


# ---------------------------------------------------------------------------
# 6. Seeded runs are reproducible
# ---------------------------------------------------------------------------

class TestReproducibility:
    def test_analysis_reproducible_with_seed(self, small_events):
        r1 = analyze_event_dataset(small_events, null_repeats=5, seed=42)
        r2 = analyze_event_dataset(small_events, null_repeats=5, seed=42)
        assert r1["null_comparison"]["axis_percentile"] == \
               r2["null_comparison"]["axis_percentile"]

    def test_injection_reproducible(self, small_events):
        i1 = inject_synthetic_anomaly(small_events, ANOMALY_PREFERRED_AXIS, 0.5, seed=100)
        i2 = inject_synthetic_anomaly(small_events, ANOMALY_PREFERRED_AXIS, 0.5, seed=100)
        ras1 = [e["ra"] for e in i1]
        ras2 = [e["ra"] for e in i2]
        assert ras1 == ras2


# ---------------------------------------------------------------------------
# 7. Artifact files are created
# ---------------------------------------------------------------------------

class TestArtifacts:
    def test_all_artifacts_created(self, small_events, tmp_path):
        null = generate_null_events(small_events, "isotropic", seed=1)
        results = analyze_event_dataset(small_events, reference_events=null,
                                        null_repeats=5, seed=1)
        signal_eval = evaluate_signal_strength(results)
        manifest = write_analysis_artifacts(
            results=results,
            signal_eval=signal_eval,
            events=small_events,
            null_events=null,
            output_dir=str(tmp_path),
            name="test_run",
            plots_enabled=True,
        )
        assert os.path.exists(manifest["json_summary"])
        assert os.path.exists(manifest["csv_summary"])
        assert os.path.exists(manifest["markdown_summary"])
        assert os.path.exists(manifest["manifest"])

    def test_json_summary_valid(self, small_events, tmp_path):
        null = generate_null_events(small_events, "isotropic", seed=2)
        results = analyze_event_dataset(small_events, reference_events=null,
                                        null_repeats=5, seed=2)
        signal_eval = evaluate_signal_strength(results)
        manifest = write_analysis_artifacts(
            results, signal_eval, small_events, null,
            str(tmp_path), "t", plots_enabled=False,
        )
        with open(manifest["json_summary"]) as f:
            data = json.load(f)
        assert "results" in data
        assert "signal_evaluation" in data

    def test_csv_summary_has_headers(self, small_events, tmp_path):
        null = generate_null_events(small_events, "isotropic", seed=3)
        results = analyze_event_dataset(small_events, reference_events=null,
                                        null_repeats=5, seed=3)
        signal_eval = evaluate_signal_strength(results)
        manifest = write_analysis_artifacts(
            results, signal_eval, small_events, null,
            str(tmp_path), "t2", plots_enabled=False,
        )
        with open(manifest["csv_summary"]) as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert "signal_tier" in row
        assert "event_count" in row


# ---------------------------------------------------------------------------
# 8. Benchmark completes without failure
# ---------------------------------------------------------------------------

class TestBenchmark:
    def test_benchmark_runs(self, tmp_path):
        from reality_audit.data_analysis.simulation_signature_benchmark import run_benchmark
        result = run_benchmark(output_dir=str(tmp_path), n_events=50, null_repeats=5)
        assert "scenarios" in result
        assert len(result["scenarios"]) == 3

    def test_baseline_scenario_passes(self, tmp_path):
        from reality_audit.data_analysis.simulation_signature_benchmark import run_benchmark
        result = run_benchmark(output_dir=str(tmp_path), n_events=50, null_repeats=5)
        baseline = next(s for s in result["scenarios"] if s["scenario"] == "baseline_null")
        assert baseline["passed"] is True


# ---------------------------------------------------------------------------
# 9. Signal evaluation tiers
# ---------------------------------------------------------------------------

class TestSignalEvaluation:
    def _fake_results(self, percentile: float) -> dict:
        return {
            "null_comparison": {
                "hemi_percentile":  percentile,
                "axis_percentile":  0.3,
                "et_r_percentile":  0.3,
                "clust_percentile": 0.3,
            }
        }

    def test_strong_tier(self):
        ev = evaluate_signal_strength(self._fake_results(0.98))
        assert ev["tier"] == "strong_anomaly_like_deviation"

    def test_moderate_tier(self):
        ev = evaluate_signal_strength(self._fake_results(0.92))
        assert ev["tier"] == "moderate_anomaly_like_deviation"

    def test_weak_tier(self):
        ev = evaluate_signal_strength(self._fake_results(0.80))
        assert ev["tier"] == "weak_anomaly_like_deviation"

    def test_none_tier(self):
        ev = evaluate_signal_strength(self._fake_results(0.5))
        assert ev["tier"] == TIER_NONE

    def test_caveat_always_present(self):
        ev = evaluate_signal_strength(self._fake_results(0.5))
        assert "caveat" in ev
        assert len(ev["caveat"]) > 10
