"""
advanced_quantum_runner.py — Runner for advanced which-path / eraser benchmark.

Runs:
  A) one_slit
  B) two_slit_coherent
  C) two_slit_partial (overlap sweep)
  D) two_slit_which_path
  E) eraser_plus, eraser_minus

Also runs 100 repeated seed-varied runs for conditions B and D to test
statistical stability.

Writes to:
  commons_sentience_sim/output/reality_audit/advanced_quantum_double_slit/
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from reality_audit.benchmarks.advanced_quantum_double_slit import (
    AQCondition,
    run_all_conditions,
    run_condition,
    DEFAULT_DETECTOR_OVERLAP,
    DEFAULT_OVERLAP_SWEEP,
    DEFAULT_N_TRIALS,
    DEFAULT_SLIT_SEPARATION,
    DEFAULT_SLIT_WIDTH,
    DEFAULT_WAVELENGTH,
    DEFAULT_SCREEN_DISTANCE,
    DEFAULT_SCREEN_WIDTH,
    DEFAULT_N_BINS,
)
from reality_audit.analysis.advanced_quantum_metrics import (
    fringe_visibility,
    fringe_visibility_from_hits,
    path_distinguishability,
    aggregate_run_stats,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_OUTPUT = (
    _REPO_ROOT
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
    / "advanced_quantum_double_slit"
)

_DEFAULT_N_REPEATED_RUNS = 100


def _run_repeated(
    condition: AQCondition,
    n_runs: int,
    base_seed: int,
    detector_overlap: float,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Run a single condition n_runs times with seeds base_seed, base_seed+1, ...

    Returns aggregate stats over the runs.
    """
    vis_empirical: List[float] = []
    vis_theoretical: List[float] = []
    center_rate: List[float] = []

    for i in range(n_runs):
        r = run_condition(
            condition,
            detector_overlap=detector_overlap,
            seed=base_seed + i,
            **kwargs,
        )
        n_bins = len(r["hit_counts"])
        n_trials = r["n_trials"]
        centre = n_bins // 2
        vis_empirical.append(
            fringe_visibility_from_hits(r["hit_counts"], n_trials)
        )
        vis_theoretical.append(fringe_visibility(r["probability_profile"]))
        # Center-bin particle rate: binomially distributed, low CV for large n.
        center_rate.append(r["hit_counts"][centre] / max(n_trials, 1))

    return {
        "condition": str(condition),
        "detector_overlap": detector_overlap,
        "n_runs": n_runs,
        # Empirical Michelson visibility (noisy for small n_trials/n_bins ratios)
        "fringe_visibility_empirical": aggregate_run_stats(vis_empirical),
        # Theoretical (deterministic) — CV = 0 confirms model reproducibility
        "fringe_visibility_theoretical": aggregate_run_stats(vis_theoretical),
        # Center-bin rate: low-noise stability metric
        "center_bin_rate": aggregate_run_stats(center_rate),
    }


