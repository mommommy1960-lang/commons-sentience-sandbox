"""
double_slit_benchmark.py
========================
Benchmark runner for the double-slit decoherence experiment.

Runs three canonical modes and checks each against expected visibility ranges:
  1. coherent_baseline        — fully coherent, no decoherence
  2. partial_decoherence      — intermediate alpha, reduced fringe contrast
  3. measurement_classicalized — measurement_on=True, classical output

Outputs (written to benchmark_results/double_slit/ by default):
  double_slit_benchmark_report.json  — structured results per mode
  double_slit_benchmark_report.md    — human-readable table
  double_slit_benchmark_scores.csv   — one row per mode

Usage
-----
    python -m reality_audit.data_analysis.double_slit_benchmark
    python -m reality_audit.data_analysis.double_slit_benchmark --output-dir my_results/
    python -m reality_audit.data_analysis.double_slit_benchmark --seed 42
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from reality_audit.data_analysis.double_slit_sim import (
    run_double_slit_sim,
    write_all_artifacts,
)

# ---------------------------------------------------------------------------
# Benchmark mode definitions
# ---------------------------------------------------------------------------

# Each mode: name, sim kwargs (overrides), expected visibility range [lo, hi], description
_BENCHMARK_MODES: List[Dict[str, Any]] = [
    {
        "name": "coherent_baseline",
        "description": (
            "Fully coherent illumination, no decoherence or measurement. "
            "Expect strong fringe visibility (> 0.6)."
        ),
        "sim_kwargs": {
            "coherence": 1.0,
            "decoherence_strength": 0.0,
            "measurement_on": False,
        },
        "expected_visibility_min": 0.6,
        "expected_visibility_max": 1.01,
    },
    {
        "name": "partial_decoherence",
        "description": (
            "Moderate decoherence applied (strength=0.5). "
            "Expect intermediate visibility (0.1 – 0.6)."
        ),
        "sim_kwargs": {
            "coherence": 1.0,
            "decoherence_strength": 0.5,
            "measurement_on": False,
        },
        "expected_visibility_min": 0.1,
        "expected_visibility_max": 0.60,
    },
    {
        "name": "measurement_classicalized",
        "description": (
            "Measurement is active (which-path information extracted). "
            "Expect near-zero fringe visibility (< 0.15)."
        ),
        "sim_kwargs": {
            "coherence": 1.0,
            "decoherence_strength": 0.0,
            "measurement_on": True,
        },
        "expected_visibility_min": 0.0,
        "expected_visibility_max": 0.15,
    },
]

# Default simulation parameters applied to all modes
_DEFAULT_SIM_PARAMS: Dict[str, Any] = {
    "wavelength": 500e-9,
    "slit_separation": 1e-4,
    "slit_width": 2e-5,
    "screen_distance": 1.0,
    "num_particles": 5000,
    "screen_points": 500,
    "noise_level": 0.0,
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_benchmark(
    output_dir: str = "benchmark_results/double_slit",
    seed: int | None = 42,
    write_artifacts: bool = True,
) -> Dict[str, Any]:
    """
    Run all three benchmark modes and return a structured results dict.

    Parameters
    ----------
    output_dir      : directory for all benchmark artifacts
    seed            : RNG seed for reproducibility
    write_artifacts : if False, skip writing per-mode artifacts (for unit tests)

    Returns
    -------
    dict with keys: suite, timestamp, modes, overall_pass
    """
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    mode_results: List[Dict[str, Any]] = []
    all_pass = True

    for mode in _BENCHMARK_MODES:
        sim_kwargs = {**_DEFAULT_SIM_PARAMS, **mode["sim_kwargs"]}
        if seed is not None:
            sim_kwargs["seed"] = seed

        result = run_double_slit_sim(**sim_kwargs)

        vis = result["visibility"]
        lo = mode["expected_visibility_min"]
        hi = mode["expected_visibility_max"]
        passed = lo <= vis <= hi

        if not passed:
            all_pass = False

        mode_result = {
            "name": mode["name"],
            "description": mode["description"],
            "visibility_observed": round(vis, 6),
            "visibility_expected_min": lo,
            "visibility_expected_max": hi,
            "pass": passed,
            "interference_detected": result["interference_detected"],
            "regime": result["regime"],
            "measurement_on": sim_kwargs.get("measurement_on", False),
            "decoherence_strength": sim_kwargs.get("decoherence_strength", 0.0),
            "coherence": sim_kwargs.get("coherence", 1.0),
            "notes": result["notes"],
            "run_id": result["run_id"],
        }

        if write_artifacts:
            mode_dir = str(Path(output_dir) / mode["name"])
            write_all_artifacts(result, mode_dir, mode["name"])

        mode_results.append(mode_result)

    benchmark_report = {
        "suite": "double_slit_decoherence_benchmark",
        "version": "1.0",
        "timestamp": timestamp,
        "seed": seed,
        "overall_pass": all_pass,
        "modes": mode_results,
        "WARNING": (
            "This is a computational simulation benchmark. "
            "It does not constitute evidence that reality is a simulation."
        ),
    }

    if write_artifacts:
        _write_benchmark_artifacts(benchmark_report, output_dir)

    return benchmark_report


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------

def _write_benchmark_artifacts(report: Dict[str, Any], output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = out / "double_slit_benchmark_report.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    # Markdown table
    md_path = out / "double_slit_benchmark_report.md"
    lines = [
        "# Double-Slit Benchmark Report",
        "",
        f"**Suite:** {report['suite']}  ",
        f"**Version:** {report['version']}  ",
        f"**Timestamp:** {report['timestamp']}  ",
        f"**Seed:** {report['seed']}  ",
        f"**Overall Pass:** {'✅ PASS' if report['overall_pass'] else '❌ FAIL'}",
        "",
        "| Mode | Visibility | Expected Range | Pass | Regime | Interference |",
        "|------|-----------|----------------|------|--------|-------------|",
    ]
    for m in report["modes"]:
        status = "✅" if m["pass"] else "❌"
        lines.append(
            f"| {m['name']} | {m['visibility_observed']:.4f} | "
            f"[{m['visibility_expected_min']:.2f}, {m['visibility_expected_max']:.2f}] | "
            f"{status} | {m['regime']} | {m['interference_detected']} |"
        )
    lines += [
        "",
        "---",
        "",
        "> **Warning:** This is a computational simulation. Results do not constitute",
        "> evidence that reality is a simulation.",
    ]
    md_path.write_text("\n".join(lines) + "\n")

    # CSV
    csv_path = out / "double_slit_benchmark_scores.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "visibility_observed", "visibility_expected_min",
            "visibility_expected_max", "pass", "regime", "interference_detected",
            "measurement_on", "decoherence_strength",
        ])
        writer.writeheader()
        for m in report["modes"]:
            writer.writerow({
                "name": m["name"],
                "visibility_observed": m["visibility_observed"],
                "visibility_expected_min": m["visibility_expected_min"],
                "visibility_expected_max": m["visibility_expected_max"],
                "pass": m["pass"],
                "regime": m["regime"],
                "interference_detected": m["interference_detected"],
                "measurement_on": m["measurement_on"],
                "decoherence_strength": m["decoherence_strength"],
            })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run the double-slit decoherence benchmark suite.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--output-dir", type=str,
                        default="benchmark_results/double_slit",
                        help="Directory to write benchmark artifacts.")
    parser.add_argument("--seed", type=int, default=42,
                        help="RNG seed (use --seed 0 to pass seed=0 explicitly).")
    parser.add_argument("--no-artifacts", action="store_true",
                        help="Skip writing per-mode artifacts (report only).")
    args = parser.parse_args(argv)

    print("[double_slit_benchmark] Running benchmark suite …")
    report = run_benchmark(
        output_dir=args.output_dir,
        seed=args.seed,
        write_artifacts=not args.no_artifacts,
    )

    print()
    print("=" * 65)
    print("  DOUBLE-SLIT BENCHMARK RESULTS")
    print("=" * 65)
    for m in report["modes"]:
        status = "PASS" if m["pass"] else "FAIL"
        print(
            f"  [{status}] {m['name']:<30}  "
            f"visibility={m['visibility_observed']:.4f}  "
            f"regime={m['regime']}"
        )
    overall = "ALL MODES PASSED" if report["overall_pass"] else "SOME MODES FAILED"
    print("=" * 65)
    print(f"  Overall: {overall}")
    print("=" * 65)
    if not args.no_artifacts:
        print(f"  Artifacts written to: {args.output_dir}")

    sys.exit(0 if report["overall_pass"] else 1)


if __name__ == "__main__":
    main()
