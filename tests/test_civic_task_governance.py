import unittest
from types import SimpleNamespace

from commons_sentience_sim.core.tasks import TaskPlanner


class TaskGovernanceBoundaryTests(unittest.TestCase):
    def test_selected_task_is_not_complete_until_explicit_approval(self):
        planner = TaskPlanner()
        agent = SimpleNamespace(active_room="Memory Archive")
        task = planner.select_next_task(agent)
        self.assertFalse(task.completed)
        self.assertFalse(task.deferred)

    def test_denied_task_remains_retryable(self):
        planner = TaskPlanner()
        agent = SimpleNamespace(active_room="Memory Archive")
        task = planner.select_next_task(agent)
        # A governance denial does not call complete_task.
        self.assertFalse(task.completed)
        self.assertIs(planner.select_next_task(agent), task)


if __name__ == "__main__":
    unittest.main()
