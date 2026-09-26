import unittest

from commons_sentience_sim.core.identity_pressure import (
    IdentityPressureSystem,
    ValueTension,
)


class IdentityResolutionSafetyTests(unittest.TestCase):
    def test_resolution_requires_verification_reference(self):
        system = IdentityPressureSystem()
        tension = ValueTension(
            tension_id="t1",
            value_a="trust",
            value_b="autonomy",
            status="acute",
            occurrences=1,
            intensity_history=[0.5],
        )
        system.value_tensions.append(tension)
        self.assertFalse(system.resolve_tension("t1", "claimed fixed"))
        self.assertEqual(tension.status, "acute")

    def test_verified_resolution_is_recorded(self):
        system = IdentityPressureSystem()
        tension = ValueTension(
            tension_id="t1",
            value_a="trust",
            value_b="autonomy",
            status="acute",
            occurrences=1,
            intensity_history=[0.5],
        )
        system.value_tensions.append(tension)
        self.assertTrue(system.resolve_tension("t1", "reviewed", "event-1"))
        self.assertEqual(tension.status, "resolved")


if __name__ == "__main__":
    unittest.main()
