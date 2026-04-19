"""
experiment_registry.py
======================
Structured registry for planned real-data experiments.

Each ExperimentSpec captures the full analysis plan before any data is
touched: hypothesis, primary statistic, null model, signal model, decision
thresholds, blinding status, output paths, and reproducibility metadata.

The registry is append-only and queryable.  It is the authoritative record
of what we intend to test and how.

Design principles (from benchmark work):
  - freeze the analysis plan before unblinding (lab-notebook discipline)
  - separate null from signal model at registration time
  - record reproducibility metadata (seed, software version) at run time
"""

from __future__ import annotations

import datetime
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ReproducibilityMetadata:
    """Captured at run time; empty until the experiment is executed."""
    git_commit: str = ""
    python_version: str = ""
    random_seed: int = 0
    run_timestamp: str = ""
    software_versions: Dict[str, str] = field(default_factory=dict)

    def capture(self, seed: int = 0) -> "ReproducibilityMetadata":
        import sys
        import subprocess  # noqa: S404 – read-only git query
        commit = ""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, check=False,
            )
            commit = result.stdout.strip()
        except Exception:
            pass
        return ReproducibilityMetadata(
            git_commit=commit,
            python_version=sys.version,
            random_seed=seed,
            run_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            software_versions={},
        )


@dataclass
class ExperimentSpec:
    """
    Full analysis plan for one real-data experiment.

    Parameters
    ----------
    name : str
        Unique experiment identifier, e.g. "cosmic_ray_anisotropy_v1".
    hypothesis : str
        Plain-language statement of what is being tested.
    primary_statistic : str
        Name/description of the primary test statistic.
    null_model : str
        Key into NullModelLibrary, e.g. "isotropic_uniform".
    signal_model : str
        Key into SignalInjector, e.g. "preferred_axis".
    detection_threshold : float
        p-value (or equivalent) at which we claim detection.
    rejection_threshold : float
        p-value below which null is confidently retained.
    blinding_status : str
        One of "blinded", "partially_blinded", "open".
    output_dir : str
        Relative path for all outputs from this experiment.
    notes : str
        Free-text notes; updated as the plan evolves.
    reproducibility : ReproducibilityMetadata
        Populated at run time.
    tags : List[str]
        Free-form labels for filtering.
    """
    name: str
    hypothesis: str
    primary_statistic: str
    null_model: str
    signal_model: str
    detection_threshold: float = 3e-7   # ~5-sigma
    rejection_threshold: float = 0.05
    blinding_status: str = "blinded"
    output_dir: str = ""
    notes: str = ""
    reproducibility: ReproducibilityMetadata = field(
        default_factory=ReproducibilityMetadata
    )
    tags: List[str] = field(default_factory=list)

    def is_blinded(self) -> bool:
        return self.blinding_status == "blinded"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExperimentSpec":
        repro_raw = d.pop("reproducibility", {})
        spec = cls(**{k: v for k, v in d.items() if k != "reproducibility"})
        spec.reproducibility = ReproducibilityMetadata(**repro_raw)
        return spec


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class ExperimentRegistry:
    """
    Append-only registry of ExperimentSpec objects.

    Usage
    -----
    registry = ExperimentRegistry()
    registry.register(spec)
    specs = registry.all()
    registry.save("path/to/registry.json")
    registry2 = ExperimentRegistry.load("path/to/registry.json")
    """

    def __init__(self) -> None:
        self._specs: Dict[str, ExperimentSpec] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def register(self, spec: ExperimentSpec) -> None:
        """Add a new experiment spec.  Raises if name already exists."""
        if spec.name in self._specs:
            raise ValueError(
                f"Experiment '{spec.name}' already registered. "
                "Use update() to modify an existing spec."
            )
        self._specs[spec.name] = spec

    def update(self, name: str, **kwargs: Any) -> ExperimentSpec:
        """Update fields of an existing spec.  Returns updated spec."""
        if name not in self._specs:
            raise KeyError(f"No experiment named '{name}'.")
        spec = self._specs[name]
        for k, v in kwargs.items():
            if hasattr(spec, k):
                setattr(spec, k, v)
            else:
                raise AttributeError(f"ExperimentSpec has no field '{k}'.")
        return spec

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def all(self) -> List[ExperimentSpec]:
        return list(self._specs.values())

    def get(self, name: str) -> ExperimentSpec:
        if name not in self._specs:
            raise KeyError(f"No experiment named '{name}'.")
        return self._specs[name]

    def filter_by_tag(self, tag: str) -> List[ExperimentSpec]:
        return [s for s in self._specs.values() if tag in s.tags]

    def filter_by_blinding(self, status: str) -> List[ExperimentSpec]:
        return [s for s in self._specs.values() if s.blinding_status == status]

    def summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": s.name,
                "hypothesis": s.hypothesis,
                "primary_statistic": s.primary_statistic,
                "null_model": s.null_model,
                "signal_model": s.signal_model,
                "blinding_status": s.blinding_status,
                "tags": s.tags,
            }
            for s in self.all()
        ]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        data = [s.to_dict() for s in self.all()]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "ExperimentRegistry":
        reg = cls()
        with open(path) as f:
            data = json.load(f)
        for d in data:
            reg._specs[d["name"]] = ExperimentSpec.from_dict(d)
        return reg

    def __len__(self) -> int:
        return len(self._specs)


