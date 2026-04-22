"""
exposure_model_metadata.py
==========================
Compatibility-safe exposure-model metadata helpers.

Stage 16 roadmap work requires making exposure model choice explicit and
versioned, while keeping existing Stage 7-14 behavior unchanged.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def build_exposure_model_metadata(
    *,
    null_mode: str,
    exposure_map_desc: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return normalized exposure-model metadata for manifests and summaries."""
    mode = (null_mode or "isotropic").strip().lower()
    desc = exposure_map_desc if isinstance(exposure_map_desc, dict) else None

    if mode == "exposure_corrected":
        return {
            "model_id": "empirical_exposure_proxy_v1",
            "model_family": "empirical_exposure_proxy",
            "version": "1.0",
            "response_informed": False,
            "stage16_calibration_status": "empirical_proxy_baseline",
            "map_config": {
                "ra_bins": desc.get("ra_bins") if desc else None,
                "dec_bins": desc.get("dec_bins") if desc else None,
                "total_cells": desc.get("total_cells") if desc else None,
                "occupancy_fraction": desc.get("occupancy_fraction") if desc else None,
                "n_events_used": desc.get("n_events_used") if desc else None,
            },
            "limitations": (desc.get("limitations", []) if desc else []),
        }

    return {
        "model_id": "isotropic_baseline_v1",
        "model_family": "isotropic_baseline",
        "version": "1.0",
        "response_informed": False,
        "stage16_calibration_status": "baseline_unweighted",
        "map_config": None,
        "limitations": [
            "Uniform-sphere null does not model instrument sky-acceptance variation.",
        ],
    }
