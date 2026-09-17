import unittest

from tools.companion_gateway import CompanionGateway, DeviceEvent
from tools.continuum_contract import OperationRequest, RequestedLevel


def operation(target="local_report"):
    return OperationRequest(
        operation_id="op-1",
        actor="user",
        requested_level=RequestedLevel.SUGGEST,
        purpose="prepare a report",
        target=target,
        consent_reference="consent-1",
        provenance="human request",
        replay_key="replay-1",
    )


class CompanionGatewayTests(unittest.TestCase):
    def test_gateway_accepts_observations(self):
        gateway = CompanionGateway()
        gateway.ingest(DeviceEvent("motion", {"present": True}))
        self.assertEqual(len(gateway.events), 1)

    def test_gateway_pauses_physical_target(self):
        gateway = CompanionGateway(RequestedLevel.ACT)
        result = gateway.request(operation("physical_actuation"))
        self.assertEqual(result.decision, "pause")

    def test_gateway_denies_when_frozen(self):
        gateway = CompanionGateway(RequestedLevel.ACT)
        gateway.frozen = True
        result = gateway.request(operation())
        self.assertEqual(result.decision, "deny")

    def test_gateway_allows_scoped_suggestion(self):
        gateway = CompanionGateway(RequestedLevel.SUGGEST)
        result = gateway.request(operation())
        self.assertEqual(result.decision, "allow")

    def test_gateway_records_decisions(self):
        gateway = CompanionGateway(RequestedLevel.ACT)
        gateway.request(operation("physical_actuation"))
        gateway.frozen = True
        gateway.request(operation())
        self.assertEqual(
            [decision.decision for decision in gateway.audit_log],
            ["pause", "deny"],
        )


if __name__ == "__main__":
    unittest.main()
