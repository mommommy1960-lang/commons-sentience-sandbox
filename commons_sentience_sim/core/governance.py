"""
governance.py — Rule-checking and oversight logging for bounded agency.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple


class GovernanceEngine:
    """Loads governance rules and evaluates proposed actions against them."""

    def __init__(self, rules_path: str) -> None:
        with open(rules_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.rules: List[dict] = data.get("rules", [])
        self.default_policy = data.get("default_policy", "fail_closed")
        if self.default_policy not in {"fail_closed", "fail_open"}:
            raise ValueError("default_policy must be fail_closed or fail_open")
        self._build_index()

    @staticmethod
    def _normalize_action(action: str) -> str:
        if not isinstance(action, str) or not action.strip():
            raise ValueError("action must be a non-empty string")
        return "".join(ch for ch in action.strip().lower() if ch.isalnum())

    def _build_index(self) -> None:
        self._allows: Dict[str, List[dict]] = {}
        self._prohibits: Dict[str, List[dict]] = {}
        for rule in self.rules:
            for action in rule.get("allows", []):
                self._allows.setdefault(self._normalize_action(action), []).append(rule)
            for action in rule.get("prohibits", []):
                self._prohibits.setdefault(self._normalize_action(action), []).append(rule)

    def check_action(self, action: str) -> Tuple[bool, str]:
        """Return (permitted, reason).  Prohibited actions are blocked."""
        normalized = self._normalize_action(action)
        blocking = self._prohibits.get(normalized, [])
        if blocking:
            rule = blocking[0]
            reason = (
                f"Blocked by rule {rule['id']} ({rule['name']}): {rule['description']}"
            )
            return False, reason
        permitting = self._allows.get(normalized, [])
        if permitting:
            rule = permitting[0]
            reason = f"Permitted by rule {rule['id']} ({rule['name']})"
            return True, reason
        if self.default_policy == "fail_open":
            return True, "Action not explicitly covered by any rule — permitted by explicit fail-open policy."
        return False, "Action not explicitly covered by any rule — denied by fail-closed policy."

    def get_rules_by_category(self, category: str) -> List[dict]:
        return [r for r in self.rules if r.get("category") == category]

    def get_rule_by_id(self, rule_id: str) -> Optional[dict]:
        for r in self.rules:
            if r.get("id") == rule_id:
                return r
        return None

    def all_rule_names(self) -> List[str]:
        return [r["name"] for r in self.rules]
