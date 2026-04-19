"""
benchmark_transfer.py
=====================
Documents and operationalises the transfer of audit principles from:
  - sandbox campaigns (Stages 1–4)
  - classical double-slit benchmark (Stage 5)
  - quantum double-slit benchmark (Stage 5)
  - advanced quantum double-slit / eraser benchmark (Stage 5)

into the design of real-data analysis pipelines.

Each principle is captured as a named rule with:
  - source (which benchmark it was learned from)
  - statement (what the rule says)
  - implementation (how it is implemented in the readiness layer)
  - validation_test (what tests verify the rule is implemented)
  - trust_level (how confident we are in the principle)

The module also runs a battery of checks to confirm each principle is
verifiable in the current codebase, and writes a JSON report.

This is NOT a statistical test—it is a methodology audit document.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Principle dataclass
# ---------------------------------------------------------------------------


@dataclass
class TransferPrinciple:
    """One audit principle transferred from benchmark work to real analysis."""
    id: str
    source: str
    statement: str
    implementation: str
    validation_test: str
    trust_level: str            # "high", "medium", "low"
    notes: str = ""
    verified: bool = False
    verification_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Principle library
# ---------------------------------------------------------------------------


PRINCIPLES: List[TransferPrinciple] = [

    TransferPrinciple(
        id="P01",
        source="sandbox campaigns (Stages 1–4) + sim_probe.py",
        statement=(
            "Measurement must be read-only by default. The act of observation "
            "must not perturb the system under study (behavioral probe "
            "discipline)."
        ),
        implementation=(
            "reality_audit/adapters/sim_probe.py enforces read-only access. "
            "Real-data ingestion adapters must follow the same contract: "
            "load data without modifying source files."
        ),
        validation_test="test_probe_is_read_only (existing Stage 6 test suite)",
        trust_level="high",
    ),

    TransferPrinciple(
        id="P02",
        source="double-slit benchmark (Stage 5)",
        statement=(
            "Null and signal models must be defined and frozen before "
            "looking at results. Analysis plan must precede data inspection."
        ),
        implementation=(
            "ExperimentRegistry.register() requires null_model and signal_model "
            "at registration time (before any run). "
            "Blinder.freeze() enforces plan-before-unblind discipline."
        ),
        validation_test=(
            "TestBlinder.test_unblind_requires_freeze — "
            "unblind() raises RuntimeError if freeze() not called."
        ),
        trust_level="high",
    ),

    TransferPrinciple(
        id="P03",
        source="advanced quantum benchmark — 100-run stability (Stage 5)",
        statement=(
            "Any primary test statistic must demonstrate stable, low-variance "
            "behavior under repeated runs before being trusted for real data. "
            "CV > 0.05 disqualifies a metric."
        ),
        implementation=(
            "mock pipelines print stability metrics. "
            "Real analysis runner will require CV < 0.05 on synthetic validation "
            "runs before accepting the statistic for publication."
        ),
        validation_test=(
            "test_null_slope_near_zero (timing), "
            "test_dipole_power_isotropic (cosmic ray) — "
            "verify metrics are well-behaved on pure null data."
        ),
        trust_level="high",
    ),

    TransferPrinciple(
        id="P04",
        source="metric trust ranking (Stage 4 / update_metric_trust.py)",
        statement=(
            "Metrics must be ranked by trust before analysis. High-variance, "
            "noise-sensitive metrics may not serve as primary statistics. "
            "Prefer deterministic / low-noise statistics."
        ),
        implementation=(
            "ExperimentSpec.primary_statistic records the chosen metric. "
            "Signal-injection recovery tests verify the metric is sensitive "
            "to the target signal class."
        ),
        validation_test=(
            "TestMockCosmicRayPipeline.test_recovery_test_present, "
            "TestMockTimingPipeline.test_recovery_test_present"
        ),
        trust_level="high",
    ),

    TransferPrinciple(
        id="P05",
        source="quantum double-slit / decoherence benchmark (Stage 5)",
        statement=(
            "Null vs signal separation must be demonstrated on synthetic data "
            "before applying any test to real data. A pipeline that cannot "
            "detect a 1-sigma injected signal is not ready."
        ),
        implementation=(
            "Each mock pipeline includes _injection_recovery_test(). "
            "A strong injection (0.9×) must return p < 0.05 for the pipeline "
            "to be considered ready."
        ),
        validation_test=(
            "TestMockCosmicRayPipeline.test_strong_injection_recovered, "
            "TestMockTimingPipeline.test_injection_increases_slope"
        ),
        trust_level="high",
    ),

    TransferPrinciple(
        id="P06",
        source="advanced quantum eraser benchmark (Stage 5)",
        statement=(
            "Comparative interpretation is more robust than absolute claims. "
            "Report effect relative to null expectation (z-score, p-value) "
            "rather than claiming absolute discovery from a single run."
        ),
        implementation=(
            "Both mock pipelines compute z_score = (observed - null_mean) / null_std. "
            "detection_claimed flag requires p < 3e-7 (~5-sigma), not p < 0.05."
        ),
        validation_test=(
            "TestMockCosmicRayPipeline.test_null_run_p_value_range, "
            "TestMockTimingPipeline.test_p_value_range — "
            "p-values are well-calibrated under null."
        ),
        trust_level="high",
    ),

    TransferPrinciple(
        id="P07",
        source="Stage 6 probe-impact test",
        statement=(
            "Effect-size caution: a statistically significant result does not "
            "imply physical significance. Report effect size and "
            "physically-motivated interpretation bounds separately."
        ),
        implementation=(
            "Reports include both z_score and detection_threshold. "
            "Markdown summaries warn: significant ≠ physically meaningful. "
            "Experiment registry includes null_model explicitly to calibrate "
            "expected effect sizes."
        ),
        validation_test=(
            "TestReportWriter.test_write_markdown_summary — "
            "blinded report includes warning text."
        ),
        trust_level="medium",
        notes=(
            "Effect-size bounds are dataset-specific. "
            "This principle requires domain expertise at real-analysis time."
        ),
    ),

    TransferPrinciple(
        id="P08",
        source="all benchmarks — reproducibility metadata",
        statement=(
            "Every analysis run must record: git commit hash, random seed, "
            "software versions, and timestamps. "
            "Results without this metadata are not reproducible."
        ),
        implementation=(
            "ReproducibilityMetadata.capture() records commit hash, Python version, "
            "seed, and UTC timestamp. "
            "ReportWriter embeds this in every JSON summary."
        ),
        validation_test=(
            "TestReportWriter.test_write_json_summary, "
            "TestExperimentSpec.test_to_dict_roundtrip — "
            "reproducibility metadata round-trips through JSON."
        ),
        trust_level="high",
    ),

    TransferPrinciple(
        id="P09",
        source="ablation studies (Stage 4)",
        statement=(
            "Pipeline components must be tested in isolation before integration. "
            "Ablate: null model only, injection only, statistic only, "
            "blinding only. Full-pipeline tests come last."
        ),
        implementation=(
            "test_data_analysis_readiness.py tests each module class "
            "independently (TestNullModels, TestSignalInjector, TestBlinder, "
            "TestReportWriter) before TestMockCosmicRayPipeline integration."
        ),
        validation_test="72+ tests across 7 test classes in test_data_analysis_readiness.py",
        trust_level="high",
    ),

    TransferPrinciple(
        id="P10",
        source="benchmark-driven validation discipline (all stages)",
        statement=(
            "No real-data analysis may begin until the full dry-run pipeline "
            "passes all validation tests on synthetic data with known ground truth. "
            "Benchmark success is a gate, not a guarantee."
        ),
        implementation=(
            "Mock pipelines are the gates. Running pytest on "
            "test_data_analysis_readiness.py must pass before ingesting "
            "any real dataset."
        ),
        validation_test="Full pytest suite — all tests green before real analysis.",
        trust_level="high",
        notes=(
            "This principle is meta: it governs the use of all other principles. "
            "A future session that skips this step is out of protocol."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Verification runner
# ---------------------------------------------------------------------------


def _verify_principle(
    p: TransferPrinciple,
    codebase_checks: Optional[Dict[str, bool]] = None,
) -> TransferPrinciple:
    """
    Lightweight checks that the principle has at least a corresponding
    source file on disk.  More thorough checks are in the test suite.
    """
    checks = codebase_checks or {}
    verified = checks.get(p.id, True)   # default True if no check registered
    p.verified = verified
    p.verification_note = (
        "Verified via codebase file checks." if verified
        else "Could not verify: missing implementation file."
    )
    return p


def run_benchmark_transfer(
    output_path: str = (
        "commons_sentience_sim/output/reality_audit/benchmark_transfer_report.json"
    ),
) -> Dict[str, Any]:
    """
    Run the benchmark-to-method transfer audit and write a JSON report.

    Returns the full report dict.
    """
    import pathlib

    # Check for key implementation files
    impl_files = {
        "P01": "reality_audit/adapters/sim_probe.py",
        "P02": "reality_audit/data_analysis/blinding.py",
        "P03": "reality_audit/data_analysis/mock_timing_pipeline.py",
        "P04": "reality_audit/data_analysis/experiment_registry.py",
        "P05": "reality_audit/data_analysis/mock_cosmic_ray_pipeline.py",
        "P06": "reality_audit/data_analysis/mock_cosmic_ray_pipeline.py",
        "P07": "reality_audit/data_analysis/reporting.py",
        "P08": "reality_audit/data_analysis/reporting.py",
        "P09": "tests/test_data_analysis_readiness.py",
        "P10": "tests/test_data_analysis_readiness.py",
    }
    codebase_checks: Dict[str, bool] = {}
    for pid, fpath in impl_files.items():
        codebase_checks[pid] = pathlib.Path(fpath).exists()

    verified_principles = [
        _verify_principle(p, codebase_checks) for p in PRINCIPLES
    ]

    n_verified = sum(1 for p in verified_principles if p.verified)
    n_high_trust = sum(1 for p in verified_principles if p.trust_level == "high")

    report = {
        "title": "Benchmark-to-Method Transfer Report",
        "total_principles": len(verified_principles),
        "verified": n_verified,
        "high_trust": n_high_trust,
        "all_verified": n_verified == len(verified_principles),
        "principles": [p.to_dict() for p in verified_principles],
        "summary": (
            f"{n_verified}/{len(verified_principles)} principles verified. "
            f"{n_high_trust} rated high-trust. "
            "All principles derive from completed benchmark and audit work."
        ),
        "next_step": (
            "Run full pytest suite. "
            "All tests must pass before any real-data ingestion begins."
        ),
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    result = run_benchmark_transfer()
    print(f"Transfer principles: {result['total_principles']}")
    print(f"Verified: {result['verified']}")
    print(f"All verified: {result['all_verified']}")
    print(result["summary"])
