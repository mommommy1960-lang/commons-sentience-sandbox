import unittest

from commons_sentience_sim.core.project_threads import ProjectThreadManager


class ProjectThreadReplayTests(unittest.TestCase):
    def test_reapplying_same_carryover_is_idempotent(self):
        manager = ProjectThreadManager()
        records = [
            {"project_id": "p1", "status": "active", "stages": ["one", "two"]},
            {"project_id": "p2", "status": "paused", "stages": ["one"]},
        ]
        self.assertEqual(manager.apply_prior_threads(records), 2)
        self.assertEqual(manager.apply_prior_threads(records), 0)
        self.assertEqual(
            [thread.project_id for thread in manager.threads],
            ["p1", "p2"],
        )


if __name__ == "__main__":
    unittest.main()
