"""Tests for advanced_quantum_runner.py."""

import json
import csv
import pytest
from pathlib import Path
from reality_audit.benchmarks.advanced_quantum_runner import run_advanced_benchmark


@pytest.fixture(scope="module")
def benchmark_output(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("adv_runner")
    return run_advanced_benchmark(
        n_trials=200,
        n_bins=10,
        seed=0,
        screen_width=10.0,
        eraser_overlap=0.5,
        overlap_values=[1.0, 0.5, 0.0],
        n_repeated_runs=10,
        output_dir=tmp,
    ), tmp


class TestRunnerOutputFiles:
    def test_config_json(self, benchmark_output):
        _, tmp = benchmark_output
        assert (tmp / "config.json").exists()

    def test_raw_results_json(self, benchmark_output):
        _, tmp = benchmark_output
        assert (tmp / "raw_results.json").exists()

    def test_summary_json(self, benchmark_output):
        _, tmp = benchmark_output
        assert (tmp / "summary.json").exists()

    def test_aggregate_summary_json(self, benchmark_output):
        _, tmp = benchmark_output
        assert (tmp / "aggregate_summary.json").exists()

    def test_raw_results_csv(self, benchmark_output):
        _, tmp = benchmark_output
        assert (tmp / "raw_results.csv").exists()

    def test_per_condition_dirs(self, benchmark_output):
        _, tmp = benchmark_output
        for cond in ["one_slit", "two_slit_coherent", "two_slit_which_path"]:
            assert (tmp / cond / "summary.json").exists()


class TestRunnerReturnValue:
    def test_has_expected_keys(self, benchmark_output):
        result, _ = benchmark_output
        for k in ["config", "results", "aggregate_100run", "output_dir"]:
            assert k in result

    def test_results_has_all_conditions(self, benchmark_output):
        result, _ = benchmark_output
        for k in ["one_slit", "two_slit_coherent", "two_slit_which_path",
                  "eraser_plus", "eraser_minus", "overlap_sweep"]:
            assert k in result["results"]


class TestRunnerConfigContent:
    def test_config_n_trials(self, benchmark_output):
        result, _ = benchmark_output
        assert result["config"]["n_trials"] == 200

    def test_config_honest_framing(self, benchmark_output):
        result, _ = benchmark_output
        assert "honest_framing" in result["config"]


class TestRunnerAggregateSummary:
    def test_aggregate_has_expected_keys(self, benchmark_output):
        result, _ = benchmark_output
        agg = result["aggregate_100run"]
        assert "two_slit_coherent" in agg
        assert "two_slit_which_path" in agg

    def test_stability_assessment_present(self, benchmark_output):
        result, _ = benchmark_output
        assert "stability_assessment" in result["aggregate_100run"]

    def test_n_repeated_runs_correct(self, benchmark_output):
        result, _ = benchmark_output
        assert result["aggregate_100run"]["n_repeated_runs"] == 10


class TestRunnerCSV:
    def test_csv_has_required_columns(self, benchmark_output):
        _, tmp = benchmark_output
        with open(tmp / "raw_results.csv", newline="") as f:
            row = next(csv.DictReader(f))
        for col in ["condition", "detector_overlap", "bin_index", "screen_position",
                    "probability", "hit_count"]:
            assert col in row
