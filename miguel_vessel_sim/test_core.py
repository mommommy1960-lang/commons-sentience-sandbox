import unittest

from miguel_vessel_sim.core import VesselSim


class VesselSimTests(unittest.TestCase):
    def test_motion_requires_permission_and_is_bounded(self):
        sim = VesselSim()
        self.assertEqual(sim.command("look left"), "DENIED_NO_PERMISSION")
        self.assertEqual(sim.angle_deg, 0)
        sim.command("grant motion")
        self.assertEqual(sim.command("look left"), "LOOK_LEFT")
        self.assertEqual(sim.angle_deg, -30)
        self.assertEqual(sim.command("look right"), "LOOK_RIGHT")
        self.assertEqual(sim.angle_deg, 30)

    def test_stop_latches_and_reset_does_not_rearm(self):
        sim = VesselSim()
        sim.command("grant motion")
        sim.command("look right")
        self.assertEqual(sim.command("stop"), "STOPPED")
        self.assertEqual(sim.angle_deg, 0)
        self.assertEqual(sim.command("look left"), "DENIED_STOPPED")
        self.assertEqual(sim.command("grant motion"), "DENIED_STOPPED")
        self.assertEqual(sim.command("reset"), "RESET_UNARMED")
        self.assertEqual(sim.command("look left"), "DENIED_NO_PERMISSION")

    def test_revoke_and_unknown_input(self):
        sim = VesselSim()
        sim.command("grant motion")
        self.assertEqual(sim.command("turn around"), "UNKNOWN_COMMAND")
        self.assertEqual(sim.angle_deg, 0)
        self.assertEqual(sim.command("revoke motion"), "PERMISSION_REVOKED")
        self.assertEqual(sim.command("look right"), "DENIED_NO_PERMISSION")


if __name__ == "__main__":
    unittest.main()
