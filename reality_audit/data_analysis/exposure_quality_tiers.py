"""
exposure_quality_tiers.py
==========================
Defines the five-level exposure quality tier system for the Reality Audit
public anisotropy pipeline.

Tier ladder (low → high):
  none → synthetic_sample → partial_data_derived → analysis_candidate → analysis_grade

Each tier has explicit promotion criteria.  Requirements are cumulative: a
catalog must satisfy all requirements of a lower tier before it can be promoted
to a higher one.

Author: commons-sentience-sandbox
"""

from __future__ import annotations

from typing import List, Optional

# ---------------------------------------------------------------------------
# Tier constants
# ---------------------------------------------------------------------------

TIER_NONE      = "none"
TIER_SYNTHETIC = "synthetic_sample"
TIER_PARTIAL   = "partial_data_derived"
TIER_CANDIDATE = "analysis_candidate"
TIER_GRADE     = "analysis_grade"

TIER_ORDER: List[str] = [
    TIER_NONE,
    TIER_SYNTHETIC,
    TIER_PARTIAL,
    TIER_CANDIDATE,
    TIER_GRADE,
]

# ---------------------------------------------------------------------------
# Per-tier promotion criteria
# ---------------------------------------------------------------------------

PROMOTION_CRITERIA: dict = {
    TIER_SYNTHETIC: {
        "description": (
            "Exposure derived from synthetic or randomly sampled data with no real "
            "observational basis."
        ),
        "requirements": [],
        "notes": "Useful for testing pipeline plumbing only.",
    },
    TIER_PARTIAL: {
        "description": (
            "Exposure derived from real observational data but with significant gaps "
            "or limitations."
        ),
        "requirements": [
            "non_synthetic_source",
            "minimum_event_count_present",
        ],
        "notes": (
            "Does not include instrument acceptance geometry or validated livetime."
        ),
    },
    TIER_CANDIDATE: {
        "description": (
            "Exposure quality sufficient for initial analysis; real data, documented "
            "provenance, bounded caveats."
        ),
        "requirements": [
            "non_synthetic_source",
            "minimum_event_count_present",
            "sufficient_observation_window",
            "explicit_provenance_documented",
            "bounded_caveats_documented",
        ],
        "notes": (
            "Not yet analysis-grade; instrument-response model still approximate "
            "or absent."
        ),
    },
    TIER_GRADE: {
        "description": (
            "Mission-grade exposure: instrument response modeled, validated livetime, "
            "full sky coverage assessed."
        ),
        "requirements": [
            "non_synthetic_source",
            "minimum_event_count_present",
            "sufficient_observation_window",
            "explicit_provenance_documented",
            "bounded_caveats_documented",
            "instrument_response_modeled",
            "livetime_validated",
            "sky_coverage_assessed",
        ],
        "notes": (
            "Suitable for confirmatory claims if all other pipeline criteria also met."
        ),
    },
}

# Ordered list of tiers that have explicit requirements (excludes TIER_NONE)
_TIERED_LADDER: List[str] = [
    TIER_SYNTHETIC,
    TIER_PARTIAL,
    TIER_CANDIDATE,
    TIER_GRADE,
]


# ---------------------------------------------------------------------------
# Assessment
# ---------------------------------------------------------------------------

