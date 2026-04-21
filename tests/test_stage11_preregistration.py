"""
Stage 11 tests: preregistration scaffolding and IceCube normalization.
"""

from __future__ import annotations

import csv
import os
import tempfile
import unittest

from reality_audit.data_analysis.preregistration import (
    load_preregistration_plan,
    validate_preregistration_plan,
    compute_plan_hash,
)
from reality_audit.data_analysis.public_event_catalogs import (
    load_public_catalog,
    validate_icecube_hese_schema,
)
from reality_audit.data_analysis.stage8_first_results import run_stage8_first_results


class TestStage11Preregistration(unittest.TestCase):

    def test_default_preregistration_plan_loads_and_validates(self):
        plan = load_preregistration_plan()
        issues = validate_preregistration_plan(plan)
        self.assertEqual(issues, [])
        plan_hash = compute_plan_hash(plan)
        self.assertEqual(len(plan_hash), 64)

    def test_icecube_schema_normalization_works(self):
        events = load_public_catalog("data/real/icecube_hese_events.csv")
        report = validate_icecube_hese_schema(events)
        self.assertTrue(report["valid"])
        self.assertGreater(report["n_events"], 0)
        self.assertEqual(report["n_missing_pos"], 0)

    def test_preregistration_metadata_is_recorded_in_summary(self):
        plan = load_preregistration_plan()

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "tiny_catalog.csv")
            out_dir = os.path.join(tmpdir, "out")

            with open(csv_path, "w", newline="") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=["event_id", "ra", "dec", "energy", "arrival_time", "instrument"],
                )
                w.writeheader()
                for i in range(24):
                    w.writerow(
                        {
                            "event_id": f"E{i:03d}",
                            "ra": str((i * 17) % 360),
                            "dec": str(-60 + (i * 5) % 120),
                            "energy": "10.0",
                            "arrival_time": str(55000 + i),
                            "instrument": "TEST",
                        }
                    )

            bundle = run_stage8_first_results(
                input_path=csv_path,
                output_dir=out_dir,
                name="stage11_prereg_test",
                null_repeats=20,
                axis_count=12,
                seed=7,
                plots=False,
                save_normalized=False,
                null_mode="isotropic",
                preregistration_plan=plan,
                preregistration_plan_path="configs/preregistered_anisotropy_plan.json",
            )

            rm = bundle.get("study_results", {}).get("run_metadata", {})
            prereg = rm.get("preregistration") or {}
            self.assertEqual(prereg.get("hypothesis_name"), "catalog_independent_sky_anisotropy")
            self.assertIn("plan_hash_sha256", prereg)
            self.assertEqual(prereg.get("plan_path"), "configs/preregistered_anisotropy_plan.json")


if __name__ == "__main__":
    unittest.main()
