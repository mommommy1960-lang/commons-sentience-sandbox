"""
null_models.py
==============
Library of configurable null models for real-data analysis.

Each null model is a callable that generates synthetic null-hypothesis
datasets matching the shape/statistics of one experiment class.

Available models
----------------
isotropic_uniform          : uniform sphere (cosmic-ray anisotropy null)
no_delay                   : zero timing delay (timing-delay null)
symmetric_no_preferred_axis: symmetric multipole distribution (CMB null)
white_noise_background     : generic white-noise baseline
bandwidth_flat             : flat spectral density baseline

All generators accept a random seed for reproducibility.
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seeded_rng(seed: int) -> random.Random:
    return random.Random(seed)


def _uniform_sphere(rng: random.Random, n: int) -> List[Tuple[float, float]]:
    """
    Draw n points uniformly distributed on a unit sphere.
    Returns list of (theta_rad, phi_rad) in physics convention:
        theta in [0, pi], phi in [0, 2*pi).
    Uses rejection-free method: cos(theta) uniform in [-1, 1].
    """
    points = []
    two_pi = 2.0 * math.pi
    for _ in range(n):
        cos_theta = rng.uniform(-1.0, 1.0)
        theta = math.acos(cos_theta)
        phi = rng.uniform(0.0, two_pi)
        points.append((theta, phi))
    return points


# ---------------------------------------------------------------------------
# Null model library
# ---------------------------------------------------------------------------


class NullModelLibrary:
    """
    Provides synthetic null-hypothesis datasets for pipeline validation.

    Methods return raw event lists; summary statistics are computed by
    the pipeline's analysis module, not here.
    """

    # ------------------------------------------------------------------
    # Cosmic-ray anisotropy null
    # ------------------------------------------------------------------

    @staticmethod
    def isotropic_uniform(
        n_events: int,
        seed: int = 0,
        energy_range_eV: Tuple[float, float] = (1e18, 1e20),
    ) -> Dict[str, Any]:
        """
        Null model: cosmic rays arrive from uniformly random sky directions
        with energies drawn from a power-law distribution (index -3).

        Returns
        -------
        dict with keys:
          theta_rad  : list[float]  polar angle [0, pi]
          phi_rad    : list[float]  azimuthal angle [0, 2*pi)
          energy_eV  : list[float]  event energy
          n_events   : int
          model      : str
          seed       : int
        """
        rng = _seeded_rng(seed)
        directions = _uniform_sphere(rng, n_events)
        theta = [d[0] for d in directions]
        phi = [d[1] for d in directions]

        # Power-law energies via inverse-CDF (index -3, so CDF ~ E^{-2})
        E_lo, E_hi = energy_range_eV
        inv_lo = 1.0 / (E_lo * E_lo)
        inv_hi = 1.0 / (E_hi * E_hi)
        energies = []
        for _ in range(n_events):
            u = rng.random()
            inv_E2 = inv_lo + u * (inv_hi - inv_lo)
            energies.append(1.0 / math.sqrt(inv_E2))

        return {
            "theta_rad": theta,
            "phi_rad": phi,
            "energy_eV": energies,
            "n_events": n_events,
            "model": "isotropic_uniform",
            "seed": seed,
        }

    # ------------------------------------------------------------------
    # Timing-delay null
    # ------------------------------------------------------------------

    @staticmethod
    def no_delay(
        n_events: int,
        seed: int = 0,
        energy_range_GeV: Tuple[float, float] = (0.1, 300.0),
        distance_range_Mpc: Tuple[float, float] = (100.0, 5000.0),
    ) -> Dict[str, Any]:
        """
        Null model: photon arrival times have no energy dependence.
        Residual timing offsets are pure Gaussian noise.

        Returns dict with:
          energy_GeV      : list[float]
          distance_Mpc    : list[float]
          timing_offset_s : list[float]  — pure noise, sigma=0.01 s
          n_events        : int
          model           : str
          seed            : int
        """
        rng = _seeded_rng(seed)
        E_lo, E_hi = energy_range_GeV
        D_lo, D_hi = distance_range_Mpc
        NOISE_SIGMA = 0.01  # seconds

        energies = [rng.uniform(E_lo, E_hi) for _ in range(n_events)]
        distances = [rng.uniform(D_lo, D_hi) for _ in range(n_events)]
        offsets = [rng.gauss(0.0, NOISE_SIGMA) for _ in range(n_events)]

        return {
            "energy_GeV": energies,
            "distance_Mpc": distances,
            "timing_offset_s": offsets,
            "n_events": n_events,
            "model": "no_delay",
            "seed": seed,
        }

    # ------------------------------------------------------------------
    # CMB / multipole null
    # ------------------------------------------------------------------

    @staticmethod
    def symmetric_no_preferred_axis(
        n_pixels: int = 1024,
        seed: int = 0,
        l_max: int = 5,
    ) -> Dict[str, Any]:
        """
        Null model: CMB-like map with no preferred axis.
        Generates a_lm coefficients drawn from isotropic Gaussian with
        power C_l ~ 1/l(l+1) (Harrison-Zel'dovich-like).

        Returns dict with:
          alm_real : dict {(l,m): float}  real part
          alm_imag : dict {(l,m): float}  imag part
          n_pixels  : int
          l_max     : int
          model     : str
          seed      : int
        """
        rng = _seeded_rng(seed)
        alm_real: Dict[Tuple[int, int], float] = {}
        alm_imag: Dict[Tuple[int, int], float] = {}

        for l in range(1, l_max + 1):
            C_l = 1.0 / (l * (l + 1))
            sigma = math.sqrt(C_l)
            for m in range(-l, l + 1):
                alm_real[(l, m)] = rng.gauss(0.0, sigma)
                alm_imag[(l, m)] = rng.gauss(0.0, sigma)

        return {
            "alm_real": {str(k): v for k, v in alm_real.items()},
            "alm_imag": {str(k): v for k, v in alm_imag.items()},
            "n_pixels": n_pixels,
            "l_max": l_max,
            "model": "symmetric_no_preferred_axis",
            "seed": seed,
        }

    # ------------------------------------------------------------------
    # Generic baseline models
    # ------------------------------------------------------------------

    @staticmethod
    def white_noise_background(
        n_samples: int,
        seed: int = 0,
        sigma: float = 1.0,
        mean: float = 0.0,
    ) -> Dict[str, Any]:
        """Gaussian white-noise time series."""
        rng = _seeded_rng(seed)
        samples = [rng.gauss(mean, sigma) for _ in range(n_samples)]
        return {
            "samples": samples,
            "n_samples": n_samples,
            "mean": mean,
            "sigma": sigma,
            "model": "white_noise_background",
            "seed": seed,
        }

    @staticmethod
    def bandwidth_flat(
        n_bins: int,
        seed: int = 0,
        baseline: float = 1.0,
        noise_fraction: float = 0.01,
    ) -> Dict[str, Any]:
        """Flat spectral density with small Poisson-like perturbations."""
        rng = _seeded_rng(seed)
        counts = [
            max(0.0, rng.gauss(baseline, baseline * noise_fraction))
            for _ in range(n_bins)
        ]
        return {
            "counts": counts,
            "n_bins": n_bins,
            "baseline": baseline,
            "model": "bandwidth_flat",
            "seed": seed,
        }

    # ------------------------------------------------------------------
    # Registry lookup
    # ------------------------------------------------------------------

    MODEL_KEYS = [
        "isotropic_uniform",
        "no_delay",
        "symmetric_no_preferred_axis",
        "white_noise_background",
        "bandwidth_flat",
    ]

    @classmethod
    def available(cls) -> List[str]:
        return list(cls.MODEL_KEYS)

    @classmethod
    def get(cls, key: str, **kwargs: Any) -> Dict[str, Any]:
        """Dispatch by model key."""
        dispatch = {
            "isotropic_uniform": cls.isotropic_uniform,
            "no_delay": cls.no_delay,
            "symmetric_no_preferred_axis": cls.symmetric_no_preferred_axis,
            "white_noise_background": cls.white_noise_background,
            "bandwidth_flat": cls.bandwidth_flat,
        }
        if key not in dispatch:
            raise KeyError(
                f"Unknown null model '{key}'. "
                f"Available: {cls.MODEL_KEYS}"
            )
        return dispatch[key](**kwargs)
