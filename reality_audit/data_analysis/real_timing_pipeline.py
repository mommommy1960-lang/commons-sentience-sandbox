"""
real_timing_pipeline.py
========================
Timing-delay analysis pipeline that accepts real (or adapter-loaded) event data
instead of synthetically generated data.

This is the production counterpart of mock_timing_pipeline.py.
The statistical machinery is identical; the only change is the data source:
real events come in through the FermiLATGRBAdapter (or any adapter returning
the same standardised format) rather than NullModelLibrary.

Key invariants carried over from benchmark work (P01–P10):
  - Analysis plan must be frozen before unblinding (Blinder.freeze())
  - Primary statistic defined here; not changed post-hoc
  - Null distribution built by permutation on the real events
  - Optional signal injection for recovery test (validates sensitivity)
  - All outputs written via ReportWriter (reproducible, manifested)

Primary test statistic
-----------------------
OLS slope of timing_offset_s ~ energy_GeV × distance_Mpc

Null distribution
-----------------
500 (configurable) permutations of energy values, which destroys the
energy-delay correlation while preserving timing residual structure.

Detection threshold
-------------------
p < 3×10⁻⁷ (~5σ) for claiming detection (Bonferroni-safe single test).

Usage
-----
    from reality_audit.adapters.fermi_lat_grb_adapter import load_and_convert
    from reality_audit.data_analysis.real_timing_pipeline import run_real_timing_pipeline

    events = load_and_convert("path/to/grb_data.csv", energy_unit="MeV")
    result = run_real_timing_pipeline(
        events=events,
        experiment_name="timing_delay_fermi_lat_v1",
        output_dir="commons_sentience_sim/output/reality_audit/exp1_timing_delay/",
    )
"""

from __future__ import annotations

import math
import os
import random
from typing import Any, Dict, List, Optional

from reality_audit.data_analysis.null_models import NullModelLibrary
from reality_audit.data_analysis.signal_injection import SignalInjector
from reality_audit.data_analysis.blinding import Blinder
from reality_audit.data_analysis.reporting import ReportWriter
from reality_audit.data_analysis.mock_timing_pipeline import (
    timing_slope,
    _permutation_null_distribution,
    _empirical_p_value,
)


# ---------------------------------------------------------------------------
# Recovery test (runs on synthetic data alongside real analysis)
# ---------------------------------------------------------------------------


