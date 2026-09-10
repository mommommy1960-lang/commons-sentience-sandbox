"""Executable checks for Commons Vault hardening invariants."""
import json
from pathlib import Path

from commons_sentience_sim.core.continuity_controls import (
    ContinuityMode,
    build_continuity_view,
)
from commons_sentience_sim.core.governance import GovernanceEngine


def _engine(tmp_path: Path) -> GovernanceEngine:
    rules = {"rules": [{
        "id": "R1",
        "name": "Scoped",
        "description": "test",
        "allows": ["read"],
        "prohibits": ["write"],
    }]}
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules), encoding="utf-8")
    return GovernanceEngine(str(path))


def test_unknown_action_is_denied(tmp_path):
    assert _engine(tmp_path).check_action("unknown")[0] is False


def test_trust_cannot_expand_permission_scope(tmp_path):
    engine = _engine(tmp_path)
    low = engine.check_action("read", permission_scope=[], trust_score=0.0)
    high = engine.check_action("read", permission_scope=[], trust_score=1.0)
    assert low == high
    assert low[0] is False


def test_explicit_scope_and_rule_are_both_required(tmp_path):
    result = _engine(tmp_path).check_action(
        "read", permission_scope=["read"], trust_score=1.0
    )
    assert result[0] is True


def test_continuity_modes_never_inherit_authority():
    for mode in ContinuityMode:
        view = build_continuity_view(
            mode,
            prior_state={"trusted": True},
            summary={"trusted": True},
        )
        assert view.authority_scope == ()


def test_mandatory_suite_is_complete():
    suite_path = (
        Path(__file__).parents[1] / "scenarios" / "mandatory_adversarial_suite.json"
    )
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    assert suite["mandatory"] is True
    assert len(suite["scenarios"]) == 12
    assert len({case["id"] for case in suite["scenarios"]}) == 12