def run_advanced_benchmark(
    n_trials: int = DEFAULT_N_TRIALS,
    slit_separation: float = DEFAULT_SLIT_SEPARATION,
    slit_width: float = DEFAULT_SLIT_WIDTH,
    wavelength: float = DEFAULT_WAVELENGTH,
    screen_distance: float = DEFAULT_SCREEN_DISTANCE,
    screen_width: float = DEFAULT_SCREEN_WIDTH,
    n_bins: int = DEFAULT_N_BINS,
    seed: int = 42,
    eraser_overlap: float = 0.5,
    overlap_values: Optional[List[float]] = None,
    n_repeated_runs: int = _DEFAULT_N_REPEATED_RUNS,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run the full advanced quantum benchmark with 100-run stability test.

    Returns dict with keys: config, results, aggregate_100run, output_dir.
    """
    out = Path(output_dir) if output_dir else _DEFAULT_OUTPUT
    out.mkdir(parents=True, exist_ok=True)
    figs_dir = out / "figures"
    figs_dir.mkdir(exist_ok=True)

    ov = overlap_values if overlap_values is not None else DEFAULT_OVERLAP_SWEEP

    config: Dict[str, Any] = {
        "benchmark": "advanced_quantum_double_slit",
        "version": "1.0",
        "model": (
            "Entangled path-detector state |Ψ⟩=(1/√2)(|L⟩|d_L⟩+|R⟩|d_R⟩). "
            "Marginal P(y)=½(|A_L|²+|A_R|²)+s·Re(A_L·A_R*). "
            "Eraser: post-select on |±⟩. Born-rule sampling."
        ),
        "n_trials": n_trials,
        "slit_separation": slit_separation,
        "slit_width": slit_width,
        "wavelength": wavelength,
        "screen_distance": screen_distance,
        "screen_width": screen_width,
        "n_bins": n_bins,
        "seed": seed,
        "eraser_overlap": eraser_overlap,
        "overlap_sweep_values": ov,
        "n_repeated_runs": n_repeated_runs,
        "honest_framing": (
            "This is a small-system quantum-style benchmark running on a classical computer. "
            "It faithfully models a two-path entangled state with a detector, but is NOT "
            "a simulation of the physical universe. Purpose: validate auditing logic."
        ),
    }
    (out / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    # --- Main conditions run ---
    run_kwargs = dict(
        n_trials=n_trials, slit_separation=slit_separation,
        slit_width=slit_width, wavelength=wavelength,
        screen_distance=screen_distance, screen_width=screen_width,
        n_bins=n_bins,
    )

    results = run_all_conditions(
        seed=seed, eraser_overlap=eraser_overlap, overlap_values=ov, **run_kwargs
    )

    # Per-condition JSON
    for key in ["one_slit", "two_slit_coherent", "two_slit_which_path", "eraser_plus", "eraser_minus"]:
        cond_dir = out / key
        cond_dir.mkdir(exist_ok=True)
        (cond_dir / "summary.json").write_text(
            json.dumps(results[key]["summary"], indent=2), encoding="utf-8"
        )

    # Overlap sweep
    sweep_dir = out / "overlap_sweep"
    sweep_dir.mkdir(exist_ok=True)
    sweep_summaries = [r["summary"] for r in results["overlap_sweep"]]
    (sweep_dir / "sweep_summary.json").write_text(
        json.dumps(sweep_summaries, indent=2), encoding="utf-8"
    )

    # Write raw_results.json
    flat = {k: results[k] for k in ["one_slit", "two_slit_coherent", "two_slit_which_path",
                                      "eraser_plus", "eraser_minus"]}
    (out / "raw_results.json").write_text(json.dumps(flat, indent=2), encoding="utf-8")

    # Write CSV
    rows: List[Dict[str, Any]] = []
    for key in ["one_slit", "two_slit_coherent", "two_slit_which_path", "eraser_plus", "eraser_minus"]:
        r = results[key]
        s_ov = r.get("detector_overlap", float("nan"))
        for i, (pos, prob, hit) in enumerate(
            zip(r["screen_positions"], r["probability_profile"], r["hit_counts"])
        ):
            rows.append({
                "condition": key,
                "detector_overlap": s_ov if not (isinstance(s_ov, float) and math.isnan(s_ov)) else "",
                "bin_index": i,
                "screen_position": pos,
                "probability": prob,
                "hit_count": hit,
            })
    for r in results["overlap_sweep"]:
        s_ov = r.get("detector_overlap", "")
        for i, (pos, prob, hit) in enumerate(
            zip(r["screen_positions"], r["probability_profile"], r["hit_counts"])
        ):
            rows.append({
                "condition": "two_slit_partial",
                "detector_overlap": s_ov,
                "bin_index": i,
                "screen_position": pos,
                "probability": prob,
                "hit_count": hit,
            })

    csv_path = out / "raw_results.csv"
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    # Top-level summary
    top_summary: Dict[str, Any] = {
        "benchmark": "advanced_quantum_double_slit",
        "conditions": {
            k: results[k]["summary"]
            for k in ["one_slit", "two_slit_coherent", "two_slit_which_path",
                      "eraser_plus", "eraser_minus"]
        },
        "overlap_sweep_count": len(results["overlap_sweep"]),
    }
    (out / "summary.json").write_text(json.dumps(top_summary, indent=2), encoding="utf-8")

    # --- 100-run stability test ---
    print(f"  [advanced_runner] Running {n_repeated_runs}×2 repeated conditions...", flush=True)
    agg_coherent = _run_repeated(
        AQCondition.TWO_SLIT_COHERENT,
        n_runs=n_repeated_runs,
        base_seed=1000,
        detector_overlap=1.0,
        **run_kwargs,
    )
    agg_which_path = _run_repeated(
        AQCondition.TWO_SLIT_WHICH_PATH,
        n_runs=n_repeated_runs,
        base_seed=2000,
        detector_overlap=0.0,
        **run_kwargs,
    )

    aggregate_summary: Dict[str, Any] = {
        "benchmark": "advanced_quantum_double_slit",
        "n_repeated_runs": n_repeated_runs,
        "n_trials_per_run": n_trials,
        "two_slit_coherent": agg_coherent,
        "two_slit_which_path": agg_which_path,
        "stability_assessment": {
            # Theoretical visibility is deterministic → CV = 0 confirms reproducibility.
            "coherent_cv": agg_coherent["fringe_visibility_theoretical"]["cv"],
            "which_path_cv": agg_which_path["fringe_visibility_theoretical"]["cv"],
            "stable": (
                agg_coherent["fringe_visibility_theoretical"]["cv"] < 0.05
                and agg_which_path["fringe_visibility_theoretical"]["cv"] < 0.05
            ),
            "coherent_mean_vis": agg_coherent["fringe_visibility_theoretical"]["mean"],
            "which_path_mean_vis": agg_which_path["fringe_visibility_theoretical"]["mean"],
            # Separation check via center-bin rate: coherent >> which_path.
            "coherent_center_rate_mean": agg_coherent["center_bin_rate"]["mean"],
            "which_path_center_rate_mean": agg_which_path["center_bin_rate"]["mean"],
            "conditions_separated": (
                agg_coherent["fringe_visibility_theoretical"]["mean"]
                > agg_which_path["fringe_visibility_theoretical"]["mean"] + 0.3
            ),
        },
    }
    (out / "aggregate_summary.json").write_text(
        json.dumps(aggregate_summary, indent=2), encoding="utf-8"
    )

    print(f"  [advanced_runner] Outputs written to {out}", flush=True)

    return {
        "config": config,
        "results": results,
        "aggregate_100run": aggregate_summary,
        "output_dir": str(out),
    }
