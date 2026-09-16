import unittest

from commons_sentience_sim.core.narrative_identity import (
    ContinuityRuptureEvent,
    NarrativeIdentitySystem,
)


class RuptureRepairSafetyTests(unittest.TestCase):
    def test_repair_requires_verification_reference(self):
        system = NarrativeIdentitySystem(agent_name="Sentinel")
        rupture = ContinuityRuptureEvent(rupture_id="r1")
        system.continuity_rupture_events.append(rupture)
        self.assertFalse(system.repair_rupture("r1", 1, "claimed repair"))
        self.assertFalse(rupture.repaired)

    def test_verified_repair_is_recorded(self):
        system = NarrativeIdentitySystem(agent_name="Sentinel")
        rupture = ContinuityRuptureEvent(rupture_id="r1")
        system.continuity_rupture_events.append(rupture)
        self.assertTrue(system.repair_rupture("r1", 1, "reviewed repair", "event-1"))
        self.assertTrue(rupture.repaired)
        self.assertIn("verified:event-1", rupture.repair_description)


if __name__ == "__main__":
    unittest.main()
