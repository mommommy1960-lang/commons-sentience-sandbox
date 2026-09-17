import unittest

from commons_sentience_sim.core.narrative_identity import NarrativeIdentitySystem


class IdentityCarryoverSafetyTests(unittest.TestCase):
    def test_invalid_prior_state_is_ignored(self):
        system = NarrativeIdentitySystem(agent_name="Sentinel")
        self.assertEqual(system.apply_prior_run([], "run-2"), 0)
        self.assertEqual(system.apply_prior_run({"narrative_coherence_score": 4.0}, "run-2"), 0)
        self.assertEqual(system.narrative_coherence_score, 0.7)

    def test_reapplying_empty_state_is_idempotent(self):
        system = NarrativeIdentitySystem(agent_name="Sentinel")
        state = {"identity_timeline": [], "milestone_memories": [], "narrative_themes": []}
        self.assertEqual(system.apply_prior_run(state, "run-2"), 0)
        self.assertEqual(system.apply_prior_run(state, "run-2"), 0)


if __name__ == "__main__":
    unittest.main()
