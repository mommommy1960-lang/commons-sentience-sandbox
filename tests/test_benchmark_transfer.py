"""
tests/test_benchmark_transfer.py
=================================
Tests for the benchmark-to-method transfer module.

Covers:
  - TransferPrinciple dataclass
  - PRINCIPLES library completeness
  - run_benchmark_transfer() output structure
  - Each principle has a known source and trust level
  - Report is written to disk
  - All principles verified when implementation files exist
"""

import json
import os
import pytest

from reality_audit.analysis.benchmark_transfer import (
    TransferPrinciple,
    PRINCIPLES,
    run_benchmark_transfer,
)


class TestTransferPrinciple:
    def test_dataclass_fields(self):
        p = TransferPrinciple(
            id="PXX",
            source="test source",
            statement="test statement",
            implementation="test impl",
            validation_test="test_something",
            trust_level="high",
        )
        assert p.id == "PXX"
        assert p.trust_level == "high"
        assert p.verified is False

    def test_to_dict_has_all_fields(self):
        p = TransferPrinciple(
            id="P01", source="s", statement="x",
            implementation="i", validation_test="v",
            trust_level="medium",
        )
        d = p.to_dict()
        for key in ("id", "source", "statement", "implementation",
                    "validation_test", "trust_level", "verified"):
            assert key in d


class TestPrinciplesLibrary:
    def test_minimum_principles(self):
        assert len(PRINCIPLES) >= 10

    def test_all_have_unique_ids(self):
        ids = [p.id for p in PRINCIPLES]
        assert len(ids) == len(set(ids))

    def test_all_have_non_empty_statement(self):
        for p in PRINCIPLES:
            assert len(p.statement) > 10, f"{p.id} has empty statement"

    def test_all_have_trust_level(self):
        valid = {"high", "medium", "low"}
        for p in PRINCIPLES:
            assert p.trust_level in valid, f"{p.id}: bad trust level"

    def test_all_have_source(self):
        for p in PRINCIPLES:
            assert len(p.source) > 0, f"{p.id} missing source"

    def test_at_least_one_from_each_benchmark(self):
        sources = " ".join(p.source for p in PRINCIPLES).lower()
        assert "double-slit" in sources
        assert "quantum" in sources
        assert "sandbox" in sources or "stage" in sources

    def test_majority_high_trust(self):
        high = sum(1 for p in PRINCIPLES if p.trust_level == "high")
        assert high >= len(PRINCIPLES) // 2


class TestRunBenchmarkTransfer:
    def test_returns_dict(self, tmp_path):
        out = str(tmp_path / "transfer_report.json")
        result = run_benchmark_transfer(output_path=out)
        assert isinstance(result, dict)

    def test_output_keys(self, tmp_path):
        out = str(tmp_path / "transfer_report.json")
        result = run_benchmark_transfer(output_path=out)
        for key in ("title", "total_principles", "verified",
                    "high_trust", "all_verified", "principles", "summary"):
            assert key in result

    def test_all_verified_when_files_exist(self, tmp_path):
        out = str(tmp_path / "transfer_report.json")
        result = run_benchmark_transfer(output_path=out)
        # Implementation files exist — all principles should be verified
        assert result["all_verified"] is True

    def test_total_matches_library(self, tmp_path):
        out = str(tmp_path / "transfer_report.json")
        result = run_benchmark_transfer(output_path=out)
        assert result["total_principles"] == len(PRINCIPLES)

    def test_file_written(self, tmp_path):
        out = str(tmp_path / "transfer_report.json")
        run_benchmark_transfer(output_path=out)
        assert os.path.exists(out)

    def test_json_valid(self, tmp_path):
        out = str(tmp_path / "transfer_report.json")
        run_benchmark_transfer(output_path=out)
        with open(out) as f:
            data = json.load(f)
        assert isinstance(data["principles"], list)

    def test_summary_string_non_empty(self, tmp_path):
        out = str(tmp_path / "report.json")
        result = run_benchmark_transfer(output_path=out)
        assert len(result["summary"]) > 10

    def test_principles_list_in_report(self, tmp_path):
        out = str(tmp_path / "report.json")
        result = run_benchmark_transfer(output_path=out)
        for p in result["principles"]:
            assert "id" in p
            assert "trust_level" in p
            assert "verified" in p

    def test_next_step_present(self, tmp_path):
        out = str(tmp_path / "report.json")
        result = run_benchmark_transfer(output_path=out)
        assert "next_step" in result
        assert len(result["next_step"]) > 0
