"""
public_anisotropy_benchmark.py
===============================
Validation benchmark for the Stage 7 public-data anisotropy analysis pipeline.

Scenarios
---------
1. synthetic_isotropic_baseline
   Confirm that a purely isotropic synthetic dataset produces no significant
   anomaly (axis_percentile should be < 0.90).

2. synthetic_preferred_axis_recovery
   Confirm that a dataset with a known preferred-axis injection (strength 0.6)
   is detected above the weak-signal threshold (axis_percentile > 0.50).

3. real_catalog_baseline
   If a real public catalog CSV exists in data/real/, run the analysis on it
   and report results without applying a pass/fail criterion (the result is
   data-dependent and unknown in advance).

Usage
-----
    python reality_audit/data_analysis/public_anisotropy_benchmark.py

Results are printed to stdout and written to:
    outputs/public_anisotropy_benchmark/
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.public_event_catalogs import (
    load_public_catalog,
    describe_catalog_coverage,
    KNOWN_REAL_CATALOGS,
    _real_data_dir,
)
from reality_audit.data_analysis.public_anisotropy_study import (
    run_public_anisotropy_study,
    write_public_study_artifacts,
)

_OUTPUT_BASE = os.path.join(_REPO_ROOT, "outputs", "public_anisotropy_benchmark")


def _run_scenario(
    scenario_name: str,
    catalog_source: str,
    catalog_label: str,
    null_repeats: int = 50,
    num_axes: int = 48,
    seed: int = 42,
    plots: bool = False,
    expected_pass_fn=None,
) -> dict:
    """Run one benchmark scenario and return a result summary dict."""
    print(f"\n[BENCHMARK] Running scenario: {scenario_name}")
    out_dir = os.path.join(_OUTPUT_BASE, scenario_name)

    events = load_public_catalog(catalog_source)
    coverage = describe_catalog_coverage(events)

    # Ensure internal fields
    import math
    for e in events:
        if e.get("dec") is not None and "_b_proxy" not in e:
            e["_b_proxy"] = abs(float(e["dec"]))
        e.setdefault("_parse_warnings", [])

    results = run_public_anisotropy_study(
        events,
        null_repeats=null_repeats,
        seed=seed,
        num_axes=num_axes,
    )

    write_public_study_artifacts(
        results=results,
        events=events,
        null_events_example=None,
        output_dir=out_dir,
        name=scenario_name,
        plots_enabled=plots,
        catalog_name=catalog_label,
        coverage=coverage,
    )

    sig_eval = results.get("signal_evaluation", {})
    nc       = results.get("null_comparison", {})
    tier     = sig_eval.get("tier", "unknown")
    axis_pct = nc.get("axis_percentile", 0.0)
    max_pct  = sig_eval.get("max_percentile", 0.0)

    passed = True
    pass_msg = "PASS (no strict criterion)"
    if expected_pass_fn is not None:
        passed = expected_pass_fn(results)
        pass_msg = "PASS" if passed else "FAIL"

    print(f"  Events       : {results.get('event_count', 0)}")
    print(f"  Signal tier  : {tier}")
    print(f"  Axis pct     : {axis_pct:.4f}")
    print(f"  Max pct      : {max_pct:.4f}")
    print(f"  Result       : {pass_msg}")

    return {
        "scenario":     scenario_name,
        "catalog":      catalog_label,
        "event_count":  results.get("event_count", 0),
        "tier":         tier,
        "axis_pct":     axis_pct,
        "max_pct":      max_pct,
        "passed":       passed,
    }


def run_benchmark(plots: bool = False) -> list:
    """Run all benchmark scenarios and return a list of result dicts."""
    results_list = []

    # ---- Scenario 1: isotropic baseline ----
    results_list.append(
        _run_scenario(
            scenario_name   = "synthetic_isotropic_baseline",
            catalog_source  = "synthetic_isotropic",
            catalog_label   = "synthetic_isotropic",
            null_repeats    = 50,
            num_axes        = 48,
            seed            = 42,
            plots           = plots,
            expected_pass_fn = lambda r: (
                r["null_comparison"]["axis_percentile"] < 0.90
            ),
        )
    )

    # ---- Scenario 2: preferred-axis recovery ----
    results_list.append(
        _run_scenario(
            scenario_name   = "synthetic_preferred_axis_recovery",
            catalog_source  = "synthetic_preferred_axis",
            catalog_label   = "synthetic_preferred_axis",
            null_repeats    = 50,
            num_axes        = 48,
            seed            = 42,
            plots           = plots,
            expected_pass_fn = lambda r: (
                r["null_comparison"]["axis_percentile"] > 0.50
            ),
        )
    )

    # ---- Scenario 3: real catalog (opportunistic) ----
    real_dir = _real_data_dir()
    real_found = False
    for cat_name, fname in KNOWN_REAL_CATALOGS.items():
        if fname is None:
            continue
        candidate = os.path.join(real_dir, fname)
        if os.path.exists(candidate):
            results_list.append(
                _run_scenario(
                    scenario_name   = "real_catalog_baseline",
                    catalog_source  = candidate,
                    catalog_label   = cat_name,
                    null_repeats    = 50,
                    num_axes        = 48,
                    seed            = 42,
                    plots           = plots,
                    expected_pass_fn = None,  # no strict criterion
                )
            )
            real_found = True
            break

    if not real_found:
        print(
            "\n[BENCHMARK] Skipping real_catalog_baseline: "
            "no real catalog CSV found in data/real/. "
            "See data/real/README_public_catalog_ingest.md."
        )

    # ---- Print summary ----
    print("\n" + "=" * 60)
    print("  BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"  {'Scenario':<40} {'Pass?':<6} {'Axis pct'}")
    print(f"  {'-'*40} {'-'*6} {'-'*8}")
    for r in results_list:
        p = "PASS" if r["passed"] else "FAIL"
        print(f"  {r['scenario']:<40} {p:<6} {r['axis_pct']:.4f}")
    print("=" * 60)

    all_pass = all(r["passed"] for r in results_list)
    print(f"\nOverall: {'ALL PASSED' if all_pass else 'SOME FAILED'}")
    return results_list


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Run public anisotropy benchmark.")
    p.add_argument("--plots", action="store_true", help="Generate PNG plots.")
    args = p.parse_args()
    run_benchmark(plots=args.plots)
