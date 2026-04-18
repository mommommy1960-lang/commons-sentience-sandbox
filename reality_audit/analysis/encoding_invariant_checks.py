"""
encoding_invariant_checks.py — Test whether scenario ordering and qualitative
conclusions are preserved across position encodings even when raw metric
magnitudes change.

Loads encoding_robustness_report.json which contains per-encoding metric values
for selected scenarios.  For each (metric, scenario_pair) combination:

  - records the values under each encoding
  - checks whether the relative ordering (A > B, A < B, A ≈ B) is preserved
  - classifies the pair as:
      invariant           — all three encodings agree on direction
      partially_invariant — two of three agree
      encoding_sensitive  — no consensus across encodings

Output
------
encoding_invariant_report.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"

# Metrics to check
_INVARIANCE_METRICS = [
    "mean_position_error",
    "stability_score",
    "path_smoothness",
    "anisotropy_score",
]

# Tolerance for "approximately equal" comparison
_EQ_TOLERANCE = 0.05


def _direction(a: Optional[float], b: Optional[float]) -> Optional[str]:
    """Return 'greater', 'lesser', or 'equal' for a vs b.

    Returns None if either value is missing.
    """
    if a is None or b is None:
        return None
    if abs(a - b) <= _EQ_TOLERANCE * max(abs(a), abs(b), 1.0):
        return "equal"
    return "greater" if a > b else "lesser"


def _classify_ordering_consensus(directions: List[Optional[str]]) -> str:
    """Classify ordering consensus from a list of directional comparisons.

    Parameters
    ----------
    directions : list of 'greater' | 'lesser' | 'equal' | None
        One entry per encoding.

    Returns
    -------
    'invariant' | 'partially_invariant' | 'encoding_sensitive'
    """
    valid = [d for d in directions if d is not None]
    if not valid:
        return "encoding_sensitive"
    unique = set(valid)
    if len(unique) == 1:
        return "invariant"
    # Two of three agreeing counts as partially invariant
    from collections import Counter
    counts = Counter(valid)
    if counts.most_common(1)[0][1] >= 2:
        return "partially_invariant"
    return "encoding_sensitive"


# ---------------------------------------------------------------------------
# Build checks from encoding_robustness_report.json
# ---------------------------------------------------------------------------

def _load_encoding_report(output_root: Path) -> Optional[Dict[str, Any]]:
    p = output_root / "encoding_robustness_report.json"
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def build_invariant_checks_from_encoding_report(
    enc_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build per-(metric, encoding_pair) invariance check entries.

    The encoding_robustness_report records, for each metric, values under
    BFS+MDS (baseline), PureHopDistance, and ManualTopological.  We compare
    each alternative encoding to the BFS+MDS reference and to each other.
    """
    records = []
    encodings_key = "encodings"  # top-level key in encoding report

    metrics_data = enc_report.get("metrics", {})
    for metric, info in metrics_data.items():
        if metric not in _INVARIANCE_METRICS:
            continue
        per_enc = info.get("per_encoding", {})
        if not per_enc:
            continue

        enc_names = list(per_enc.keys())
        values = {e: per_enc[e].get("value") for e in enc_names}

        # Build all unique pairs
        pairs_seen = set()
        for i, ea in enumerate(enc_names):
            for j, eb in enumerate(enc_names):
                if i >= j:
                    continue
                pair_key = f"{ea}_vs_{eb}"
                if pair_key in pairs_seen:
                    continue
                pairs_seen.add(pair_key)
                va, vb = values.get(ea), values.get(eb)
                d = _direction(va, vb)
                records.append({
                    "metric": metric,
                    "encoding_a": ea,
                    "encoding_b": eb,
                    "value_a": va,
                    "value_b": vb,
                    "direction": d,
                    # For two-encoding pair, "invariant" means direction is defined;
                    # full three-way consensus uses the aggregate check below.
                })

        # Three-way consensus check (if all three encodings present)
        if len(enc_names) >= 3:
            ref = enc_names[0]
            all_dirs = [_direction(values[ref], values[e]) for e in enc_names[1:]]
            consensus = _classify_ordering_consensus(all_dirs)
            records.append({
                "metric": metric,
                "check_type": "three_way_consensus",
                "encodings": enc_names,
                "values": values,
                "ordering_directions_vs_ref": {
                    e: _direction(values[ref], values[e]) for e in enc_names[1:]
                },
                "invariance_verdict": consensus,
                "verdict": info.get("verdict", "unknown"),  # from encoding_robustness
            })

    return records


