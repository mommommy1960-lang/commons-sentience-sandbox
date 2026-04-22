"""
test_exposure_corrected_nulls.py
=================================
Tests for the Stage 9 exposure-corrected null module.

Tests cover:
  1. build_empirical_exposure_map returns expected structure.
  2. Weights sum to 1 and are all positive.
  3. A catalog with a clear sky-coverage asymmetry produces an asymmetric map.
  4. sample_exposure_weighted_null_events preserves event count.
  5. Seeded null sampling is reproducible.
  6. Exposure-corrected nulls differ from isotropic nulls when coverage is skewed.
  7. generate_exposure_corrected_null_ensemble returns the right number of draws.
  8. describe_exposure_map returns all required keys.
  9. Fallback uniform map when events have no valid RA/Dec.
 10. run_public_anisotropy_study accepts null_mode="exposure_corrected".
 11. run_stage8_first_results accepts null_mode="exposure_corrected".
 12. Memo produced by Stage 8 with exposure_corrected null includes null label.
"""

from __future__ import annotations

import csv
import math
import os
import random
import sys
import tempfile
import unittest

_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.exposure_corrected_nulls import (
    build_empirical_exposure_map,
    sample_exposure_weighted_null_events,
    generate_exposure_corrected_null_ensemble,
    describe_exposure_map,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_events(n: int, seed: int = 7, ra_range=(0, 360), dec_range=(-90, 90)):
    """Return a list of minimal event dicts with RA/Dec."""
    rng = random.Random(seed)
    events = []
    for i in range(n):
        ra  = rng.uniform(*ra_range)
        dec = rng.uniform(*dec_range)
        events.append({
            "event_id":    f"E{i:04d}",
            "ra":          ra,
            "dec":         dec,
            "energy":      1.0,
            "arrival_time": 55000.0 + i,
            "instrument":  "TEST",
        })
    return events


def _make_skewed_events(n: int = 200, seed: int = 13):
    """Return events heavily concentrated in the northern hemisphere."""
    rng = random.Random(seed)
    events = []
    for i in range(n):
        ra  = rng.uniform(0.0, 360.0)
        # 90% of events in dec 0–90 (north), 10% in dec -90–0 (south)
        if rng.random() < 0.9:
            dec = rng.uniform(0.0, 90.0)
        else:
            dec = rng.uniform(-90.0, 0.0)
        events.append({
            "event_id":    f"SK{i:04d}",
            "ra":          ra,
            "dec":         dec,
            "energy":      1.0,
            "arrival_time": 55000.0,
            "instrument":  "TEST",
        })
    return events


def _write_catalog_csv(path: str, events):
    """Write events list to CSV."""
    fieldnames = ["event_id", "ra", "dec", "energy", "arrival_time", "instrument"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for e in events:
            writer.writerow(e)


# ===========================================================================
# 1. build_empirical_exposure_map — structure
# ===========================================================================

class TestBuildExposureMap(unittest.TestCase):

    def setUp(self):
        self.events = _make_events(100, seed=1)
        self.emap   = build_empirical_exposure_map(self.events, ra_bins=12, dec_bins=6)

    def test_required_keys(self):
        for key in ("ra_bins", "dec_bins", "weights", "cell_counts",
                    "n_events_used", "ra_edges", "dec_edges",
                    "description", "limitations"):
            self.assertIn(key, self.emap, f"Missing key: {key}")

    def test_correct_bin_counts(self):
        self.assertEqual(self.emap["ra_bins"],  12)
        self.assertEqual(self.emap["dec_bins"],  6)

    def test_weights_length(self):
        self.assertEqual(len(self.emap["weights"]),     12 * 6)
        self.assertEqual(len(self.emap["cell_counts"]), 12 * 6)

    def test_edges_length(self):
        self.assertEqual(len(self.emap["ra_edges"]),  12 + 1)
        self.assertEqual(len(self.emap["dec_edges"]),  6 + 1)

    def test_n_events_used(self):
        self.assertEqual(self.emap["n_events_used"], 100)

    def test_ra_edges_range(self):
        self.assertAlmostEqual(self.emap["ra_edges"][0],   0.0)
        self.assertAlmostEqual(self.emap["ra_edges"][-1], 360.0)

    def test_dec_edges_range(self):
        self.assertAlmostEqual(self.emap["dec_edges"][0],   -90.0)
        self.assertAlmostEqual(self.emap["dec_edges"][-1],   90.0)


# ===========================================================================
# 2. Weights sum to 1 and all positive
# ===========================================================================

class TestWeightProperties(unittest.TestCase):

    def test_weights_sum_to_one(self):
        events = _make_events(50, seed=2)
        emap   = build_empirical_exposure_map(events)
        self.assertAlmostEqual(sum(emap["weights"]), 1.0, places=10)

    def test_weights_all_positive(self):
        events = _make_events(50, seed=3)
        emap   = build_empirical_exposure_map(events)
        for w in emap["weights"]:
            self.assertGreater(w, 0.0)


# ===========================================================================
# 3. Skewed coverage → asymmetric map
# ===========================================================================

class TestAsymmetricMap(unittest.TestCase):

    def test_northern_concentration(self):
        """Events concentrated in north → northern half cells have higher weight."""
        events = _make_skewed_events(300, seed=5)
        emap   = build_empirical_exposure_map(events, ra_bins=4, dec_bins=4)
        # The flat weights array is laid out as dec_idx * ra_bins + ra_idx.
        # dec_idx 0 = dec -90..-45, idx 1 = -45..0, idx 2 = 0..45, idx 3 = 45..90.
        n_ra = emap["ra_bins"]
        south_weight = sum(emap["weights"][i * n_ra + j]
                           for i in range(2) for j in range(n_ra))
        north_weight = sum(emap["weights"][i * n_ra + j]
                           for i in range(2, 4) for j in range(n_ra))
        self.assertGreater(north_weight, south_weight)


# ===========================================================================
# 4. sample_exposure_weighted_null_events — event count preserved
# ===========================================================================

class TestSampleNullEvents(unittest.TestCase):

    def test_same_event_count(self):
        events = _make_events(80, seed=6)
        emap   = build_empirical_exposure_map(events)
        null   = sample_exposure_weighted_null_events(events, emap, seed=42)
        self.assertEqual(len(null), len(events))

    def test_ra_dec_replaced(self):
        """Null RA/Dec should differ from originals (with overwhelming probability)."""
        events = _make_events(100, seed=7)
        emap   = build_empirical_exposure_map(events)
        null   = sample_exposure_weighted_null_events(events, emap, seed=99)
        orig_ra  = set(round(float(e["ra"]),  4) for e in events)
        null_ra  = set(round(float(e["ra"]),  4) for e in null)
        # Almost certainly some positions differ
        self.assertFalse(orig_ra == null_ra)

    def test_non_position_fields_preserved(self):
        """Non-spatial fields (energy, instrument) are preserved from some orig event."""
        events = _make_events(50, seed=8)
        emap   = build_empirical_exposure_map(events)
        null   = sample_exposure_weighted_null_events(events, emap, seed=1)
        orig_energies = {e["energy"] for e in events}
        for ne in null:
            # energy must come from the original pool
            self.assertIn(ne["energy"], orig_energies)


# ===========================================================================
# 5. Seeded runs are reproducible
# ===========================================================================

class TestReproducibility(unittest.TestCase):

    def test_same_seed_same_ra(self):
        events = _make_events(60, seed=9)
        emap   = build_empirical_exposure_map(events)
        null_a = sample_exposure_weighted_null_events(events, emap, seed=123)
        null_b = sample_exposure_weighted_null_events(events, emap, seed=123)
        ra_a   = [e["ra"]  for e in null_a]
        ra_b   = [e["ra"]  for e in null_b]
        self.assertEqual(ra_a, ra_b)

    def test_different_seed_different_ra(self):
        events = _make_events(60, seed=10)
        emap   = build_empirical_exposure_map(events)
        null_a = sample_exposure_weighted_null_events(events, emap, seed=1)
        null_b = sample_exposure_weighted_null_events(events, emap, seed=2)
        ra_a   = [e["ra"]  for e in null_a]
        ra_b   = [e["ra"]  for e in null_b]
        self.assertNotEqual(ra_a, ra_b)


# ===========================================================================
# 6. Exposure-corrected nulls differ from isotropic for skewed coverage
# ===========================================================================

class TestCorrectedVsIsotropicNulls(unittest.TestCase):

    def test_dec_distribution_differs(self):
        """A skewed catalog → corrected nulls should also be skewed, isotropic less so."""
        from reality_audit.data_analysis.simulation_signature_analysis import (
            generate_null_events,
        )
        events = _make_skewed_events(200, seed=11)
        emap   = build_empirical_exposure_map(events)

        corr_null = sample_exposure_weighted_null_events(events, emap, seed=7)
        iso_null  = generate_null_events(events, mode="isotropic", seed=7)

        # Average Dec for corrected null should be > average Dec for isotropic null
        avg_dec_corr = sum(float(e["dec"]) for e in corr_null) / len(corr_null)
        avg_dec_iso  = sum(float(e["dec"]) for e in iso_null)  / len(iso_null)
        # Corrected null absorbs the northern bias, so should have higher avg Dec
        self.assertGreater(avg_dec_corr, avg_dec_iso)


# ===========================================================================
# 7. generate_exposure_corrected_null_ensemble — count and shape
# ===========================================================================

class TestGenerateEnsemble(unittest.TestCase):

    def test_ensemble_length(self):
        events = _make_events(50, seed=12)
        ensemble, emap = generate_exposure_corrected_null_ensemble(
            events, repeats=5, seed=42, config={})
        self.assertEqual(len(ensemble), 5)

    def test_each_draw_length(self):
        events = _make_events(50, seed=13)
        ensemble, emap = generate_exposure_corrected_null_ensemble(
            events, repeats=4, seed=1, config={})
        for draw in ensemble:
            self.assertEqual(len(draw), len(events))

    def test_exposure_map_returned(self):
        events = _make_events(50, seed=14)
        ensemble, emap = generate_exposure_corrected_null_ensemble(
            events, repeats=3, seed=0, config={})
        self.assertIn("weights", emap)
        self.assertIn("ra_bins", emap)


# ===========================================================================
# 8. describe_exposure_map — required keys
# ===========================================================================

class TestDescribeExposureMap(unittest.TestCase):

    def test_required_keys(self):
        events = _make_events(80, seed=15)
        emap   = build_empirical_exposure_map(events)
        desc   = describe_exposure_map(emap)
        for key in ("ra_bins", "dec_bins", "total_cells", "n_events_used",
                    "n_occupied_cells", "n_empty_cells", "occupancy_fraction",
                    "max_cell_weight", "min_cell_weight", "description", "limitations"):
            self.assertIn(key, desc, f"Missing key: {key}")

    def test_total_cells_consistent(self):
        events = _make_events(80, seed=16)
        emap   = build_empirical_exposure_map(events, ra_bins=6, dec_bins=4)
        desc   = describe_exposure_map(emap)
        self.assertEqual(desc["total_cells"], 6 * 4)

    def test_occupancy_fraction_range(self):
        events = _make_events(80, seed=17)
        emap   = build_empirical_exposure_map(events)
        desc   = describe_exposure_map(emap)
        self.assertGreaterEqual(desc["occupancy_fraction"], 0.0)
        self.assertLessEqual(   desc["occupancy_fraction"], 1.0)


# ===========================================================================
# 9. Fallback to uniform when no valid RA/Dec
# ===========================================================================

class TestFallbackUniform(unittest.TestCase):

    def test_no_valid_radec_uniform_fallback(self):
        events = [{"event_id": "X", "energy": 1.0, "arrival_time": 55000.0}] * 10
        emap   = build_empirical_exposure_map(events)
        self.assertEqual(emap["n_events_used"], 0)
        # All weights should be equal (uniform)
        w = emap["weights"]
        self.assertAlmostEqual(max(w) - min(w), 0.0, places=10)


# ===========================================================================
# 10. run_public_anisotropy_study supports null_mode="exposure_corrected"
# ===========================================================================

class TestPublicAnisotropyStudyNullMode(unittest.TestCase):

    def _make_event_list(self, n=50, seed=20):
        return _make_events(n, seed=seed)

    def test_exposure_corrected_mode_runs(self):
        from reality_audit.data_analysis.public_anisotropy_study import (
            run_public_anisotropy_study,
        )
        events = self._make_event_list(60, seed=21)
        result = run_public_anisotropy_study(
            events,
            config={"null_repeats": 5, "axis_count": 6, "seed": 5},
            null_mode="exposure_corrected",
        )
        self.assertIn("null_comparison", result)
        self.assertEqual(result["null_comparison"]["null_mode"], "exposure_corrected")
        model = result.get("run_metadata", {}).get("exposure_model", {})
        self.assertEqual(model.get("model_family"), "empirical_exposure_proxy")
        self.assertEqual(model.get("stage16_calibration_status"), "empirical_proxy_baseline")

    def test_isotropic_mode_still_works(self):
        from reality_audit.data_analysis.public_anisotropy_study import (
            run_public_anisotropy_study,
        )
        events = self._make_event_list(60, seed=22)
        result = run_public_anisotropy_study(
            events,
            config={"null_repeats": 5, "axis_count": 6, "seed": 5},
            null_mode="isotropic",
        )
        self.assertEqual(result["null_comparison"]["null_mode"], "isotropic")
        model = result.get("run_metadata", {}).get("exposure_model", {})
        self.assertEqual(model.get("model_family"), "isotropic_baseline")

    def test_invalid_null_mode_raises(self):
        from reality_audit.data_analysis.public_anisotropy_study import (
            run_public_anisotropy_study,
        )
        events = self._make_event_list(60, seed=23)
        with self.assertRaises(ValueError):
            run_public_anisotropy_study(
                events,
                config={"null_repeats": 3, "axis_count": 4, "seed": 1},
                null_mode="bogus_mode",
            )


# ===========================================================================
# 11. run_stage8_first_results accepts null_mode="exposure_corrected"
# ===========================================================================

class TestStage8WithExposureCorrected(unittest.TestCase):

    def _write_catalog(self, path, n=50):
        events = _make_events(n, seed=30)
        _write_catalog_csv(path, events)

    def test_stage8_runs_with_exposure_corrected_null(self):
        from reality_audit.data_analysis.stage8_first_results import (
            run_stage8_first_results,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            cat_path = os.path.join(tmpdir, "fermi_lat_grb_catalog.csv")
            self._write_catalog(cat_path)
            result = run_stage8_first_results(
                input_path=cat_path,
                name="test_stage9",
                output_dir=tmpdir,
                null_repeats=5,
                axis_count=6,
                seed=1,
                null_mode="exposure_corrected",
                plots=False,
                save_normalized=False,
            )
            self.assertIn("null_mode", result["run_metadata"])
            self.assertEqual(result["run_metadata"]["null_mode"], "exposure_corrected")

    def test_stage8_runs_with_isotropic_null(self):
        from reality_audit.data_analysis.stage8_first_results import (
            run_stage8_first_results,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            cat_path = os.path.join(tmpdir, "fermi_lat_grb_catalog.csv")
            self._write_catalog(cat_path)
            result = run_stage8_first_results(
                input_path=cat_path,
                name="test_stage8_iso",
                output_dir=tmpdir,
                null_repeats=5,
                axis_count=6,
                seed=1,
                null_mode="isotropic",
                plots=False,
                save_normalized=False,
            )
            self.assertEqual(result["run_metadata"]["null_mode"], "isotropic")


# ===========================================================================
# 12. Memo includes null label for exposure_corrected
# ===========================================================================

class TestMemoNullLabel(unittest.TestCase):

    def test_memo_mentions_exposure_corrected(self):
        from reality_audit.data_analysis.stage8_first_results import (
            run_stage8_first_results,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            cat_path = os.path.join(tmpdir, "fermi_lat_grb_catalog.csv")
            events = _make_events(50, seed=40)
            _write_catalog_csv(cat_path, events)
            run_stage8_first_results(
                input_path=cat_path,
                name="memo_test",
                output_dir=tmpdir,
                null_repeats=5,
                axis_count=6,
                seed=2,
                null_mode="exposure_corrected",
                plots=False,
                save_normalized=False,
            )
            memo_path = os.path.join(tmpdir, "memo_test_memo.md")
            self.assertTrue(os.path.exists(memo_path))
            with open(memo_path) as f:
                content = f.read()
            self.assertIn("exposure", content.lower())


if __name__ == "__main__":
    unittest.main()
