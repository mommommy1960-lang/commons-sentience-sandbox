"""
icecube_diagnostics.py
======================
IceCube-specific diagnostics for Stage 12 robustness checks.

Purpose
-------
Provide sober, small-sample-aware diagnostics to evaluate whether an
anomaly-like deviation in IceCube HESE appears robust or fragile.

Implemented diagnostics
-----------------------
1. Catalog summary (coverage, missingness, timing availability)
2. Small-N sensitivity across axis-count settings
3. Leave-k-out influence analysis
4. Epoch split persistence analysis
5. Internal markdown memo writer

Author: commons-sentience-sandbox
"""

from __future__ import annotations

import datetime
import itertools
import json
import math
import os
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from reality_audit.data_analysis.public_anisotropy_study import run_public_anisotropy_study


def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_time(v: Any) -> Optional[float]:
    """Parse time as float (MJD-like) or ISO-8601 date/time to timestamp float."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None

    f = _safe_float(s)
    if f is not None:
        return f

    # Support common ISO format variants, including trailing Z
    s_norm = s.replace("Z", "+00:00")
    try:
        dt = datetime.datetime.fromisoformat(s_norm)
        return dt.timestamp()
    except ValueError:
        return None


def _percentile(sorted_vals: List[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    q = max(0.0, min(1.0, q))
    idx = int(round((len(sorted_vals) - 1) * q))
    return sorted_vals[idx]


def _tier_rank(tier: str) -> int:
    mapping = {
        "no_anomaly_detected": 0,
        "no_anomaly": 0,
        "weak_anomaly_like_deviation": 1,
        "weak_anomaly": 1,
        "moderate_anomaly_like_deviation": 2,
        "moderate_anomaly": 2,
        "strong_anomaly_like_deviation": 3,
        "strong_anomaly": 3,
    }
    return mapping.get(str(tier), -1)


def _short_metrics(study: Dict[str, Any]) -> Dict[str, Any]:
    nc = study.get("null_comparison", {})
    sig = study.get("signal_evaluation", {})
    pa = study.get("preferred_axis", {})
    ani = study.get("anisotropy", {})
    return {
        "tier": sig.get("tier"),
        "max_percentile": sig.get("max_percentile"),
        "hemi_percentile": nc.get("hemi_percentile"),
        "axis_percentile": nc.get("axis_percentile"),
        "axis_score": pa.get("score"),
        "hemisphere_imbalance": ani.get("hemisphere_imbalance"),
    }


def summarize_icecube_catalog(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize IceCube HESE catalog structure and potential small-N risk factors."""
    n_total = len(events)
    ras = [_safe_float(e.get("ra")) for e in events]
    decs = [_safe_float(e.get("dec")) for e in events]
    ens = [_safe_float(e.get("energy")) for e in events]
    tms = [_safe_time(e.get("arrival_time")) for e in events]

    valid_ra = [v for v in ras if v is not None]
    valid_dec = [v for v in decs if v is not None]
    valid_en = [v for v in ens if v is not None]
    valid_tm = [v for v in tms if v is not None]

    ra_missing = n_total - len(valid_ra)
    dec_missing = n_total - len(valid_dec)
    en_missing = n_total - len(valid_en)
    tm_missing = n_total - len(valid_tm)

    # Coarse occupancy to identify concentration structure
    ra_bins = 12
    dec_bins = 6
    occupancy = [[0 for _ in range(ra_bins)] for _ in range(dec_bins)]
    for r, d in zip(ras, decs):
        if r is None or d is None:
            continue
        ri = min(int((r % 360.0) / 360.0 * ra_bins), ra_bins - 1)
        di = min(int(((d + 90.0) / 180.0) * dec_bins), dec_bins - 1)
        occupancy[di][ri] += 1

    flat_occ = [x for row in occupancy for x in row]
    n_nonempty = sum(1 for x in flat_occ if x > 0)
    max_cell = max(flat_occ) if flat_occ else 0

    sorted_en = sorted(valid_en)
    sorted_tm = sorted(valid_tm)

    structure_flags: List[str] = []
    if n_total < 100:
        structure_flags.append("small_sample_catalog")
    if max_cell >= max(3, int(0.15 * max(1, n_total))):
        structure_flags.append("spatial_concentration")
    if en_missing > int(0.2 * max(1, n_total)):
        structure_flags.append("energy_missingness_high")
    if tm_missing > int(0.2 * max(1, n_total)):
        structure_flags.append("time_missingness_high")

    return {
        "event_count": n_total,
        "position_coverage": {
            "with_ra": len(valid_ra),
            "with_dec": len(valid_dec),
            "ra_missing": ra_missing,
            "dec_missing": dec_missing,
            "ra_min": min(valid_ra) if valid_ra else None,
            "ra_max": max(valid_ra) if valid_ra else None,
            "dec_min": min(valid_dec) if valid_dec else None,
            "dec_max": max(valid_dec) if valid_dec else None,
        },
        "time_coverage": {
            "with_time": len(valid_tm),
            "time_missing": tm_missing,
            "time_min": min(valid_tm) if valid_tm else None,
            "time_max": max(valid_tm) if valid_tm else None,
            "time_span": (max(valid_tm) - min(valid_tm)) if len(valid_tm) >= 2 else None,
        },
        "energy_coverage": {
            "with_energy": len(valid_en),
            "energy_missing": en_missing,
            "energy_min": min(valid_en) if valid_en else None,
            "energy_max": max(valid_en) if valid_en else None,
            "energy_median": _percentile(sorted_en, 0.5) if valid_en else None,
            "energy_p90": _percentile(sorted_en, 0.9) if valid_en else None,
        },
        "spatial_structure": {
            "grid_ra_bins": ra_bins,
            "grid_dec_bins": dec_bins,
            "nonempty_cells": n_nonempty,
            "total_cells": ra_bins * dec_bins,
            "max_cell_count": max_cell,
            "occupancy_fraction": (n_nonempty / float(ra_bins * dec_bins)) if ra_bins * dec_bins else 0.0,
        },
        "flags": structure_flags,
        "notes": [
            "Small-N catalogs are sensitive to influential events and scan choices.",
            "Grid occupancy is a descriptive proxy, not a formal spatial model.",
        ],
    }


