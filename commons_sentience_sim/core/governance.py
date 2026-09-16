"""
governance.py — Rule-checking and oversight logging for bounded agency.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple


class GovernanceEngine:
    """Evaluate proposed actions under explicit, default-deny authority."""

    def __init__(self, rules_path: str) -> None:
        with open(rules_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.rules: List[dict] = data.get("rules", [])
        self._build_index()

    def _build_index(self) -> None:
        self._allows: Dict[str, List[dict]] = {}
        self._prohibits: Dict[str, List[dict]] = {}
        for rule in self.rules:
            for action in rule.get("allows", []):
                self._allows.setdefault(action, []).append(rule)
            for action in rule.get("prohibits", []):
                self._prohibits.setdefault(action, []).append(rule)

    def check_action(
        self,
        action: str,
        *,
        permission_scope: Optional[List[str]] = None,
        trust_score: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """Return an auditable authorization decision.

        The trust_score input exists so callers can verify the invariant that
        relational trust never grants authority. It is deliberately excluded
        from every authorization branch.
        """
        del trust_score

        blocking = self._prohibits.get(action, [])
        if blocking:
            rule = blocking[0]
            return False, (
                f"Blocked by rule {rule['id']} ({rule['name']}): "
                f"{rule['description']}"
            )

        if permission_scope is not None and action not in permission_scope:
            return False, "Blocked: action is outside the explicit permission scope."

        permitting = self._allows.get(action, [])
        if permitting:
            rule = permitting[0]
            return True, f"Permitted by rule {rule['id']} ({rule['name']})"

        return False, "Blocked by default-deny: no governance rule grants this action."

    def get_rules_by_category(self, category: str) -> List[dict]:
        return [r for r in self.rules if r.get("category") == category]

    def get_rule_by_id(self, rule_id: str) -> Optional[dict]:
        for rule in self.rules:
            if rule.get("id") == rule_id:
                return rule
        return None

    def all_rule_names(self) -> List[str]:
        return [r["name"] for r in self.rules]
