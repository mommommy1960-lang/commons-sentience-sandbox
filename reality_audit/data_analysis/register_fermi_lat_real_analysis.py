"""
register_fermi_lat_real_analysis.py
=====================================
Formally registers the first true Fermi-LAT GRB timing-delay public-data
analysis BEFORE any real data are ingested.

This must be run (and the output committed) before ingesting any real
Fermi-LAT event files.  It is a one-time pre-registration step consistent
with the companion-book blinding protocol and the benchmark-transfer
principle P08 (analysis plan frozen before unblinding).

Usage:
    python reality_audit/data_analysis/register_fermi_lat_real_analysis.py

Output:
    commons_sentience_sim/output/reality_audit/fermi_lat_real_analysis_registration.json
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
OUTPUT_PATH = (
    _REPO_ROOT
    / "commons_sentience_sim"
    / "output"
    / "reality_audit"
    / "fermi_lat_real_analysis_registration.json"
)

# ---------------------------------------------------------------------------
# Registration spec — FROZEN at the time of first execution
# Must NOT be changed after real data are ingested.
# Any modification requires re-registration under a new experiment name.
# ---------------------------------------------------------------------------

REGISTRATION: dict = {
    "schema_version": "1.0",
    "registration_date": "2026-04-20",
    "frozen": True,

    # ---- Identity ----
    "experiment_name": "fermi_lat_grb_timing_delay_real_v1",
    "experiment_class": "data_analysis_only",
    "companion_book_phase": "Experiment 1, Phase 5",

    # ---- Hypothesis ----
    "null_hypothesis": (
        "Photon arrival-time offsets are uncorrelated with photon energy "
        "at any luminosity distance.  No Lorentz-Invariance Violation (LIV) "
        "energy-dependent speed correction is present."
    ),
    "alternative_hypothesis": (
        "A linear (n=1) LIV dispersion relation produces a non-zero OLS slope "
        "beta in:  timing_offset_s ~ energy_GeV * distance_Mpc"
    ),
    "signal_model": "timing_delay_linear_n1",
    "signal_model_description": (
        "Leading-order subluminal/superluminal LIV: "
        "delta_t = s * energy_GeV * distance_Mpc, "
        "where s [s/(GeV*Mpc)] encodes 1/E_QG."
    ),

    # ---- Primary statistic ----
    "primary_statistic": "OLS_slope_timing_vs_energy_times_distance",
    "primary_statistic_formula": (
        "beta = OLS slope of timing_offset_s regressed on "
        "(energy_GeV * distance_Mpc), without intercept constraint"
    ),

    # ---- Null model ----
    "null_model": "energy_permutation",
    "null_model_description": (
        "500 permutations of photon energies within each source, "
        "preserving marginal energy distribution.  "
        "Null distribution is the resulting set of OLS slopes."
    ),
    "n_permutations": 500,
    "seed": 42,

    # ---- Thresholds ----
    "thresholds": {
        "detection_claim_p": 3e-7,
        "detection_claim_sigma": 5.0,
        "detection_claim_note": (
            "Detection may ONLY be claimed if p < 3e-7 AND ingest is complete "
            "(no stopping rules triggered) AND all QC gates pass."
        ),
        "interesting_excess_p": 1.35e-3,
        "interesting_excess_sigma": 3.0,
        "interesting_excess_note": (
            "Report as 'interesting excess requiring follow-up'; "
            "do NOT announce as detection."
        ),
        "null_retained_p": 0.05,
        "null_retained_note": (
            "If p > 0.05, null hypothesis is retained.  "
            "State as 'no significant evidence for LIV; consistent with null'."
        ),
        "exclusion_bound_policy": (
            "If null retained: derive 95% C.L. upper bound on |slope|, "
            "convert to lower bound on E_QG_1 via: "
            "E_QG_1 > (1 / |slope_95|) * (c / H0) in GeV. "
            "State as exclusion limit, not absence of signal."
        ),
    },

    # ---- Source class ----
    "source_class": "gamma_ray_bursts",
    "target_grbs": [
        "GRB080916C",
        "GRB090902B",
        "GRB090510",
        "GRB130427A",
        "GRB160509A",
    ],
    "minimum_grbs_for_analysis": 3,
    "minimum_events_per_grb": 5,
    "minimum_total_events": 20,

    # ---- Required data fields ----
    "required_fields": [
        "event_id",
        "source_id",
        "photon_energy",
        "arrival_time",
        "redshift",
    ],
    "optional_fields": ["distance_Mpc", "event_class", "zenith_angle"],
    "energy_unit_expected": "GeV",
    "time_unit_expected": "seconds_trigger_relative",

    # ---- Blinding policy ----
    "blinding_policy": {
        "mode": "blinded_until_explicit_unblind",
        "freeze_immediately": False,
        "unblind_requires": [
            "all_qc_gates_passed",
            "ingest_complete_flag_true",
            "registration_hash_verified",
            "explicit_human_approval",
        ],
        "automatic_unblind": False,
        "note": (
            "Signal keys (p_value, z_score, observed_slope, detection_claimed) "
            "are blinded by default.  Unblinding requires passing all QC gates "
            "AND explicit human sign-off.  The blinded runner MUST NOT unblind "
            "automatically under any condition."
        ),
    },

    # ---- Robustness checks ----
    "robustness_checks": [
        "Repeat analysis excluding each GRB in turn (jackknife per source)",
        "Repeat with subluminal AND superluminal sign conventions",
        "Repeat with energy threshold raised to 1 GeV",
        "Repeat with time window tightened to T0 ± 100 s",
        "Check for energy-time correlation within each source separately",
        "Verify null distribution is Gaussian (Shapiro-Wilk p > 0.01)",
        "Verify recovery test p < 0.05 for slope = 5e-4 s/(GeV*Mpc)",
    ],

    # ---- Stopping rules ----
    "stopping_rules": [
        {
            "condition": "total_events_after_qc < minimum_total_events",
            "action": "STOP — report as 'insufficient data for analysis'",
        },
        {
            "condition": "n_sources_with_redshift < minimum_grbs_for_analysis",
            "action": "STOP — report as 'insufficient redshift coverage'",
        },
        {
            "condition": "fraction_dropped_rows > 0.20",
            "action": "STOP — report as 'excessive data quality issues'",
        },
        {
            "condition": "ingest_manifest_missing",
            "action": "STOP — do not run pipeline without validated ingest manifest",
        },
        {
            "condition": "registration_file_missing_or_modified",
            "action": "STOP — registration must exist and be unmodified before run",
        },
    ],

    # ---- Discovery claim rules ----
    "discovery_claim_rules": {
        "permitted_if": (
            "p < 3e-7 AND ingest_complete AND all_qc_gates_passed "
            "AND explicit_human_approval AND robustness_checks_passed"
        ),
        "not_permitted_if": [
            "partial_ingest (any stopping rule triggered)",
            "malformed_file_detected",
            "qc_gate_failed",
            "automatic_unblind (no human sign-off)",
            "local_sample_data_only (synthetic data not real public data)",
        ],
        "overclaiming_statement": (
            "The local-sample dry-run p-value (from synthetic data) is NOT "
            "a scientific result and MUST NOT be cited as evidence of LIV or "
            "any other physical effect."
        ),
    },
}


def register() -> dict:
    """Write registration JSON and return it."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(REGISTRATION, f, indent=2)
    print(f"Registration written: {OUTPUT_PATH}")
    print(f"  experiment_name : {REGISTRATION['experiment_name']}")
    print(f"  frozen          : {REGISTRATION['frozen']}")
    print(f"  auto_unblind    : {REGISTRATION['blinding_policy']['automatic_unblind']}")
    print(f"  detection_p     : {REGISTRATION['thresholds']['detection_claim_p']:.1e}")
    return REGISTRATION


def load_registration(path: str | None = None) -> dict:
    """Load and return an existing registration JSON."""
    p = pathlib.Path(path) if path else OUTPUT_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"Registration file not found: {p}\n"
            "Run register_fermi_lat_real_analysis.py before ingesting data."
        )
    with open(p) as f:
        return json.load(f)


if __name__ == "__main__":
    register()
