import math
import unittest

from tools.aquashield_trade_study import AquaInputs, calculate, cylindrical_water_mass
from tools.care_routing_sim import IncidentCard, validate_card


class AquaShieldTests(unittest.TestCase):
    def test_baseline_calculations(self):
        result = calculate(AquaInputs())
        self.assertAlmostEqual(result["shield_mass_kg"], 1000.0)
        self.assertAlmostEqual(result["areal_density_kg_m2"], 100.0)
        self.assertAlmostEqual(result["drag_force_n"], 12.5)
        self.assertAlmostEqual(result["electrical_power_w"], 666.6666667)
        self.assertAlmostEqual(result["drain_time_s"], 20.0)

    def test_full_room_scale(self):
        self.assertAlmostEqual(cylindrical_water_mass(1.5, 3.0), math.pi * 6.75 * 1000)

    def test_rejects_impossible_efficiency(self):
        with self.assertRaises(ValueError):
            calculate(AquaInputs(pump_efficiency=0))


class CareTests(unittest.TestCase):
    def test_complete_card_only_allows_human_review(self):
        card = IncidentCard("A", "medical", "one", "unknown", ("audio:1",), 0.8)
        result = validate_card(card)
        self.assertTrue(result["eligible_for_human_prealert_review"])
        self.assertFalse(result["autonomous_dispatch_allowed"])

    def test_missing_location_blocks_prealert(self):
        card = IncidentCard(None, "fire", "unknown", "smoke", ("text:1",), 0.9)
        result = validate_card(card)
        self.assertIn("location", result["missing"])
        self.assertFalse(result["eligible_for_human_prealert_review"])

    def test_untraceable_card_blocks_prealert(self):
        card = IncidentCard("A", "fire", "one", "smoke", (), 0.9)
        self.assertFalse(validate_card(card)["eligible_for_human_prealert_review"])


if __name__ == "__main__":
    unittest.main()

