"""Stage 12 tests: IceCube diagnostics and confirmatory run-mode support."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.icecube_diagnostics import (
    summarize_icecube_catalog,
    run_small_n_sensitivity_analysis,
    run_leave_k_out_analysis,
    run_epoch_split_analysis,
    run_full_icecube_diagnostics,
    write_icecube_diagnostics_memo,
)
from reality_audit.data_analysis.public_event_catalogs import load_public_catalog
from reality_audit.data_analysis.preregistration import load_preregistration_plan
from reality_audit.data_analysis.stage8_first_results import run_stage8_first_results


def _write_mock_catalog(path: str, n: int = 16) -> str:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["event_id", "ra", "dec", "energy", "arrival_time", "instrument"],
        )
        w.writeheader()
        for i in range(n):
            w.writerow(
                {
                    "event_id": f"E{i:03d}",
                    "ra": str((i * 23) % 360),
                    "dec": str(-70 + ((i * 9) % 140)),
                    "energy": str(20 + i),
                    "arrival_time": str(55000 + i),
                    "instrument": "IceCube",
                }
            )
    return path


class TestStage12IceCubeDiagnostics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.events = load_public_catalog("data/real/icecube_hese_events.csv")

    def test_icecube_summary_works(self):
        s = summarize_icecube_catalog(self.events)
        self.assertIn("event_count", s)
        self.assertIn("position_coverage", s)
        self.assertIn("energy_coverage", s)
        self.assertGreater(s["event_count"], 0)

    def test_small_n_sensitivity_structure(self):
        out = run_small_n_sensitivity_analysis(self.events, repeats=3, seed=42, axis_modes=[48, 96])
        self.assertIn("by_axis", out)
        self.assertIn("trend_rows", out)
        self.assertEqual(out["axis_modes"], [48, 96])

    def test_leave_k_out_structure(self):
        out = run_leave_k_out_analysis(self.events, k=1, seed=42)
        self.assertIn("baseline", out)
        self.assertIn("rows", out)
        self.assertIn("fraction_tier_drops", out)
        self.assertGreater(out["n_combinations_evaluated"], 0)

    def test_confirmatory_run_metadata_is_recorded(self):
        plan = load_preregistration_plan("configs/preregistered_anisotropy_plan.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = _write_mock_catalog(os.path.join(tmpdir, "mock_icecube.csv"), n=14)
            out_dir = os.path.join(tmpdir, "out")

            bundle = run_stage8_first_results(
                input_path=csv_path,
                output_dir=out_dir,
                name="stage12_run_mode_test",
                null_repeats=30,
                axis_count=48,
                seed=7,
                plots=False,
                save_normalized=False,
                null_mode="isotropic",
                preregistration_plan=plan,
                preregistration_plan_path="configs/preregistered_anisotropy_plan.json",
                run_mode="preregistered_confirmatory",
            )

            rm = bundle.get("study_results", {}).get("run_metadata", {})
            self.assertIn("run_mode", rm)
            self.assertTrue(str(rm.get("run_mode", "")).startswith("preregistered_confirmatory"))
            self.assertIn("preregistration_match", rm)

    def test_diagnostics_memo_is_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = run_full_icecube_diagnostics(self.events, repeats=2, seed=42, axis_modes=[48], leave_k_out=1)
            path = write_icecube_diagnostics_memo(res, tmpdir)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                txt = f.read()
            self.assertIn("Stage 12 IceCube Diagnostics Memo", txt)

    def test_cli_succeeds_on_small_mock_catalog(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = _write_mock_catalog(os.path.join(tmpdir, "mock_icecube.csv"), n=14)
            out_dir = os.path.join(tmpdir, "cli_out")
            cmd = [
                sys.executable,
                "reality_audit/data_analysis/run_stage12_icecube_diagnostics.py",
                "--input", csv_path,
                "--output-dir", out_dir,
                "--seed", "42",
                "--axis-modes", "48", "96",
                "--leave-k-out", "1",
                "--repeats", "2",
                "--run-mode", "exploratory",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)
            self.assertTrue(os.path.exists(os.path.join(out_dir, "stage12_icecube_diagnostics_summary.json")))
            self.assertTrue(os.path.exists(os.path.join(out_dir, "stage12_icecube_diagnostics_memo.md")))

    def test_run_mode_label_propagates_to_memo(self):
        plan = load_preregistration_plan("configs/preregistered_anisotropy_plan.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = _write_mock_catalog(os.path.join(tmpdir, "mock_icecube.csv"), n=14)
            out_dir = os.path.join(tmpdir, "out")

            bundle = run_stage8_first_results(
                input_path=csv_path,
                output_dir=out_dir,
                name="stage12_memo_run_mode",
                null_repeats=30,
                axis_count=48,
                seed=11,
                plots=False,
                save_normalized=False,
                null_mode="isotropic",
                preregistration_plan=plan,
                preregistration_plan_path="configs/preregistered_anisotropy_plan.json",
                run_mode="preregistered_confirmatory",
            )

            memo_path = bundle.get("memo_path")
            self.assertTrue(os.path.exists(memo_path))
            with open(memo_path) as f:
                txt = f.read()
            self.assertIn("Run mode", txt)
            self.assertIn("preregistered_confirmatory", txt)


if __name__ == "__main__":
    unittest.main()
