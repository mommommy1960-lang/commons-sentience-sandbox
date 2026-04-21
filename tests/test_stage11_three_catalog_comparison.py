"""
Stage 11 tests: three-catalog comparison and CLI graceful failure.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

from reality_audit.data_analysis.catalog_comparison import (
    load_stage_results,
    compare_three_catalog_results,
    write_three_catalog_comparison_memo,
)


def _make_summary_json(
    path: str,
    catalog_name: str,
    event_count: int,
    null_mode: str,
    hemi_percentile: float,
    axis_percentile: float,
    tier: str,
    max_percentile: float,
) -> str:
    data = {
        "experiment": "test",
        "catalog": catalog_name,
        "written_at": "2026-01-01T00:00:00Z",
        "results": {
            "event_count": event_count,
            "events_with_position": event_count,
            "anisotropy": {"hemisphere_imbalance": hemi_percentile - 0.5},
            "preferred_axis": {"score": axis_percentile * 0.2},
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
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


class TestStage11ThreeCatalogComparison(unittest.TestCase):

    def test_compare_three_catalogs_returns_expected_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a = _make_summary_json(
                os.path.join(tmpdir, "a.json"),
                "fermi", 3000, "exposure_corrected", 0.86, 0.89,
                "weak_anomaly_like_deviation", 0.89,
            )
            b = _make_summary_json(
                os.path.join(tmpdir, "b.json"),
                "swift", 872, "exposure_corrected", 0.62, 0.57,
                "no_anomaly_detected", 0.62,
            )
            c = _make_summary_json(
                os.path.join(tmpdir, "c.json"),
                "icecube", 37, "isotropic", 0.99, 0.67,
                "strong_anomaly_like_deviation", 0.99,
            )

            cmp = compare_three_catalog_results(
                load_stage_results(a),
                load_stage_results(b),
                load_stage_results(c),
            )
            self.assertEqual(cmp.get("comparison_mode"), "three_catalog")
            self.assertIn("consistency_verdict", cmp)
            self.assertEqual(len(cmp.get("catalog_rows", [])), 3)
            self.assertIn(cmp.get("consistency_verdict"), (
                "consistent_null", "broad_replication", "partial_replication", "inconsistent"
            ))

    def test_three_catalog_memo_is_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a = _make_summary_json(os.path.join(tmpdir, "a.json"), "cat_a", 100, "isotropic", 0.5, 0.5, "no_anomaly_detected", 0.5)
            b = _make_summary_json(os.path.join(tmpdir, "b.json"), "cat_b", 100, "isotropic", 0.5, 0.5, "no_anomaly_detected", 0.5)
            c = _make_summary_json(os.path.join(tmpdir, "c.json"), "cat_c", 100, "isotropic", 0.5, 0.5, "no_anomaly_detected", 0.5)
            cmp = compare_three_catalog_results(load_stage_results(a), load_stage_results(b), load_stage_results(c))
            memo_path = write_three_catalog_comparison_memo(cmp, tmpdir, name="three_cmp")
            self.assertTrue(os.path.exists(memo_path))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "three_cmp.json")))

    def test_cli_graceful_failure_when_require_three_and_missing_c(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a = _make_summary_json(
                os.path.join(tmpdir, "a.json"),
                "fermi", 3000, "exposure_corrected", 0.86, 0.89,
                "weak_anomaly_like_deviation", 0.89,
            )
            b = _make_summary_json(
                os.path.join(tmpdir, "b.json"),
                "swift", 872, "exposure_corrected", 0.62, 0.57,
                "no_anomaly_detected", 0.62,
            )
            missing_c = os.path.join(tmpdir, "missing_c.json")

            cmd = [
                sys.executable,
                "reality_audit/data_analysis/run_stage10_catalog_comparison.py",
                "--summary-a", a,
                "--summary-b", b,
                "--summary-c", missing_c,
                "--require-three",
                "--name", "three_cmp_cli_missing",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Missing prerequisite files", proc.stdout)
            self.assertIn("Catalog C summary", proc.stdout)


if __name__ == "__main__":
    unittest.main()
