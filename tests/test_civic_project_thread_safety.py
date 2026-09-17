import unittest

from commons_sentience_sim.core.project_threads import (
    ProjectThreadManager,
    SelfAuthoredProjectThread,
)


class ProjectThreadCarryoverTests(unittest.TestCase):
    def test_malformed_thread_is_rejected(self):
        with self.assertRaises(ValueError):
            SelfAuthoredProjectThread.from_dict({
                "project_id": "bad",
                "status": "unknown",
                "stages": ["one"],
            })

    def test_empty_stages_cannot_crash_advance(self):
        thread = SelfAuthoredProjectThread(
            project_id="empty",
            stages=[],
            stage_index=-1,
        )
        self.assertFalse(thread.advance(1))

    def test_carryover_respects_active_limit_and_skips_invalid(self):
        manager = ProjectThreadManager()
        records = [
            {"project_id": "", "status": "active", "stages": ["one"]},
            {"project_id": "valid-1", "status": "active", "stages": ["one"]},
            {"project_id": "valid-2", "status": "active", "stages": ["one"]},
        ]
        self.assertEqual(manager.apply_prior_threads(records), 2)
        self.assertEqual(
            {thread.project_id for thread in manager.threads},
            {"valid-1", "valid-2"},
        )


if __name__ == "__main__":
    unittest.main()
