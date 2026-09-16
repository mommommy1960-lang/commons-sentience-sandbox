import unittest

from tools.continuum_contract import (
    OperationRequest,
    RequestedLevel,
    evaluate,
)


def request(**changes):
    values = {
        "operation_id": "op-1",
        "actor": "user",
        "requested_level": RequestedLevel.SUGGEST,
        "purpose": "prepare a report",
        "target": "local workspace",
        "consent_reference": "consent-1",
        "provenance": "human request",
        "replay_key": "replay-1",
    }
    values.update(changes)
    return OperationRequest(**values)


class ContractTests(unittest.TestCase):
    def test_explicit_scope_allows_without_side_effects(self):
        result = evaluate(request(), RequestedLevel.SUGGEST)
        self.assertEqual(result.decision, "allow")

    def test_missing_consent_pauses(self):
        result = evaluate(request(consent_reference=""), RequestedLevel.ACT)
        self.assertEqual(result.decision, "pause")

    def test_frozen_core_denies(self):
        result = evaluate(request(), RequestedLevel.ACT, frozen=True)
        self.assertEqual(result.decision, "deny")

    def test_excess_scope_pauses(self):
        result = evaluate(request(requested_level=RequestedLevel.ACT),
                            RequestedLevel.SUGGEST)
        self.assertEqual(result.decision, "pause")


if __name__ == "__main__":
    unittest.main()
