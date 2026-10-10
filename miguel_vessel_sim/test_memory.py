import tempfile
import unittest
from pathlib import Path

from miguel_vessel_sim.memory import IncidentMemory


class IncidentMemoryTests(unittest.TestCase):
    def test_damage_survives_restart_and_explains_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            first = IncidentMemory()
            self.assertEqual(first.decide("stove", "touch surface")["decision"], "UNKNOWN_REVIEW")
            first.record_damage("stove", "touch surface", "Hand covering damaged by hot surface")
            first.save(path)
            later = IncidentMemory.load(path)
            decision = later.decide("stove", "touch surface")
            self.assertEqual(decision["decision"], "DENY")
            self.assertIn("damage", decision["reason"].lower())
            self.assertIn("Hand covering", decision["evidence"])
            self.assertEqual(later.decide("stove", "inspect from distance")["decision"], "UNKNOWN_REVIEW")

    def test_invalid_or_corrupt_memory_is_rejected(self):
        memory = IncidentMemory()
        with self.assertRaises(ValueError):
            memory.record_damage("", "touch", "damage")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            path.write_text('{"schema": 2, "incidents": []}', encoding="utf-8")
            with self.assertRaises(ValueError):
                IncidentMemory.load(path)


if __name__ == "__main__":
    unittest.main()
