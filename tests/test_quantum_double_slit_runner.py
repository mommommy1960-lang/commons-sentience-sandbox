"""Tests for quantum_double_slit_runner.py."""

import json
import csv
from pathlib import Path
import pytest
from reality_audit.benchmarks.quantum_double_slit_runner import run_quantum_double_slit_benchmark


@pytest.fixture()
def benchmark_output(tmp_path):
    return run_quantum_double_slit_benchmark(
        n_trials=200,
        n_bins=10,
        seed=0,
        screen_width=10.0,
        partial_gammas=[0.0, 0.5, 1.0],
        output_dir=tmp_path,
    )


class TestRunnerOutputFiles:
    def test_config_json_written(self, benchmark_output, tmp_path):
        assert (tmp_path / "config.json").exists()

    def test_raw_results_json_written(self, benchmark_output, tmp_path):
        assert (tmp_path / "raw_results.json").exists()

    def test_summary_json_written(self, benchmark_output, tmp_path):
        assert (tmp_path / "summary.json").exists()

    def test_decoherence_sweep_json_written(self, benchmark_output, tmp_path):
        assert (tmp_path / "decoherence_sweep.json").exists()

    def test_raw_results_csv_written(self, benchmark_output, tmp_path):
        assert (tmp_path / "raw_results.csv").exists()


class TestRunnerConfigContent:
    def test_config_has_expected_keys(self, benchmark_output, tmp_path):
        cfg = json.loads((tmp_path / "config.json").read_text())
        for key in ["benchmark", "n_trials", "slit_separation", "wavelength", "partial_gammas"]:
            assert key in cfg

    def test_config_n_trials(self, benchmark_output, tmp_path):
        cfg = json.loads((tmp_path / "config.json").read_text())
        assert cfg["n_trials"] == 200

    def test_config_honest_framing_present(self, benchmark_output, tmp_path):
        cfg = json.loads((tmp_path / "config.json").read_text())
        assert "honest_framing" in cfg


class TestRunnerReturnValue:
    def test_return_has_config_results_output_dir(self, benchmark_output):
        for key in ["config", "results", "output_dir"]:
            assert key in benchmark_output

    def test_results_has_all_conditions(self, benchmark_output):
        results = benchmark_output["results"]
        for key in ["one_slit", "two_slit_coherent", "two_slit_decohered", "decoherence_sweep"]:
            assert key in results


class TestRunnerCSV:
    def test_csv_has_required_columns(self, benchmark_output, tmp_path):
        with open(tmp_path / "raw_results.csv", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        for col in ["condition", "gamma", "bin_index", "screen_position", "probability", "hit_count"]:
            assert col in row

    def test_csv_has_rows_for_sweep(self, benchmark_output, tmp_path):
        with open(tmp_path / "raw_results.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        sweep_rows = [r for r in rows if r["condition"] == "two_slit_partial"]
        # 3 gammas × 10 bins = 30 sweep rows
        assert len(sweep_rows) == 30


class TestRunnerPerConditionDirs:
    def test_one_slit_summary_written(self, benchmark_output, tmp_path):
        assert (tmp_path / "one_slit" / "summary.json").exists()

    def test_two_slit_coherent_summary_written(self, benchmark_output, tmp_path):
        assert (tmp_path / "two_slit_coherent" / "summary.json").exists()

    def test_decoherence_sweep_dir_created(self, benchmark_output, tmp_path):
        assert (tmp_path / "decoherence_sweep").is_dir()
