"""
test_stage13_publication_gate.py
=================================
Tests for Stage 13: publication gate, first-results package, output hygiene,
and the Stage 13 runner CLI.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Helpers to build minimal mock summaries
# ---------------------------------------------------------------------------

def _fermi_summary(tier="weak_anomaly_like_deviation", n=3000, null="exposure_corrected",
                   run_mode="exploratory", correction_method="holm"):
    return {
        "catalog":  "fermi_lat_grb_catalog",
        "event_count": n,
        "null_mode": null,
        "hemi_percentile": 0.85,
        "axis_percentile": 0.89,
        "tier": tier,
        "run_mode": run_mode,
        "trial_correction_method": correction_method,
        "preregistration_hash": "abc123",
    }

def _swift_summary():
    return {
        "catalog":  "swift_bat3_grb_catalog",
        "event_count": 872,
        "null_mode": "exposure_corrected",
        "hemi_percentile": 0.63,
        "axis_percentile": 0.57,
        "tier": "no_anomaly_detected",
        "run_mode": "exploratory",
        "trial_correction_method": "holm",
        "preregistration_hash": None,
    }

def _icecube_summary():
    return {
        "catalog":  "icecube_hese_events",
        "event_count": 37,
        "null_mode": "isotropic",
        "hemi_percentile": 0.981,
        "axis_percentile": 0.972,
        "tier": "strong_anomaly_like_deviation",
        "run_mode": "exploratory",
        "trial_correction_method": "holm",
        "preregistration_hash": None,
    }

def _comparison_summary(verdict="partial_replication"):
    return {
        "consistency_verdict": verdict,
        "interpretation": (
            "Two catalogs show anomaly-like deviation while one does not. "
            "Mixed evidence. No metaphysical claim is warranted."
        ),
        "caveats": [
            "Small catalogs are underpowered.",
            "Instrument acceptance correction is an approximation.",
        ],
        "catalog_rows": [_fermi_summary(), _swift_summary(), _icecube_summary()],
    }

def _diag_summary():
    return {
        "robustness_label": "relatively_stable",
        "fragile_signals": [],
        "robust_signals": ["axis_density_stable", "leave_k_out_stable"],
    }


# ---------------------------------------------------------------------------
# Test: publication gate loads
# ---------------------------------------------------------------------------

class TestPublicationGateLoad(unittest.TestCase):

    def test_gate_config_loads(self):
        from reality_audit.data_analysis.publication_gate import load_publication_gate
        cfg = load_publication_gate()
        self.assertIn("gates", cfg)
        self.assertIsInstance(cfg["gates"], list)
        gate_ids = [g["id"] for g in cfg["gates"]]
        self.assertIn("prereg_present", gate_ids)
        self.assertIn("trial_correction_applied", gate_ids)

    def test_gate_config_loads_from_explicit_path(self):
        import reality_audit.data_analysis.publication_gate as pg
        cfg = pg.load_publication_gate(pg.DEFAULT_GATE_PATH)
        self.assertIn("gates", cfg)


# ---------------------------------------------------------------------------
# Test: gate evaluation returns required keys
# ---------------------------------------------------------------------------

class TestEvaluatePublicationGate(unittest.TestCase):

    def setUp(self):
        self.run_meta  = {"catalogs": [_fermi_summary(), _swift_summary(), _icecube_summary()]}
        self.comparison = _comparison_summary()
        self.diag      = _diag_summary()

    def test_evaluate_returns_required_keys(self):
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        result = evaluate_publication_gate(self.run_meta, self.comparison, self.diag)
        for k in ("verdict", "gates", "failing_required", "failing_recommended",
                  "notes", "generated_at", "readiness_description"):
            self.assertIn(k, result, f"Missing key: {k}")

    def test_verdict_is_known_label(self):
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate, _READINESS_ORDER
        result = evaluate_publication_gate(self.run_meta, self.comparison, self.diag)
        self.assertIn(result["verdict"], _READINESS_ORDER)

    def test_gates_list_has_expected_ids(self):
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        result = evaluate_publication_gate(self.run_meta, self.comparison, self.diag)
        ids = {g["id"] for g in result["gates"]}
        for gid in ("prereg_present", "trial_correction_applied", "at_least_two_catalogs",
                    "replication_status_labeled", "no_metaphysical_language"):
            self.assertIn(gid, ids)


# ---------------------------------------------------------------------------
# Test: missing preregistration lowers readiness
# ---------------------------------------------------------------------------

class TestLowerReadinessOnMissingPrereg(unittest.TestCase):

    def test_no_prereg_fails_prereg_present(self):
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        meta = {"catalogs": [
            {**_fermi_summary(), "preregistration_hash": None},
            _swift_summary(),
        ]}
        result = evaluate_publication_gate(meta, _comparison_summary())
        self.assertIn("prereg_present", result["failing_required"])

    def test_missing_replication_catalog_lowers_readiness(self):
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        # Comparison with only 1 row
        comp = {
            "consistency_verdict": "no_comparison",
            "interpretation": "single catalog only",
            "caveats": ["note"],
            "catalog_rows": [_fermi_summary()],
        }
        result = evaluate_publication_gate({"catalogs": [_fermi_summary()]}, comp)
        self.assertIn(result["verdict"], ("not_ready", "internally_reviewable"))


# ---------------------------------------------------------------------------
# Test: first-results brief is created
# ---------------------------------------------------------------------------

class TestFirstResultsBrief(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write_json(self, data, fname):
        p = os.path.join(self.tmpdir, fname)
        with open(p, "w") as f:
            json.dump(data, f)
        return p

    def test_brief_is_created(self):
        from reality_audit.data_analysis.first_results_package import (
            build_first_results_package, write_first_results_brief
        )
        fermi_p  = self._write_json(_fermi_summary(),    "fermi.json")
        swift_p  = self._write_json(_swift_summary(),    "swift.json")
        ice_p    = self._write_json(_icecube_summary(),  "icecube.json")
        comp_p   = self._write_json(_comparison_summary(), "comp.json")
        diag_p   = self._write_json(_diag_summary(),     "diag.json")
        package  = build_first_results_package(
            fermi_path=fermi_p, swift_path=swift_p, icecube_path=ice_p,
            comparison_path=comp_p, diagnostics_path=diag_p,
        )
        brief_path = write_first_results_brief(package, self.tmpdir)
        self.assertTrue(os.path.isfile(brief_path))
        with open(brief_path) as f:
            text = f.read()
        self.assertIn("What Was Tested", text)
        self.assertIn("Evidence Status", text)

    def test_package_has_blockers(self):
        from reality_audit.data_analysis.first_results_package import build_first_results_package
        package = build_first_results_package()
        self.assertIn("blockers", package)
        self.assertIsInstance(package["blockers"], list)
        self.assertTrue(len(package["blockers"]) > 0)


# ---------------------------------------------------------------------------
# Test: output hygiene report is created
# ---------------------------------------------------------------------------

class TestOutputHygieneReport(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_hygiene_report_is_created(self):
        from reality_audit.data_analysis.output_hygiene import (
            classify_output_paths, write_output_hygiene_report
        )
        # Classify a temp dir with a few fake files
        base = tempfile.mkdtemp()
        os.makedirs(os.path.join(base, "stage9_fermi_smoke"), exist_ok=True)
        open(os.path.join(base, "stage9_fermi_smoke", "foo_summary.json"), "w").close()
        classification = classify_output_paths(base)
        report_path = write_output_hygiene_report(classification, self.tmpdir)
        self.assertTrue(os.path.isfile(report_path))
        with open(report_path) as f:
            text = f.read()
        self.assertIn("Hygiene", text)

    def test_classification_keys_present(self):
        from reality_audit.data_analysis.output_hygiene import classify_output_paths
        base = tempfile.mkdtemp()
        result = classify_output_paths(base)
        for k in ("deliverable", "smoke", "transient_plot", "benchmark", "legacy", "unknown", "summary"):
            self.assertIn(k, result)


# ---------------------------------------------------------------------------
# Test: Stage 13 runner CLI succeeds with mock summaries
# ---------------------------------------------------------------------------

class TestStage13Runner(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write_json(self, data, fname):
        p = os.path.join(self.tmpdir, fname)
        with open(p, "w") as f:
            json.dump(data, f)
        return p

    def test_runner_succeeds_with_mock_data(self):
        from reality_audit.data_analysis.run_stage13_publication_gate import main
        fermi_p  = self._write_json(_fermi_summary(),      "fermi.json")
        swift_p  = self._write_json(_swift_summary(),      "swift.json")
        ice_p    = self._write_json(_icecube_summary(),    "icecube.json")
        comp_p   = self._write_json(_comparison_summary(), "comp.json")
        diag_p   = self._write_json(_diag_summary(),       "diag.json")
        out_dir  = os.path.join(self.tmpdir, "stage13_out")
        rc = main([
            "--fermi",      fermi_p,
            "--swift",      swift_p,
            "--icecube",    ice_p,
            "--comparison", comp_p,
            "--diagnostics",diag_p,
            "--output-dir", out_dir,
            "--name",       "test_run",
        ])
        self.assertEqual(rc, 0)
        manifest_path = os.path.join(out_dir, "test_run_manifest.json")
        self.assertTrue(os.path.isfile(manifest_path))
        with open(manifest_path) as f:
            manifest = json.load(f)
        self.assertEqual(manifest["stage"], 13)


# ---------------------------------------------------------------------------
# Test: verdict labels are stable and explicit
# ---------------------------------------------------------------------------

class TestVerdictLabels(unittest.TestCase):

    def test_all_required_gates_pass_gives_at_least_internally_reviewable(self):
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        # Provide well-formed inputs; may still fail prereg_locked
        meta = {"catalogs": [
            {**_fermi_summary(), "preregistration_locked": True},
            _swift_summary(),
            _icecube_summary(),
        ]}
        result = evaluate_publication_gate(meta, _comparison_summary(), _diag_summary())
        self.assertNotEqual(result["verdict"], "not_ready")

    def test_metaphysical_language_fails_gate(self):
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        comp = {**_comparison_summary(),
                "interpretation": "This result implies consciousness is influencing the data."}
        result = evaluate_publication_gate(
            {"catalogs": [_fermi_summary(), _swift_summary()]},
            comp,
        )
        self.assertIn("no_metaphysical_language", result["failing_required"])
        self.assertEqual(result["verdict"], "not_ready")

    def test_empty_comparison_gives_not_ready(self):
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        result = evaluate_publication_gate({"catalogs": [_fermi_summary()]}, {})
        self.assertEqual(result["verdict"], "not_ready")


if __name__ == "__main__":
    unittest.main()
