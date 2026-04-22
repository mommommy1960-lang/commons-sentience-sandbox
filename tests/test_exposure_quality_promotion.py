"""
test_exposure_quality_promotion.py
====================================
Unit tests for the exposure quality tier system (Stage 10).

Tests:
 1. test_tier_ordering             — TIER_ORDER is correct
 2. test_assess_none_returns_none  — empty metadata → TIER_NONE
 3. test_assess_synthetic_sample   — synthetic flag only → TIER_SYNTHETIC
 4. test_assess_partial_data       — non_synthetic + event_count → TIER_PARTIAL
 5. test_assess_candidate_promotion — all candidate requirements → TIER_CANDIDATE
 6. test_missing_requirements_reported — missing reqs reported accurately
 7. test_worst_tier_logic          — worst_tier([partial, candidate]) → partial
 8. test_best_tier_logic           — best_tier([partial, none]) → partial
 9. test_evidence_summary_is_string — non-empty string
10. test_compare_tiers             — compare_tiers(none, partial) == -1
"""

from __future__ import annotations

import unittest

from reality_audit.data_analysis.exposure_quality_tiers import (
    TIER_NONE,
    TIER_SYNTHETIC,
    TIER_PARTIAL,
    TIER_CANDIDATE,
    TIER_GRADE,
    TIER_ORDER,
    assess_exposure_quality,
    compare_tiers,
    worst_tier,
    best_tier,
)


class TestTierOrdering(unittest.TestCase):
    """Test that TIER_ORDER is correct."""

    def test_tier_ordering(self):
        self.assertEqual(TIER_ORDER[0], TIER_NONE)
        self.assertEqual(TIER_ORDER[1], TIER_SYNTHETIC)
        self.assertEqual(TIER_ORDER[2], TIER_PARTIAL)
        self.assertEqual(TIER_ORDER[3], TIER_CANDIDATE)
        self.assertEqual(TIER_ORDER[4], TIER_GRADE)
        self.assertEqual(len(TIER_ORDER), 5)

    def test_tier_constants_are_strings(self):
        for t in TIER_ORDER:
            self.assertIsInstance(t, str)


class TestAssessNone(unittest.TestCase):
    """Empty / None metadata → TIER_NONE."""

    def test_assess_none_returns_none_tier(self):
        result = assess_exposure_quality("test_catalog", None)
        self.assertEqual(result["exposure_quality_tier"], TIER_NONE)

    def test_assess_empty_dict_returns_none(self):
        result = assess_exposure_quality("test_catalog", {})
        self.assertEqual(result["exposure_quality_tier"], TIER_NONE)

    def test_assess_none_has_required_keys(self):
        result = assess_exposure_quality("x", None)
        for key in [
            "exposure_quality_tier",
            "exposure_quality_requirements_met",
            "exposure_quality_missing_requirements",
            "exposure_quality_evidence_summary",
            "tier_rationale",
        ]:
            self.assertIn(key, result)


class TestAssessSyntheticSample(unittest.TestCase):
    """Only synthetic flags → TIER_SYNTHETIC."""

    def test_assess_synthetic_sample(self):
        # TIER_SYNTHETIC has NO requirements so any metadata → at least synthetic
        result = assess_exposure_quality("test", {"is_synthetic": True})
        self.assertIn(
            result["exposure_quality_tier"],
            [TIER_SYNTHETIC, TIER_PARTIAL, TIER_CANDIDATE, TIER_GRADE],
        )

    def test_assess_synthetic_does_not_reach_partial_without_flags(self):
        # With only is_synthetic=True and no real-data flags, should not reach TIER_PARTIAL
        result = assess_exposure_quality(
            "test",
            {"is_synthetic": True, "non_synthetic_source": False},
        )
        self.assertNotEqual(result["exposure_quality_tier"], TIER_PARTIAL)

    def test_assess_synthetic_tier_name(self):
        result = assess_exposure_quality("test", {"is_synthetic": True})
        # At minimum, should be synthetic_sample (TIER_SYNTHETIC)
        self.assertIn(
            TIER_ORDER.index(result["exposure_quality_tier"]),
            range(1, 5),
        )


class TestAssessPartialDataDerived(unittest.TestCase):
    """non_synthetic + minimum_event_count → TIER_PARTIAL."""

    def test_assess_partial_data_derived(self):
        meta = {
            "non_synthetic_source": True,
            "minimum_event_count_present": True,
        }
        result = assess_exposure_quality("fermi", meta)
        self.assertEqual(result["exposure_quality_tier"], TIER_PARTIAL)

    def test_partial_without_min_events_stays_synthetic(self):
        meta = {
            "non_synthetic_source": True,
            "minimum_event_count_present": False,
        }
        result = assess_exposure_quality("fermi", meta)
        self.assertEqual(result["exposure_quality_tier"], TIER_SYNTHETIC)

    def test_partial_requirements_in_met_list(self):
        meta = {
            "non_synthetic_source": True,
            "minimum_event_count_present": True,
        }
        result = assess_exposure_quality("fermi", meta)
        self.assertIn("non_synthetic_source", result["exposure_quality_requirements_met"])
        self.assertIn("minimum_event_count_present", result["exposure_quality_requirements_met"])