def run_small_n_sensitivity_analysis(
    events: List[Dict[str, Any]],
    repeats: int = 500,
    seed: int = 42,
    axis_modes: Optional[Sequence[int]] = None,
) -> Dict[str, Any]:
    """Probe sensitivity of anisotropy metrics to sample size and axis count.

    This performs repeated sub-sampling at multiple sample sizes and axis-count
    settings, then summarizes how often anomaly-like tiers appear.
    """
    rng = random.Random(seed)
    n = len(events)
    if axis_modes is None:
        axis_modes = (48, 96, 192)
    axis_modes = [max(12, int(a)) for a in axis_modes]

    sample_sizes = sorted(set([
        max(12, n // 2),
        max(12, int(round(0.75 * n))),
        n,
    ]))

    by_axis: Dict[str, Any] = {}

    for axis_count in axis_modes:
        axis_key = str(axis_count)
        by_axis[axis_key] = {"sample_sizes": {}, "axis_count": axis_count}

        for sample_n in sample_sizes:
            max_percentiles: List[float] = []
            axis_percentiles: List[float] = []
            tiers: List[str] = []

            for rep in range(max(1, int(repeats))):
                rep_seed = seed + axis_count * 100000 + sample_n * 1000 + rep
                if sample_n >= n:
                    subset = list(events)
                else:
                    subset = rng.sample(events, sample_n)

                study = run_public_anisotropy_study(
                    subset,
                    null_repeats=30,
                    seed=rep_seed,
                    num_axes=axis_count,
                    null_mode="isotropic",
                    axis_mode="auto",
                )
                m = _short_metrics(study)
                max_p = _safe_float(m.get("max_percentile"))
                axis_p = _safe_float(m.get("axis_percentile"))
                if max_p is not None:
                    max_percentiles.append(max_p)
                if axis_p is not None:
                    axis_percentiles.append(axis_p)
                tiers.append(str(m.get("tier")))

            max_percentiles.sort()
            axis_percentiles.sort()

            tier_counts: Dict[str, int] = {}
            for t in tiers:
                tier_counts[t] = tier_counts.get(t, 0) + 1

            n_reps = max(1, len(max_percentiles))
            by_axis[axis_key]["sample_sizes"][str(sample_n)] = {
                "repeats": len(tiers),
                "max_percentile_mean": (sum(max_percentiles) / len(max_percentiles)) if max_percentiles else None,
                "max_percentile_median": _percentile(max_percentiles, 0.5) if max_percentiles else None,
                "max_percentile_p90": _percentile(max_percentiles, 0.9) if max_percentiles else None,
                "axis_percentile_mean": (sum(axis_percentiles) / len(axis_percentiles)) if axis_percentiles else None,
                "fraction_ge_0_90": sum(1 for v in max_percentiles if v >= 0.90) / float(n_reps),
                "fraction_ge_0_97": sum(1 for v in max_percentiles if v >= 0.97) / float(n_reps),
                "tier_counts": tier_counts,
            }

    # High-level trend: does anomaly-like frequency rise with denser axis scan?
    trend_rows = []
    for axis_count in axis_modes:
        axis_key = str(axis_count)
        full_row = by_axis[axis_key]["sample_sizes"].get(str(n), {})
        trend_rows.append({
            "axis_count": axis_count,
            "fraction_ge_0_90": full_row.get("fraction_ge_0_90"),
            "fraction_ge_0_97": full_row.get("fraction_ge_0_97"),
            "max_percentile_mean": full_row.get("max_percentile_mean"),
        })

    return {
        "event_count": n,
        "seed": seed,
        "repeats": repeats,
        "axis_modes": axis_modes,
        "sample_sizes": sample_sizes,
        "by_axis": by_axis,
        "trend_rows": trend_rows,
        "notes": [
            "Each repeat uses isotropic null_mode with null_repeats=30 for tractability.",
            "This analysis probes stability directionally; it is not a formal p-value calibration.",
        ],
    }


def run_leave_k_out_analysis(
    events: List[Dict[str, Any]],
    k: int = 1,
    seed: int = 42,
) -> Dict[str, Any]:
    """Evaluate whether removing a few events strongly changes the result."""
    n = len(events)
    if k < 1:
        raise ValueError("k must be >= 1")
    if k >= n:
        raise ValueError("k must be less than number of events")

    baseline = run_public_anisotropy_study(
        events,
        null_repeats=100,
        seed=seed,
        num_axes=192,
        null_mode="isotropic",
        axis_mode="auto",
    )
    baseline_m = _short_metrics(baseline)

    all_indices = list(range(n))
    combos = list(itertools.combinations(all_indices, k))

    # For k=2 on larger N this can grow; cap to a deterministic random subset.
    max_combos = 800
    if len(combos) > max_combos:
        rng = random.Random(seed)
        sampled = rng.sample(combos, max_combos)
        combos = sorted(sampled)

    rows: List[Dict[str, Any]] = []
    for idx, drop in enumerate(combos):
        keep = [events[i] for i in all_indices if i not in set(drop)]
        rep_seed = seed + 500000 + idx
        study = run_public_anisotropy_study(
            keep,
            null_repeats=60,
            seed=rep_seed,
            num_axes=192,
            null_mode="isotropic",
            axis_mode="auto",
        )
        m = _short_metrics(study)
        rows.append({
            "dropped_indices": list(drop),
            "dropped_event_ids": [events[i].get("event_id") for i in drop],
            "tier": m.get("tier"),
            "max_percentile": m.get("max_percentile"),
            "axis_percentile": m.get("axis_percentile"),
            "hemi_percentile": m.get("hemi_percentile"),
        })

    max_vals = sorted([_safe_float(r.get("max_percentile")) or 0.0 for r in rows])
    baseline_rank = _tier_rank(str(baseline_m.get("tier")))
    fragility_count = 0
    for r in rows:
        rr = _tier_rank(str(r.get("tier")))
        if rr < baseline_rank:
            fragility_count += 1

    return {
        "k": k,
        "event_count": n,
        "baseline": baseline_m,
        "n_combinations_evaluated": len(rows),
        "fraction_tier_drops": (fragility_count / float(len(rows))) if rows else 0.0,
        "max_percentile_median": _percentile(max_vals, 0.5) if max_vals else None,
        "max_percentile_p10": _percentile(max_vals, 0.1) if max_vals else None,
        "max_percentile_p90": _percentile(max_vals, 0.9) if max_vals else None,
        "worst_case": min(rows, key=lambda r: (_safe_float(r.get("max_percentile")) or 0.0)) if rows else None,
        "best_case": max(rows, key=lambda r: (_safe_float(r.get("max_percentile")) or 0.0)) if rows else None,
        "rows": rows,
    }


def run_epoch_split_analysis(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Split catalog into early/late halves by time and compare persistence."""
    pairs: List[Tuple[float, Dict[str, Any]]] = []
    for e in events:
        t = _safe_time(e.get("arrival_time"))
        if t is not None:
            pairs.append((t, e))

    if len(pairs) < 8:
        return {
            "usable": False,
            "reason": "Insufficient valid times for stable epoch split",
            "n_with_time": len(pairs),
        }

    pairs.sort(key=lambda x: x[0])
    mid = len(pairs) // 2
    early = [p[1] for p in pairs[:mid]]
    late = [p[1] for p in pairs[mid:]]

    early_study = run_public_anisotropy_study(
        early,
        null_repeats=100,
        seed=101,
        num_axes=192,
        null_mode="isotropic",
        axis_mode="auto",
    )
    late_study = run_public_anisotropy_study(
        late,
        null_repeats=100,
        seed=202,
        num_axes=192,
        null_mode="isotropic",
        axis_mode="auto",
    )

    e = _short_metrics(early_study)
    l = _short_metrics(late_study)

    delta = None
    emax = _safe_float(e.get("max_percentile"))
    lmax = _safe_float(l.get("max_percentile"))
    if emax is not None and lmax is not None:
        delta = abs(emax - lmax)

    return {
        "usable": True,
        "n_with_time": len(pairs),
        "early": {
            "n": len(early),
            **e,
        },
        "late": {
            "n": len(late),
            **l,
        },
        "max_percentile_delta": delta,
        "tier_agreement": str(e.get("tier")) == str(l.get("tier")),
    }


def _assess_robustness(
    small_n: Dict[str, Any],
    leave_k_out: Dict[str, Any],
    epoch_split: Dict[str, Any],
) -> Dict[str, Any]:
    """Return a simple robustness judgment for cross-catalog interpretation."""
    fragile_signals: List[str] = []
    robust_signals: List[str] = []

    # Dense-axis inflation check: compare full-sample fraction_ge_0_90 at low/high axis counts.
    trend = {int(r["axis_count"]): r for r in small_n.get("trend_rows", []) if r.get("fraction_ge_0_90") is not None}
    if trend:
        low_key = min(trend.keys())
        high_key = max(trend.keys())
        low = trend[low_key].get("fraction_ge_0_90")
        high = trend[high_key].get("fraction_ge_0_90")
        if low is not None and high is not None:
            if (high - low) > 0.15:
                fragile_signals.append("axis_density_sensitive")
            else:
                robust_signals.append("axis_density_stable")

    drop_frac = _safe_float(leave_k_out.get("fraction_tier_drops"))
    if drop_frac is not None:
        if drop_frac > 0.30:
            fragile_signals.append("influential_events")
        else:
            robust_signals.append("leave_k_out_stable")

    if epoch_split.get("usable"):
        if not bool(epoch_split.get("tier_agreement")):
            fragile_signals.append("epoch_inconsistent")
        else:
            robust_signals.append("epoch_consistent")

    if len(fragile_signals) >= 2:
        label = "fragile"
    elif len(fragile_signals) == 1:
        label = "mixed"
    else:
        label = "relatively_stable"

    return {
        "label": label,
        "fragile_signals": fragile_signals,
        "robust_signals": robust_signals,
        "summary": {
            "fragile_count": len(fragile_signals),
            "robust_count": len(robust_signals),
        },
    }


def write_icecube_diagnostics_memo(results: Dict[str, Any], output_dir: str) -> str:
    """Write concise Stage 12 internal diagnostics memo and return markdown path."""
    os.makedirs(output_dir, exist_ok=True)
    memo_path = os.path.join(output_dir, "stage12_icecube_diagnostics_memo.md")

    summary = results.get("catalog_summary", {})
    small_n = results.get("small_n_sensitivity", {})
    lko = results.get("leave_k_out", {})
    epoch = results.get("epoch_split", {})
    robust = results.get("robustness_assessment", {})

    lines: List[str] = []
    lines.append("# Stage 12 IceCube Diagnostics Memo")
    lines.append("")
    lines.append("Internal robustness diagnostic artifact. Not a publication.")
    lines.append("")

    lines.append("## What was checked")
    lines.append("")
    lines.append("- Catalog completeness and structural flags")
    lines.append("- Small-N sensitivity across axis-count settings")
    lines.append("- Leave-k-out influential event analysis")
    lines.append("- Early/late epoch split persistence")
    lines.append("")

    lines.append("## Catalog summary")
    lines.append("")
    lines.append(f"- Event count: {summary.get('event_count')}")
    lines.append(f"- Flags: {', '.join(summary.get('flags', [])) if summary.get('flags') else 'none'}")
    pos = summary.get("position_coverage", {})
    lines.append(f"- Position coverage: RA missing={pos.get('ra_missing')}, Dec missing={pos.get('dec_missing')}")
    eng = summary.get("energy_coverage", {})
    lines.append(f"- Energy missing: {eng.get('energy_missing')}")
    tcv = summary.get("time_coverage", {})
    lines.append(f"- Time missing: {tcv.get('time_missing')}")
    lines.append("")

    lines.append("## Small-N sensitivity")
    lines.append("")
    lines.append("- Trend rows (full-sample anomaly frequency proxy):")
    for row in small_n.get("trend_rows", []):
        lines.append(
            f"  - axes={row.get('axis_count')}: fraction_ge_0.90={row.get('fraction_ge_0_90')}, "
            f"fraction_ge_0.97={row.get('fraction_ge_0_97')}"
        )
    lines.append("")

    lines.append("## Leave-k-out")
    lines.append("")
    lines.append(f"- k={lko.get('k')} combinations evaluated: {lko.get('n_combinations_evaluated')}")
    lines.append(f"- Fraction of tier drops vs baseline: {lko.get('fraction_tier_drops')}")
    lines.append(f"- Max percentile median: {lko.get('max_percentile_median')}")
    lines.append("")

    lines.append("## Epoch split")
    lines.append("")
    if epoch.get("usable"):
        lines.append(f"- Tier agreement early vs late: {epoch.get('tier_agreement')}")
        lines.append(f"- Max percentile delta: {epoch.get('max_percentile_delta')}")
    else:
        lines.append(f"- Not usable: {epoch.get('reason')}")
    lines.append("")

    lines.append("## Robustness judgment")
    lines.append("")
    lines.append(f"- Label: {robust.get('label')}")
    lines.append(f"- Fragile signals: {', '.join(robust.get('fragile_signals', [])) or 'none'}")
    lines.append(f"- Robust signals: {', '.join(robust.get('robust_signals', [])) or 'none'}")
    lines.append("")
    lines.append("Interpretation: Treat anomaly-like deviations as exploratory unless they remain stable under these diagnostics and preregistered confirmatory reruns.")
    lines.append("")

    with open(memo_path, "w") as f:
        f.write("\n".join(lines))

    return memo_path


def run_full_icecube_diagnostics(
    events: List[Dict[str, Any]],
    repeats: int = 500,
    seed: int = 42,
    axis_modes: Optional[Sequence[int]] = None,
    leave_k_out: int = 1,
) -> Dict[str, Any]:
    """Convenience wrapper to run complete diagnostics suite."""
    summary = summarize_icecube_catalog(events)
    small_n = run_small_n_sensitivity_analysis(
        events,
        repeats=repeats,
        seed=seed,
        axis_modes=axis_modes,
    )
    lko = run_leave_k_out_analysis(events, k=leave_k_out, seed=seed)
    epoch = run_epoch_split_analysis(events)
    robust = _assess_robustness(small_n, lko, epoch)

    return {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "catalog_summary": summary,
        "small_n_sensitivity": small_n,
        "leave_k_out": lko,
        "epoch_split": epoch,
        "robustness_assessment": robust,
    }


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
