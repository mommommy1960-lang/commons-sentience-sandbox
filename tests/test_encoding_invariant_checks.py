"""Tests for reality_audit/analysis/encoding_invariant_checks.py"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from reality_audit.analysis.encoding_invariant_checks import (
    _direction,
    _classify_ordering_consensus,
    build_invariant_checks_from_encoding_report,
    _build_synthetic_checks,
    run_encoding_invariant_checks,
)


# ---------------------------------------------------------------------------
# _direction
# ---------------------------------------------------------------------------

class TestDirection:
    def test_greater(self):
        assert _direction(2.0, 1.0) == "greater"

    def test_lesser(self):
        assert _direction(1.0, 2.0) == "lesser"

    def test_equal_within_tolerance(self):
        assert _direction(1.0, 1.04) == "equal"

    def test_none_input(self):
        assert _direction(None, 1.0) is None
        assert _direction(1.0, None) is None

    def test_both_none(self):
        assert _direction(None, None) is None

    def test_large_values_equal(self):
        # 100 vs 104 — within 5%
        assert _direction(100.0, 104.0) == "equal"

    def test_large_values_greater(self):
        assert _direction(100.0, 50.0) == "greater"


# ---------------------------------------------------------------------------
# _classify_ordering_consensus
# ---------------------------------------------------------------------------

class TestClassifyOrderingConsensus:
    def test_all_same(self):
        assert _classify_ordering_consensus(["greater", "greater", "greater"]) == "invariant"

    def test_two_of_three(self):
        assert _classify_ordering_consensus(["greater", "greater", "lesser"]) == "partially_invariant"

    def test_all_different(self):
        assert _classify_ordering_consensus(["greater", "lesser", "equal"]) == "encoding_sensitive"

    def test_empty(self):
        assert _classify_ordering_consensus([]) == "encoding_sensitive"

    def test_all_none_filtered(self):
        assert _classify_ordering_consensus([None, None, None]) == "encoding_sensitive"

    def test_single_valid(self):
        assert _classify_ordering_consensus([None, None, "greater"]) == "invariant"


# ---------------------------------------------------------------------------
# build_invariant_checks_from_encoding_report
# ---------------------------------------------------------------------------

class TestBuildChecksFromReport:
    def _make_enc_report(self, metric_values: dict) -> dict:
        """Build a minimal encoding_robustness_report structure."""
        metrics = {}
        for metric, per_enc in metric_values.items():
            metrics[metric] = {
                "per_encoding": {
                    enc: {"value": v} for enc, v in per_enc.items()
                },
                "verdict": "ENCODING-SENSITIVE",
            }
        return {"metrics": metrics}

    def test_returns_list(self):
        report = self._make_enc_report(
            {"path_smoothness": {"A": 0.4, "B": 0.41, "C": 0.39}}
        )
        records = build_invariant_checks_from_encoding_report(report)
        assert isinstance(records, list)

    def test_three_way_consensus_created(self):
        report = self._make_enc_report(
            {"path_smoothness": {"enc1": 0.4, "enc2": 0.39, "enc3": 0.41}}
        )
        records = build_invariant_checks_from_encoding_report(report)
        three_way = [r for r in records if r.get("check_type") == "three_way_consensus"]
        assert len(three_way) >= 1

    def test_non_target_metric_excluded(self):
        report = self._make_enc_report(
            {"audit_bandwidth": {"enc1": 1.0, "enc2": 1.0}}
        )
        records = build_invariant_checks_from_encoding_report(report)
        assert not any(r.get("metric") == "audit_bandwidth" for r in records)

    def test_pair_records_created(self):
        report = self._make_enc_report(
            {"mean_position_error": {"enc1": 2.0, "enc2": 3.0, "enc3": 2.5}}
        )
        records = build_invariant_checks_from_encoding_report(report)
        pairwise = [r for r in records if r.get("check_type") != "three_way_consensus"]
        assert len(pairwise) >= 1


# ---------------------------------------------------------------------------
# _build_synthetic_checks
# ---------------------------------------------------------------------------

class TestBuildSyntheticChecks:
    def test_returns_four_entries(self):
        checks = _build_synthetic_checks()
        assert len(checks) == 4

    def test_path_smoothness_invariant(self):
        checks = _build_synthetic_checks()
        ps = next(c for c in checks if c["metric"] == "path_smoothness")
        assert ps["invariance_verdict"] == "invariant"

    def test_position_error_sensitive(self):
        checks = _build_synthetic_checks()
        pe = next(c for c in checks if c["metric"] == "mean_position_error")
        assert pe["invariance_verdict"] == "encoding_sensitive"

    def test_all_have_required_keys(self):
        for c in _build_synthetic_checks():
            assert "metric" in c
            assert "invariance_verdict" in c


# ---------------------------------------------------------------------------
# run_encoding_invariant_checks
# ---------------------------------------------------------------------------

class TestRunEncodingInvariantChecks:
    def test_uses_synthetic_when_no_report(self, tmp_path):
        result = run_encoding_invariant_checks(output_root=tmp_path)
        assert result["source"] == "synthetic_from_stage4"

    def test_report_written(self, tmp_path):
        run_encoding_invariant_checks(output_root=tmp_path)
        assert (tmp_path / "encoding_invariant_report.json").exists()

    def test_invariance_summary_present(self, tmp_path):
        result = run_encoding_invariant_checks(output_root=tmp_path)
        assert "invariance_summary" in result
        assert len(result["invariance_summary"]) > 0

    def test_path_smoothness_invariant_in_synthetic(self, tmp_path):
        result = run_encoding_invariant_checks(output_root=tmp_path)
        assert result["invariance_summary"].get("path_smoothness") == "invariant"

    def test_uses_live_report_when_present(self, tmp_path):
        enc_report = {
            "metrics": {
                "path_smoothness": {
                    "per_encoding": {
                        "BFS_MDS": {"value": 0.4},
                        "PureHop": {"value": 0.41},
                        "Manual": {"value": 0.39},
                    },
                    "verdict": "ROBUST",
                }
            }
        }
        (tmp_path / "encoding_robustness_report.json").write_text(json.dumps(enc_report))
        result = run_encoding_invariant_checks(output_root=tmp_path)
        assert result["source"] == "live"

    def test_interpretation_keys_present(self, tmp_path):
        result = run_encoding_invariant_checks(output_root=tmp_path)
        assert "invariant" in result["interpretation"]
        assert "encoding_sensitive" in result["interpretation"]
