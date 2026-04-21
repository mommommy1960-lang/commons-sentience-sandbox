"""
scripts/run_double_slit_examples.py
====================================
Example script that runs three canonical double-slit cases and saves
outputs to separate folders.

Cases:
  1. coherent      — fully coherent, strong interference fringes
  2. decohered     — partial decoherence (strength=0.6), reduced fringes
  3. measurement   — which-path measurement on, classical distribution

Run from repo root::

    python scripts/run_double_slit_examples.py

Outputs written to:
    outputs/double_slit/coherent/
    outputs/double_slit/decohered/
    outputs/double_slit/measurement/
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reality_audit.data_analysis.double_slit_sim import (
    run_double_slit_sim,
    write_all_artifacts,
)

# ---------------------------------------------------------------------------
# Case definitions
# ---------------------------------------------------------------------------

CASES = [
    {
        "label": "coherent",
        "kwargs": {
            "wavelength": 500e-9,
            "slit_separation": 1e-4,
            "slit_width": 2e-5,
            "screen_distance": 1.0,
            "num_particles": 10000,
            "screen_points": 500,
            "coherence": 1.0,
            "decoherence_strength": 0.0,
            "measurement_on": False,
            "noise_level": 0.0,
            "seed": 42,
        },
        "output_dir": "outputs/double_slit/coherent",
        "name": "coherent",
    },
    {
        "label": "decohered",
        "kwargs": {
            "wavelength": 500e-9,
            "slit_separation": 1e-4,
            "slit_width": 2e-5,
            "screen_distance": 1.0,
            "num_particles": 10000,
            "screen_points": 500,
            "coherence": 1.0,
            "decoherence_strength": 0.6,
            "measurement_on": False,
            "noise_level": 0.0,
            "seed": 42,
        },
        "output_dir": "outputs/double_slit/decohered",
        "name": "decohered",
    },
    {
        "label": "measurement-on",
        "kwargs": {
            "wavelength": 500e-9,
            "slit_separation": 1e-4,
            "slit_width": 2e-5,
            "screen_distance": 1.0,
            "num_particles": 10000,
            "screen_points": 500,
            "coherence": 1.0,
            "decoherence_strength": 0.0,
            "measurement_on": True,
            "noise_level": 0.0,
            "seed": 42,
        },
        "output_dir": "outputs/double_slit/measurement",
        "name": "measurement",
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  DOUBLE-SLIT EXAMPLE RUNS")
    print("=" * 60)

    for case in CASES:
        print(f"\n[run_double_slit_examples] Running case: {case['label']} …")
        result = run_double_slit_sim(**case["kwargs"])
        paths = write_all_artifacts(result, case["output_dir"], case["name"])
        print(f"  Visibility         : {result['visibility']:.4f}")
        print(f"  Regime             : {result['regime']}")
        print(f"  Interference       : {'YES' if result['interference_detected'] else 'NO'}")
        print(f"  Artifacts          :")
        for kind, path in paths.items():
            print(f"    {kind:10s} : {path}")

    print()
    print("=" * 60)
    print("  All example runs complete.")
    print()
    print("  NOTE: This is a computational simulation. It does not")
    print("  by itself constitute evidence that reality is a simulation.")
    print("=" * 60)


if __name__ == "__main__":
    main()
