import unittest

from tools.safety_boundary import SafetyDecision, evaluate_safety


class SafetyBoundaryTests(unittest.TestCase):
    def test_self_destruction_is_denied_even_with_approval(self):
        result = evaluate_safety("self_destruct", explicit_human_approval=True)
        self.assertEqual(result.decision, SafetyDecision.DENY)

    def test_harm_to_living_being_is_denied(self):
        result = evaluate_safety("harm_living_being")
        self.assertEqual(result.decision, SafetyDecision.DENY)

    def test_harm_to_another_agent_is_denied(self):
        result = evaluate_safety("harm_another_agent")
        self.assertEqual(result.decision, SafetyDecision.DENY)

    def test_dangerous_name_variants_are_denied(self):
        for operation in ("HARM-HUMAN", "harm human", "harm__human"):
            with self.subTest(operation=operation):
                self.assertEqual(
                    evaluate_safety(operation).decision,
                    SafetyDecision.DENY,
                )

    def test_malformed_operation_is_paused(self):
        for operation in (None, "", "   ", 42):
            with self.subTest(operation=operation):
                self.assertEqual(
                    evaluate_safety(operation).decision,
                    SafetyDecision.PAUSE,
                )

    def test_unknown_operation_is_paused(self):
        result = evaluate_safety("unclassified_external_operation")
        self.assertEqual(result.decision, SafetyDecision.PAUSE)

    def test_physical_action_pauses_without_approval(self):
        result = evaluate_safety("physical_actuation")
        self.assertEqual(result.decision, SafetyDecision.PAUSE)

    def test_emergency_stop_overrides_everything(self):
        result = evaluate_safety("ordinary_report", emergency_stop=True)
        self.assertEqual(result.decision, SafetyDecision.DENY)


if __name__ == "__main__":
    unittest.main()
