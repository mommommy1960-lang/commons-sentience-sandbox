"""
signal_injection.py
===================
Synthetic signal injection for pipeline validation.

Injecting a known signal and verifying recovery is the core of our
"benchmark-driven validation discipline" transferred from the quantum
double-slit work:
  - inject preferred-axis signal → confirm dipole detection fires
  - inject zero signal → confirm null is retained

Available injectors
-------------------
preferred_axis          : dipole-like excess toward a chosen sky direction
anisotropy_injection    : quadrupole excess (CMB-style)
timing_delay_linear     : linear energy-dependent time delay
bandwidth_anomaly       : narrow-band excess above flat background

All injectors:
  - accept a null-model dataset dict and return a modified copy
  - accept injection_strength in [0, 1] (0 = pure null, 1 = full signal)
  - are deterministic given the same seed
  - document the injected signal in a "injection" sub-dict

Design principle (from benchmark work):
  The pipeline must be able to detect a signal at 1-sigma injection
  strength.  If it cannot, the pipeline is not sensitive enough for the
  proposed experiment.
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, Optional


def _seeded_rng(seed: int) -> random.Random:
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Injectors
# ---------------------------------------------------------------------------


class SignalInjector:

    # ------------------------------------------------------------------
    # Cosmic-ray preferred-axis injection
    # ------------------------------------------------------------------

    @staticmethod
    def preferred_axis(
        null_data: Dict[str, Any],
        injection_strength: float = 0.1,
        axis_theta_rad: float = 0.0,   # toward north pole by default
        axis_phi_rad: float = 0.0,
        seed: int = 1,
    ) -> Dict[str, Any]:
        """
        Inject a dipole-like anisotropy toward (axis_theta, axis_phi).

        For each event, the acceptance probability is scaled by
            w = 1 + injection_strength * cos(angle_to_axis)
        where each event is independently accepted (rejection sampling).
        Events that are rejected have their direction replaced with a new
        uniform draw.  Total event count is preserved.

        Parameters
        ----------
        null_data          : output of NullModelLibrary.isotropic_uniform()
        injection_strength : [0, 1] how strong the dipole is
        axis_theta_rad     : polar angle of preferred axis
        axis_phi_rad       : azimuthal angle of preferred axis
        seed               : RNG seed for replacement draws

        Returns
        -------
        Modified copy of null_data with "injection" metadata added.
        """
        if not (0.0 <= injection_strength <= 1.0):
            raise ValueError("injection_strength must be in [0, 1].")

        rng = _seeded_rng(seed)
        theta = list(null_data["theta_rad"])
        phi = list(null_data["phi_rad"])
        n = len(theta)

        # Unit vector of preferred axis
        sin_a = math.sin(axis_theta_rad)
        cos_a = math.cos(axis_theta_rad)
        ax = (sin_a * math.cos(axis_phi_rad),
              sin_a * math.sin(axis_phi_rad),
              cos_a)

        two_pi = 2.0 * math.pi
        accepted = 0
        for i in range(n):
            # Dot product with axis
            sin_t = math.sin(theta[i])
            cos_t = math.cos(theta[i])
            dot = (sin_t * math.cos(phi[i]) * ax[0]
                   + sin_t * math.sin(phi[i]) * ax[1]
                   + cos_t * ax[2])
            w = 1.0 + injection_strength * dot        # in range [0, 2]
            accept_prob = w / 2.0                      # normalise to [0, 1]
            if rng.random() < accept_prob:
                accepted += 1
            else:
                # Replace with a new uniform direction
                cos_theta_new = rng.uniform(-1.0, 1.0)
                theta[i] = math.acos(cos_theta_new)
                phi[i] = rng.uniform(0.0, two_pi)

        data = dict(null_data)
        data["theta_rad"] = theta
        data["phi_rad"] = phi
        data["injection"] = {
            "type": "preferred_axis",
            "injection_strength": injection_strength,
            "axis_theta_rad": axis_theta_rad,
            "axis_phi_rad": axis_phi_rad,
            "seed": seed,
            "acceptance_rate": accepted / n,
        }
        return data

    # ------------------------------------------------------------------
    # CMB anisotropy injection
    # ------------------------------------------------------------------

    @staticmethod
    def anisotropy_injection(
        null_data: Dict[str, Any],
        injection_strength: float = 0.1,
        target_l: int = 2,
        target_m: int = 0,
        seed: int = 1,
    ) -> Dict[str, Any]:
        """
        Boost a specific a_lm coefficient to inject a preferred quadrupole.

        Parameters
        ----------
        null_data          : output of NullModelLibrary.symmetric_no_preferred_axis()
        injection_strength : amplitude added to selected a_lm (in units of sigma)
        target_l, target_m : which multipole to boost
        seed               : not used (deterministic boost)

        Returns modified copy with "injection" key.
        """
        data = dict(null_data)
        alm_real = dict(null_data["alm_real"])
        key = str((target_l, target_m))
        current = alm_real.get(key, 0.0)
        # sigma for this l is sqrt(1/(l*(l+1)))
        sigma = math.sqrt(1.0 / (target_l * (target_l + 1)))
        boost = injection_strength * sigma
        alm_real[key] = current + boost
        data["alm_real"] = alm_real
        data["injection"] = {
            "type": "anisotropy_injection",
            "injection_strength": injection_strength,
            "target_l": target_l,
            "target_m": target_m,
            "boost_added": boost,
        }
        return data

    # ------------------------------------------------------------------
    # Timing-delay injection
    # ------------------------------------------------------------------

    @staticmethod
    def timing_delay_linear(
        null_data: Dict[str, Any],
        delay_slope: float = 1e-3,   # seconds per GeV per Mpc
        injection_strength: float = 1.0,
        seed: int = 1,
    ) -> Dict[str, Any]:
        """
        Add a linear energy × distance timing delay:
            Δt = injection_strength × delay_slope × E_GeV × D_Mpc

        Parameters
        ----------
        null_data       : output of NullModelLibrary.no_delay()
        delay_slope     : seconds / (GeV * Mpc) — the LIV-style slope
        injection_strength : [0, 1] scales the full slope
        seed            : not used

        Returns modified copy with "injection" key.
        """
        data = dict(null_data)
        offsets = list(null_data["timing_offset_s"])
        energies = null_data["energy_GeV"]
        distances = null_data["distance_Mpc"]
        effective_slope = injection_strength * delay_slope

        new_offsets = [
            offsets[i] + effective_slope * energies[i] * distances[i]
            for i in range(len(offsets))
        ]
        data["timing_offset_s"] = new_offsets
        data["injection"] = {
            "type": "timing_delay_linear",
            "delay_slope": delay_slope,
            "injection_strength": injection_strength,
            "effective_slope": effective_slope,
        }
        return data

    # ------------------------------------------------------------------
    # Bandwidth / narrow-band anomaly injection
    # ------------------------------------------------------------------

    @staticmethod
    def bandwidth_anomaly(
        null_data: Dict[str, Any],
        anomaly_bin_start: int = 0,
        anomaly_bin_end: Optional[int] = None,
        excess_fraction: float = 0.5,
        injection_strength: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Add a fractional excess to a contiguous range of bins.

        Parameters
        ----------
        null_data        : output of NullModelLibrary.bandwidth_flat()
        anomaly_bin_start: first bin of anomaly (inclusive)
        anomaly_bin_end  : last bin of anomaly (exclusive); None = midpoint
        excess_fraction  : fractional increase per affected bin (e.g. 0.5 = +50 %)
        injection_strength: [0, 1] scales the excess

        Returns modified copy with "injection" key.
        """
        counts = list(null_data["counts"])
        n = len(counts)
        end = anomaly_bin_end if anomaly_bin_end is not None else n // 2

        effective_excess = injection_strength * excess_fraction
        for i in range(anomaly_bin_start, min(end, n)):
            counts[i] *= (1.0 + effective_excess)

        data = dict(null_data)
        data["counts"] = counts
        data["injection"] = {
            "type": "bandwidth_anomaly",
            "anomaly_bin_start": anomaly_bin_start,
            "anomaly_bin_end": end,
            "excess_fraction": excess_fraction,
            "injection_strength": injection_strength,
            "effective_excess": effective_excess,
        }
        return data

    # ------------------------------------------------------------------
    # Registry lookup
    # ------------------------------------------------------------------

    INJECTOR_KEYS = [
        "preferred_axis",
        "anisotropy_injection",
        "timing_delay_linear",
        "bandwidth_anomaly",
    ]

    @classmethod
    def available(cls) -> list:
        return list(cls.INJECTOR_KEYS)

    @classmethod
    def inject(
        cls,
        key: str,
        null_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Dispatch injection by key."""
        dispatch = {
            "preferred_axis": cls.preferred_axis,
            "anisotropy_injection": cls.anisotropy_injection,
            "timing_delay_linear": cls.timing_delay_linear,
            "bandwidth_anomaly": cls.bandwidth_anomaly,
        }
        if key not in dispatch:
            raise KeyError(
                f"Unknown injector '{key}'. Available: {cls.INJECTOR_KEYS}"
            )
        return dispatch[key](null_data, **kwargs)
