import unittest

from commons_sentience_sim.core.relationships import (
    AgentRelationship,
    INTERACTION_TYPES,
)


class RelationshipSafetyTests(unittest.TestCase):
    def test_unknown_interaction_type_is_rejected(self):
        relationship = AgentRelationship(name="Aster")
        with self.assertRaises(ValueError):
            relationship.record_interaction(
                turn=1,
                interaction_type="invented_type",
                note="invalid",
            )
        self.assertEqual(relationship.cooperation_count, 0)
        self.assertEqual(relationship.conflict_count, 0)

    def test_trust_delta_override_is_bounded(self):
        relationship = AgentRelationship(name="Aster", trust=0.5)
        relationship.record_interaction(
            turn=1,
            interaction_type=INTERACTION_TYPES[0],
            note="bounded",
            trust_delta=1.0,
        )
        self.assertLessEqual(relationship.trust, 0.6)

    def test_negative_turn_is_rejected(self):
        relationship = AgentRelationship(name="Aster")
        with self.assertRaises(ValueError):
            relationship.record_interaction(
                turn=-1,
                interaction_type=INTERACTION_TYPES[0],
                note="invalid",
            )


if __name__ == "__main__":
    unittest.main()
