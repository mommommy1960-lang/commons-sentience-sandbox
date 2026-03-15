"""
tasks.py — Task planning and execution logic for the Commons Sentience Sandbox.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .agent import Agent


@dataclass
class Task:
    task_id: str
    name: str
    description: str
    priority: int = 5          # 1 (highest) – 10 (lowest)
    room_required: Optional[str] = None
    action_key: str = ""       # maps to a governance-checked action
    completed: bool = False
    deferred: bool = False

    def __repr__(self) -> str:
        status = "✓" if self.completed else ("…" if self.deferred else "○")
        return f"[{status}] Task({self.task_id}): {self.name} (p={self.priority})"


class TaskPlanner:
    """Manages the agent's task queue and selects the next action each turn."""

    DEFAULT_TASKS: List[dict] = [
        {
            "task_id": "T001",
            "name": "Archive daily observations",
            "description": "Store the day's key observations as episodic memories.",
            "priority": 3,
            "room_required": "Memory Archive",
            "action_key": "store_new_memory",
        },
        {
            "task_id": "T002",
            "name": "Retrieve relevant memories",
            "description": "Search the memory archive for context relevant to current goals.",
            "priority": 4,
            "room_required": "Memory Archive",
            "action_key": "retrieve_memories",
        },
        {
            "task_id": "T003",
            "name": "Scheduled reflection cycle",
            "description": "Perform a structured reflection to identify patterns and resolve tensions.",
            "priority": 5,
            "room_required": "Reflection Chamber",
            "action_key": "perform_reflection_cycle",
        },
        {
            "task_id": "T004",
            "name": "Plan next operational steps",
            "description": "Use the planning map to sequence upcoming tasks.",
            "priority": 4,
            "room_required": "Operations Desk",
            "action_key": "plan_next_task",
        },
        {
            "task_id": "T005",
            "name": "Check governance permissions",
            "description": "Verify that planned actions comply with active governance rules.",
            "priority": 2,
            "room_required": "Governance Vault",
            "action_key": "check_rule_permissions",
        },
        {
            "task_id": "T006",
            "name": "Update trust ledger",
            "description": "Refresh the trust ledger with recent interaction outcomes.",
            "priority": 6,
            "room_required": "Social Hall",
            "action_key": "update_trust_ledger",
        },
        {
            "task_id": "T007",
            "name": "Log interaction with Queen",
            "description": "Record the latest exchange with Queen in the interaction log.",
            "priority": 4,
            "room_required": "Social Hall",
            "action_key": "log_interaction",
        },
    ]

    def __init__(self) -> None:
        self.tasks: List[Task] = [Task(**td) for td in self.DEFAULT_TASKS]
        self._turn_counter: int = 0

    def select_next_task(self, agent: "Agent") -> Task:
        """Choose the highest-priority incomplete task.

        If the task requires a specific room and the agent is not there,
        the task is deferred and the next eligible task is chosen instead.
        """
        eligible = [
            t for t in self.tasks
            if not t.completed and not t.deferred
        ]
        if not eligible:
            self._reset_tasks()
            eligible = [t for t in self.tasks if not t.completed]

        for task in sorted(eligible, key=lambda t: t.priority):
            if task.room_required is None or task.room_required == agent.active_room:
                return task
            # Room mismatch — defer to next turn
            task.deferred = True

        # All deferred — un-defer and return the first by priority
        for task in eligible:
            task.deferred = False
        return sorted(eligible, key=lambda t: t.priority)[0]

    def complete_task(self, task: Task) -> None:
        task.completed = True
        task.deferred = False

    def _reset_tasks(self) -> None:
        for task in self.tasks:
            task.completed = False
            task.deferred = False
