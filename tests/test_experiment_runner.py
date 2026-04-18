import json
import tempfile
import unittest
from pathlib import Path

from reality_audit.experiment import ExperimentConfig, ExperimentRunner

class ExperimentRunnerTests(unittest.TestCase):
    def test_experiment_outputs_are_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExperimentConfig(
                name="unit_test_audit",
                world_mode="continuous_baseline",
                controllers=["proportional"],
                seeds=[0],
                duration=1.0,
                dt=0.1,
                start_position=[0.0, 0.0],
                goal_position=[2.0, 0.0],
                world_params={"max_speed": 1.5},
                output_dir=str(tmpdir),
            )
            runner = ExperimentRunner(config)
            results = runner.run()
            self.assertEqual(len(results), 1)
            output_path = Path(tmpdir) / config.name
            self.assertTrue((output_path / "summary.json").exists())
            self.assertTrue((output_path / "config.json").exists())
            run_dir = next(p for p in output_path.iterdir() if p.is_dir())
            self.assertTrue((run_dir / "raw_log.json").exists())
            self.assertTrue((run_dir / "summary.json").exists())
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertIn("position_error", summary)

if __name__ == "__main__":
    unittest.main()
