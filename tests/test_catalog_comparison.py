"""
test_catalog_comparison.py
===========================
Tests for the Stage 10 cross-catalog comparison module.

Tests cover:
  1. load_stage_results reads a summary JSON correctly.
  2. compare_catalog_results includes all required keys.
  3. write_catalog_comparison_memo creates both files.
  4. CLI fails gracefully when only one catalog summary is available.
  5. CLI succeeds when both mock summaries are available.
  6. Null-model labels are preserved through the comparison.
  7. Comparison identifies differing interpretation tiers.
  8. Consistent-null verdict when both catalogs show no anomaly.
  9. Partial-agreement verdict when both show anomaly.
 10. default_null_mode_for_catalog returns expected values.
 11. Swift catalog loads and pipeline runs end-to-end with per-catalog default null.
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import unittest

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.catalog_comparison import (
    load_stage_results,
    compare_catalog_results,
    write_catalog_comparison_memo,
)
from reality_audit.data_analysis.public_event_catalogs import (
    default_null_mode_for_catalog,
)


# ---------------------------------------------------------------------------
# Helpers: create minimal synthetic summary JSONs
# ---------------------------------------------------------------------------

def _make_summary_json(
    path: str,
    catalog_name: str = "test_catalog",
    event_count: int = 100,
    null_mode: str = "exposure_corrected",
    hemi_percentile: float = 0.50,
    axis_percentile: float = 0.55,
    tier: str = "no_anomaly_detected",
    max_percentile: float = 0.55,
) -> str:
    data = {
        "experiment": "test",
        "catalog": catalog_name,
        "written_at": "2026-01-01T00:00:00Z",
        "results": {
            "event_count": event_count,
            "events_with_position": event_count,
            "events_with_energy": event_count,
            "events_with_time": event_count,
            "energy_stats": {},
            "anisotropy": {
                "hemisphere_imbalance": hemi_percentile - 0.5,
            },
            "preferred_axis": {
                "score": axis_percentile * 0.3,
            },
            "axis_scan": [],
            "energy_time_correlation": {},
            "cluster_score": {},
            "null_comparison": {
                "null_mode": null_mode,
                "hemi_percentile": hemi_percentile,
                "axis_percentile": axis_percentile,
            },
            "signal_evaluation": {
                "tier": tier,
                "max_percentile": max_percentile,
            },
            "run_metadata": {
                "null_mode": null_mode,
                "seed": 42,
            },
        },
        "coverage": {},
        "config": {},
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def _make_event_csv(path: str, n: int = 50, seed: int = 1) -> str:
    rng = random.Random(seed)
    fieldnames = ["event_id", "ra", "dec", "energy", "arrival_time", "instrument"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(n):
            ra  = rng.uniform(0.0, 360.0)
            dec = rng.uniform(-90.0, 90.0)
            writer.writerow({
                "event_id":    f"E{i:04d}",
                "ra":          f"{ra:.4f}",
                "dec":         f"{dec:.4f}",
                "energy":      "1.0",
                "arrival_time": "55000.0",
                "instrument":  "TEST",
            })
    return path


# ===========================================================================
# 1. load_stage_results reads a summary JSON correctly
# ===========================================================================

class TestLoadStageResults(unittest.TestCase):

    def test_loads_required_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = _make_summary_json(os.path.join(tmpdir, "summary.json"),
                                   catalog_name="fermi_test")
            result = load_stage_results(p)
            for key in ("path", "catalog", "event_count", "null_mode",
                        "hemi_percentile", "axis_percentile", "tier", "max_percentile"):
                self.assertIn(key, result, f"Missing key: {key}")

    def test_catalog_name_preserved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = _make_summary_json(os.path.join(tmpdir, "s.json"),
                                   catalog_name="my_catalog")
            result = load_stage_results(p)
            self.assertEqual(result["catalog"], "my_catalog")

    def test_null_mode_preserved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = _make_summary_json(os.path.join(tmpdir, "s.json"),
                                   null_mode="isotropic")
            result = load_stage_results(p)
            self.assertEqual(result["null_mode"], "isotropic")

    def test_file_not_found_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_stage_results("/nonexistent/path/summary.json")

    def test_percentiles_loaded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = _make_summary_json(os.path.join(tmpdir, "s.json"),
                                   hemi_percentile=0.85, axis_percentile=0.89)
            result = load_stage_results(p)
            self.assertAlmostEqual(result["hemi_percentile"], 0.85)
            self.assertAlmostEqual(result["axis_percentile"], 0.89)


# ===========================================================================
# 2. compare_catalog_results includes required keys
# ===========================================================================

class TestCompareCatalogResults(unittest.TestCase):

    def _make_two_results(self, tier_a="no_anomaly_detected", tier_b="no_anomaly_detected"):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"),
                                    catalog_name="cat_a", tier=tier_a,
                                    max_percentile=0.50)
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"),
                                    catalog_name="cat_b", tier=tier_b,
                                    max_percentile=0.55)
            return load_stage_results(pa), load_stage_results(pb)

    def test_required_keys(self):
        ra, rb = self._make_two_results()
        cmp = compare_catalog_results(ra, rb)
        for key in ("catalog_a", "catalog_b", "event_count_a", "event_count_b",
                    "null_mode_a", "null_mode_b", "hemi_percentile_a", "hemi_percentile_b",
                    "axis_percentile_a", "axis_percentile_b", "tier_a", "tier_b",
                    "tiers_agree", "both_anomaly", "neither_anomaly",
                    "consistency_verdict", "interpretation", "caveats", "timestamp"):
            self.assertIn(key, cmp, f"Missing key: {key}")

    def test_catalog_names_preserved(self):
        ra, rb = self._make_two_results()
        cmp = compare_catalog_results(ra, rb)
        self.assertEqual(cmp["catalog_a"], "cat_a")
        self.assertEqual(cmp["catalog_b"], "cat_b")

    def test_caveats_is_list(self):
        ra, rb = self._make_two_results()
        cmp = compare_catalog_results(ra, rb)
        self.assertIsInstance(cmp["caveats"], list)
        self.assertGreater(len(cmp["caveats"]), 0)


# ===========================================================================
# 3. write_catalog_comparison_memo creates both files
# ===========================================================================

class TestWriteComparisonMemo(unittest.TestCase):

    def test_creates_md_and_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"), catalog_name="ca")
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"), catalog_name="cb")
            ra = load_stage_results(pa)
            rb = load_stage_results(pb)
            cmp = compare_catalog_results(ra, rb)
            memo_path = write_catalog_comparison_memo(cmp, tmpdir, name="test_cmp")
            self.assertTrue(os.path.exists(memo_path))
            json_path = os.path.join(tmpdir, "test_cmp.json")
            self.assertTrue(os.path.exists(json_path))

    def test_memo_contains_catalog_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"), catalog_name="fermi_test")
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"), catalog_name="swift_test")
            cmp = compare_catalog_results(load_stage_results(pa), load_stage_results(pb))
            memo_path = write_catalog_comparison_memo(cmp, tmpdir, name="test_cmp")
            with open(memo_path) as f:
                content = f.read()
            self.assertIn("fermi_test", content)
            self.assertIn("swift_test", content)

    def test_memo_contains_verdict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"))
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"))
            cmp = compare_catalog_results(load_stage_results(pa), load_stage_results(pb))
            memo_path = write_catalog_comparison_memo(cmp, tmpdir, name="c")
            with open(memo_path) as f:
                content = f.read()
            self.assertIn("Verdict", content)


# ===========================================================================
# 4. CLI fails gracefully when only one catalog is available
# ===========================================================================

class TestCLIGracefulFail(unittest.TestCase):

    def test_cli_fails_with_missing_summary_b(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"), catalog_name="x")
            # summary_b does not exist → expect exit code 1
            result = subprocess.run(
                [sys.executable, "-m", "reality_audit.data_analysis.run_stage10_catalog_comparison",
                 "--summary-a", pa,
                 "--summary-b", os.path.join(tmpdir, "nonexistent_b.json"),
                 "--output-dir", tmpdir],
                capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing", result.stdout + result.stderr)

    def test_cli_fails_with_no_summaries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, "-m", "reality_audit.data_analysis.run_stage10_catalog_comparison",
                 "--summary-a", os.path.join(tmpdir, "nonexistent_a.json"),
                 "--summary-b", os.path.join(tmpdir, "nonexistent_b.json"),
                 "--output-dir", tmpdir],
                capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)


# ===========================================================================
# 5. CLI succeeds when both mock summaries are available
# ===========================================================================

class TestCLISuccess(unittest.TestCase):

    def test_cli_produces_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"), catalog_name="fermi_x")
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"), catalog_name="swift_x")
            out_dir = os.path.join(tmpdir, "out")
            result = subprocess.run(
                [sys.executable, "-m", "reality_audit.data_analysis.run_stage10_catalog_comparison",
                 "--summary-a", pa, "--summary-b", pb,
                 "--output-dir", out_dir, "--name", "test_run"],
                capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(os.path.isfile(os.path.join(out_dir, "test_run_memo.md")))
            self.assertTrue(os.path.isfile(os.path.join(out_dir, "test_run.json")))

    def test_cli_prints_verdict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"))
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"))
            result = subprocess.run(
                [sys.executable, "-m", "reality_audit.data_analysis.run_stage10_catalog_comparison",
                 "--summary-a", pa, "--summary-b", pb,
                 "--output-dir", tmpdir, "--name", "v_test"],
                capture_output=True, text=True
            )
            self.assertIn("Verdict", result.stdout)


# ===========================================================================
# 6. Null-model labels are preserved
# ===========================================================================

class TestNullModeLabelPreservation(unittest.TestCase):

    def test_null_mode_a_preserved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"), null_mode="isotropic")
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"), null_mode="exposure_corrected")
            ra = load_stage_results(pa)
            rb = load_stage_results(pb)
            cmp = compare_catalog_results(ra, rb)
            self.assertEqual(cmp["null_mode_a"], "isotropic")
            self.assertEqual(cmp["null_mode_b"], "exposure_corrected")

    def test_null_modes_in_memo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"), null_mode="isotropic")
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"), null_mode="exposure_corrected")
            cmp = compare_catalog_results(load_stage_results(pa), load_stage_results(pb))
            memo_path = write_catalog_comparison_memo(cmp, tmpdir, name="nm")
            with open(memo_path) as f:
                content = f.read()
            self.assertIn("isotropic", content)
            self.assertIn("exposure_corrected", content)


# ===========================================================================
# 7. Comparison identifies differing interpretation tiers
# ===========================================================================

class TestDifferingTiers(unittest.TestCase):

    def test_inconsistent_verdict_on_tier_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"),
                                    tier="weak_anomaly_like_deviation", max_percentile=0.87)
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"),
                                    tier="no_anomaly_detected", max_percentile=0.50)
            cmp = compare_catalog_results(load_stage_results(pa), load_stage_results(pb))
            self.assertEqual(cmp["consistency_verdict"], "inconsistent")
            self.assertFalse(cmp["tiers_agree"])

    def test_tier_names_in_comparison(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"),
                                    tier="moderate_anomaly_like_deviation")
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"),
                                    tier="no_anomaly_detected")
            cmp = compare_catalog_results(load_stage_results(pa), load_stage_results(pb))
            self.assertEqual(cmp["tier_a"], "moderate_anomaly_like_deviation")
            self.assertEqual(cmp["tier_b"], "no_anomaly_detected")


# ===========================================================================
# 8. Consistent-null verdict when both show no anomaly
# ===========================================================================

class TestConsistentNullVerdict(unittest.TestCase):

    def test_neither_anomaly_verdict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"),
                                    tier="no_anomaly_detected", max_percentile=0.45)
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"),
                                    tier="no_anomaly_detected", max_percentile=0.50)
            cmp = compare_catalog_results(load_stage_results(pa), load_stage_results(pb))
            self.assertEqual(cmp["consistency_verdict"], "consistent_null")
            self.assertTrue(cmp["neither_anomaly"])
            self.assertFalse(cmp["both_anomaly"])


# ===========================================================================
# 9. Partial-agreement verdict when both show anomaly
# ===========================================================================

class TestPartialAgreementVerdict(unittest.TestCase):

    def test_both_anomaly_verdict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pa = _make_summary_json(os.path.join(tmpdir, "a.json"),
                                    tier="weak_anomaly_like_deviation", max_percentile=0.87)
            pb = _make_summary_json(os.path.join(tmpdir, "b.json"),
                                    tier="moderate_anomaly_like_deviation", max_percentile=0.92)
            cmp = compare_catalog_results(load_stage_results(pa), load_stage_results(pb))
            self.assertEqual(cmp["consistency_verdict"], "partial_agreement")
            self.assertTrue(cmp["both_anomaly"])
            self.assertFalse(cmp["neither_anomaly"])


# ===========================================================================
# 10. default_null_mode_for_catalog returns expected values
# ===========================================================================

class TestDefaultNullMode(unittest.TestCase):

    def test_fermi_defaults_exposure_corrected(self):
        self.assertEqual(
            default_null_mode_for_catalog("fermi_lat_grb_catalog"),
            "exposure_corrected"
        )

    def test_swift_defaults_exposure_corrected(self):
        self.assertEqual(
            default_null_mode_for_catalog("swift_bat3_grb_catalog"),
            "exposure_corrected"
        )

    def test_icecube_defaults_isotropic(self):
        self.assertEqual(
            default_null_mode_for_catalog("icecube_hese_events"),
            "isotropic"
        )

    def test_unknown_defaults_isotropic(self):
        self.assertEqual(
            default_null_mode_for_catalog("some_unknown_catalog"),
            "isotropic"
        )

    def test_short_labels(self):
        self.assertEqual(default_null_mode_for_catalog("fermi_lat_grb"), "exposure_corrected")
        self.assertEqual(default_null_mode_for_catalog("swift_bat3_grb"), "exposure_corrected")
        self.assertEqual(default_null_mode_for_catalog("icecube_hese"), "isotropic")


# ===========================================================================
# 11. Swift catalog loads and pipeline runs with per-catalog default null
# ===========================================================================

class TestSwiftPipelineDefaultNull(unittest.TestCase):

    def _write_swift_like_catalog(self, path: str, n: int = 50) -> None:
        rng = random.Random(77)
        fieldnames = ["event_id", "ra", "dec", "energy", "arrival_time", "instrument", "t90_s"]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(n):
                ra  = rng.uniform(0.0, 360.0)
                dec = rng.uniform(-90.0, 90.0)
                writer.writerow({
                    "event_id":    f"GRB{i:04d}",
                    "ra":          f"{ra:.4f}",
                    "dec":         f"{dec:.4f}",
                    "energy":      f"{rng.uniform(1e-8, 1e-5):.3e}",
                    "arrival_time": "2010-01-01T00:00:00",
                    "instrument":  "Swift-BAT",
                    "t90_s":       f"{rng.uniform(0.5, 200.0):.1f}",
                })

    def test_auto_null_mode_for_swift_catalog_file(self):
        """Catalog file named 'swift_bat3_grb_catalog.csv' auto-selects exposure_corrected."""
        # We just test the catalog detection logic without running the full pipeline
        from reality_audit.data_analysis.public_event_catalogs import default_null_mode_for_catalog
        # The label is derived from the file basename (without extension)
        self.assertEqual(
            default_null_mode_for_catalog("swift_bat3_grb_catalog"),
            "exposure_corrected"
        )

    def test_swift_like_catalog_runs_through_stage8(self):
        """A small Swift-like catalog file runs through Stage 8 without error."""
        from reality_audit.data_analysis.stage8_first_results import run_stage8_first_results
        with tempfile.TemporaryDirectory() as tmpdir:
            cat_path = os.path.join(tmpdir, "swift_bat3_grb_catalog.csv")
            self._write_swift_like_catalog(cat_path)
            result = run_stage8_first_results(
                input_path=cat_path,
                output_dir=tmpdir,
                name="swift_test",
                null_repeats=5,
                axis_count=6,
                seed=1,
                # null_mode=None → auto-selects exposure_corrected for swift_bat3_grb_catalog
                null_mode=None,
                plots=False,
                save_normalized=False,
            )
            self.assertEqual(result["run_metadata"]["null_mode"], "exposure_corrected")


if __name__ == "__main__":
    unittest.main()
