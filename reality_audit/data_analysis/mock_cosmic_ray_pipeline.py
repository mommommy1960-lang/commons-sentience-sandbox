"""
mock_cosmic_ray_pipeline.py
===========================
Dry-run version of a cosmic-ray anisotropy analysis pipeline.

Purpose
-------
Build and validate the exact pipeline structure we will later apply to
real public-data cosmic-ray datasets (e.g. Pierre Auger Observatory).

This mock pipeline:
  1. Generates synthetic cosmic-ray events (via NullModelLibrary)
  2. Optionally injects a preferred-axis signal (via SignalInjector)
  3. Computes the dipole power as the primary test statistic
  4. Runs a null-hypothesis permutation test
  5. Performs signal-injection recovery test
  6. Produces blinded and unblinded outputs (via Blinder + ReportWriter)

No real external data is fetched.

Key design choices (from benchmark work):
  - test statistic defined BEFORE looking at results
  - null reference distribution built by permutation (direction scrambling)
  - recovery test verifies pipeline sensitivity
  - blinding maintained until analysis plan is frozen
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
# Primary test statistic
# ---------------------------------------------------------------------------


def _unit_vector(theta: float, phi: float) -> Tuple[float, float, float]:
    s = math.sin(theta)
    return (s * math.cos(phi), s * math.sin(phi), math.cos(theta))


def dipole_power(theta_list: List[float], phi_list: List[float]) -> float:
    """
    Compute the squared dipole amplitude |d|² from event arrival directions.

    d_i = mean(unit_vectors[:, i])
    dipole_power = |d|² = d_x² + d_y² + d_z²

    Under isotropy E[dipole_power] ≈ 3/N.
    Under a dipole anisotropy the power is enhanced.
    """
    n = len(theta_list)
    if n == 0:
        return 0.0
    dx = dy = dz = 0.0
    for t, p in zip(theta_list, phi_list):
        v = _unit_vector(t, p)
        dx += v[0]
        dy += v[1]
        dz += v[2]
    dx /= n
    dy /= n
    dz /= n
    return dx * dx + dy * dy + dz * dz


def _permutation_null_distribution(
    theta_list: List[float],
    phi_list: List[float],
    n_permutations: int = 500,
    seed: int = 0,
) -> List[float]:
    """
    Build a null distribution by randomly scrambling event directions.
    Each permutation pairs each theta with a random phi.
    """
    rng = random.Random(seed)
    null_powers = []
    phi_pool = list(phi_list)
    for _ in range(n_permutations):
        rng.shuffle(phi_pool)
        null_powers.append(dipole_power(theta_list, phi_pool))
    return null_powers


def _empirical_p_value(
    observed: float, null_distribution: List[float]
) -> float:
    """Fraction of null samples >= observed."""
    if not null_distribution:
        return 1.0
    return sum(1 for x in null_distribution if x >= observed) / len(null_distribution)


# ---------------------------------------------------------------------------
# Recovery test
# ---------------------------------------------------------------------------


def _injection_recovery_test(
    n_events: int,
    injection_strength: float,
    n_permutations: int,
    seed: int,
) -> Dict[str, Any]:
    """
    Inject a known dipole signal and verify the pipeline detects it.
    Returns recovery dict.
    """
    null_data = NullModelLibrary.isotropic_uniform(n_events, seed=seed)
    injected_data = SignalInjector.preferred_axis(
        null_data,
        injection_strength=injection_strength,
        axis_theta_rad=0.0,
        axis_phi_rad=0.0,
        seed=seed + 1,
    )
    observed_power = dipole_power(
        injected_data["theta_rad"], injected_data["phi_rad"]
    )
    null_dist = _permutation_null_distribution(
        injected_data["theta_rad"], injected_data["phi_rad"],
        n_permutations=n_permutations, seed=seed + 2,
    )
    p_value = _empirical_p_value(observed_power, null_dist)
    recovered = p_value < 0.05

    pure_null = NullModelLibrary.isotropic_uniform(n_events, seed=seed + 3)
    null_power = dipole_power(pure_null["theta_rad"], pure_null["phi_rad"])

    return {
        "injection_strength": injection_strength,
        "observed_dipole_power": observed_power,
        "null_expected_dipole_power": null_power,
        "p_value": p_value,
        "recovered": recovered,
        "signal_to_null_ratio": (
            observed_power / null_power if null_power > 0 else float("inf")
        ),
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_cosmic_ray_pipeline(
    n_events: int = 2000,
    inject_signal: bool = False,
    injection_strength: float = 0.15,
    n_permutations: int = 500,
    seed: int = 42,
    output_dir: str = (
        "commons_sentience_sim/output/reality_audit/mock_cosmic_ray/"
    ),
    run_recovery_test: bool = True,
) -> Dict[str, Any]:
    """
    Execute the mock cosmic-ray anisotropy pipeline.

    Parameters
    ----------
    n_events          : number of simulated cosmic-ray events
    inject_signal     : whether to inject a preferred-axis signal
    injection_strength: dipole amplitude [0, 1]
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
    null_data = NullModelLibrary.isotropic_uniform(n_events, seed=seed)

    # 2. Optionally inject signal
    if inject_signal:
        analysis_data = SignalInjector.preferred_axis(
            null_data,
            injection_strength=injection_strength,
            axis_theta_rad=0.0,
            axis_phi_rad=0.0,
            seed=seed + 1,
        )
    else:
        analysis_data = dict(null_data)
        analysis_data["injection"] = {"type": "none", "injection_strength": 0.0}

    theta = analysis_data["theta_rad"]
    phi = analysis_data["phi_rad"]

    # 3. Compute primary test statistic
    observed_power = dipole_power(theta, phi)

    # 4. Build null distribution by permutation
    null_distribution = _permutation_null_distribution(
        theta, phi, n_permutations=n_permutations, seed=seed + 10
    )
    null_mean = sum(null_distribution) / len(null_distribution)
    null_std = math.sqrt(
        sum((x - null_mean) ** 2 for x in null_distribution) / len(null_distribution)
    )
    p_value = _empirical_p_value(observed_power, null_distribution)
    z_score = (
        (observed_power - null_mean) / null_std if null_std > 0 else 0.0
    )

    # 5. Recovery test
    recovery = {}
    if run_recovery_test:
        recovery = _injection_recovery_test(
            n_events=n_events,
            injection_strength=0.2,
            n_permutations=min(n_permutations, 200),
            seed=seed + 20,
        )

    # 6. Assemble full results
    full_results = {
        "experiment": "cosmic_ray_anisotropy_v1_mock",
        "n_events": n_events,
        "inject_signal": inject_signal,
        "injection": analysis_data.get("injection", {}),
        "primary_statistic": "dipole_power",
        "observed_dipole_power": observed_power,
        "null_mean_dipole_power": null_mean,
        "null_std_dipole_power": null_std,
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
        blind_keys=["p_value", "z_score", "detection_claimed", "null_retained"],
        experiment_name="cosmic_ray_anisotropy_v1_mock",
    )
    writer = ReportWriter(output_dir, "cosmic_ray_anisotropy_mock")

    blinded = blinder.blind(full_results)
    writer.write_json_summary(blinded, blinded=True)
    writer.write_markdown_summary(blinded, blinded=True)

    # Freeze and unblind (in mock we always unblind immediately)
    blinder.freeze(reason="Mock pipeline: immediate unblind for validation.")
    unblinded = blinder.unblind(full_results)
    writer.write_json_summary(unblinded, blinded=False)
    writer.write_markdown_summary(unblinded, blinded=False)

    paths = writer.write_manifest()
    full_results["output_dir"] = output_dir
    full_results["blinding_summary"] = blinder.summary()

    return full_results
