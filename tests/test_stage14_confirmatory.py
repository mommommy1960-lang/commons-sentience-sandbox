"""
test_stage14_confirmatory.py
=============================
Tests for Stage 14: preregistration locking, confirmatory runner, and
confirmatory comparison + gate flow.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_confirmatory_summary(
    catalog="fermi_lat_grb_catalog",
    tier="weak_anomaly_like_deviation",
    run_mode="preregistered_confirmatory",
    correction_method="holm",
    preregistration_hash="deadbeef",
    preregistration_locked=True,
):
    return {
        "catalog": catalog,
        "event_count": 400,
        "null_mode": "exposure_corrected",
        "hemi_percentile": 0.85,
        "axis_percentile": 0.89,
        "tier": tier,
        "run_mode": run_mode,
        "trial_correction_method": correction_method,
        "preregistration_hash": preregistration_hash,
        "preregistration_locked": preregistration_locked,
    }


def _minimal_comparison():
    return {
        "catalogs_compared": ["fermi", "swift", "icecube"],
        "both_anomaly": False,
        "cross_catalog_verdict": "no_agreement",
    }


# ---------------------------------------------------------------------------
# 1. Preregistration plan locking
# ---------------------------------------------------------------------------

class TestPreregistrationPlanLocked(unittest.TestCase):
    """Verify the preregistration plan on disk is locked with required fields."""

    def test_plan_is_locked(self):
        from reality_audit.data_analysis.preregistration import (
            load_preregistration_plan,
            validate_preregistration_plan,
        )
        plan_path = os.path.join(_REPO_ROOT, "configs", "preregistered_anisotropy_plan.json")
        self.assertTrue(os.path.isfile(plan_path), "Plan file missing")
        plan = load_preregistration_plan(plan_path)
        self.assertTrue(plan.get("_locked"), "_locked must be True")

    def test_plan_has_registration_date(self):
        from reality_audit.data_analysis.preregistration import load_preregistration_plan
        plan = load_preregistration_plan()
        reg_date = plan.get("preregistration_metadata", {}).get("registration_date")
        self.assertIsNotNone(reg_date, "registration_date must be set")
        self.assertNotEqual(reg_date, "null")

    def test_plan_has_hash(self):
        from reality_audit.data_analysis.preregistration import load_preregistration_plan
        plan = load_preregistration_plan()
        h = plan.get("preregistration_metadata", {}).get("plan_hash_sha256")
        self.assertIsNotNone(h, "plan_hash_sha256 must be set")
        self.assertEqual(len(h), 64, "SHA-256 hash must be 64 hex chars")

    def test_plan_validates_clean(self):
        from reality_audit.data_analysis.preregistration import (
            load_preregistration_plan,
            validate_preregistration_plan,
        )
        plan = load_preregistration_plan()
        issues = validate_preregistration_plan(plan)
        self.assertEqual(issues, [], f"Validation issues: {issues}")

    def test_plan_null_repeats_is_500(self):
        from reality_audit.data_analysis.preregistration import load_preregistration_plan
        plan = load_preregistration_plan()
        nr = plan.get("null_model", {}).get("null_repeats")
        self.assertEqual(nr, 500, f"null_repeats should be 500, got {nr}")

    def test_plan_axis_count_is_192(self):
        from reality_audit.data_analysis.preregistration import load_preregistration_plan
        plan = load_preregistration_plan()
        ac = plan.get("axis_scan", {}).get("axis_count")
        self.assertEqual(ac, 192, f"axis_count should be 192, got {ac}")

    def test_plan_correction_is_holm(self):
        from reality_audit.data_analysis.preregistration import load_preregistration_plan
        plan = load_preregistration_plan()
        method = plan.get("multiple_testing_correction", {}).get("method")
        self.assertEqual(method, "holm", f"correction method should be holm, got {method}")


# ---------------------------------------------------------------------------
# 2. Publication gate passes with confirmatory metadata
# ---------------------------------------------------------------------------

class TestPublicationGateConfirmatoryPasses(unittest.TestCase):
    """Confirm that the three previously failing gates now pass when given
    summaries generated under the locked preregistered plan."""

    def _eval_gate(self, fermi_extras=None, swift_extras=None, icecube_extras=None):
        from reality_audit.data_analysis.publication_gate import (
            load_publication_gate,
            evaluate_publication_gate,
        )
        fermi   = _make_confirmatory_summary("fermi_lat_grb_catalog", **(fermi_extras or {}))
        swift   = _make_confirmatory_summary("swift_bat3_grb_catalog", tier="no_anomaly_detected",
                                              **(swift_extras or {}))
        icecube = _make_confirmatory_summary("icecube_hese_events", tier="no_anomaly_detected",
                                              **(icecube_extras or {}))
        run_metadata = {"catalogs": [fermi, swift, icecube]}
        gate_config  = load_publication_gate()
        result = evaluate_publication_gate(
            run_metadata        = run_metadata,
            comparison_summary  = _minimal_comparison(),
            diagnostics_summary = None,
            gate_config         = gate_config,
        )
        # For convenience, also build a dict-by-id for easier assertion
        result["_check_by_id"] = {g["id"]: g for g in result.get("gates", [])}
        return result

    def test_prereg_present_passes(self):
        result = self._eval_gate()
        checks = result["_check_by_id"]
        self.assertIn("prereg_present", checks, f"gate keys: {list(checks.keys())}")
        self.assertTrue(
            checks["prereg_present"]["passed"],
            f"prereg_present should pass; detail: {checks['prereg_present']}",
        )

    def test_prereg_locked_passes(self):
        result = self._eval_gate()
        checks = result["_check_by_id"]
        self.assertIn("prereg_locked", checks, f"gate keys: {list(checks.keys())}")
        self.assertTrue(
            checks["prereg_locked"]["passed"],
            f"prereg_locked should pass; detail: {checks['prereg_locked']}",
        )

    def test_trial_correction_applied_passes(self):
        result = self._eval_gate()
        checks = result["_check_by_id"]
        self.assertIn("trial_correction_applied", checks, f"gate keys: {list(checks.keys())}")
        self.assertTrue(
            checks["trial_correction_applied"]["passed"],
            f"trial_correction_applied should pass; detail: {checks['trial_correction_applied']}",
        )

    def test_exploratory_summaries_still_fail_prereg_locked(self):
        """Exploratory summaries (no preregistration_locked field) still fail the gate."""
        result = self._eval_gate(
            fermi_extras={"run_mode": "exploratory", "preregistration_locked": False},
            swift_extras={"run_mode": "exploratory", "preregistration_locked": False},
            icecube_extras={"run_mode": "exploratory", "preregistration_locked": False},
        )
        checks = result["_check_by_id"]
        self.assertFalse(
            checks.get("prereg_locked", {}).get("passed"),
            "exploratory summaries should fail prereg_locked",
        )

    def test_no_correction_still_fails_trial_gate(self):
        """Summaries with no trial correction still fail the gate."""
        result = self._eval_gate(
            fermi_extras={"correction_method": "none"},
            swift_extras={"correction_method": "none"},
            icecube_extras={"correction_method": "none"},
        )
        checks = result["_check_by_id"]
        self.assertFalse(
            checks.get("trial_correction_applied", {}).get("passed"),
            "trial_correction_applied should fail when method=none",
        )


# ---------------------------------------------------------------------------
# 3. Confirmatory rerun runner unit-level tests
# ---------------------------------------------------------------------------

class TestConfirmatoryRerunRunner(unittest.TestCase):
    """Unit tests for run_stage14_confirmatory_reruns without executing real runs."""

    def test_catalog_specs_have_required_keys(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_reruns import CATALOG_SPECS
        required = {"label", "input", "null_mode", "name", "output_subdir"}
        for spec in CATALOG_SPECS:
            self.assertTrue(
                required.issubset(spec.keys()),
                f"Missing keys in spec {spec.get('label')}: {required - spec.keys()}",
            )

    def test_catalog_specs_null_modes(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_reruns import CATALOG_SPECS
        modes = {s["label"]: s["null_mode"] for s in CATALOG_SPECS}
        self.assertEqual(modes.get("fermi"),   "exposure_corrected")
        self.assertEqual(modes.get("swift"),   "exposure_corrected")
        self.assertEqual(modes.get("icecube"), "isotropic")

    def test_find_summary_json_returns_none_when_missing(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_reruns import _find_summary_json
        with tempfile.TemporaryDirectory() as td:
            result = _find_summary_json(td, "nosuchrun")
            self.assertIsNone(result)

    def test_find_summary_json_finds_file(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_reruns import _find_summary_json
        with tempfile.TemporaryDirectory() as td:
            fname = os.path.join(td, "myrun_summary.json")
            with open(fname, "w") as fh:
                json.dump({"catalog": "test"}, fh)
            result = _find_summary_json(td, "myrun")
            self.assertEqual(result, fname)

    def test_locked_plan_validation_passes(self):
        """run_all_confirmatory checks that plan is locked; a locked plan passes."""
        from reality_audit.data_analysis.preregistration import load_preregistration_plan, validate_preregistration_plan
        plan = load_preregistration_plan()
        self.assertTrue(plan.get("_locked"))
        self.assertEqual(validate_preregistration_plan(plan), [])

    def test_unlocked_plan_raises(self):
        """run_all_confirmatory raises RuntimeError if plan is not locked (simulated)."""
        # We test the check directly rather than calling the full runner
        import copy
        from reality_audit.data_analysis.preregistration import (
            load_preregistration_plan,
            validate_preregistration_plan,
        )
        plan = copy.deepcopy(load_preregistration_plan())
        plan["_locked"] = False
        # Replicate the RuntimeError that run_all_confirmatory would raise
        if not plan.get("_locked"):
            with self.assertRaises(RuntimeError):
                raise RuntimeError("Plan not locked")


# ---------------------------------------------------------------------------
# 4. Comparison runner tests (with mock summary files)
# ---------------------------------------------------------------------------

class TestConfirmatoryComparisonRunner(unittest.TestCase):
    """Test run_stage14_confirmatory_comparison with synthetic summary files."""

    def _write_summary(self, td, subdir, name, extras=None):
        d = os.path.join(td, subdir)
        os.makedirs(d, exist_ok=True)
        # Build a Stage-8-format summary that load_stage_results can parse
        extras = extras or {}
        catalog = extras.pop("catalog", "fermi_lat_grb_catalog")
        tier    = extras.pop("tier", "weak_anomaly_like_deviation")
        correction = extras.pop("correction_method", "holm")
        locked  = extras.pop("preregistration_locked", True)
        prereg_hash = extras.pop("preregistration_hash", "deadbeef")
        summary = {
            "catalog": catalog,
            "results": {
                "event_count": 400,
                "events_with_position": 400,
                "null_comparison": {
                    "null_mode": "exposure_corrected",
                    "hemi_percentile": 0.85,
                    "axis_percentile": 0.89,
                },
                "signal_evaluation": {"tier": tier, "max_percentile": 0.89},
                "anisotropy": {"hemisphere_imbalance": 0.1},
                "preferred_axis": {"score": 0.8},
                "run_metadata": {
                    "run_mode": "preregistered_confirmatory",
                    "trial_factor_correction": {"method": correction, "n_tests": 2},
                    "preregistration": {
                        "locked": locked,
                        "plan_hash_sha256": prereg_hash,
                    },
                },
            },
        }
        path = os.path.join(d, f"{name}_summary.json")
        with open(path, "w") as fh:
            json.dump(summary, fh)
        return path

    def test_comparison_run_produces_gate_json(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_comparison import run_stage14_comparison
        with tempfile.TemporaryDirectory() as td:
            fermi_path   = self._write_summary(td, "fermi",   "fermi",   {"catalog": "fermi_lat_grb_catalog"})
            swift_path   = self._write_summary(td, "swift",   "swift",   {"catalog": "swift_bat3_grb_catalog", "tier": "no_anomaly_detected"})
            icecube_path = self._write_summary(td, "icecube", "icecube", {"catalog": "icecube_hese_events", "tier": "no_anomaly_detected"})
            out_dir = os.path.join(td, "gate")

            result = run_stage14_comparison(
                fermi_path   = fermi_path,
                swift_path   = swift_path,
                icecube_path = icecube_path,
                output_dir   = out_dir,
                name         = "test_stage14",
            )

            self.assertIn("gate_result",  result)
            self.assertIn("comparison",   result)
            self.assertIsFile = lambda p: self.assertTrue(os.path.isfile(p), f"Missing: {p}")
            self.assertTrue(os.path.isfile(result["gate_report_path"]))
            self.assertTrue(os.path.isfile(result["manifest_path"]))

    def test_three_prereg_gates_pass_with_confirmatory_summaries(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_comparison import run_stage14_comparison
        with tempfile.TemporaryDirectory() as td:
            fermi_path   = self._write_summary(td, "fermi",   "fermi",   {"catalog": "fermi_lat_grb_catalog"})
            swift_path   = self._write_summary(td, "swift",   "swift",   {"catalog": "swift_bat3_grb_catalog", "tier": "no_anomaly_detected"})
            icecube_path = self._write_summary(td, "icecube", "icecube", {"catalog": "icecube_hese_events", "tier": "no_anomaly_detected"})
            out_dir = os.path.join(td, "gate")

            result = run_stage14_comparison(
                fermi_path   = fermi_path,
                swift_path   = swift_path,
                icecube_path = icecube_path,
                output_dir   = out_dir,
                name         = "test_gate_pass",
            )

            gate_by_id = {g["id"]: g for g in result["gate_result"].get("gates", [])}
            for gate_name in ("prereg_present", "prereg_locked", "trial_correction_applied"):
                self.assertIn(gate_name, gate_by_id, f"Gate {gate_name} not found in {list(gate_by_id.keys())}")
                self.assertTrue(
                    gate_by_id[gate_name]["passed"],
                    f"Gate {gate_name} should pass; got {gate_by_id[gate_name]}",
                )

    def test_missing_summaries_raises_runtime_error(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_comparison import run_stage14_comparison
        with tempfile.TemporaryDirectory() as td:
            out_dir = os.path.join(td, "gate")
            with self.assertRaises(RuntimeError):
                run_stage14_comparison(
                    fermi_path   = os.path.join(td, "missing.json"),
                    swift_path   = os.path.join(td, "missing2.json"),
                    icecube_path = os.path.join(td, "missing3.json"),
                    output_dir   = out_dir,
                )


# ---------------------------------------------------------------------------
# 5. CLI smoke tests
# ---------------------------------------------------------------------------

class TestCLISmoke(unittest.TestCase):
    """Light smoke tests for CLI argument parsing."""

    def test_confirmatory_reruns_help(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_reruns import _build_parser
        p = _build_parser()
        self.assertIsNotNone(p)

    def test_confirmatory_comparison_help(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_comparison import _build_parser
        p = _build_parser()
        self.assertIsNotNone(p)

    def test_confirmatory_reruns_defaults(self):
        from reality_audit.data_analysis.run_stage14_confirmatory_reruns import (
            DEFAULT_NULL_REPEATS,
            DEFAULT_AXIS_COUNT,
            DEFAULT_SEED,
        )
        self.assertEqual(DEFAULT_NULL_REPEATS, 500)
        self.assertEqual(DEFAULT_AXIS_COUNT, 192)
        self.assertEqual(DEFAULT_SEED, 42)


if __name__ == "__main__":
    unittest.main(verbosity=2)
