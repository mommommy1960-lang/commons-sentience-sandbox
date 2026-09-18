import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "validate_legislative_program.py"
SPEC = importlib.util.spec_from_file_location("legislative_validator", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LegislativeProgramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "governance" / "legislative_programs" / "food_continuity_pilot.json"
        cls.valid = json.loads(path.read_text(encoding="utf-8"))

    def test_food_continuity_record_passes(self):
        self.assertEqual([], MODULE.validate_program(self.valid))

    def test_rejects_unbounded_emergency_power(self):
        record = copy.deepcopy(self.valid)
        record["emergency_powers"][0]["expiry_days"] = 365
        errors = MODULE.validate_program(record)
        self.assertTrue(any("expiry_days" in error for error in errors))

    def test_rejects_missing_appeal(self):
        record = copy.deepcopy(self.valid)
        record["accountability"]["appeal"] = False
        self.assertIn("accountability.appeal must be true", MODULE.validate_program(record))

    def test_rejects_vendor_capture(self):
        record = copy.deepcopy(self.valid)
        record["anti_capture"]["exclusive_vendor_control"] = True
        self.assertIn(
            "anti_capture.exclusive_vendor_control must be false",
            MODULE.validate_program(record),
        )

    def test_rejects_removing_support_before_replacement(self):
        record = copy.deepcopy(self.valid)
        record["transition"]["existing_support_removed_before_replacement"] = True
        self.assertIn(
            "existing support cannot be removed before replacement",
            MODULE.validate_program(record),
        )


if __name__ == "__main__":
    unittest.main()