# ---------------------------------------------------------------------------
# Pre-registered candidate experiments
# ---------------------------------------------------------------------------


def build_default_registry() -> ExperimentRegistry:
    """
    Returns a registry pre-populated with the three candidate Year-1
    real-data experiments.  All are blinded until analysis plan is frozen.
    """
    registry = ExperimentRegistry()

    registry.register(ExperimentSpec(
        name="cosmic_ray_anisotropy_v1",
        hypothesis=(
            "The arrival directions of ultra-high-energy cosmic rays are "
            "isotropic (null). A preferred-axis signal would show a "
            "statistically significant dipole or quadrupole component."
        ),
        primary_statistic="spherical_harmonic_power_l1_l2",
        null_model="isotropic_uniform",
        signal_model="preferred_axis",
        detection_threshold=3e-7,
        rejection_threshold=0.05,
        blinding_status="blinded",
        output_dir="commons_sentience_sim/output/reality_audit/exp1_cosmic_ray/",
        notes="Target dataset: Auger public release or equivalent.",
        tags=["cosmic_ray", "anisotropy", "year1", "data_analysis"],
    ))

    registry.register(ExperimentSpec(
        name="astrophysical_timing_delay_v1",
        hypothesis=(
            "There is no systematic energy-dependent timing delay between "
            "photon arrival times from astrophysical transients (null). "
            "A linear energy-distance delay signature would indicate "
            "Lorentz-invariance violation or novel propagation physics."
        ),
        primary_statistic="linear_energy_delay_slope_eV_inv_Mpc",
        null_model="no_delay",
        signal_model="timing_delay_linear",
        detection_threshold=3e-7,
        rejection_threshold=0.05,
        blinding_status="blinded",
        output_dir="commons_sentience_sim/output/reality_audit/exp1_timing_delay/",
        notes="Target dataset: Fermi-LAT GRB catalog (public).",
        tags=["timing_delay", "lorentz", "year1", "data_analysis"],
    ))

    registry.register(ExperimentSpec(
        name="cmb_axis_alignment_v1",
        hypothesis=(
            "CMB low-multipole power is statistically consistent with "
            "isotropy (null). An 'axis of evil' alignment would appear "
            "as anomalous correlation between low-l multipole orientations."
        ),
        primary_statistic="multipole_alignment_statistic_l2_l3",
        null_model="symmetric_no_preferred_axis",
        signal_model="anisotropy_injection",
        detection_threshold=3e-7,
        rejection_threshold=0.05,
        blinding_status="blinded",
        output_dir="commons_sentience_sim/output/reality_audit/exp1_cmb_axis/",
        notes="Target dataset: Planck public legacy maps.",
        tags=["cmb", "anisotropy", "year1", "data_analysis"],
    ))

    return registry
