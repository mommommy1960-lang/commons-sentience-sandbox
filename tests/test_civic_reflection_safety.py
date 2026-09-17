import unittest

from commons_sentience_sim.core.reflection import ReflectionEngine


class ReflectionSafetyTests(unittest.TestCase):
    def test_pending_contradictions_are_not_claimed_resolved(self):
        class Agent:
            turn = 1
            pending_contradictions = ["unverified contradiction"]
            affective_state = {"trust": 0.5, "urgency": 0.1}
            goals = []
            relational_memory = {}
            episodic_memory = []

        entry = ReflectionEngine().run_cycle(
            Agent(), "test", [], reflection_type="immediate"
        )
        self.assertEqual(entry.contradictions_resolved, [])
        self.assertEqual(Agent.pending_contradictions, ["unverified contradiction"])


if __name__ == "__main__":
    unittest.main()
