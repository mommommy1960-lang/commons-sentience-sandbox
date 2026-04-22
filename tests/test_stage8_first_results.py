"""
test_stage8_first_results.py
=============================
Tests for the Stage 8 first real-catalog results package.

Tests cover:
  1. Auto-detection of known and fallback catalog filenames.
  2. Auto-detection graceful failure when no real catalog present.
  3. Full Stage 8 workflow produces required keys.
  4. Memo file is created.
  5. Stage 8 manifest is created.
  6. Seeded runs are reproducible.
  7. Convenience script completes or exits cleanly.

All tests use lightweight in-memory fixtures and temporary directories.
No internet access required.
"""

from __future__ import annotations

import csv
import importlib
import json
import os
import sys
import subprocess
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Ensure repo root on path
# ---------------------------------------------------------------------------
_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.stage8_first_results import (
    discover_real_catalog,
    run_stage8_first_results,
    build_stage8_status_summary,
    write_stage8_first_results_memo,
    write_stage8_manifest,
    _KNOWN_CATALOG_FILES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_minimal_catalog(path: str, n: int = 40) -> None:
    """Write a minimal synthetic CSV catalog for testing."""
    import math, random
    rng = random.Random(99)
    fieldnames = ["event_id", "ra", "dec", "energy", "arrival_time", "instrument"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(n):
            ra  = rng.uniform(0.0, 360.0)
            dec = math.degrees(math.asin(rng.uniform(-1.0, 1.0)))
            writer.writerow({
                "event_id":    f"E{i:04d}",
                "ra":          f"{ra:.4f}",
                "dec":         f"{dec:.4f}",
                "energy":      f"{rng.uniform(1.0, 100.0):.3f}",
                "arrival_time": f"{55000 + rng.uniform(0, 3650):.2f}",
                "instrument":  "TEST",
            })


# ===========================================================================
# 1. Auto-detection
# ===========================================================================

class TestDiscoverRealCatalog(unittest.TestCase):

    def test_known_catalog_detected(self):
        """discover_real_catalog returns known_filename for a recognised name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = _KNOWN_CATALOG_FILES[0]["filename"]
            fpath = os.path.join(tmpdir, fname)
            _write_minimal_catalog(fpath, n=20)

            result = discover_real_catalog(data_dir=tmpdir)
            self.assertTrue(result["usable"])
            self.assertEqual(result["detection_method"], "known_filename")
            self.assertEqual(result["detected_path"], fpath)
            self.assertEqual(
                result["detected_catalog_label"],
                _KNOWN_CATALOG_FILES[0]["label"],
            )

    def test_fallback_csv_detected(self):
        """discover_real_catalog falls back to any non-skip CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = os.path.join(tmpdir, "my_custom_catalog.csv")
            _write_minimal_catalog(fpath, n=20)

            result = discover_real_catalog(data_dir=tmpdir)
            self.assertTrue(result["usable"])
            self.assertEqual(result["detection_method"], "fallback_csv")
            self.assertEqual(result["detected_catalog_label"], "my_custom_catalog")

    def test_example_catalog_skipped(self):
        """discover_real_catalog skips example_event_catalog.csv."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = os.path.join(tmpdir, "example_event_catalog.csv")
            _write_minimal_catalog(fpath, n=20)

            result = discover_real_catalog(data_dir=tmpdir)
            self.assertFalse(result["usable"])
            self.assertEqual(result["detection_method"], "not_found")

    def test_no_catalog_not_found(self):
        """discover_real_catalog returns usable=False when directory is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = discover_real_catalog(data_dir=tmpdir)
            self.assertFalse(result["usable"])
            self.assertEqual(result["detection_method"], "not_found")
            self.assertIn("message", result)
            self.assertTrue(len(result["message"]) > 0)

    def test_missing_directory_handled(self):
        """discover_real_catalog handles a non-existent directory gracefully."""
        result = discover_real_catalog(data_dir="/tmp/no_such_dir_stage8_test_xyz")
        self.assertFalse(result["usable"])
        self.assertIn("message", result)

    def test_known_priority_over_fallback(self):
        """Known catalog name is preferred over a generic CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a generic CSV first
            generic_path = os.path.join(tmpdir, "aaa_first_alphabetically.csv")
            _write_minimal_catalog(generic_path, n=10)
            # Write a known catalog
            known_fname  = _KNOWN_CATALOG_FILES[0]["filename"]
            known_path   = os.path.join(tmpdir, known_fname)
            _write_minimal_catalog(known_path, n=10)

            result = discover_real_catalog(data_dir=tmpdir)
            self.assertTrue(result["usable"])
            self.assertEqual(result["detection_method"], "known_filename")
            self.assertEqual(result["detected_path"], known_path)


# ===========================================================================
# 2. Full Stage 8 workflow
# ===========================================================================

class TestRunStage8FirstResults(unittest.TestCase):

    def _make_catalog(self, tmpdir: str, n: int = 50) -> str:
        fname = _KNOWN_CATALOG_FILES[0]["filename"]
        fpath = os.path.join(tmpdir, fname)
        _write_minimal_catalog(fpath, n=n)
        return fpath

    def test_run_returns_required_keys(self):
        """run_stage8_first_results returns all required bundle keys."""
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            cat_path = self._make_catalog(catalog_dir, n=40)
            bundle = run_stage8_first_results(
                input_path=cat_path,
                output_dir=out_dir,
                name="test_s8_keys",
                null_repeats=5,
                axis_count=12,
                seed=7,
                plots=False,
                save_normalized=True,
            )
            for key in [
                "run_name", "input_path", "output_dir", "catalog_label",
                "event_count", "coverage", "study_results", "manifest",
                "memo_path", "stage8_manifest_path", "run_metadata",
            ]:
                self.assertIn(key, bundle, f"Missing key: {key}")

    def test_event_count_positive(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            cat_path = self._make_catalog(catalog_dir, n=40)
            bundle = run_stage8_first_results(
                input_path=cat_path,
                output_dir=out_dir,
                name="test_evcount",
                null_repeats=5,
                axis_count=12,
                seed=7,
                plots=False,
                save_normalized=False,
            )
            self.assertGreater(bundle["event_count"], 0)

    def test_study_results_signal_evaluation_present(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            cat_path = self._make_catalog(catalog_dir, n=40)
            bundle = run_stage8_first_results(
                input_path=cat_path,
                output_dir=out_dir,
                name="test_sig",
                null_repeats=5,
                axis_count=12,
                seed=7,
                plots=False,
                save_normalized=False,
            )
            sr = bundle["study_results"]
            self.assertIn("signal_evaluation", sr)
            self.assertIn("tier", sr["signal_evaluation"])

    def test_normalized_csv_created_when_requested(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            cat_path = self._make_catalog(catalog_dir, n=30)
            bundle = run_stage8_first_results(
                input_path=cat_path,
                output_dir=out_dir,
                name="test_norm",
                null_repeats=3,
                axis_count=12,
                seed=1,
                plots=False,
                save_normalized=True,
            )
            self.assertIsNotNone(bundle.get("normalised_path"))
            self.assertTrue(os.path.isfile(bundle["normalised_path"]))

    def test_normalized_csv_not_created_when_skipped(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            cat_path = self._make_catalog(catalog_dir, n=30)
            bundle = run_stage8_first_results(
                input_path=cat_path,
                output_dir=out_dir,
                name="test_no_norm",
                null_repeats=3,
                axis_count=12,
                seed=1,
                plots=False,
                save_normalized=False,
            )
            self.assertIsNone(bundle.get("normalised_path"))

    def test_stage16_refinement_metadata_surfaces_in_run_metadata(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            cat_path = self._make_catalog(catalog_dir, n=40)
            bundle = run_stage8_first_results(
                input_path=cat_path,
                output_dir=out_dir,
                name="test_stage16_meta",
                null_repeats=5,
                axis_count=12,
                seed=7,
                plots=False,
                save_normalized=False,
                null_mode="exposure_corrected",
            )
            rm = bundle.get("run_metadata", {})
            self.assertIn("exposure_model", rm)
            self.assertIn("time_coverage_refinement", rm)
            self.assertIn("mission_grade_promotion_blockers", rm)
            self.assertIn("confirmatory_readiness", rm)

    def test_confirmatory_readiness_flags_prereg_mismatch(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            cat_path = self._make_catalog(catalog_dir, n=40)
            bundle = run_stage8_first_results(
                input_path=cat_path,
                output_dir=out_dir,
                name="test_confirmatory_readiness",
                null_repeats=5,
                axis_count=12,
                seed=7,
                plots=False,
                save_normalized=False,
                null_mode="exposure_corrected",
                run_mode="preregistered_confirmatory",
            )
            readiness = bundle.get("run_metadata", {}).get("confirmatory_readiness", {})
            self.assertFalse(readiness.get("ready_for_confirmatory_promotion"))
            self.assertEqual(readiness.get("reason"), "preregistration_mismatch")


# ===========================================================================
# 3. Memo creation
# ===========================================================================

class TestMemo(unittest.TestCase):

    def _make_bundle(self, tmpdir: str) -> dict:
        import tempfile
        cat_dir = tempfile.mkdtemp()
        fname = _KNOWN_CATALOG_FILES[0]["filename"]
        _write_minimal_catalog(os.path.join(cat_dir, fname), n=30)
        return run_stage8_first_results(
            input_path=os.path.join(cat_dir, fname),
            output_dir=tmpdir,
            name="test_memo",
            null_repeats=3,
            axis_count=12,
            seed=2,
            plots=False,
            save_normalized=False,
        )

    def test_memo_file_created(self):
        with tempfile.TemporaryDirectory() as out_dir:
            bundle = self._make_bundle(out_dir)
            memo_path = bundle.get("memo_path")
            self.assertIsNotNone(memo_path)
            self.assertTrue(os.path.isfile(memo_path))

    def test_memo_contains_key_sections(self):
        with tempfile.TemporaryDirectory() as out_dir:
            bundle = self._make_bundle(out_dir)
            with open(bundle["memo_path"]) as f:
                content = f.read()
            for section in [
                "Stage 8 First-Results Internal Memo",
                "What Was Run",
                "Key Metrics",
                "Interpretation",
                "What This Result Does NOT Prove",
                "Current Limitations",
                "Recommended Next Upgrades",
            ]:
                self.assertIn(section, content, f"Missing section: {section}")

    def test_memo_does_not_claim_simulation(self):
        """Memo must not assert that reality is a simulation."""
        with tempfile.TemporaryDirectory() as out_dir:
            bundle = self._make_bundle(out_dir)
            with open(bundle["memo_path"]) as f:
                content = f.read().lower()
            # The memo must contain a disclaimer, not an assertion
            # Confirm it contains "does not" or "not proof" near relevant word
            self.assertIn("not prove", content)


# ===========================================================================
# 4. Manifest creation
# ===========================================================================

class TestManifest(unittest.TestCase):

    def test_manifest_file_created(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            fname = _KNOWN_CATALOG_FILES[0]["filename"]
            _write_minimal_catalog(os.path.join(catalog_dir, fname), n=30)
            bundle = run_stage8_first_results(
                input_path=os.path.join(catalog_dir, fname),
                output_dir=out_dir,
                name="test_manifest",
                null_repeats=3,
                axis_count=12,
                seed=3,
                plots=False,
                save_normalized=False,
            )
            self.assertTrue(os.path.isfile(bundle["stage8_manifest_path"]))

    def test_manifest_is_valid_json(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            fname = _KNOWN_CATALOG_FILES[0]["filename"]
            _write_minimal_catalog(os.path.join(catalog_dir, fname), n=30)
            bundle = run_stage8_first_results(
                input_path=os.path.join(catalog_dir, fname),
                output_dir=out_dir,
                name="test_mf_json",
                null_repeats=3,
                axis_count=12,
                seed=3,
                plots=False,
                save_normalized=False,
            )
            with open(bundle["stage8_manifest_path"]) as f:
                data = json.load(f)
            self.assertIn("stage", data)
            self.assertEqual(data["stage"], "stage8_first_results")
            self.assertIn("artifacts", data)
            self.assertIn("stage8_memo", data["artifacts"])

    def test_manifest_signal_tier_present(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            fname = _KNOWN_CATALOG_FILES[0]["filename"]
            _write_minimal_catalog(os.path.join(catalog_dir, fname), n=30)
            bundle = run_stage8_first_results(
                input_path=os.path.join(catalog_dir, fname),
                output_dir=out_dir,
                name="test_tier",
                null_repeats=3,
                axis_count=12,
                seed=3,
                plots=False,
                save_normalized=False,
            )
            with open(bundle["stage8_manifest_path"]) as f:
                data = json.load(f)
            self.assertIn("signal_tier", data)


# ===========================================================================
# 5. Status summary
# ===========================================================================

class TestBuildStatusSummary(unittest.TestCase):

    def test_status_summary_required_keys(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            fname = _KNOWN_CATALOG_FILES[0]["filename"]
            _write_minimal_catalog(os.path.join(catalog_dir, fname), n=30)
            bundle = run_stage8_first_results(
                input_path=os.path.join(catalog_dir, fname),
                output_dir=out_dir,
                name="test_status",
                null_repeats=3,
                axis_count=12,
                seed=5,
                plots=False,
                save_normalized=False,
            )
            status = build_stage8_status_summary(bundle)
            for key in [
                "catalog_label", "event_count", "preferred_axis_score",
                "preferred_axis_percentile", "interpretation_label",
                "interpretation_text", "caveats", "next_recommended_actions",
            ]:
                self.assertIn(key, status, f"Missing key: {key}")

    def test_caveats_non_empty(self):
        with tempfile.TemporaryDirectory() as catalog_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            fname = _KNOWN_CATALOG_FILES[0]["filename"]
            _write_minimal_catalog(os.path.join(catalog_dir, fname), n=30)
            bundle = run_stage8_first_results(
                input_path=os.path.join(catalog_dir, fname),
                output_dir=out_dir,
                name="test_caveats",
                null_repeats=3,
                axis_count=12,
                seed=5,
                plots=False,
                save_normalized=False,
            )
            status = build_stage8_status_summary(bundle)
            self.assertGreater(len(status["caveats"]), 0)
            self.assertGreater(len(status["next_recommended_actions"]), 0)


# ===========================================================================
# 6. Reproducibility
# ===========================================================================

class TestReproducibility(unittest.TestCase):

    def test_seeded_runs_produce_same_tier(self):
        """Two runs with identical seed produce the same signal tier."""
        with tempfile.TemporaryDirectory() as catalog_dir:
            fname = _KNOWN_CATALOG_FILES[0]["filename"]
            cat_path = os.path.join(catalog_dir, fname)
            _write_minimal_catalog(cat_path, n=50)

            results = []
            for _ in range(2):
                with tempfile.TemporaryDirectory() as out_dir:
                    bundle = run_stage8_first_results(
                        input_path=cat_path,
                        output_dir=out_dir,
                        name="test_repro",
                        null_repeats=10,
                        axis_count=12,
                        seed=42,
                        plots=False,
                        save_normalized=False,
                    )
                    tier = bundle["study_results"]["signal_evaluation"]["tier"]
                    results.append(tier)

            self.assertEqual(results[0], results[1])

    def test_seeded_runs_produce_same_axis_score(self):
        """Two runs with identical seed produce the same preferred-axis score."""
        with tempfile.TemporaryDirectory() as catalog_dir:
            fname = _KNOWN_CATALOG_FILES[0]["filename"]
            cat_path = os.path.join(catalog_dir, fname)
            _write_minimal_catalog(cat_path, n=50)

            scores = []
            for _ in range(2):
                with tempfile.TemporaryDirectory() as out_dir:
                    bundle = run_stage8_first_results(
                        input_path=cat_path,
                        output_dir=out_dir,
                        name="test_repro_score",
                        null_repeats=10,
                        axis_count=12,
                        seed=42,
                        plots=False,
                        save_normalized=False,
                    )
                    score = bundle["study_results"]["preferred_axis"]["score"]
                    scores.append(score)

            self.assertAlmostEqual(scores[0], scores[1], places=10)


# ===========================================================================
# 7. CLI graceful failure (--auto-detect with no catalog)
# ===========================================================================

class TestCLIGracefulFailure(unittest.TestCase):

    def test_auto_detect_no_catalog_exits_with_message(self):
        """CLI with --auto-detect exits with rc=1 and a helpful message
        when no real catalog is present in data/real/."""
        cli_path = os.path.join(
            _REPO_ROOT,
            "reality_audit", "data_analysis", "run_stage8_first_results.py"
        )
        # Monkeypatching data/real to an empty tempdir via discover override
        # is complex; instead just invoke the module function directly.
        from reality_audit.data_analysis.run_stage8_first_results import (
            _graceful_no_catalog_error,
        )
        # _graceful_no_catalog_error returns 1 and prints instructions
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = _graceful_no_catalog_error()
        self.assertEqual(rc, 1)
        output = buf.getvalue()
        self.assertIn("No real catalog found", output)
        self.assertIn("data/real", output)

    def test_convenience_script_no_catalog_exits_cleanly(self):
        """Convenience script exits 0 (not error) when no catalog present,
        and prints instructional output."""
        script_path = os.path.join(_REPO_ROOT, "scripts", "run_stage8_first_results.py")
        # Run in a subprocess with data/real/ pointing to empty dir via env override is
        # not easily portable; instead import and monkeypatch discover_real_catalog
        import types
        # Save original and patch
        import reality_audit.data_analysis.stage8_first_results as s8
        original_discover = s8.discover_real_catalog

        def _empty_discover(data_dir="data/real"):
            return {
                "detected_path": None,
                "detected_catalog_label": None,
                "detection_method": "not_found",
                "usable": False,
                "candidates": [],
                "message": "No catalog present (patched).",
            }

        # Patch in scripts module
        import scripts.run_stage8_first_results as script_mod
        script_mod.discover_real_catalog = _empty_discover

        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = script_mod.main()
        finally:
            script_mod.discover_real_catalog = original_discover

        self.assertEqual(rc, 0)
        output = buf.getvalue()
        self.assertIn("No real catalog found", output)


if __name__ == "__main__":
    unittest.main()
