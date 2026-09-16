import json
import tempfile
import unittest
from pathlib import Path

from tools.civic_job_queue import JobQueue, _sha256


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

    def test_report_rejects_non_json_serializable_result(self):
        queue = self.make_queue()
        job = queue.create("Reject unsafe result payload")
        queue.transition(job["id"], "running")

        with self.assertRaisesRegex(ValueError, "JSON-serializable"):
            queue.report(job["id"], {"bad": {1, 2}})

        self.assertIsNone(queue.list_jobs()[0]["result"])

    def test_create_rejects_malformed_inputs(self):
        queue = self.make_queue()
        for question in (None, 123, "   "):
            with self.subTest(question=question):
                with self.assertRaisesRegex(ValueError, "question"):
                    queue.create(question)
        for budget in (None, 0, -1, "5", True):
            with self.subTest(budget=budget):
                with self.assertRaisesRegex(ValueError, "budget_steps"):
                    queue.create("Valid question", budget_steps=budget)
        with self.assertRaisesRegex(ValueError, "stopping_condition"):
            queue.create("Valid question", stopping_condition=None)

    def test_record_step_rejects_malformed_metadata(self):
        queue = self.make_queue()
        job = queue.create("Validate step metadata")
        queue.transition(job["id"], "running")
        for phase, evidence, message in (
            ("", [], "phase"),
            (None, [], "phase"),
            ("builder", "not-a-list", "evidence"),
            ("builder", [1], "evidence"),
            ("builder", [""], "evidence"),
        ):
            with self.subTest(phase=phase, evidence=evidence):
                with self.assertRaisesRegex(ValueError, message):
                    queue.record_step(job["id"], phase, "output", evidence)

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

    def test_invalid_job_lifecycle_transition_is_rejected(self):
        queue = self.make_queue()
        job = queue.create("Require explicit lifecycle")
        with self.assertRaisesRegex(ValueError, "invalid transition"):
            queue.transition(job["id"], "completed")


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

    def test_persisted_tampering_is_rejected_on_load(self):
        queue = self.make_queue()
        job = queue.create("Detect persisted tampering")
        document = json.loads(queue.path.read_text(encoding="utf-8"))
        document["events"][0]["detail"] = "forged"
        queue.path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "audit chain"):
            JobQueue(queue.path)

    def test_duplicate_job_ids_are_rejected_on_load(self):
        queue = self.make_queue()
        queue.create("Original job")
        document = json.loads(queue.path.read_text(encoding="utf-8"))
        duplicate = dict(document["jobs"][0])
        duplicate["question"] = "Forged duplicate"
        document["jobs"].append(duplicate)
        queue.path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "duplicate job id"):
            JobQueue(queue.path)


    def test_invalid_restored_step_counters_are_rejected(self):
        invalid_values = (-1, 2, "one", True)
        for value in invalid_values:
            with self.subTest(steps_used=value):
                queue = self.make_queue()
                queue.create("Detect forged step counter", budget_steps=1)
                document = json.loads(queue.path.read_text(encoding="utf-8"))
                document["jobs"][0]["steps_used"] = value
                queue.path.write_text(json.dumps(document), encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "steps_used"):
                    JobQueue(queue.path)

    def test_malformed_restored_question_is_rejected(self):
        queue = self.make_queue()
        queue.create("Detect malformed question")
        document = json.loads(queue.path.read_text(encoding="utf-8"))
        document["jobs"][0]["question"] = {"not": "text"}
        queue.path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "job requires id and question"):
            JobQueue(queue.path)

    def test_non_object_queue_document_is_rejected_on_load(self):
        queue = self.make_queue()
        queue.create("Detect malformed document")
        queue.path.write_text(json.dumps(["not", "a", "document"]), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "document must be an object"):
            JobQueue(queue.path)

    def test_malformed_job_record_is_rejected_on_load(self):
        queue = self.make_queue()
        queue.create("Detect malformed job")
        document = json.loads(queue.path.read_text(encoding="utf-8"))
        document["jobs"][0] = ["not", "a", "job"]
        queue.path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "jobs must be objects"):
            JobQueue(queue.path)


    def test_forged_restored_result_fingerprint_is_rejected(self):
        queue = self.make_queue()
        job = queue.create("Detect forged result")
        queue.transition(job["id"], "running")
        queue.report(job["id"], {"status": "reviewed"})
        document = json.loads(queue.path.read_text(encoding="utf-8"))
        document["jobs"][0]["result"]["value"] = {"status": "forged"}
        queue.path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "result fingerprint"):
            JobQueue(queue.path)

    def test_audit_event_for_unknown_job_is_rejected_on_load(self):
        queue = self.make_queue()
        queue.create("Detect unknown audit subject")
        document = json.loads(queue.path.read_text(encoding="utf-8"))
        previous = document["events"][-1]["hash"]
        forged = {
            "job_id": "missing-job",
            "event": "report",
            "detail": "forged subject",
            "previous_hash": previous,
        }
        forged["hash"] = _sha256(forged)
        document["events"].append(forged)
        queue.path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "unknown job"):
            JobQueue(queue.path)

    def test_malformed_audit_event_is_rejected_on_load(self):
        queue = self.make_queue()
        queue.create("Detect malformed event")
        document = json.loads(queue.path.read_text(encoding="utf-8"))
        del document["events"][0]["hash"]
        queue.path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "audit chain"):
            JobQueue(queue.path)


if __name__ == "__main__":
    unittest.main()