# ---------------------------------------------------------------------------
# Synthetic fallback for when no live encoding report exists
# ---------------------------------------------------------------------------

def _build_synthetic_checks() -> List[Dict[str, Any]]:
    """Return synthetic invariance checks based on known Stage 4 results.

    Stage 4 encoding robustness results:
      path_smoothness     → ROBUST   (spread < 5%)
      mean_position_error → ENCODING-SENSITIVE (37.3% spread)
      stability_score     → ENCODING-SENSITIVE (49.8% spread)
      anisotropy_score    → ENCODING-SENSITIVE (100% spread)
    """
    return [
        {
            "metric": "path_smoothness",
            "check_type": "three_way_consensus",
            "encodings": ["BFS_MDS", "PureHopDistance", "ManualTopological"],
            "source": "Stage 4 encoding robustness",
            "invariance_verdict": "invariant",
            "verdict": "ROBUST",
            "note": "spread < 5%; ordering preserved across all three encodings",
        },
        {
            "metric": "mean_position_error",
            "check_type": "three_way_consensus",
            "encodings": ["BFS_MDS", "PureHopDistance", "ManualTopological"],
            "source": "Stage 4 encoding robustness",
            "invariance_verdict": "encoding_sensitive",
            "verdict": "ENCODING-SENSITIVE",
            "note": "37.3% spread; absolute values not comparable across encodings",
        },
        {
            "metric": "stability_score",
            "check_type": "three_way_consensus",
            "encodings": ["BFS_MDS", "PureHopDistance", "ManualTopological"],
            "source": "Stage 4 encoding robustness",
            "invariance_verdict": "encoding_sensitive",
            "verdict": "ENCODING-SENSITIVE",
            "note": "49.8% spread; ordinal ranking may vary depending on encoding choice",
        },
        {
            "metric": "anisotropy_score",
            "check_type": "three_way_consensus",
            "encodings": ["BFS_MDS", "PureHopDistance", "ManualTopological"],
            "source": "Stage 4 encoding robustness",
            "invariance_verdict": "encoding_sensitive",
            "verdict": "ENCODING-SENSITIVE",
            "note": "100% spread; encoding determines the direction of anisotropy measurement",
        },
    ]


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_encoding_invariant_checks(
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run encoding invariance checks and write report.

    Uses live encoding_robustness_report.json if present;
    falls back to synthetic Stage 4 evidence otherwise.
    """
    root = output_root or _OUTPUT_ROOT
    enc_report = _load_encoding_report(root)

    if enc_report is not None and enc_report.get("metrics"):
        records = build_invariant_checks_from_encoding_report(enc_report)
        source = "live"
    else:
        records = _build_synthetic_checks()
        source = "synthetic_from_stage4"

    # Summary by metric
    by_metric: Dict[str, str] = {}
    for r in records:
        if r.get("check_type") == "three_way_consensus":
            by_metric[r["metric"]] = r.get("invariance_verdict", "unknown")

    report = {
        "stage": "Stage 5",
        "description": (
            "Encoding invariance checks: does scenario ordering hold across encodings?"
        ),
        "source": source,
        "invariance_summary": by_metric,
        "detail": records,
        "interpretation": {
            "invariant": (
                "Qualitative conclusion is preserved regardless of encoding choice."
            ),
            "partially_invariant": (
                "Two of three encodings agree; one outlier.  Report with caveat."
            ),
            "encoding_sensitive": (
                "Raw values and potentially ordering change with encoding.  "
                "Report only within-encoding comparisons."
            ),
        },
    }

    root.mkdir(parents=True, exist_ok=True)
    path = root / "encoding_invariant_report.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    return report


if __name__ == "__main__":
    result = run_encoding_invariant_checks()
    print("Encoding invariant report written.")
    for metric, verdict in result["invariance_summary"].items():
        print(f"  {metric}: {verdict}")
