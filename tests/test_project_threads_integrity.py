import unittest

from commons_sentience_sim.core.project_threads import (
    ProjectThreadManager,
    SelfAuthoredProjectThread,
)


class ProjectThreadIntegrityTests(unittest.TestCase):
    def valid_payload(self, **overrides):
        payload = {
            "project_id": "thread-1",
            "title": "Test thread",
            "origin_category": "self_consistency",
            "status": "active",
            "stages": ["review", "verify"],
            "stage_index": 0,
            "progress_score": 0.0,
            "created_at_turn": 2,
            "last_updated_turn": 2,
            "horizon": 4,
            "revision_log": [],
        }
        payload.update(overrides)
        return payload

    def test_from_dict_rejects_invalid_status(self):
        with self.assertRaises(ValueError):
            SelfAuthoredProjectThread.from_dict(
                self.valid_payload(status="unknown")
            )

    def test_from_dict_rejects_invalid_stage_state(self):
        with self.assertRaises(ValueError):
            SelfAuthoredProjectThread.from_dict(
                self.valid_payload(stage_index=3)
            )

    def test_from_dict_rejects_invalid_score_and_blank_id(self):
        with self.assertRaises(ValueError):
            SelfAuthoredProjectThread.from_dict(
                self.valid_payload(progress_score=1.5)
            )
        with self.assertRaises(ValueError):
            SelfAuthoredProjectThread.from_dict(
                self.valid_payload(project_id="")
            )

    def test_advance_malformed_empty_stages_does_not_crash(self):
        thread = SelfAuthoredProjectThread(
            project_id="thread-1",
            stages=[],
            stage_index=-1,
        )
        self.assertFalse(thread.advance(turn=1))

    def test_prior_threads_skip_invalid_and_respect_limit(self):
        manager = ProjectThreadManager()
        records = [
            self.valid_payload(project_id=f"thread-{i}")
            for i in range(manager.MAX_ACTIVE + 2)
        ]
        records.append(self.valid_payload(project_id=""))
        carried = manager.apply_prior_threads(records)
        self.assertEqual(carried, manager.MAX_ACTIVE)
        self.assertEqual(len(manager._active_threads()), manager.MAX_ACTIVE)


if __name__ == "__main__":
    unittest.main()