def assess_exposure_quality(
    catalog_label: str,
    exposure_metadata: Optional[dict],
) -> dict:
    """Assess the exposure quality tier for a catalog run.

    Parameters
    ----------
    catalog_label : str
        Human-readable label (e.g. "fermi", "swift", "icecube").
    exposure_metadata : dict or None
        Key/value pairs indicating which quality requirements are met.
        Boolean flags like ``non_synthetic_source``, ``minimum_event_count_present``,
        etc.  Absent keys are treated as ``False``.

    Returns
    -------
    dict with keys:
      - exposure_quality_tier                  : str
      - exposure_quality_requirements_met      : list[str]
      - exposure_quality_missing_requirements  : list[str]
      - exposure_quality_evidence_summary      : str
      - tier_rationale                         : str
    """
    if not exposure_metadata:
        return {
            "exposure_quality_tier": TIER_NONE,
            "exposure_quality_requirements_met": [],
            "exposure_quality_missing_requirements": [],
            "exposure_quality_evidence_summary": (
                f"[{catalog_label}] No exposure metadata provided; "
                "tier defaults to 'none'."
            ),
            "tier_rationale": "Empty or absent exposure_metadata.",
        }

    # Collect all unique requirements across the ladder
    all_reqs: List[str] = []
    for tier in _TIERED_LADDER:
        for req in PROMOTION_CRITERIA[tier]["requirements"]:
            if req not in all_reqs:
                all_reqs.append(req)

    met     = [r for r in all_reqs if exposure_metadata.get(r)]
    missing = [r for r in all_reqs if not exposure_metadata.get(r)]

    # Meaningful flags include quality requirements plus the is_synthetic indicator.
    # If absolutely none are True, the metadata signals "no exposure data" → TIER_NONE.
    _meaningful = all_reqs + ["is_synthetic"]
    if not any(exposure_metadata.get(f) for f in _meaningful):
        return {
            "exposure_quality_tier": TIER_NONE,
            "exposure_quality_requirements_met": [],
            "exposure_quality_missing_requirements": missing,
            "exposure_quality_evidence_summary": (
                f"[{catalog_label}] All exposure flags are absent or False; "
                "no exposure data available; tier=none."
            ),
            "tier_rationale": "No meaningful exposure flags are True.",
        }

    # Walk up the ladder: pick the highest tier where all requirements are met
    achieved = TIER_NONE
    for tier in _TIERED_LADDER:
        reqs = PROMOTION_CRITERIA[tier]["requirements"]
        if all(exposure_metadata.get(r) for r in reqs):
            achieved = tier
        else:
            # Requirements not met — stop climbing
            break

    # Build evidence summary
    if achieved == TIER_NONE:
        summary = (
            f"[{catalog_label}] No exposure quality requirements met; tier=none."
        )
    elif achieved == TIER_SYNTHETIC:
        summary = (
            f"[{catalog_label}] Synthetic-sample exposure only; "
            "no real observational basis."
        )
    elif achieved == TIER_PARTIAL:
        summary = (
            f"[{catalog_label}] Real observations present with minimum event count, "
            "but observation window, provenance, or caveats are incomplete; "
            "tier=partial_data_derived."
        )
    elif achieved == TIER_CANDIDATE:
        summary = (
            f"[{catalog_label}] Real data with documented provenance and bounded "
            "caveats; no instrument-response model; tier=analysis_candidate."
        )
    else:
        summary = (
            f"[{catalog_label}] Mission-grade exposure: IRF modeled, livetime "
            "validated, sky coverage assessed; tier=analysis_grade."
        )

    # Tier-specific rationale
    tier_reqs = PROMOTION_CRITERIA.get(achieved, {}).get("requirements", [])
    if achieved == TIER_NONE:
        rationale = "No requirements satisfied."
    else:
        rationale = (
            f"All {len(tier_reqs)} requirement(s) for '{achieved}' satisfied. "
            f"Missing requirements for next tier: "
            + (
                str(_next_tier_missing(achieved, exposure_metadata))
                if achieved != TIER_GRADE
                else "N/A (already at top tier)"
            )
        )

    return {
        "exposure_quality_tier": achieved,
        "exposure_quality_requirements_met": met,
        "exposure_quality_missing_requirements": missing,
        "exposure_quality_evidence_summary": summary,
        "tier_rationale": rationale,
    }


def _next_tier_missing(current_tier: str, metadata: dict) -> List[str]:
    """Return requirement keys missing to reach the next tier above *current_tier*."""
    idx = TIER_ORDER.index(current_tier)
    if idx >= len(TIER_ORDER) - 1:
        return []
    next_tier = TIER_ORDER[idx + 1]
    reqs = PROMOTION_CRITERIA.get(next_tier, {}).get("requirements", [])
    return [r for r in reqs if not metadata.get(r)]


# ---------------------------------------------------------------------------
# Utility comparators
# ---------------------------------------------------------------------------

def compare_tiers(tier_a: str, tier_b: str) -> int:
    """Compare two tier strings by ladder position.

    Returns
    -------
    int
        -1 if tier_a < tier_b, 0 if equal, 1 if tier_a > tier_b.

    Raises
    ------
    ValueError
        If either tier is not in TIER_ORDER.
    """
    if tier_a not in TIER_ORDER:
        raise ValueError(f"Unknown tier: {tier_a!r}")
    if tier_b not in TIER_ORDER:
        raise ValueError(f"Unknown tier: {tier_b!r}")
    a, b = TIER_ORDER.index(tier_a), TIER_ORDER.index(tier_b)
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def worst_tier(tiers: List[str]) -> str:
    """Return the lowest quality tier from a list.

    Parameters
    ----------
    tiers : list[str]
        Non-empty list of tier strings.

    Returns
    -------
    str
        The tier with the lowest index in TIER_ORDER.
    """
    if not tiers:
        return TIER_NONE
    valid = [t for t in tiers if t in TIER_ORDER]
    if not valid:
        return TIER_NONE
    return min(valid, key=lambda t: TIER_ORDER.index(t))


def best_tier(tiers: List[str]) -> str:
    """Return the highest quality tier from a list.

    Parameters
    ----------
    tiers : list[str]
        Non-empty list of tier strings.

    Returns
    -------
    str
        The tier with the highest index in TIER_ORDER.
    """
    if not tiers:
        return TIER_NONE
    valid = [t for t in tiers if t in TIER_ORDER]
    if not valid:
        return TIER_NONE
    return max(valid, key=lambda t: TIER_ORDER.index(t))
