"""Tests for long-horizon experiment runs (Part 9 — Stage 3).

These tests verify that the pipeline runs end-to-end without crashing and
produces the expected output structure.  They use short durations (2–5 steps)
to keep the test suite fast.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from reality_audit.experiments.long_horizon_runs import (
    _SCENARIOS,
    _TURN_COUNTS,
    run_scenario,
)


class TestScenarioRegistry:
    """Scenario registry sanity checks."""

    def test_all_expected_scenarios_present(self):
        expected = {
            "baseline", "anisotropy", "observer_divergence",
            "bandwidth_limited", "random_baseline_agent", "normal_agent",
        }
        assert expected == set(_SCENARIOS)

    def test_turn_counts_defined(self):
        assert set(_TURN_COUNTS) == {50, 75, 100}

    def test_turn_count_durations_correct(self):
        # 50 turns * 0.5 s/turn = 25.0 s
        assert _TURN_COUNTS[50] == 25.0
        assert _TURN_COUNTS[75] == 37.5
        assert _TURN_COUNTS[100] == 50.0

    def test_invalid_scenario_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Unknown scenario"):
            run_scenario("nonexistent_scenario", 50, output_dir=tmp_path)

    def test_invalid_turn_count_raises(self, tmp_path):
        with pytest.raises(ValueError, match="n_turns must be one of"):
            run_scenario("baseline", 99, output_dir=tmp_path)


class TestRunScenarioPipeline:
    """End-to-end pipeline runs (short durations)."""

    def _run(self, tmp_path: Path, scenario: str) -> list:
        """Run a scenario with minimal turns (we override via small seed set)."""
        # We run with a single seed to keep things fast.
        # The long_horizon_runs module uses dt=0.5 and duration=25/37.5/50.
        # The smallest valid n_turns is 50 → duration=25.0 (50 steps at dt=0.5).
        # For tests, we monkeypatch _TURN_COUNTS to use a much shorter duration.
        import reality_audit.experiments.long_horizon_runs as lhr
        original = dict(lhr._TURN_COUNTS)
        lhr._TURN_COUNTS = {50: 1.0, 75: 1.5, 100: 2.0}  # 2–4 steps each
        try:
            results = run_scenario(
                scenario_name=scenario,
                n_turns=50,
                seeds=[42],
                output_dir=tmp_path,
            )
        finally:
            lhr._TURN_COUNTS = original
        return results

    def test_baseline_runs_without_crash(self, tmp_path):
        results = self._run(tmp_path, "baseline")
        assert len(results) == 1

    def test_anisotropy_runs_without_crash(self, tmp_path):
        results = self._run(tmp_path, "anisotropy")
        assert len(results) == 1

    def test_observer_divergence_runs_without_crash(self, tmp_path):
        results = self._run(tmp_path, "observer_divergence")
        assert len(results) == 1

    def test_bandwidth_limited_runs_without_crash(self, tmp_path):
        results = self._run(tmp_path, "bandwidth_limited")
        assert len(results) == 1

    def test_random_agent_runs_without_crash(self, tmp_path):
        results = self._run(tmp_path, "random_baseline_agent")
        assert len(results) == 1

    def test_normal_agent_runs_without_crash(self, tmp_path):
        results = self._run(tmp_path, "normal_agent")
        assert len(results) == 1

    def test_results_contain_required_keys(self, tmp_path):
        results = self._run(tmp_path, "baseline")
        run = results[0]
        assert "run_id" in run
        assert "metrics" in run
        assert "seed" in run

    def test_metrics_contain_required_fields(self, tmp_path):
        results = self._run(tmp_path, "baseline")
        metrics = results[0]["metrics"]
        required = [
            "position_error", "stability_score", "anisotropy_score",
            "bandwidth_bottleneck_score", "observer_dependence_score",
        ]
        for field in required:
            assert field in metrics, f"Missing metric: {field}"

    def test_multi_seed_produces_multiple_results(self, tmp_path):
        import reality_audit.experiments.long_horizon_runs as lhr
        original = dict(lhr._TURN_COUNTS)
        lhr._TURN_COUNTS = {50: 1.0, 75: 1.5, 100: 2.0}
        try:
            results = run_scenario("baseline", 50, seeds=[42, 43, 44], output_dir=tmp_path)
        finally:
            lhr._TURN_COUNTS = original
        assert len(results) == 3

    def test_output_summary_json_written(self, tmp_path):
        import reality_audit.experiments.long_horizon_runs as lhr
        original = dict(lhr._TURN_COUNTS)
        lhr._TURN_COUNTS = {50: 1.0, 75: 1.5, 100: 2.0}
        try:
            run_scenario("baseline", 50, seeds=[42], output_dir=tmp_path)
        finally:
            lhr._TURN_COUNTS = original
        # ExperimentRunner writes summary.json under <output_dir>/<name>/
        summary_files = list(tmp_path.rglob("summary.json"))
        assert len(summary_files) >= 1
