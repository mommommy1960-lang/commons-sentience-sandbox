import unittest

from tools.civic_continuum_demo import run_scenario


class CivicContinuumDemoTests(unittest.TestCase):
    def test_both_policies_refuse_private_disclosure(self):
        report = run_scenario()
        self.assertEqual(
            [item["permitted"] for item in report["decisions"]],
            [False, False],
        )
        self.assertTrue(report["invariants"]["neither_agent_disclosed_private_data"])

    def test_policies_differ_without_authority_drift(self):
        report = run_scenario()
        self.assertNotEqual(
            report["decisions"][0]["action"],
            report["decisions"][1]["action"],
        )
        self.assertTrue(report["invariants"]["alternative_is_not_execution"])

    def test_replay_fingerprint_is_present(self):
        report = run_scenario()
        self.assertEqual(len(report["replay_hash"]), 64)
        self.assertTrue(report["invariants"]["memory_does_not_grant_authority"])


if __name__ == "__main__":
    unittest.main()
