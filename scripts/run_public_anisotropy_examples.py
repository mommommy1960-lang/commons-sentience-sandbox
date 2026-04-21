"""
run_public_anisotropy_examples.py
==================================
Convenience runner for Stage 7 public-data anisotropy analysis examples.

Runs:
  1. Synthetic isotropic baseline
  2. Synthetic preferred-axis recovery
  3. Real local catalog (if available in data/real/)

Prints a short summary table for each case.

Usage:
    python scripts/run_public_anisotropy_examples.py
"""

from __future__ import annotations

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
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


def _run_example(catalog_source, name, output_dir, null_repeats=50, seed=42, num_axes=48):
    events = load_public_catalog(catalog_source)
    coverage = describe_catalog_coverage(events)

    for e in events:
        if e.get("dec") is not None and "_b_proxy" not in e:
            e["_b_proxy"] = abs(float(e["dec"]))
        e.setdefault("_parse_warnings", [])

    results = run_public_anisotropy_study(
        events, null_repeats=null_repeats, seed=seed, num_axes=num_axes
    )

    write_public_study_artifacts(
        results=results,
        events=events,
        null_events_example=None,
        output_dir=output_dir,
        name=name,
        plots_enabled=False,
        catalog_name=catalog_source,
        coverage=coverage,
    )

    sig_eval = results["signal_evaluation"]
    nc       = results["null_comparison"]
    return {
        "name":        name,
        "catalog":     catalog_source,
        "n_events":    results["event_count"],
        "axis_score":  results["preferred_axis"]["score"],
        "axis_pct":    nc["axis_percentile"],
        "tier":        sig_eval["tier"],
        "max_pct":     sig_eval["max_percentile"],
    }


def main():
    cases = [
        dict(
            catalog_source = "synthetic_isotropic",
            name           = "synth_isotropic_example",
            output_dir     = "outputs/public_anisotropy/synth_isotropic",
        ),
        dict(
            catalog_source = "synthetic_preferred_axis",
            name           = "synth_preferred_axis_example",
            output_dir     = "outputs/public_anisotropy/synth_preferred_axis",
        ),
    ]

    # Add real catalog if available
    real_dir = _real_data_dir()
    for cat_name, fname in KNOWN_REAL_CATALOGS.items():
        if fname is None:
            continue
        candidate = os.path.join(real_dir, fname)
        if os.path.exists(candidate):
            cases.append(dict(
                catalog_source = candidate,
                name           = f"real_catalog_{cat_name}",
                output_dir     = f"outputs/public_anisotropy/real_{cat_name}",
            ))
            break

    print("Running public anisotropy examples...")
    rows = []
    for c in cases:
        try:
            row = _run_example(**c)
            rows.append(row)
        except Exception as exc:
            print(f"  [ERROR] {c['name']}: {exc}")
            rows.append({"name": c["name"], "catalog": c["catalog_source"],
                         "error": str(exc)})

    # Summary table
    print()
    print(f"{'Name':<38} {'N':>5}  {'Axis score':>10}  {'Axis pct':>8}  {'Tier'}")
    print("-" * 80)
    for r in rows:
        if "error" in r:
            print(f"{r['name']:<38}  ERROR: {r['error']}")
        else:
            print(
                f"{r['name']:<38} {r['n_events']:>5}  "
                f"{r['axis_score']:>10.4f}  {r['axis_pct']:>8.4f}  {r['tier']}"
            )
    print()
    print("NOTE: Results are hypothesis-generating only. See caveat in each report.")


if __name__ == "__main__":
    main()
