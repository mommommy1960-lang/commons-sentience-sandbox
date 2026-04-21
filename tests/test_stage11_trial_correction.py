"""
Stage 11 tests: multiple-testing correction and dense-axis determinism.
"""

from __future__ import annotations

import csv
import os
import tempfile
import unittest

from reality_audit.data_analysis.trial_factor_correction import (
    apply_trial_correction,
    correct_pvalues_bonferroni,
    correct_pvalues_holm,
)
from reality_audit.data_analysis.public_anisotropy_study import scan_trial_axes
from reality_audit.data_analysis.stage8_first_results import run_stage8_first_results


class TestStage11TrialCorrection(unittest.TestCase):

    def test_bonferroni_and_holm_structure(self):
        pvals = {"a": 0.01, "b": 0.02, "c": 0.20}
        bonf = correct_pvalues_bonferroni(pvals)
        holm = correct_pvalues_holm(pvals)
        self.assertEqual(set(bonf.keys()), set(pvals.keys()))
        self.assertEqual(set(holm.keys()), set(pvals.keys()))
        self.assertLessEqual(bonf["a"], 1.0)
        self.assertLessEqual(holm["a"], 1.0)

    def test_apply_trial_correction_labels_verdict(self):
        metric_percentiles = {
            "hemisphere_imbalance": 0.99,
            "preferred_axis_score": 0.98,
            "energy_time_pearson_r": 0.40,
            "clustering_score": 0.50,
        }
        out = apply_trial_correction(metric_percentiles, method="holm")
        self.assertIn("summary_verdict", out)
        self.assertIn(out["summary_verdict"], ("corrected_discovery", "corrected_notable", "corrected_null"))
        self.assertIn("flags", out)
        self.assertIn("hemisphere_imbalance", out["flags"])

    def test_dense_axis_generation_is_deterministic(self):
        events = [
            {"ra": 0.0, "dec": 0.0},
            {"ra": 90.0, "dec": 10.0},
            {"ra": 180.0, "dec": -20.0},
            {"ra": 270.0, "dec": 30.0},
        ]
        a = scan_trial_axes(events, num_axes=192, seed=1, axis_mode="dense")
        b = scan_trial_axes(events, num_axes=192, seed=999, axis_mode="dense")
        self.assertEqual(a["num_axes"], 192)
        self.assertEqual(b["num_axes"], 192)
        self.assertEqual(a["all_scores"], b["all_scores"])

    def test_stage8_records_trial_correction_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "tiny_catalog.csv")
            out_dir = os.path.join(tmpdir, "out")

            with open(csv_path, "w", newline="") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=["event_id", "ra", "dec", "energy", "arrival_time", "instrument"],
                )
                w.writeheader()
                for i in range(20):
                    w.writerow(
                        {
                            "event_id": f"E{i:03d}",
                            "ra": str((i * 13) % 360),
                            "dec": str(-50 + (i * 6) % 100),
                            "energy": "12.0",
                            "arrival_time": str(56000 + i),
                            "instrument": "TEST",
                        }
                    )

            bundle = run_stage8_first_results(
                input_path=csv_path,
                output_dir=out_dir,
                name="stage11_trialcorr_test",
                null_repeats=20,
                axis_count=48,
                seed=11,
                plots=False,
                save_normalized=False,
                null_mode="isotropic",
            )

            tfc = bundle.get("study_results", {}).get("trial_factor_correction", {})
            self.assertTrue(tfc)
            self.assertIn("method", tfc)
            self.assertIn("corrected_percentiles", tfc)
            self.assertIn("summary_verdict", tfc)


if __name__ == "__main__":
    unittest.main()
