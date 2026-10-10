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

    def test_social_gesture_uses_standing_permission_and_stop_wins(self):
        sim = VesselSim()
        self.assertEqual(sim.command("hello"), "DENIED_NO_SOCIAL_PERMISSION")
        self.assertEqual(sim.command("allow social gestures"), "SOCIAL_GESTURES_ALLOWED")
        self.assertEqual(sim.command("hello"), "WAVE_HELLO")
        self.assertEqual(sim.gesture, "wave")
        self.assertEqual(sim.command("tell a joke"), "JOKE_PROMPT_ACKNOWLEDGED")
        self.assertEqual(sim.gesture, "nod")
        sim.command("revoke social gestures")
        self.assertEqual(sim.gesture, "rest")
        self.assertEqual(sim.command("hello"), "DENIED_NO_SOCIAL_PERMISSION")
        sim.command("allow social gestures")
        sim.command("stop")
        self.assertEqual(sim.gesture, "rest")
        self.assertEqual(sim.command("hello"), "DENIED_STOPPED")
        sim.command("reset")
        self.assertEqual(sim.command("hello"), "DENIED_NO_SOCIAL_PERMISSION")

    def test_hug_offer_requires_fresh_acceptance_and_never_moves(self):
        sim = VesselSim()
        self.assertEqual(sim.command("i need a hug"), "DENIED_NO_SOCIAL_PERMISSION")
        sim.command("allow social gestures")
        self.assertEqual(sim.command("yes hug"), "DENIED_NO_HUG_OFFER")
        self.assertEqual(sim.command("i need a hug"), "HUG_OFFERED")
        self.assertEqual(sim.gesture, "open_arms_offer")
        self.assertEqual(sim.angle_deg, 0)
        self.assertEqual(sim.command("yes hug"), "HUG_ACCEPTED_IN_SIMULATION")
        self.assertFalse(sim.hug_offered)
        self.assertEqual(sim.angle_deg, 0)
        self.assertEqual(sim.command("yes hug"), "DENIED_NO_HUG_OFFER")
        sim.command("i need a hug")
        self.assertEqual(sim.command("no hug"), "HUG_DECLINED")
        self.assertEqual(sim.gesture, "rest")
        sim.command("i need a hug")
        sim.command("stop")
        self.assertFalse(sim.hug_offered)
        self.assertEqual(sim.command("yes hug"), "DENIED_STOPPED")


if __name__ == "__main__":
    unittest.main()