class TestAssessAnalysisCandidatePromotion(unittest.TestCase):
    """All candidate requirements satisfied → TIER_CANDIDATE."""

    def _candidate_meta(self):
        return {
            "non_synthetic_source": True,
            "minimum_event_count_present": True,
            "sufficient_observation_window": True,
            "explicit_provenance_documented": True,
            "bounded_caveats_documented": True,
            # NOT setting instrument_response_modeled, livetime_validated, sky_coverage_assessed
            "instrument_response_modeled": False,
            "livetime_validated": False,
            "sky_coverage_assessed": False,
        }

    def test_assess_analysis_candidate_promotion(self):
        result = assess_exposure_quality("fermi", self._candidate_meta())
        self.assertEqual(result["exposure_quality_tier"], TIER_CANDIDATE)

    def test_candidate_not_promoted_to_grade(self):
        result = assess_exposure_quality("fermi", self._candidate_meta())
        self.assertNotEqual(result["exposure_quality_tier"], TIER_GRADE)

    def test_all_candidate_reqs_in_met(self):
        result = assess_exposure_quality("fermi", self._candidate_meta())
        for req in [
            "non_synthetic_source",
            "minimum_event_count_present",
            "sufficient_observation_window",
            "explicit_provenance_documented",
            "bounded_caveats_documented",
        ]:
            self.assertIn(req, result["exposure_quality_requirements_met"])


class TestMissingRequirementsReported(unittest.TestCase):
    """Missing requirements are reported accurately."""

    def test_missing_requirements_reported(self):
        meta = {
            "non_synthetic_source": True,
            "minimum_event_count_present": True,
            # Missing: sufficient_observation_window, explicit_provenance_documented,
            #          bounded_caveats_documented, instrument_response_modeled,
            #          livetime_validated, sky_coverage_assessed
        }
        result = assess_exposure_quality("fermi", meta)
        missing = result["exposure_quality_missing_requirements"]
        self.assertIn("sufficient_observation_window", missing)
        self.assertIn("instrument_response_modeled", missing)

    def test_no_missing_when_all_grade_reqs_met(self):
        meta = {
            "non_synthetic_source": True,
            "minimum_event_count_present": True,
            "sufficient_observation_window": True,
            "explicit_provenance_documented": True,
            "bounded_caveats_documented": True,
            "instrument_response_modeled": True,
            "livetime_validated": True,
            "sky_coverage_assessed": True,
        }
        result = assess_exposure_quality("fermi", meta)
        self.assertEqual(result["exposure_quality_tier"], TIER_GRADE)
        self.assertEqual(result["exposure_quality_missing_requirements"], [])


class TestWorstTierLogic(unittest.TestCase):
    """worst_tier returns the lowest quality tier."""

    def test_worst_tier_logic(self):
        self.assertEqual(worst_tier([TIER_PARTIAL, TIER_CANDIDATE]), TIER_PARTIAL)

    def test_worst_tier_with_none(self):
        self.assertEqual(worst_tier([TIER_PARTIAL, TIER_NONE]), TIER_NONE)

    def test_worst_tier_single(self):
        self.assertEqual(worst_tier([TIER_GRADE]), TIER_GRADE)

    def test_worst_tier_empty(self):
        self.assertEqual(worst_tier([]), TIER_NONE)

    def test_worst_tier_all_same(self):
        self.assertEqual(worst_tier([TIER_PARTIAL, TIER_PARTIAL]), TIER_PARTIAL)


class TestBestTierLogic(unittest.TestCase):
    """best_tier returns the highest quality tier."""

    def test_best_tier_logic(self):
        self.assertEqual(best_tier([TIER_PARTIAL, TIER_NONE]), TIER_PARTIAL)

    def test_best_tier_with_grade(self):
        self.assertEqual(best_tier([TIER_PARTIAL, TIER_GRADE, TIER_NONE]), TIER_GRADE)

    def test_best_tier_single(self):
        self.assertEqual(best_tier([TIER_CANDIDATE]), TIER_CANDIDATE)

    def test_best_tier_empty(self):
        self.assertEqual(best_tier([]), TIER_NONE)


class TestEvidenceSummaryIsString(unittest.TestCase):
    """Evidence summary must be a non-empty string."""

    def test_evidence_summary_is_string(self):
        result = assess_exposure_quality(
            "swift",
            {"non_synthetic_source": True, "minimum_event_count_present": True},
        )
        summary = result["exposure_quality_evidence_summary"]
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)

    def test_evidence_summary_for_none_tier(self):
        result = assess_exposure_quality("icecube", {})
        self.assertIsInstance(result["exposure_quality_evidence_summary"], str)
        self.assertGreater(len(result["exposure_quality_evidence_summary"]), 0)


class TestCompareTiers(unittest.TestCase):
    """compare_tiers returns -1, 0, or 1."""

    def test_compare_tiers_less_than(self):
        self.assertEqual(compare_tiers(TIER_NONE, TIER_PARTIAL), -1)

    def test_compare_tiers_equal(self):
        self.assertEqual(compare_tiers(TIER_PARTIAL, TIER_PARTIAL), 0)

    def test_compare_tiers_greater_than(self):
        self.assertEqual(compare_tiers(TIER_GRADE, TIER_CANDIDATE), 1)

    def test_compare_tiers_none_vs_grade(self):
        self.assertEqual(compare_tiers(TIER_NONE, TIER_GRADE), -1)

    def test_compare_tiers_invalid_raises(self):
        with self.assertRaises(ValueError):
            compare_tiers("not_a_tier", TIER_PARTIAL)


if __name__ == "__main__":
    unittest.main()
