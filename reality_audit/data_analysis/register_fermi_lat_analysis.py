"""
register_fermi_lat_analysis.py
================================
Formally registers the first real Fermi-LAT GRB timing-delay analysis
plan BEFORE any real data is ingested.

This implements lab-notebook discipline: the complete analysis plan
(hypothesis, statistic, null model, signal model, thresholds, blinding
policy) is recorded and frozen before the analyst ever sees the data.

Running this script:
  python reality_audit/data_analysis/register_fermi_lat_analysis.py

Creates:
  commons_sentience_sim/output/reality_audit/fermi_lat_analysis_registration.json

Important:
  - This script is idempotent: re-running it reads the existing file and
    prints its contents rather than overwriting (append-only discipline).
  - Modifying the analysis plan after registration requires creating a new
    versioned spec (e.g. "fermi_lat_grb_timing_v2").
  - No discovery claim may be made on the basis of partial ingest.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from reality_audit.data_analysis.experiment_registry import (
    ExperimentSpec,
    ExperimentRegistry,
)

# ---------------------------------------------------------------------------
# Registration path
# ---------------------------------------------------------------------------

REGISTRATION_PATH = (
    _REPO_ROOT
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
    / "fermi_lat_analysis_registration.json"
)

OUTPUT_DIR = str(
    _REPO_ROOT
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
    / "fermi_lat_real_analysis"
)

# ---------------------------------------------------------------------------
# Analysis plan (frozen at registration time)
# ---------------------------------------------------------------------------

FERMI_LAT_SPEC = ExperimentSpec(
    name="fermi_lat_grb_timing_v1",
    hypothesis=(
        "Photon arrival-time offsets from Fermi-LAT GRBs are correlated "
        "with photon energy (in GeV) scaled by luminosity distance (in Mpc), "
        "consistent with a linear Lorentz-invariance-violating dispersion "
        "relation of the form: delta_t = s * E * D_L."
    ),
    primary_statistic=(
        "OLS slope of timing_offset_s ~ energy_GeV × distance_Mpc "
        "(units: seconds per [GeV × Mpc]). "
        "Computed by reality_audit.data_analysis.mock_timing_pipeline.timing_slope()."
    ),
    null_model=(
        "permutation_energy_shuffle: energies shuffled within each source "
        "500 times (2000 for publication-quality); timing offsets and distances "
        "held fixed. Null distribution: OLS slopes from shuffled data. "
        "P-value: fraction of null slopes at least as extreme as observed."
    ),
    signal_model=(
        "timing_delay_linear (n=1): delta_t_LIV = s * energy_GeV * distance_Mpc "
        "where s = 1 / E_QG,1 / c in appropriate units. "
        "Recovery test uses s = 5e-4 s/(GeV·Mpc). "
        "Exclusion target: E_QG,1 > 10 * E_Planck (~1.22e19 GeV)."
    ),
    detection_threshold=3e-7,   # ~5σ  — required for detection claim
    rejection_threshold=0.05,   # p > 0.05 ⟹ null retained
    blinding_status="blinded",
    output_dir=OUTPUT_DIR,
    notes=(
        "PHASE 5 — first real public-data analysis run. "
        "Data source: Fermi-LAT GRB photon event catalogs, local CSV/FITS-derived files. "
        "Minimum viable dataset: ≥5 GRBs with confirmed spectroscopic redshift, "
        "≥5 events per GRB, energy range 0.1–300 GeV. "
        "Blinding: freeze_immediately=False required throughout real ingest. "
        "Unblinding condition: all quality-control checks pass per "
        "docs/FERMI_LAT_QC_CHECKLIST.md. "
        "No discovery claim is allowed on the basis of partial, incomplete, "
        "or unvalidated ingest. "
        "Exclusion bound may be reported without full discovery evidence. "
        "This plan was frozen BEFORE real data was touched — 2026-04-20."
    ),
    tags=["experiment1", "fermi_lat", "grb", "timing_delay", "liv", "phase5"],
)

# Supplementary fields not in ExperimentSpec dataclass — stored in extended JSON
SUPPLEMENTARY = {
    "source_class": "Fermi-LAT GRB photon event catalog",
    "required_data_fields": [
        "event_id",
        "source_id",
        "photon_energy (GeV or MeV with unit declared)",
        "arrival_time (seconds since trigger or MJD)",
        "redshift (spectroscopic preferred; photometric flagged)",
    ],
    "optional_data_fields": [
        "distance_Mpc (computed from z if absent)",
        "event_class / quality flag",
        "zenith_angle (for Earth-limb cut)",
    ],
    "minimum_viable_dataset": {
        "min_grbs_with_redshift": 5,
        "min_events_per_grb": 5,
        "min_total_events": 30,
        "energy_range_GeV": [0.1, 300.0],
    },
    "planned_robustness_checks": [
        "permutation test with 500 and 2000 trials",
        "bootstrap 95% CI on OLS slope",
        "jackknife: drop one GRB at a time, recompute slope",
        "energy-bin split: low-E (<1 GeV) vs high-E (>1 GeV)",
        "subluminal vs superluminal search (s > 0 and s < 0)",
        "sensitivity curve: slope limit as function of total N",
    ],
    "blinding_policy": {
        "freeze_immediately": False,
        "blind_keys": [
            "p_value",
            "z_score",
            "detection_claimed",
            "null_retained",
            "observed_slope",
        ],
        "unblinding_requires": [
            "all QC checks passed (docs/FERMI_LAT_QC_CHECKLIST.md)",
            "analysis plan registered and unmodified",
            "recovery test passed (p < 0.05)",
            "no partial-ingest warning in ingest manifest",
            "explicit human decision — not automatic",
        ],
    },
    "stopping_rules": [
        "STOP if n_events < 30 total after quality cuts",
        "STOP if any source has n_events < 5 after quality cuts",
        "STOP if redshift coverage < 5 independent GRBs",
        "STOP if recovery test fails at injection strength 5e-4",
        "STOP if duplicate event IDs exceed 0.1% of total",
        "STOP if energy-unit metadata is missing and cannot be inferred",
    ],
    "discovery_claim_policy": (
        "No detection claim is permitted unless: "
        "(1) p_value < 3e-7, "
        "(2) all robustness checks have been run and pass, "
        "(3) at least one independent analysis has been registered and run, "
        "(4) unblinding was performed exactly once. "
        "Partial ingest or single-dataset significance is NOT sufficient for "
        "a discovery claim under any circumstances."
    ),
    "exclusion_bound_policy": (
        "If p_value > 0.05 after a complete validated ingest, "
        "a 95% C.L. exclusion bound on E_QG,1 may be reported. "
        "Report as: E_QG,1 > X * E_Planck (95% C.L.) "
        "where X is computed from the 95th percentile of the null-permutation "
        "slope distribution converted to energy units."
    ),
    "registration_date": "2026-04-20",
    "registration_status": "FROZEN — do not modify this file after first data access",
}


def register_and_save() -> dict:
    """Write registration JSON.  Idempotent: will not overwrite existing file."""
    REGISTRATION_PATH.parent.mkdir(parents=True, exist_ok=True)

    if REGISTRATION_PATH.exists():
        print(f"[INFO] Registration already exists: {REGISTRATION_PATH}")
        with open(REGISTRATION_PATH) as f:
            existing = json.load(f)
        print(json.dumps(existing, indent=2)[:1000] + "\n... (truncated)")
        return existing

    registry = ExperimentRegistry()
    registry.register(FERMI_LAT_SPEC)

    full_record = {
        "spec": FERMI_LAT_SPEC.to_dict(),
        "supplementary": SUPPLEMENTARY,
    }

    with open(REGISTRATION_PATH, "w") as f:
        json.dump(full_record, f, indent=2)

    print(f"[OK] Registered: {REGISTRATION_PATH}")
    print(f"     Experiment : {FERMI_LAT_SPEC.name}")
    print(f"     Status     : {FERMI_LAT_SPEC.blinding_status}")
    print(f"     Threshold  : detection p < {FERMI_LAT_SPEC.detection_threshold:.0e}")
    print(f"     Note       : registration is FROZEN before first data access")
    return full_record


def load_registration(path: str | pathlib.Path | None = None) -> dict:
    """Load and return the registration record."""
    p = pathlib.Path(path) if path else REGISTRATION_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"Analysis registration not found at {p}. "
            "Run register_fermi_lat_analysis.py first."
        )
    with open(p) as f:
        return json.load(f)


if __name__ == "__main__":
    register_and_save()
