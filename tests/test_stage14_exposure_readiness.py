"""
test_stage14_exposure_readiness.py
=====================================
Tests for Stage 14 exposure readiness:
  - mission_calibration_loader.build_exposure_quality_summary_for_manifest
  - time_exposure_loader.load_exposure_window / get_exposure_quality_for_catalog
"""

from __future__ import annotations

import unittest

from reality_audit.data_analysis.exposure_quality_tiers import (
    TIER_NONE,
    TIER_PARTIAL,
    TIER_CANDIDATE,
    TIER_ORDER,
)


class TestBuildExposureQualitySummaryReturnsDict(unittest.TestCase):
    """mission_calibration_loader.build_exposure_quality_summary_for_manifest returns valid dict."""

    def setUp(self):
        from reality_audit.data_analysis.mission_calibration_loader import (
            build_exposure_quality_summary_for_manifest,
        )
        self.summary = build_exposure_quality_summary_for_manifest()

    def test_build_exposure_quality_summary_returns_dict(self):
        self.assertIsInstance(self.summary, dict)

    def test_summary_is_non_empty(self):
        self.assertGreater(len(self.summary), 0)


class TestAllThreeCatalogsPresent(unittest.TestCase):
    """fermi, swift, icecube all have tier entries."""

    def setUp(self):
        from reality_audit.data_analysis.mission_calibration_loader import (
            build_exposure_quality_summary_for_manifest,
        )
        self.summary = build_exposure_quality_summary_for_manifest()

    def test_all_three_catalogs_present(self):
        tier_by = self.summary.get("exposure_quality_tier_by_catalog", {})
        self.assertIn("fermi", tier_by)
        self.assertIn("swift", tier_by)
        self.assertIn("icecube", tier_by)

    def test_all_catalogs_have_string_tier(self):
        tier_by = self.summary.get("exposure_quality_tier_by_catalog", {})
        for label, tier in tier_by.items():
            self.assertIsInstance(tier, str, f"{label} tier is not a string")
            self.assertIn(tier, TIER_ORDER)


class TestIcecubeTierIsNone(unittest.TestCase):
    """IceCube tier should be TIER_NONE (no exposure data)."""

    def setUp(self):
        from reality_audit.data_analysis.mission_calibration_loader import (
            build_exposure_quality_summary_for_manifest,
        )
        self.summary = build_exposure_quality_summary_for_manifest()

    def test_icecube_tier_is_none(self):
        tier_by = self.summary.get("exposure_quality_tier_by_catalog", {})
        self.assertEqual(tier_by.get("icecube"), TIER_NONE)


class TestFermiTierIsAtLeastPartial(unittest.TestCase):
    """Fermi is at least partial_data_derived."""

    def setUp(self):
        from reality_audit.data_analysis.mission_calibration_loader import (
            build_exposure_quality_summary_for_manifest,
        )
        self.summary = build_exposure_quality_summary_for_manifest()

    def test_fermi_tier_is_at_least_partial(self):
        tier_by = self.summary.get("exposure_quality_tier_by_catalog", {})
        fermi_tier = tier_by.get("fermi", TIER_NONE)
        self.assertGreaterEqual(
            TIER_ORDER.index(fermi_tier),
            TIER_ORDER.index(TIER_PARTIAL),
            f"Expected fermi tier >= partial_data_derived, got {fermi_tier}",
        )


class TestManifestFieldsPresent(unittest.TestCase):
    """All required manifest keys present."""

    REQUIRED_KEYS = [
        "exposure_quality_tier_by_catalog",
        "exposure_quality_requirements_met_by_catalog",
        "exposure_quality_missing_requirements_by_catalog",
        "exposure_quality_evidence_summary_by_catalog",
        "worst_exposure_quality_tier",
        "any_catalog_at_analysis_candidate",
        "confirmatory_exposure_quality_readiness",
        "confirmatory_exposure_quality_readiness_reason",
    ]

    def setUp(self):
        from reality_audit.data_analysis.mission_calibration_loader import (
            build_exposure_quality_summary_for_manifest,
        )
        self.summary = build_exposure_quality_summary_for_manifest()

    def test_manifest_fields_present(self):
        for key in self.REQUIRED_KEYS:
            self.assertIn(key, self.summary, f"Missing key: {key}")


