"""
scripts/run_simulation_signature_examples.py
=============================================
Convenience runner: executes three example analysis runs and prints a summary.

Runs:
  1. Baseline null analysis on synthetic example data
  2. Preferred-axis anomaly injection test
  3. Energy-dependent-delay anomaly injection test

Outputs are stored in separate sub-folders under
  outputs/simulation_signature/

Usage
-----
    python scripts/run_simulation_signature_examples.py
"""

from __future__ import annotations

import os
import sys

# Ensure parent package is importable when run from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reality_audit.data_analysis.example_event_data import generate_example_event_dataset
from reality_audit.data_analysis.simulation_signature_analysis import (
    analyze_event_dataset,
    evaluate_signal_strength,
    generate_null_events,
    inject_synthetic_anomaly,
    standardize_events,
    write_analysis_artifacts,
)

DATA_PATH   = "data/real/example_event_catalog.csv"
BASE_OUTPUT = "outputs/simulation_signature"
NULL_REPEATS = 25
SEED = 42


def _run_case(
    name: str,
    output_subdir: str,
    inject: str | None,
    strength: float,
    null_mode: str,
    plots: bool = True,
) -> dict:
    print(f"\n{'='*60}")
    print(f"  Case: {name}")

    # Load + standardize
    import csv as _csv

    raw_events: list[dict] = []
    with open(DATA_PATH, newline="") as f:
        reader = _csv.DictReader(f)
        for row in reader:
            raw_events.append(dict(row))

    events = standardize_events(raw_events)

    # Null
    null_events = generate_null_events(events, mode=null_mode, seed=SEED)

    # Optional injection
    if inject:
        events = inject_synthetic_anomaly(events, anomaly_type=inject,
                                          strength=strength, seed=SEED)
        print(f"  Injected: {inject} (strength={strength})")

    # Analyze
    config = {"null_mode": null_mode, "null_repeats": NULL_REPEATS, "seed": SEED}
    results = analyze_event_dataset(events, reference_events=null_events,
                                    config=config, null_repeats=NULL_REPEATS, seed=SEED)
    signal_eval = evaluate_signal_strength(results)

    output_dir = os.path.join(BASE_OUTPUT, output_subdir)
    manifest = write_analysis_artifacts(
        results=results,
        signal_eval=signal_eval,
        events=events,
        null_events=null_events,
        output_dir=output_dir,
        name=name,
        plots_enabled=plots,
        config=config,
    )

    print(f"  Tier:            {signal_eval['tier']}")
    print(f"  Max percentile:  {signal_eval['max_percentile']:.3f}")
    print(f"  Artifacts in:    {output_dir}")
    return {"name": name, "tier": signal_eval["tier"],
            "max_percentile": signal_eval["max_percentile"],
            "manifest": manifest}


def main() -> None:
    print("Running simulation-signature example suite...")

    case_results = []

    case_results.append(_run_case(
        name="baseline_run",
        output_subdir="baseline",
        inject=None,
        strength=0.0,
        null_mode="isotropic",
        plots=True,
    ))

    case_results.append(_run_case(
        name="preferred_axis_run",
        output_subdir="preferred_axis",
        inject="preferred_axis",
        strength=0.5,
        null_mode="isotropic",
        plots=True,
    ))

    case_results.append(_run_case(
        name="energy_delay_run",
        output_subdir="energy_delay",
        inject="energy_dependent_delay",
        strength=0.5,
        null_mode="shuffled_time",
        plots=True,
    ))

    # Compact summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Case':<30} {'Tier':<35} {'Max pct'}")
    print(f"  {'-'*30} {'-'*35} {'-'*7}")
    for r in case_results:
        print(f"  {r['name']:<30} {r['tier']:<35} {r['max_percentile']:.3f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
