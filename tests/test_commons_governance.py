import unittest
from datetime import datetime, timedelta, timezone

from commons_governance import ConsentGrant, GovernanceCore, MoralMemoryRecord


class Clock:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


class GovernanceCoreTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)
        self.clock = Clock(self.start)
        self.core = GovernanceCore(
            self.clock,
            authorized_reviewers={"independent-reviewer"},
            authorized_revokers={"safety-officer"},
        )
        self.grant = ConsentGrant(
            grant_id="grant-1",
            issuer="human-reviewer",
            subject="maya-node",
            scopes=frozenset({"read:weather", "draft:summary"}),
            not_before=self.start,
            expires_at=self.start + timedelta(hours=1),
        )
        self.core.add_grant(self.grant)

    def test_authorizes_only_exact_scope_and_subject(self):
        self.assertEqual(self.core.authorize("grant-1", "maya-node", "read:weather"), (True, "allowed"))
        self.assertEqual(self.core.authorize("grant-1", "other-node", "read:weather"), (False, "wrong_subject"))
        self.assertEqual(self.core.authorize("grant-1", "maya-node", "send:email"), (False, "scope_denied"))

    def test_expiry_is_fail_closed(self):
        self.clock.value = self.start + timedelta(hours=1)
        self.assertEqual(self.core.authorize("grant-1", "maya-node", "read:weather"), (False, "expired"))

    def test_revocation_is_immediate(self):
        self.core.revoke("grant-1", "human-reviewer", "permission withdrawn")
        self.assertEqual(self.core.authorize("grant-1", "maya-node", "read:weather"), (False, "revoked"))

    def test_unauthorized_actor_cannot_revoke(self):
        with self.assertRaises(PermissionError):
            self.core.revoke("grant-1", "stranger", "attempted takeover")
        self.assertEqual(self.core.authorize("grant-1", "maya-node", "read:weather"), (True, "allowed"))

    def test_freeze_blocks_and_restore_does_not_revive_revoked_grant(self):
        self.core.freeze("operator", "integrity uncertainty")
        self.assertEqual(self.core.authorize("grant-1", "maya-node", "read:weather"), (False, "system_frozen"))
        self.core.revoke("grant-1", "human-reviewer", "permission withdrawn")
        self.core.restore("independent-reviewer", "integrity review complete")
        self.assertEqual(self.core.authorize("grant-1", "maya-node", "read:weather"), (False, "revoked"))

    def test_unauthorized_reviewer_cannot_restore(self):
        self.core.freeze("operator", "integrity uncertainty")
        with self.assertRaises(PermissionError):
            self.core.restore("stranger", "trust me")
        self.assertTrue(self.core.frozen)

    def test_unknown_grant_is_denied_and_logged(self):
        self.assertEqual(self.core.authorize("missing", "maya-node", "read:weather"), (False, "unknown_grant"))
        self.assertEqual(self.core.audit.events[-1].payload["allowed"], False)

    def test_duplicate_identifiers_are_rejected(self):
        with self.assertRaises(ValueError):
            self.core.add_grant(self.grant)

    def test_audit_tampering_is_detected(self):
        self.core.authorize("grant-1", "maya-node", "read:weather")
        self.assertEqual(self.core.audit.verify(), (True, None))
        self.core.audit.events[0].payload["issuer"] = "attacker"
        valid, index = self.core.audit.verify()
        self.assertFalse(valid)
        self.assertEqual(index, 0)

    def test_moral_memory_requires_evidence_and_retention(self):
        record = MoralMemoryRecord(
            record_id="memory-1",
            incident_id="incident-7",
            observed_harm="Overconfident answer obscured uncertainty",
            corrective_action="Display confidence and request review",
            evidence_refs=("audit:event:17",),
            retain_until=self.start + timedelta(days=30),
        )
        self.core.remember(record)
        self.assertEqual(self.core.memory, (record,))
        with self.assertRaises(ValueError):
            self.core.remember(record)


if __name__ == "__main__":
    unittest.main()
