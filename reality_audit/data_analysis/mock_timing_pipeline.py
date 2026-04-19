"""
mock_timing_pipeline.py
=======================
Dry-run version of an astrophysical timing-delay analysis pipeline.

Purpose
-------
Build and validate the exact pipeline structure we will later apply to
real public-data astrophysical transient datasets (e.g. Fermi-LAT GRB catalog).

This mock pipeline:
  1. Generates synthetic photon events with energy and distance (NullModelLibrary)
  2. Optionally injects a linear energy × distance timing delay (SignalInjector)
  3. Computes the linear regression slope as the primary test statistic
  4. Runs a null-hypothesis permutation test (shuffle energies)
  5. Performs signal-injection recovery test
  6. Produces blinded and unblinded outputs (Blinder + ReportWriter)

No real external data is fetched.

Key design choices:
  - primray statistic = slope of linear fit (timing_offset ~ energy × distance)
  - null distribution from permuted energies (breaks true energy-delay correlation)
  - recovery at 1× injection strength must succeed for pipeline to be approved
"""

from __future__ import annotations

import math
import os
import random
from typing import Any, Dict, List, Optional, Tuple

from reality_audit.data_analysis.null_models import NullModelLibrary
from reality_audit.data_analysis.signal_injection import SignalInjector
from reality_audit.data_analysis.blinding import Blinder
from reality_audit.data_analysis.reporting import ReportWriter


# ---------------------------------------------------------------------------
# Primary test statistic: linear regression slope
# ---------------------------------------------------------------------------


def _linear_regression_slope(
    x_list: List[float], y_list: List[float]
) -> Tuple[float, float]:
    """
    Ordinary-least-squares slope and intercept of y ~ x.
    Returns (slope, intercept).
    """
    n = len(x_list)
    if n < 2:
        return (0.0, 0.0)
    mean_x = sum(x_list) / n
    mean_y = sum(y_list) / n
    ss_xx = sum((x - mean_x) ** 2 for x in x_list)
    ss_xy = sum((x - mean_x) * (y - mean_y)
                for x, y in zip(x_list, y_list))
    if ss_xx == 0.0:
        return (0.0, mean_y)
    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x
    return (slope, intercept)


def timing_slope(
    energy_GeV: List[float],
    distance_Mpc: List[float],
    timing_offset_s: List[float],
) -> float:
    """
    Primary statistic: slope of timing_offset ~ energy_GeV × distance_Mpc.

    Non-zero slope indicates energy-dependent propagation delay.
    """
    x = [e * d for e, d in zip(energy_GeV, distance_Mpc)]
    slope, _ = _linear_regression_slope(x, timing_offset_s)
    return slope


def _permutation_null_distribution(
    energy_GeV: List[float],
    distance_Mpc: List[float],
    timing_offset_s: List[float],
    n_permutations: int = 500,
    seed: int = 0,
) -> List[float]:
    """
    Build null distribution by shuffling energies (destroying true correlation).
    """
    rng = random.Random(seed)
    energy_pool = list(energy_GeV)
    null_slopes = []
    for _ in range(n_permutations):
        rng.shuffle(energy_pool)
        null_slopes.append(timing_slope(energy_pool, distance_Mpc, timing_offset_s))
    return null_slopes


def _empirical_p_value(
    observed: float, null_distribution: List[float]
) -> float:
    """Two-sided empirical p-value."""
    if not null_distribution:
        return 1.0
    abs_obs = abs(observed)
    return sum(1 for x in null_distribution if abs(x) >= abs_obs) / len(null_distribution)


# ---------------------------------------------------------------------------
# Recovery test
# ---------------------------------------------------------------------------