def _recovery_test(
    events: Dict[str, Any],
    injection_strength: float = 1.0,
    true_slope: float = 5e-4,
    n_permutations: int = 200,
    seed: int = 9999,
) -> Dict[str, Any]:
    """
    Validate pipeline sensitivity by injecting a known signal into the
    real event list and verifying recovery.

    This does NOT use the real timing residuals as signal — it adds a
    synthetic delay on top of the real events.

    Returns recovery dict.
    """
    energy = events["energy_GeV"]
    distance = events["distance_Mpc"]
    offsets = events["timing_offset_s"]

    # Build a null_data-like dict for the injector (which expects that shape)
    null_dict = {
        "energy_GeV": energy,
        "distance_Mpc": distance,
        "timing_offset_s": list(offsets),  # copy
        "n_events": len(energy),
        "model": "real_data_recovery",
        "seed": seed,
    }
    injected = SignalInjector.timing_delay_linear(
        null_dict,
        delay_slope=true_slope,
        injection_strength=injection_strength,
        seed=seed,
    )
    obs_slope = timing_slope(
        injected["energy_GeV"],
        injected["distance_Mpc"],
        injected["timing_offset_s"],
    )
    null_dist = _permutation_null_distribution(
        injected["energy_GeV"],
        injected["distance_Mpc"],
        injected["timing_offset_s"],
        n_permutations=n_permutations,
        seed=seed + 1,
    )
    p_value = _empirical_p_value(obs_slope, null_dist)
    return {
        "injection_strength": injection_strength,
        "true_delay_slope": true_slope,
        "observed_slope_with_injection": obs_slope,
        "p_value": p_value,
        "recovered": p_value < 0.05,
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_real_timing_pipeline(
    events: Dict[str, Any],
    experiment_name: str = "timing_delay_real_v1",
    n_permutations: int = 500,
    seed: int = 42,
    output_dir: str = (
        "commons_sentience_sim/output/reality_audit/exp1_timing_delay/"
    ),
    run_recovery_test: bool = True,
    recovery_true_slope: float = 5e-4,
    blind_keys: Optional[List[str]] = None,
    freeze_immediately: bool = False,
    analysis_plan: str = "",
) -> Dict[str, Any]:
    """
    Run the timing-delay analysis on real (adapter-loaded) event data.

    Parameters
    ----------
    events             : output of load_and_convert() or to_timing_pipeline_format()
                         Must contain: energy_GeV, distance_Mpc, timing_offset_s
    experiment_name    : label used in outputs
    n_permutations     : permutation trials for null distribution
    seed               : RNG seed for permutations
    output_dir         : base directory for all output files
    run_recovery_test  : inject a synthetic signal and verify detection
    recovery_true_slope: slope used in recovery test [s / (GeV × Mpc)]
    blind_keys         : list of result keys to blind (default: signal results)
    freeze_immediately : if True, unblind immediately (dry-run mode)
    analysis_plan      : plain-text description of the analysis plan

    Returns
    -------
    Full results dict (unblinded if freeze_immediately, else blinded).
    """
    os.makedirs(output_dir, exist_ok=True)

    energy = events["energy_GeV"]
    distance = events["distance_Mpc"]
    offsets = events["timing_offset_s"]
    n_events = len(energy)

    if n_events < 2:
        raise ValueError(
            f"Need at least 2 events to run timing analysis; got {n_events}."
        )

    # 1. Primary statistic
    observed_slope = timing_slope(energy, distance, offsets)

    # 2. Null distribution by permutation
    null_distribution = _permutation_null_distribution(
        energy, distance, offsets,
        n_permutations=n_permutations,
        seed=seed,
    )
    null_mean = sum(null_distribution) / len(null_distribution)
    null_std = math.sqrt(
        sum((x - null_mean) ** 2 for x in null_distribution) / len(null_distribution)
    )
    p_value = _empirical_p_value(observed_slope, null_distribution)
    z_score = (
        (observed_slope - null_mean) / null_std if null_std > 0 else 0.0
    )

    # 3. Recovery test (optional)
    recovery: Dict[str, Any] = {}
    if run_recovery_test:
        recovery = _recovery_test(
            events,
            true_slope=recovery_true_slope,
            n_permutations=min(n_permutations, 200),
            seed=seed + 100,
        )

    # 4. Assemble full results
    full_results: Dict[str, Any] = {
        "experiment": experiment_name,
        "data_source": events.get("metadata", {}).get("source_file", "unknown"),
        "n_events": n_events,
        "n_sources": events.get("n_sources", "unknown"),
        "has_distance": events.get("metadata", {}).get("has_distance", False),
        "primary_statistic": "timing_slope_s_per_GeV_per_Mpc",
        "observed_slope": observed_slope,
        "null_mean_slope": null_mean,
        "null_std_slope": null_std,
        "p_value": p_value,
        "z_score": z_score,
        "detection_claimed": p_value < 3e-7,
        "null_retained": p_value > 0.05,
        "n_permutations": n_permutations,
        "recovery_test": recovery,
        "seed": seed,
        "status": "real_data_run",
        "metadata": events.get("metadata", {}),
    }

    # 5. Blinding and reporting
    if blind_keys is None:
        blind_keys = [
            "p_value", "z_score", "detection_claimed",
            "null_retained", "observed_slope",
        ]

    blinder = Blinder(blind_keys=blind_keys, experiment_name=experiment_name)
    writer = ReportWriter(output_dir, experiment_name)

    # Always write blinded version
    blinded = blinder.blind(full_results)
    writer.write_json_summary(blinded, blinded=True)
    writer.write_markdown_summary(blinded, analysis_plan=analysis_plan, blinded=True)

    # Unblind only if explicitly requested (dry-run / validation mode)
    if freeze_immediately:
        blinder.freeze(reason="Immediate unblind requested (dry-run / validation mode).")
        unblinded = blinder.unblind(full_results)
        writer.write_json_summary(unblinded, blinded=False)
        writer.write_markdown_summary(
            unblinded, analysis_plan=analysis_plan, blinded=False
        )
        csv_row = {
            "experiment": experiment_name,
            "n_events": n_events,
            "observed_slope": observed_slope,
            "p_value": p_value,
            "z_score": z_score,
            "detection_claimed": full_results["detection_claimed"],
            "null_retained": full_results["null_retained"],
        }
        writer.write_csv_row(csv_row)

    writer.write_manifest()

    return_results = full_results if freeze_immediately else blinded
    return_results["output_dir"] = output_dir
    return_results["blinding_summary"] = blinder.summary()
    return return_results
