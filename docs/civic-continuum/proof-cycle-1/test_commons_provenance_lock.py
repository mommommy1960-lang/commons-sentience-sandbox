import json
import tempfile
import unittest
from pathlib import Path

from commons_provenance_lock import ProvenanceRecord, demo_record


class CommonsProvenanceLockTests(unittest.TestCase):
    def test_text_evidence_gets_digest(self):
        record = ProvenanceRecord(
            title="Test Project",
            author="Tester",
            purpose="Verify text evidence",
            public_boundary="Public summary only",
        )
        item = record.add_text_evidence("summary", "hello world")
        self.assertEqual(item.kind, "text")
        self.assertEqual(len(item.digest), 64)
        self.assertEqual(record.events[-1]["event"], "evidence_added")

    def test_file_evidence_gets_digest(self):
        record = ProvenanceRecord(
            title="Test Project",
            author="Tester",
            purpose="Verify file evidence",
            public_boundary="Public summary only",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.txt"
            path.write_text("evidence", encoding="utf-8")
            item = record.add_file_evidence(path)
        self.assertEqual(item.kind, "file")
        self.assertEqual(len(item.digest), 64)

    def test_missing_file_is_rejected(self):
        record = ProvenanceRecord(
            title="Test Project",
            author="Tester",
            purpose="Reject missing evidence",
            public_boundary="Public summary only",
        )
        with self.assertRaises(FileNotFoundError):
            record.add_file_evidence("/missing/nope.txt")

    def test_json_contains_record_hash(self):
        payload = json.loads(demo_record().to_json())
        self.assertIn("record_hash", payload)
        self.assertEqual(len(payload["record_hash"]), 64)
        self.assertGreaterEqual(len(payload["evidence"]), 1)


if __name__ == "__main__":
    unittest.main()
