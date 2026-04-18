import json
import math
import tempfile
import unittest
from pathlib import Path

from reality_audit.experiment import ExperimentConfig, ExperimentRunner
from reality_audit.measurement import MeasurementSuite
from reality_audit.world import RealityWorld, WorldConfig, WorldMode


class ContinuousBaselineTests(unittest.TestCase):
    def test_continuous_baseline_runs(self):
        config = WorldConfig(mode=WorldMode.CONTINUOUS_BASELINE, duration=1.0, dt=0.1)
        world = RealityWorld(config)
        state = world.step((1.0, 0.0), observe=True)
        self.assertEqual(state.observed, True)
        self.assertIsInstance(state.position, tuple)


class DiscreteGridTests(unittest.TestCase):
    def test_quantizes_position(self):
        config = WorldConfig(mode=WorldMode.DISCRETE_GRID, duration=1.0, dt=0.1, params={"grid_size": 0.5})
        world = RealityWorld(config)
        for _ in range(20):
            state = world.step((1.0, 0.5), observe=True)
            self.assertAlmostEqual(state.position[0] % 0.5, 0.0, places=6)
            self.assertAlmostEqual(state.position[1] % 0.5, 0.0, places=6)


class NoisyQuantizedTests(unittest.TestCase):
    def test_measured_position_is_quantized(self):
        config = WorldConfig(
            mode=WorldMode.NOISY_QUANTIZED_MEASUREMENT,
            duration=1.0,
            dt=0.1,
            params={"quantization_step": 0.25, "measurement_noise": 0.0},
        )
        world = RealityWorld(config)
        for _ in range(10):
            state = world.step((1.0, 0.0), observe=True)
            self.assertAlmostEqual(state.measured_position[0] % 0.25, 0.0, places=6)


class AnisotropyTests(unittest.TestCase):
    def test_anisotropy_actually_changes_outcomes(self):
        """Anisotropic mode must produce a measurably different trajectory than baseline."""
        params = {"preferred_axis": 0.0, "axis_strength": 3.0, "measurement_noise": 0.0}
        baseline_config = WorldConfig(
            mode=WorldMode.CONTINUOUS_BASELINE, duration=2.0, dt=0.1,
            start_position=(0.0, 0.0), seed=1,
        )
        aniso_config = WorldConfig(
            mode=WorldMode.ANISOTROPIC_PREFERRED_AXIS, duration=2.0, dt=0.1,
            start_position=(0.0, 0.0), params=params, seed=1,
        )
        baseline_world = RealityWorld(baseline_config)
        aniso_world = RealityWorld(aniso_config)
        control = (1.0, 1.0)
        for _ in range(20):
            baseline_state = baseline_world.step(control)
            aniso_state = aniso_world.step(control)
        self.assertNotAlmostEqual(
            baseline_state.position[0], aniso_state.position[0], places=3,
            msg="Anisotropic mode produced same x-position as baseline; distortion had no effect",
        )

    def test_anisotropy_score_higher_in_aniso_mode(self):
        """MeasurementSuite.anisotropy_score must be higher under anisotropic mode."""
        params = {"preferred_axis": 0.0, "axis_strength": 3.0, "measurement_noise": 0.0}

        def run_log(mode, extra_params):
            cfg = WorldConfig(mode=mode, duration=3.0, dt=0.1, start_position=(0.0, 0.0),
                               params=extra_params, seed=7)
            world = RealityWorld(cfg)
            log = []
            for _ in range(30):
                s = world.step((1.0, 1.0), observe=True)
                log.append({"measured_position": s.measured_position, "measured_velocity": s.measured_velocity})
            return log

        baseline_log = run_log(WorldMode.CONTINUOUS_BASELINE, {})
        aniso_log = run_log(WorldMode.ANISOTROPIC_PREFERRED_AXIS, params)
        self.assertGreater(
            MeasurementSuite.anisotropy_score(aniso_log),
            MeasurementSuite.anisotropy_score(baseline_log),
            "Anisotropy score not higher under anisotropic mode",
        )


