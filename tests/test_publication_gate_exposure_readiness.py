"""
test_publication_gate_exposure_readiness.py
=============================================
Tests for the new exposure_quality_documented gate and exposure_quality_summary
in the publication gate (Stage 13 / Stage 14).
"""

from __future__ import annotations

import unittest

from reality_audit.data_analysis.exposure_quality_tiers import (
    TIER_NONE,
    TIER_PARTIAL,
    TIER_CANDIDATE,
    TIER_ORDER,
)


# ---------------------------------------------------------------------------
# Minimal helpers (mirrored from test_stage13_publication_gate.py style)
# ---------------------------------------------------------------------------

def _fermi_summary(**kw):
    d = {
        "catalog": "fermi_lat_grb_catalog",
        "event_count": 3000,
        "null_mode": "exposure_corrected",
        "hemi_percentile": 0.85,
        "axis_percentile": 0.89,
        "tier": "weak_anomaly_like_deviation",
        "run_mode": "exploratory",
        "trial_correction_method": "holm",
        "preregistration_hash": "abc123",
    }
    d.update(kw)
    return d


def _swift_summary(**kw):
    d = {
        "catalog": "swift_bat3_grb_catalog",
        "event_count": 872,
        "null_mode": "exposure_corrected",
        "hemi_percentile": 0.63,
        "axis_percentile": 0.57,
        "tier": "no_anomaly_detected",
        "run_mode": "exploratory",
        "trial_correction_method": "holm",
        "preregistration_hash": None,
    }
    d.update(kw)
    return d


def _icecube_summary(**kw):
    d = {
        "catalog": "icecube_hese_events",
        "event_count": 37,
        "null_mode": "isotropic",
        "hemi_percentile": 0.981,
        "axis_percentile": 0.972,
        "tier": "strong_anomaly_like_deviation",
        "run_mode": "exploratory",
        "trial_correction_method": "holm",
        "preregistration_hash": None,
    }
    d.update(kw)
    return d


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


def _run_metadata(extra_fermi=None, extra_swift=None, extra_icecube=None):
    fermi   = _fermi_summary(**(extra_fermi or {}))
    swift   = _swift_summary(**(extra_swift or {}))
    icecube = _icecube_summary(**(extra_icecube or {}))
    return {"catalogs": [fermi, swift, icecube]}


def _evaluate(**kw):
    from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
    rm  = kw.get("run_metadata", _run_metadata())
    cs  = kw.get("comparison_summary", _comparison_summary())
    return evaluate_publication_gate(rm, cs)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGatePassesWithExposureSummary(unittest.TestCase):
    """Gate runs and result contains exposure_quality_summary."""

    def test_gate_passes_with_exposure_summary(self):
        result = _evaluate()
        self.assertIn("exposure_quality_summary", result)
        eq = result["exposure_quality_summary"]
        self.assertIsInstance(eq, dict)
        self.assertIn("worst_exposure_quality_tier", eq)


class TestExposureQualityDocumentedGateExists(unittest.TestCase):
    """New gate 'exposure_quality_documented' is present in gate_results."""

    def test_exposure_quality_documented_gate_exists(self):
        result = _evaluate()
        gate_ids = [g["id"] for g in result.get("gates", [])]
        self.assertIn("exposure_quality_documented", gate_ids)

    def test_gate_has_severity(self):
        result = _evaluate()
        eq_gate = next(
            (g for g in result["gates"] if g["id"] == "exposure_quality_documented"),
            None,
        )
        self.assertIsNotNone(eq_gate)
        self.assertIn("severity", eq_gate)


class TestExposureQualityWorstTierReported(unittest.TestCase):
    """worst_exposure_quality_tier is reported in exposure_quality_summary."""

    def test_exposure_quality_worst_tier_reported(self):
        result = _evaluate()
        eq = result.get("exposure_quality_summary", {})
        worst = eq.get("worst_exposure_quality_tier")
        self.assertIsNotNone(worst)
        self.assertIn(worst, TIER_ORDER)


