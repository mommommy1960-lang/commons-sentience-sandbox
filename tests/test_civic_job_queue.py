import json
import tempfile
import unittest
from pathlib import Path

from tools.civic_job_queue import JobQueue


class JobQueueTests(unittest.TestCase):
    def make_queue(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return JobQueue(Path(directory.name) / "queue.json")

    def test_create_run_record_and_report(self):
        queue = self.make_queue()
        job = queue.create("Prepare a reproducible research brief", budget_steps=2)
        queue.transition(job["id"], "running")
        step = queue.record_step(job["id"], "builder", {"finding": "example"})
        self.assertEqual(step["step"], 1)
        reported = queue.report(job["id"], {"status": "needs-review"})
        self.assertEqual(reported["result"]["value"]["status"], "needs-review")
        self.assertTrue(queue.verify_audit_chain())

    def test_step_budget_is_enforced(self):
        queue = self.make_queue()
        job = queue.create("Bounded task", budget_steps=1)
        queue.transition(job["id"], "running")
        queue.record_step(job["id"], "breaker", "one")
        with self.assertRaises(ValueError):
            queue.record_step(job["id"], "repairer", "two")

    def test_pause_and_resume_are_explicit(self):
        queue = self.make_queue()
        job = queue.create("Pause when evidence is missing")
        queue.transition(job["id"], "running")
        queue.transition(job["id"], "paused", "missing independent evidence")
        self.assertEqual(queue.list_jobs()[0]["status"], "paused")
        queue.transition(job["id"], "running")
        self.assertEqual(queue.list_jobs()[0]["status"], "running")

    def test_terminal_jobs_cannot_be_reopened(self):
        queue = self.make_queue()
        job = queue.create("Finished task")
        queue.transition(job["id"], "cancelled")
        with self.assertRaises(ValueError):
            queue.transition(job["id"], "running")

    def test_tampering_breaks_audit_chain(self):
        queue = self.make_queue()
        job = queue.create("Detect tampering")
        queue.data["events"][0]["detail"] = "changed"
        self.assertFalse(queue.verify_audit_chain())


if __name__ == "__main__":
    unittest.main()
