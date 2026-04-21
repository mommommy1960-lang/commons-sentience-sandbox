"""
simulation_signature_benchmark.py
===================================
Benchmark suite for the simulation-signature analysis pipeline.

Runs three standard scenarios and checks that the pipeline behaves as expected:

1. baseline_null
   – isotropic synthetic data, no anomaly
   – expect: no strong anomaly detected

2. preferred_axis_injection
   – isotropic data with preferred-axis anomaly injected at strength 0.6
   – expect: axis_percentile elevated (> null median)

3. energy_delay_injection
   – isotropic data with energy-dependent delay injected at strength 0.6
   – expect: et_r_percentile elevated (> null median)

For each scenario:
  - generates or loads a dataset
  - runs the full analysis pipeline
  - records whether anomaly recovery matched expectation
  - saves results to outputs/simulation_signature/benchmark/

Usage
-----
    python reality_audit/data_analysis/simulation_signature_benchmark.py
"""

from __future__ import annotations

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from reality_audit.data_analysis.example_event_data import generate_example_event_dataset
from reality_audit.data_analysis.simulation_signature_analysis import (
    analyze_event_dataset,
    evaluate_signal_strength,
    generate_null_events,
    inject_synthetic_anomaly,
    standardize_events,
    write_analysis_artifacts,
)

OUTPUT_DIR = "outputs/simulation_signature/benchmark"

# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "name":           "baseline_null",
        "anomaly_type":   None,
        "anomaly_strength": 0.0,
        "null_mode":      "isotropic",
        "expected_tier":  "no_anomaly_detected",
        "expected_check": lambda r: r["null_comparison"]["axis_percentile"] < 0.90,
        "expected_description": "axis_percentile < 0.90",
        "seed":           42,
    },
    {
        "name":           "preferred_axis_injection",
        "anomaly_type":   "preferred_axis",
        "anomaly_strength": 0.6,
        "null_mode":      "isotropic",
        "expected_tier":  None,  # At least elevated vs null
        "expected_check": lambda r: r["null_comparison"]["axis_percentile"] > 0.50,
        "expected_description": "axis_percentile > 0.50 (elevated vs null)",
        "seed":           42,
    },
    {
        "name":           "energy_delay_injection",
        "anomaly_type":   "energy_dependent_delay",
        "anomaly_strength": 0.6,
        "null_mode":      "shuffled_time",
        "expected_tier":  None,
        "expected_check": lambda r: r["null_comparison"]["et_r_percentile"] > 0.50,
        "expected_description": "et_r_percentile > 0.50 (elevated vs null)",
        "seed":           42,
    },
]

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_benchmark(output_dir: str = OUTPUT_DIR, n_events: int = 300,
                  null_repeats: int = 25) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    scenario_results = []
    all_passed = True

    for sc in SCENARIOS:
        print(f"\n[benchmark] Running scenario: {sc['name']}")

        # Generate dataset
        raw = generate_example_event_dataset(n=n_events, seed=sc["seed"])
        events = standardize_events(raw)

        # Inject anomaly if needed
        if sc["anomaly_type"]:
            events = inject_synthetic_anomaly(
                events,
                anomaly_type=sc["anomaly_type"],
                strength=sc["anomaly_strength"],
                seed=sc["seed"],
            )

        # Null
        null_events = generate_null_events(events, mode=sc["null_mode"], seed=sc["seed"])

        # Analyze
        config = {"null_mode": sc["null_mode"], "null_repeats": null_repeats,
                  "seed": sc["seed"]}
        results = analyze_event_dataset(
            events,
            reference_events=null_events,
            config=config,
            null_repeats=null_repeats,
            seed=sc["seed"],
        )
        signal_eval = evaluate_signal_strength(results)

        # Check expectation
        passed = sc["expected_check"](results)
        if not passed:
            all_passed = False
            status = "FAIL"
        else:
            status = "PASS"

        print(f"  Tier:    {signal_eval['tier']}")
        print(f"  Check ({sc['expected_description']}): {status}")

        # Save artifacts
        sc_dir = os.path.join(output_dir, sc["name"])
        manifest = write_analysis_artifacts(
            results=results,
            signal_eval=signal_eval,
            events=events,
            null_events=null_events,
            output_dir=sc_dir,
            name=sc["name"],
            plots_enabled=False,  # skip plots in benchmark for speed
            config=config,
        )

        scenario_results.append({
            "scenario":       sc["name"],
            "anomaly_type":   sc["anomaly_type"],
            "anomaly_strength": sc["anomaly_strength"],
            "tier":           signal_eval["tier"],
            "max_percentile": signal_eval["max_percentile"],
            "axis_percentile":results["null_comparison"]["axis_percentile"],
            "et_r_percentile":results["null_comparison"]["et_r_percentile"],
            "expected":       sc["expected_description"],
            "passed":         passed,
            "status":         status,
            "artifacts":      manifest,
        })

    # Write benchmark summary
    summary = {
        "benchmark": "simulation_signature_benchmark",
        "written_at": ts,
        "n_events":   n_events,
        "null_repeats": null_repeats,
        "all_passed": all_passed,
        "scenarios":  scenario_results,
    }
    summary_path = os.path.join(output_dir, "benchmark_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[benchmark] Summary written to {summary_path}")
    print(f"[benchmark] All scenarios passed: {all_passed}")
    return summary


if __name__ == "__main__":
    result = run_benchmark()
    sys.exit(0 if result["all_passed"] else 1)