def _injection_recovery_test(
    n_events: int,
    injection_strength: float,
    true_slope: float,
    n_permutations: int,
    seed: int,
) -> Dict[str, Any]:
    """Inject known delay and verify recovery."""
    null_data = NullModelLibrary.no_delay(n_events, seed=seed)
    injected = SignalInjector.timing_delay_linear(
        null_data,
        delay_slope=true_slope,
        injection_strength=injection_strength,
        seed=seed + 1,
    )
    observed = timing_slope(
        injected["energy_GeV"],
        injected["distance_Mpc"],
        injected["timing_offset_s"],
    )
    null_dist = _permutation_null_distribution(
        injected["energy_GeV"],
        injected["distance_Mpc"],
        injected["timing_offset_s"],
        n_permutations=n_permutations,
        seed=seed + 2,
    )
    p_value = _empirical_p_value(observed, null_dist)
    recovered = p_value < 0.05
    expected_slope = injection_strength * true_slope * (
        sum(injected["energy_GeV"]) / n_events
    ) * (sum(injected["distance_Mpc"]) / n_events)
    _ = expected_slope  # computed for reference; used in reporting

    return {
        "injection_strength": injection_strength,
        "true_delay_slope": true_slope,
        "observed_slope": observed,
        "p_value": p_value,
        "recovered": recovered,
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_timing_pipeline(
    n_events: int = 2000,
    inject_signal: bool = False,
    injection_strength: float = 1.0,
    true_delay_slope: float = 5e-4,   # s / (GeV × Mpc)
    n_permutations: int = 500,
    seed: int = 42,
    output_dir: str = (
        "commons_sentience_sim/output/reality_audit/mock_timing_delay/"
    ),
    run_recovery_test: bool = True,
) -> Dict[str, Any]:
    """
    Execute the mock astrophysical timing-delay pipeline.

    Parameters
    ----------
    n_events          : number of simulated photon events
    inject_signal     : whether to inject a linear timing delay
    injection_strength: scale factor applied to true_delay_slope [0, 1+]
    true_delay_slope  : true delay in s / (GeV × Mpc)
    n_permutations    : permutation trials for null distribution
    seed              : master RNG seed
    output_dir        : base output directory
    run_recovery_test : whether to run signal-injection recovery test

    Returns
    -------
    dict with full pipeline results
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Generate null events
    null_data = NullModelLibrary.no_delay(n_events, seed=seed)

    # 2. Optionally inject signal
    if inject_signal:
        analysis_data = SignalInjector.timing_delay_linear(
            null_data,
            delay_slope=true_delay_slope,
            injection_strength=injection_strength,
            seed=seed + 1,
        )
    else:
        analysis_data = dict(null_data)
        analysis_data["injection"] = {"type": "none", "injection_strength": 0.0}

    energy = analysis_data["energy_GeV"]
    distance = analysis_data["distance_Mpc"]
    offsets = analysis_data["timing_offset_s"]

    # 3. Compute primary statistic
    observed_slope = timing_slope(energy, distance, offsets)

    # 4. Null distribution by permutation
    null_distribution = _permutation_null_distribution(
        energy, distance, offsets,
        n_permutations=n_permutations, seed=seed + 10,
    )
    null_mean = sum(null_distribution) / len(null_distribution)
    null_std = math.sqrt(
        sum((x - null_mean) ** 2 for x in null_distribution) / len(null_distribution)
    )
    p_value = _empirical_p_value(observed_slope, null_distribution)
    z_score = (
        (observed_slope - null_mean) / null_std if null_std > 0 else 0.0
    )

    # 5. Recovery test
    recovery = {}
    if run_recovery_test:
        recovery = _injection_recovery_test(
            n_events=n_events,
            injection_strength=injection_strength if inject_signal else 1.0,
            true_slope=true_delay_slope,
            n_permutations=min(n_permutations, 200),
            seed=seed + 20,
        )

    # 6. Full results
    full_results = {
        "experiment": "astrophysical_timing_delay_v1_mock",
        "n_events": n_events,
        "inject_signal": inject_signal,
        "injection": analysis_data.get("injection", {}),
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
        "status": "mock_dry_run",
    }

    # 7. Blinding + reporting
    blinder = Blinder(
        blind_keys=["p_value", "z_score", "detection_claimed", "null_retained",
                    "observed_slope"],
        experiment_name="astrophysical_timing_delay_v1_mock",
    )
    writer = ReportWriter(output_dir, "timing_delay_mock")

    blinded = blinder.blind(full_results)
    writer.write_json_summary(blinded, blinded=True)
    writer.write_markdown_summary(blinded, blinded=True)

    blinder.freeze(reason="Mock pipeline: immediate unblind for validation.")
    unblinded = blinder.unblind(full_results)
    writer.write_json_summary(unblinded, blinded=False)
    writer.write_markdown_summary(unblinded, blinded=False)

    writer.write_manifest()
    full_results["output_dir"] = output_dir
    full_results["blinding_summary"] = blinder.summary()

    return full_results
