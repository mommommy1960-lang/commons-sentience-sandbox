"""
quantum_double_slit_runner.py — Audit-integrated runner for quantum benchmark.

Writes standard audit output:
  commons_sentience_sim/output/reality_audit/quantum_double_slit/
    config.json
    raw_results.json
    raw_results.csv
    summary.json
    decoherence_sweep.json
    <condition>/summary.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from reality_audit.benchmarks.quantum_double_slit import (
    QSlitCondition,
    run_all_conditions,
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
    _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit" / "quantum_double_slit"
)

_PARTIAL_GAMMAS: List[float] = [0.0, 0.25, 0.5, 0.75, 1.0]


def run_quantum_double_slit_benchmark(
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seed: int = 0,
    partial_gammas: Optional[List[float]] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute quantum double-slit benchmark and write all audit outputs.

    Returns full results dict with keys:
        config, results, output_dir
    """
    out = Path(output_dir) if output_dir else _DEFAULT_OUTPUT
    out.mkdir(parents=True, exist_ok=True)

    gammas = partial_gammas or _PARTIAL_GAMMAS

    config: Dict[str, Any] = {
        "benchmark": "quantum_double_slit",
        "benchmark_version": "1.0",
        "model_type": "complex_amplitude_fraunhofer_with_decoherence",
        "formalism": (
            "Complex path amplitudes (Fraunhofer far-field). "
            "P(y) = |A_L + A_R|^2 for coherent; "
            "P(y) = |A_L|^2 + |A_R|^2 + 2*(1-gamma)*Re(A_L*conj(A_R)) for partial. "
            "Born-rule sampling (seeded multinomial)."
        ),
        "n_trials": n_trials,
        "slit_separation": slit_separation,
        "slit_width": slit_width,
        "wavelength": wavelength,
        "screen_distance": screen_distance,
        "screen_width": screen_width,
        "n_bins": n_bins,
        "seed": seed,
        "partial_gammas": gammas,
        "conditions": [
            "one_slit",
            "two_slit_coherent",
            "two_slit_decohered",
            "decoherence_sweep",
        ],
        "honest_framing": (
            "This is a quantum-style interferometer benchmark using complex amplitudes "
            "and Born-rule sampling. It is NOT a full quantum computer and does NOT "
            "simulate the physical universe. Its purpose is to validate observer-sensitive "
            "auditing logic in the Reality Audit framework."
        ),
    }
    (out / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

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
        partial_gammas=gammas,
    )

    # Write per-condition summaries
    for cond_key in ["one_slit", "two_slit_coherent", "two_slit_decohered"]:
        cond_dir = out / cond_key
        cond_dir.mkdir(exist_ok=True)
        (cond_dir / "summary.json").write_text(
            json.dumps(results[cond_key]["summary"], indent=2), encoding="utf-8"
        )

    # Write decoherence sweep
    sweep_data = [r["summary"] for r in results["decoherence_sweep"]]
    (out / "decoherence_sweep.json").write_text(
        json.dumps(sweep_data, indent=2), encoding="utf-8"
    )
    sweep_dir = out / "decoherence_sweep"
    sweep_dir.mkdir(exist_ok=True)
    for r in results["decoherence_sweep"]:
        g_str = f"gamma_{r['decoherence_gamma']:.2f}".replace(".", "_")
        g_dir = sweep_dir / g_str
        g_dir.mkdir(exist_ok=True)
        (g_dir / "summary.json").write_text(
            json.dumps(r["summary"], indent=2), encoding="utf-8"
        )

    # Write flat raw_results.json (single conditions only; sweep separate)
    flat_results = {k: results[k] for k in ["one_slit", "two_slit_coherent", "two_slit_decohered"]}
    (out / "raw_results.json").write_text(json.dumps(flat_results, indent=2), encoding="utf-8")

    # Write CSV: one row per (condition, bin)
    rows: List[Dict[str, Any]] = []
    for cond_key in ["one_slit", "two_slit_coherent", "two_slit_decohered"]:
        r = results[cond_key]
        for i, (pos, prob, hit) in enumerate(
            zip(r["screen_positions"], r["probability_profile"], r["hit_counts"])
        ):
            rows.append({
                "condition": cond_key,
                "gamma": 0.0 if cond_key != "two_slit_decohered" else 1.0,
                "bin_index": i,
                "screen_position": pos,
                "probability": prob,
                "hit_count": hit,
            })
    # Also add sweep rows
    for sweep_r in results["decoherence_sweep"]:
        g = sweep_r["decoherence_gamma"]
        for i, (pos, prob, hit) in enumerate(
            zip(sweep_r["screen_positions"], sweep_r["probability_profile"], sweep_r["hit_counts"])
        ):
            rows.append({
                "condition": "two_slit_partial",
                "gamma": g,
                "bin_index": i,
                "screen_position": pos,
                "probability": prob,
                "hit_count": hit,
            })

    csv_path = out / "raw_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Top-level summary
    top_summary: Dict[str, Any] = {
        "benchmark": "quantum_double_slit",
        "config": config,
        "conditions_run": ["one_slit", "two_slit_coherent", "two_slit_decohered", "decoherence_sweep"],
        "per_condition": {k: results[k]["summary"] for k in ["one_slit", "two_slit_coherent", "two_slit_decohered"]},
        "decoherence_sweep_summary": sweep_data,
    }
    (out / "summary.json").write_text(json.dumps(top_summary, indent=2), encoding="utf-8")

    print(f"  [quantum_runner] Output written to {out}", flush=True)

    return {
        "config": config,
        "results": results,
        "output_dir": str(out),
    }
