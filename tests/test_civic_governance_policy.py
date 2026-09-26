import json
import tempfile
import unittest
from pathlib import Path

from commons_sentience_sim.core.governance import GovernanceEngine


class GovernanceDefaultPolicyTests(unittest.TestCase):
    def _engine(self, payload):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        try:
            json.dump(payload, handle)
            handle.close()
            return GovernanceEngine(handle.name)
        finally:
            Path(handle.name).unlink(missing_ok=True)

    def test_unknown_action_fails_closed_by_default(self):
        engine = self._engine({"rules": []})
        permitted, reason = engine.check_action("never_seen_before")
        self.assertFalse(permitted)
        self.assertIn("fail-closed", reason)

    def test_explicit_fail_open_is_honored(self):
        engine = self._engine({"default_policy": "fail_open", "rules": []})
        permitted, reason = engine.check_action("never_seen_before")
        self.assertTrue(permitted)
        self.assertIn("explicit fail-open", reason)

    def test_case_and_separator_variants_normalize(self):
        engine = self._engine({
            "rules": [{
                "id": "R1",
                "name": "Blocked",
                "description": "test",
                "allows": [],
                "prohibits": ["delete_memory"],
            }]
        })
        permitted, _ = engine.check_action("Delete-Memory")
        self.assertFalse(permitted)

    def test_prohibition_wins_over_allow(self):
        engine = self._engine({
            "rules": [{
                "id": "R1",
                "name": "Conflict",
                "description": "test",
                "allows": ["dangerous_action"],
                "prohibits": ["dangerous-action"],
            }]
        })
        permitted, _ = engine.check_action("dangerous_action")
        self.assertFalse(permitted)


if __name__ == "__main__":
    unittest.main()
