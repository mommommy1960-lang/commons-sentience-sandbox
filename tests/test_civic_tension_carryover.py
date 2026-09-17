import unittest

from commons_sentience_sim.core.identity_pressure import IdentityPressureSystem, ValueTension


class TensionCarryoverSafetyTests(unittest.TestCase):
    def test_mismatched_tension_id_rejected(self):
        with self.assertRaises(ValueError):
            ValueTension.from_dict({
                "tension_id": "wrong",
                "value_a": "trust",
                "value_b": "autonomy",
                "status": "acute",
                "first_seen": 1,
                "last_seen": 1,
                "occurrences": 1,
                "intensity_history": [0.5],
            })

    def test_invalid_tension_status_rejected(self):
        with self.assertRaises(ValueError):
            ValueTension.from_dict({
                "tension_id": ValueTension.make_id("trust", "autonomy"),
                "value_a": "trust",
                "value_b": "autonomy",
                "status": "fake",
            })

    def test_malformed_carryover_is_skipped(self):
        system = IdentityPressureSystem()
        self.assertEqual(system.apply_prior_tensions([{"status": "fake"}]), 0)
        self.assertEqual(system.value_tensions, [])


if __name__ == "__main__":
    unittest.main()
