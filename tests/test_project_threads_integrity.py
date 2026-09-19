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

    def test_prior_threads_skips_invalid_records(self):
        manager = ProjectThreadManager()
        records = [
            self.valid_payload(project_id="valid-1"),
            self.valid_payload(project_id=""),
            self.valid_payload(project_id="valid-2"),
            self.valid_payload(project_id="invalid-status", status="unknown"),
        ]
        carried = manager.apply_prior_threads(records)
        self.assertEqual(carried, 2)
        self.assertEqual(
            {thread.project_id for thread in manager.threads},
            {"valid-1", "valid-2"},
        )

    def test_prior_threads_respects_active_limit(self):
        manager = ProjectThreadManager()
        records = [
            self.valid_payload(project_id=f"thread-{i}")
            for i in range(manager.MAX_ACTIVE + 2)
        ]
        carried = manager.apply_prior_threads(records)
        self.assertEqual(carried, manager.MAX_ACTIVE)
        self.assertEqual(
            len(manager._active_threads()),
            manager.MAX_ACTIVE,
        )

    def test_prior_threads_skips_completed_and_abandoned(self):
        manager = ProjectThreadManager()
        records = [
            self.valid_payload(project_id="completed", status="completed"),
            self.valid_payload(project_id="abandoned", status="abandoned"),
            self.valid_payload(project_id="active"),
        ]
        carried = manager.apply_prior_threads(records)
        self.assertEqual(carried, 1)
        self.assertEqual(manager.threads[0].project_id, "active")

    def test_prior_threads_skips_existing_duplicate(self):
        manager = ProjectThreadManager()
        existing = SelfAuthoredProjectThread.from_dict(
            self.valid_payload(project_id="existing")
        )
        manager.threads.append(existing)

        carried = manager.apply_prior_threads([
            self.valid_payload(project_id="existing"),
            self.valid_payload(project_id="new"),
        ])

        self.assertEqual(carried, 1)
        self.assertEqual(
            [thread.project_id for thread in manager.threads],
            ["existing", "new"],
        )

    def test_paused_threads_do_not_consume_active_capacity(self):
        manager = ProjectThreadManager()
        paused = SelfAuthoredProjectThread.from_dict(
            self.valid_payload(project_id="paused", status="paused")
        )
        manager.threads.append(paused)

        carried = manager.apply_prior_threads([
            self.valid_payload(project_id=f"active-{i}")
            for i in range(manager.MAX_ACTIVE)
        ])

        self.assertEqual(carried, manager.MAX_ACTIVE)
        self.assertEqual(
            len(manager._active_threads()),
            manager.MAX_ACTIVE,
        )
        self.assertEqual(len(manager.threads), manager.MAX_ACTIVE + 1)


if __name__ == "__main__":
    unittest.main()
