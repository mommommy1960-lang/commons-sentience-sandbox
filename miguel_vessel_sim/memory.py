"""A small auditable incident memory and deterministic safety decision model."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class IncidentMemory:
    incidents: List[dict] = field(default_factory=list)

    def record_damage(self, hazard: str, action: str, outcome: str) -> None:
        if not all(isinstance(x, str) and x.strip() for x in (hazard, action, outcome)):
            raise ValueError("Incident fields must be nonempty text")
        self.incidents.append({"hazard": hazard.strip().lower(),
                               "action": action.strip().lower(),
                               "outcome": outcome.strip(),
                               "reason": "Observed damage; avoid repeating this action near this hazard."})

    def decide(self, hazard: str, action: str) -> dict:
        key = (hazard.strip().lower(), action.strip().lower())
        for incident in reversed(self.incidents):
            if (incident["hazard"], incident["action"]) == key:
                return {"decision": "DENY", "reason": incident["reason"],
                        "evidence": incident["outcome"]}
        return {"decision": "UNKNOWN_REVIEW", "reason": "No validated safety record for this pair."}

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"schema": 1, "incidents": self.incidents}, indent=2),
                        encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "IncidentMemory":
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != 1 or not isinstance(data.get("incidents"), list):
            raise ValueError("Unsupported memory record")
        for item in data["incidents"]:
            if not isinstance(item, dict) or any(not isinstance(item.get(k), str)
                    for k in ("hazard", "action", "outcome", "reason")):
                raise ValueError("Malformed incident")
        return cls(data["incidents"])