class ObserverTests(unittest.TestCase):
    def test_hidden_state_decays_when_unobserved(self):
        """hidden_state must diverge from actual position after unobserved steps."""
        config = WorldConfig(
            mode=WorldMode.OBSERVER_TRIGGERED_UPDATES,
            duration=2.0,
            dt=0.1,
            params={"hidden_decay": 0.8, "measurement_noise": 0.0},
            start_position=(5.0, 5.0),
        )
        world = RealityWorld(config)
        for _ in range(10):
            state = world.step((0.0, 0.0), observe=False)
        hidden_pos = state.hidden_state["position"]
        actual_pos = state.position
        dist = math.hypot(hidden_pos[0] - actual_pos[0], hidden_pos[1] - actual_pos[1])
        self.assertGreater(dist, 0.1,
            "Hidden state did not diverge from actual position under unobserved evolution")

    def test_observer_dependence_score_is_nonzero(self):
        """observer_dependence_score must be > 0 under periodic observation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExperimentConfig(
                name="obs_test",
                world_mode="observer_triggered_updates",
                controllers=["proportional"],
                seeds=[0],
                duration=2.0,
                dt=0.1,
                start_position=[5.0, 5.0],
                goal_position=[5.0, 5.0],
                world_params={"hidden_decay": 0.7, "measurement_noise": 0.0, "max_speed": 1.0,
                               "observe_period": 5},
                observation_policy="periodic_observe",
                output_dir=str(tmpdir),
            )
            runner = ExperimentRunner(config)
            results = runner.run()
            score = results[0]["metrics"]["observer_dependence_score"]
            self.assertGreater(score, 0.0,
                f"observer_dependence_score was {score}, expected > 0 under periodic observation")


class BandwidthTests(unittest.TestCase):
    def test_bandwidth_limit_produces_stale_measurements(self):
        """Unobserved steps must return stale (frozen) measurement, not physics position."""
        # dt=0.01, max_updates_per_second=5 -> update interval=0.2s -> observe every 20 steps
        config = WorldConfig(
            mode=WorldMode.BANDWIDTH_LIMITED,
            duration=2.0,
            dt=0.01,
            start_position=(0.0, 0.0),
            params={"max_updates_per_second": 5, "measurement_noise": 0.0, "max_speed": 2.0},
            seed=0,
        )
        world = RealityWorld(config)
        stale_count = 0
        last_observed_pos = None
        for _ in range(50):
            state = world.step((1.0, 0.0), observe=True)
            if not state.observed:
                stale_count += 1
                if last_observed_pos is not None:
                    self.assertEqual(state.measured_position, last_observed_pos,
                        "Stale measurement changed on an unobserved step")
            else:
                last_observed_pos = state.measured_position
        self.assertGreater(stale_count, 0,
            "No bandwidth-suppressed steps occurred; check dt and max_updates_per_second")

    def test_actual_position_advances_during_bandwidth_suppression(self):
        """Physics must keep advancing even while sensing is suppressed."""
        config = WorldConfig(
            mode=WorldMode.BANDWIDTH_LIMITED,
            duration=1.0,
            dt=0.01,
            start_position=(0.0, 0.0),
            params={"max_updates_per_second": 2, "measurement_noise": 0.0, "max_speed": 2.0},
            seed=0,
        )
        world = RealityWorld(config)
        for _ in range(80):
            state = world.step((1.0, 0.0), observe=True)
        self.assertGreater(state.position[0], 0.5)


class PreferredFrameConsistencyTests(unittest.TestCase):
    def test_rotated_config_uses_rotated_reference_frame(self):
        """Agent must converge toward the ROTATED goal, not the original unrotated goal."""
        angle = math.pi / 4  # 45 degrees
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExperimentConfig(
                name="frame_test",
                world_mode="continuous_baseline",
                controllers=["proportional"],
                seeds=[0],
                duration=2.0,
                dt=0.05,
                start_position=[0.0, 0.0],
                goal_position=[10.0, 0.0],
                orientation_rotations=[angle],
                world_params={"max_speed": 4.0},
                output_dir=str(tmpdir),
            )
            runner = ExperimentRunner(config)
            results = runner.run()
            run_id = results[0]["run_id"]
            raw_log_path = Path(tmpdir) / "frame_test" / run_id / "raw_log.json"
            log = json.loads(raw_log_path.read_text())
            final_pos = log[-1]["position"]
            rotated_gx = 10.0 * math.cos(angle)
            rotated_gy = 10.0 * math.sin(angle)
            dist_rotated = math.hypot(final_pos[0] - rotated_gx, final_pos[1] - rotated_gy)
            dist_original = math.hypot(final_pos[0] - 10.0, final_pos[1] - 0.0)
            self.assertLess(dist_rotated, dist_original,
                f"Agent converged toward original goal (dist={dist_original:.3f}) "
                f"instead of rotated goal (dist={dist_rotated:.3f})")


if __name__ == "__main__":
    unittest.main()