class TestExposureQualityGateIsRecommendedNotRequired(unittest.TestCase):
    """New gate severity should be 'recommended', not 'required'."""

    def test_exposure_quality_gate_is_recommended_not_required(self):
        result = _evaluate()
        eq_gate = next(
            (g for g in result["gates"] if g["id"] == "exposure_quality_documented"),
            None,
        )
        self.assertIsNotNone(eq_gate)
        self.assertEqual(eq_gate["severity"], "recommended")


class TestGateHandlesMissingExposureQualityGracefully(unittest.TestCase):
    """Gate should run even when catalogs have no exposure_quality_tier field."""

    def test_gate_handles_missing_exposure_quality_gracefully(self):
        # Catalogs with no exposure_quality_tier should still produce a result
        rm = {"catalogs": [_fermi_summary(), _swift_summary()]}
        cs = _comparison_summary()
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        result = evaluate_publication_gate(rm, cs)
        self.assertIn("verdict", result)
        self.assertIn("exposure_quality_summary", result)

    def test_no_crash_on_empty_catalogs(self):
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        result = evaluate_publication_gate({}, _comparison_summary())
        self.assertIn("verdict", result)


class TestWorstTierNoneWhenNoExposureData(unittest.TestCase):
    """When no exposure data for all catalogs, worst_tier = 'none'."""

    def test_worst_tier_none_when_no_exposure_data(self):
        # Use a catalog label that won't be found in calibration products
        rm = {"catalogs": [{"catalog": "unknown_catalog_xyz"}]}
        cs = _comparison_summary()
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        result = evaluate_publication_gate(rm, cs)
        eq = result.get("exposure_quality_summary", {})
        worst = eq.get("worst_exposure_quality_tier", TIER_NONE)
        self.assertEqual(worst, TIER_NONE)


class TestNotesPopulated(unittest.TestCase):
    """exposure_quality_summary.notes is a list."""

    def test_notes_populated(self):
        result = _evaluate()
        eq = result.get("exposure_quality_summary", {})
        notes = eq.get("notes")
        self.assertIsNotNone(notes)
        self.assertIsInstance(notes, list)

    def test_notes_contains_strings(self):
        result = _evaluate()
        eq = result.get("exposure_quality_summary", {})
        notes = eq.get("notes", [])
        for note in notes:
            self.assertIsInstance(note, str)


class TestBackwardCompatExistingCatalogs(unittest.TestCase):
    """Existing catalog dicts without exposure fields still pass required gates."""

    def test_backward_compat_existing_catalogs(self):
        # Original-style catalogs (no exposure_quality_tier field)
        rm = _run_metadata()
        cs = _comparison_summary()
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        result = evaluate_publication_gate(rm, cs)
        # Required gates should still behave as before
        required_fails = result.get("failing_required", [])
        # The existing required gate list should not include the new recommended gate
        self.assertNotIn("exposure_quality_documented", required_fails)

    def test_required_gates_unaffected(self):
        """Required gate list is not changed by adding exposure quality gate."""
        rm = _run_metadata()
        cs = _comparison_summary()
        from reality_audit.data_analysis.publication_gate import evaluate_publication_gate
        result = evaluate_publication_gate(rm, cs)
        required_gate_ids = [
            g["id"] for g in result["gates"] if g["severity"] == "required"
        ]
        # All original required gates should still be present
        for gate_id in [
            "prereg_present",
            "null_model_appropriate",
            "trial_correction_applied",
            "at_least_two_catalogs",
            "replication_status_labeled",
            "systematics_documented",
            "output_artifacts_complete",
            "comparison_memo_present",
            "no_metaphysical_language",
        ]:
            self.assertIn(gate_id, required_gate_ids)


if __name__ == "__main__":
    unittest.main()
