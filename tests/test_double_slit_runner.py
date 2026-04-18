"""
tests/test_double_slit_runner.py — Tests for the double-slit benchmark runner.
"""

from __future__ import annotations

import json
import csv
from pathlib import Path

import pytest

from reality_audit.benchmarks.double_slit_runner import run_double_slit_benchmark


class TestRunDoubleSlit:
    def test_returns_required_keys(self, tmp_path):
        result = run_double_slit_benchmark(n_trials=200, n_bins=20, output_dir=tmp_path)
        for key in ["config", "conditions", "results", "summary_per_condition", "output_dir"]:
            assert key in result

    def test_all_conditions_run(self, tmp_path):
        result = run_double_slit_benchmark(n_trials=200, n_bins=20, output_dir=tmp_path)
        assert set(result["conditions"]) == {"one_slit", "two_slit", "two_slit_measured"}

    def test_config_json_written(self, tmp_path):
        run_double_slit_benchmark(n_trials=200, n_bins=20, output_dir=tmp_path)
        config_path = tmp_path / "config.json"
        assert config_path.exists()
        config = json.loads(config_path.read_text())
        assert config["benchmark"] == "double_slit"
        assert "honest_framing" in config

    def test_raw_results_json_written(self, tmp_path):
        run_double_slit_benchmark(n_trials=200, n_bins=20, output_dir=tmp_path)
        raw_path = tmp_path / "raw_results.json"
        assert raw_path.exists()
        data = json.loads(raw_path.read_text())
        assert "one_slit" in data
        assert "two_slit" in data
        assert "two_slit_measured" in data

    def test_raw_results_csv_written(self, tmp_path):
        run_double_slit_benchmark(n_trials=200, n_bins=20, output_dir=tmp_path)
        csv_path = tmp_path / "raw_results.csv"
        assert csv_path.exists()
        with open(csv_path, newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) > 0
        assert "condition" in rows[0]
        assert "screen_position" in rows[0]
        assert "intensity" in rows[0]
        assert "hit_count" in rows[0]

    def test_top_level_summary_json_written(self, tmp_path):
        run_double_slit_benchmark(n_trials=200, n_bins=20, output_dir=tmp_path)
        summary_path = tmp_path / "summary.json"
        assert summary_path.exists()
        summary = json.loads(summary_path.read_text())
        assert "per_condition" in summary

    def test_per_condition_subdirs_written(self, tmp_path):
        run_double_slit_benchmark(n_trials=200, n_bins=20, output_dir=tmp_path)
        for cond in ["one_slit", "two_slit", "two_slit_measured"]:
            cond_summary = tmp_path / cond / "summary.json"
            assert cond_summary.exists(), f"Missing {cond}/summary.json"

    def test_csv_row_count(self, tmp_path):
        n_bins = 30
        run_double_slit_benchmark(n_trials=200, n_bins=n_bins, output_dir=tmp_path)
        csv_path = tmp_path / "raw_results.csv"
        with open(csv_path, newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        # 3 conditions × n_bins rows
        assert len(rows) == 3 * n_bins

    def test_config_contains_honest_framing(self, tmp_path):
        run_double_slit_benchmark(n_trials=100, n_bins=10, output_dir=tmp_path)
        config = json.loads((tmp_path / "config.json").read_text())
        assert "classical_wave_optics" in config["model_type"]
        assert "NOT" in config["honest_framing"]