class TestWorstTierIsNoneOrPartial(unittest.TestCase):
    """Worst tier should be none (IceCube has no exposure) or partial (Fermi/Swift)."""

    def setUp(self):
        from reality_audit.data_analysis.mission_calibration_loader import (
            build_exposure_quality_summary_for_manifest,
        )
        self.summary = build_exposure_quality_summary_for_manifest()

    def test_worst_tier_is_none_or_partial(self):
        worst = self.summary.get("worst_exposure_quality_tier")
        self.assertIn(worst, [TIER_NONE, TIER_PARTIAL])


class TestConfirmatoryReadinessNotReady(unittest.TestCase):
    """confirmatory_exposure_quality_readiness is 'not_ready' since IceCube=none."""

    def setUp(self):
        from reality_audit.data_analysis.mission_calibration_loader import (
            build_exposure_quality_summary_for_manifest,
        )
        self.summary = build_exposure_quality_summary_for_manifest()

    def test_confirmatory_readiness_not_ready(self):
        readiness = self.summary.get("confirmatory_exposure_quality_readiness")
        # IceCube is TIER_NONE which is < analysis_candidate, so should be not_ready
        self.assertEqual(readiness, "not_ready")

    def test_readiness_reason_is_string(self):
        reason = self.summary.get("confirmatory_exposure_quality_readiness_reason", "")
        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 0)


class TestLoadExposureWindowFermiV1(unittest.TestCase):
    """time_exposure_loader loads fermi v1 ok."""

    def setUp(self):
        from reality_audit.data_analysis.time_exposure_loader import load_exposure_window
        self.result = load_exposure_window("fermi", "v1")

    def test_load_exposure_window_fermi_v1(self):
        self.assertEqual(self.result["load_status"], "ok")

    def test_fermi_v1_has_records(self):
        self.assertGreater(len(self.result["records"]), 0)

    def test_fermi_v1_catalog_label_correct(self):
        self.assertEqual(self.result["catalog_label"], "fermi")

    def test_fermi_v1_has_provenance(self):
        self.assertIsInstance(self.result["provenance"], dict)
        self.assertIn("source_type", self.result["provenance"])

    def test_fermi_v1_tier_at_least_partial(self):
        tier = self.result.get("exposure_quality_tier", TIER_NONE)
        self.assertGreaterEqual(
            TIER_ORDER.index(tier),
            TIER_ORDER.index(TIER_PARTIAL),
        )


class TestLoadExposureWindowMissingReturnsNotFound(unittest.TestCase):
    """Missing file → load_status=file_not_found."""

    def test_load_exposure_window_missing_returns_not_found(self):
        from reality_audit.data_analysis.time_exposure_loader import load_exposure_window
        result = load_exposure_window("fermi", "v99_nonexistent")
        self.assertEqual(result["load_status"], "file_not_found")

    def test_missing_file_tier_is_none(self):
        from reality_audit.data_analysis.time_exposure_loader import load_exposure_window
        result = load_exposure_window("fermi", "v99_nonexistent")
        self.assertEqual(result["exposure_quality_tier"], TIER_NONE)

    def test_missing_records_is_empty_list(self):
        from reality_audit.data_analysis.time_exposure_loader import load_exposure_window
        result = load_exposure_window("fermi", "v99_nonexistent")
        self.assertEqual(result["records"], [])


class TestGetExposureQualityForCatalogIcecube(unittest.TestCase):
    """icecube → TIER_NONE via get_exposure_quality_for_catalog."""

    def setUp(self):
        from reality_audit.data_analysis.time_exposure_loader import (
            get_exposure_quality_for_catalog,
        )
        self.result = get_exposure_quality_for_catalog("icecube")

    def test_get_exposure_quality_for_catalog_icecube(self):
        self.assertEqual(self.result["exposure_quality_tier"], TIER_NONE)

    def test_icecube_quality_result_has_catalog_label(self):
        self.assertEqual(self.result["catalog_label"], "icecube")

    def test_icecube_quality_result_has_load_status(self):
        self.assertIn("load_status", self.result)

    def test_icecube_quality_result_has_required_keys(self):
        for key in [
            "exposure_quality_tier",
            "exposure_quality_requirements_met",
            "exposure_quality_missing_requirements",
            "exposure_quality_evidence_summary",
            "load_status",
        ]:
            self.assertIn(key, self.result)


if __name__ == "__main__":
    unittest.main()
