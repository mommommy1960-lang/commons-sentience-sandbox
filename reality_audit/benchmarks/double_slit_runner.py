"""
double_slit_runner.py — Audit-integrated runner for double-slit benchmark.

Executes all three benchmark conditions and writes output in the same
style as other reality_audit experiments:
  commons_sentience_sim/output/reality_audit/double_slit/
    config.json
    raw_results.json
    raw_results.csv
    summary.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from reality_audit.benchmarks.double_slit import (
    SlitCondition,
    run_all_conditions,
    run_condition,
    DEFAULT_N_TRIALS,
    DEFAULT_SLIT_SEPARATION,
    DEFAULT_SLIT_WIDTH,
    DEFAULT_WAVELENGTH,
    DEFAULT_SCREEN_DISTANCE,
    DEFAULT_SCREEN_WIDTH,
    DEFAULT_N_BINS,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_OUTPUT = (
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "double_slit"
)

# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _write_config(output_dir: Path, config: Dict[str, Any]) -> None:
    (output_dir / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


def _write_raw_json(output_dir: Path, results: Dict[str, Any]) -> None:
    (output_dir / "raw_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )


def _write_csv(output_dir: Path, results: Dict[str, Dict[str, Any]]) -> None:
    """Write a flat CSV with one row per (condition, bin)."""
    rows: List[Dict[str, Any]] = []
    for cond_name, result in results.items():
        positions = result["screen_positions"]
        intensities = result["intensity_profile"]
        hits = result["hit_counts"]
        for i, (pos, intensity, hit) in enumerate(zip(positions, intensities, hits)):
            rows.append({
                "condition": cond_name,
                "bin_index": i,
                "screen_position": pos,
                "intensity": intensity,
                "hit_count": hit,
            })
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    csv_path = output_dir / "raw_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary(output_dir: Path, summary: Dict[str, Any]) -> None:
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_double_slit_benchmark(
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seed: int = 0,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute all three double-slit conditions and write audit output.

    Parameters
    ----------
    (see double_slit.py defaults for physics parameters)
    output_dir : Path, optional
        Override output directory.

    Returns
    -------
    dict with keys: config, conditions, summary_per_condition, output_dir
    """
    out = Path(output_dir) if output_dir else _DEFAULT_OUTPUT
    out.mkdir(parents=True, exist_ok=True)

    config: Dict[str, Any] = {
        "benchmark": "double_slit",
        "benchmark_version": "1.0",
        "model_type": "classical_wave_optics_approximation",
        "n_trials": n_trials,
        "slit_separation": slit_separation,
        "slit_width": slit_width,
        "wavelength": wavelength,
        "screen_distance": screen_distance,
        "screen_width": screen_width,
        "n_bins": n_bins,
        "seed": seed,
        "conditions": [c.value for c in SlitCondition],
        "honest_framing": (
            "This is a classical wave-optics benchmark model.  "
            "It is NOT a quantum simulator.  Its purpose is to provide a "
            "known observer-sensitive signal for audit framework validation."
        ),
    }
    _write_config(out, config)

    # Run all conditions
    results = run_all_conditions(
        n_trials=n_trials,
        slit_separation=slit_separation,
        slit_width=slit_width,
        wavelength=wavelength,
        screen_distance=screen_distance,
        screen_width=screen_width,
        n_bins=n_bins,
        seed=seed,
    )

    _write_raw_json(out, results)
    _write_csv(out, results)

    # Write per-condition sub-summaries
    summary_per_condition: Dict[str, Any] = {}
    for cond_name, result in results.items():
        cond_dir = out / cond_name
        cond_dir.mkdir(exist_ok=True)
        _write_summary(cond_dir, result["summary"])
        summary_per_condition[cond_name] = result["summary"]

    # Top-level summary
    top_summary: Dict[str, Any] = {
        "benchmark": "double_slit",
        "config": config,
        "conditions_run": list(results.keys()),
        "per_condition": summary_per_condition,
    }
    _write_summary(out, top_summary)

    print(f"  [double_slit_runner] Output written to {out}", flush=True)

    return {
        "config": config,
        "conditions": list(results.keys()),
        "results": results,
        "summary_per_condition": summary_per_condition,
        "output_dir": str(out),
    }
