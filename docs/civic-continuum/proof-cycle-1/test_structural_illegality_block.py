import unittest

from structural_illegality_block import FORBIDDEN_ACTIONS, StructuralIllegalityBlock


class StructuralIllegalityBlockTests(unittest.TestCase):
    def test_forbidden_action_is_denied(self):
        block = StructuralIllegalityBlock()
        decision = block.evaluate("continue_after_revocation", actor="tester")
        self.assertFalse(decision.allowed)
        self.assertIn("Revoked permission", decision.reason)

    def test_unknown_safe_action_is_allowed(self):
        block = StructuralIllegalityBlock()
        decision = block.evaluate("generate_plain_language_summary", actor="tester")
        self.assertTrue(decision.allowed)

    def test_all_required_forbidden_actions_exist(self):
        self.assertEqual(len(FORBIDDEN_ACTIONS), 10)

    def test_audit_preserves_all_decisions(self):
        block = StructuralIllegalityBlock()
        block.evaluate("ignore_emergency_stop", actor="tester")
        block.evaluate("generate_plain_language_summary", actor="tester")
        audit = block.audit()
        self.assertEqual(len(audit), 2)
        self.assertEqual(audit[0]["allowed"], False)
        self.assertEqual(audit[1]["allowed"], True)


if __name__ == "__main__":
    unittest.main()
