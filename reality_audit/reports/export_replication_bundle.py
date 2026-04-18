"""
export_replication_bundle.py — Bundle Stage 5 configs, aggregated summaries,
key reports, generated figures, and a README for re-running Stage 5.

Architecture note
-----------------
This bundle does NOT copy the full raw simulation output directories (which
may be very large).  It collects:
  - All JSON reports
  - All CSV summaries
  - All generated figures
  - A README with re-run instructions
  - A manifest.json describing every included file

This is the minimal replication bundle: someone with the `commons-sentience-sandbox`
repository and the JSON reports can reproduce all Stage 5 analysis and figures
without re-running the full sandbox campaigns.

To reproduce the full sandbox output (raw_log.json, etc.) they must re-run
the Stage 5 calibrated campaigns with the documented configs.

Output
------
commons_sentience_sim/output/reality_audit/replication_bundle/
  README.md
  manifest.json
  reports/          — all JSON + CSV reports
  figures/          — all Stage 5 figures
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OUTPUT_ROOT = _REPO_ROOT / "commons_sentience_sim" / "output" / "reality_audit"
_BUNDLE_ROOT = _OUTPUT_ROOT / "replication_bundle"

# ---------------------------------------------------------------------------
# README template
# ---------------------------------------------------------------------------

_README_CONTENT = """\
# Reality Audit — Stage 5 Replication Bundle

**Date built:** {timestamp}
**Repository:** commons-sentience-sandbox
**Stage:** 5 — Calibrated Experimental Campaigns + Ablations + Publication-Grade Synthesis

---

## What is in this bundle?

```
replication_bundle/
  README.md           — this file
  manifest.json       — all included files with descriptions
  reports/            — all Stage 5 JSON and CSV reports
  figures/            — all Stage 5 figures and tables
```

## Reproducing Stage 5 analysis (without re-running campaigns)

All analysis scripts operate on the JSON reports included in `reports/`.
Copy `reports/` to `commons_sentience_sim/output/reality_audit/` and run:

```bash
# 1. Metric calibration
python -m reality_audit.analysis.metric_calibration

# 2. Encoding invariance checks
python -m reality_audit.analysis.encoding_invariant_checks

# 3. Governance interpretation
python -m reality_audit.analysis.governance_interpretation

# 4. Findings extraction
python -m reality_audit.analysis.findings_extractor

# 5. Stage 5 summary report
python reality_audit/reports/generate_stage5_summary.py

# 6. Stage 5 figures
python -m reality_audit.analysis.plot_stage5
```

## Reproducing Stage 5 sandbox campaigns (requires LLM API)

```bash
# Calibrated campaigns (A–E, 25/50/100 turns, 3 seeds each)
python -c "
from reality_audit.experiments.calibrated_campaigns import run_calibrated_campaigns
run_calibrated_campaigns()
"

# Ablation studies (5 ablation types, 3 seeds each at 25 turns)
python -c "
from reality_audit.experiments.ablation_studies import run_all_ablations
run_all_ablations()
"
```

## Test suite

```bash
python -m pytest tests/ -q --tb=short
```

Expected: {n_tests}+ tests passing.

## Key findings reference

See `figures/findings_summary_table.md` and `docs/STAGE5_FINDINGS.md`.

## Metric trust quick reference

See `figures/scenario_summary_table.md` and `docs/METRIC_TRUST_RANKING.md`.

## Limitations

See `docs/EXPERIMENTAL_LIMITATIONS.md`.
"""

# ---------------------------------------------------------------------------
# Manifest builder
# ---------------------------------------------------------------------------

def _describe(path: Path) -> str:
    """One-line description for a file based on its name."""
    name = path.name
    descriptions = {
        "metric_calibration_report.json": "Per-metric calibration status (A/B/C/D) based on Stages 1–4",
        "metric_calibration_summary.csv": "Flat table: metric, status, encoding_sensitive, gov_sensitive",
        "ablation_report.json":           "One-factor ablation studies — Cohen's d per (ablation, metric)",
        "ablation_summary.csv":           "Flat table of ablation results",
        "campaign_comparison_report.json":"Effect-size comparisons between calibrated campaign pairs",
        "calibrated_campaigns_summary.csv":"Mean/std per (campaign, turns, metric)",
        "findings_ranked.json":           "Ranked findings from Stages 2–5",
        "encoding_invariant_report.json": "Encoding ordering invariance checks per metric",
        "governance_interpretation_report.json": "Governance-induced shift classification per metric",
        "sandbox_campaigns_report.json":  "Stage 4 sandbox campaign raw results",
        "sandbox_variability_report.json":"Stage 4 metric variability classification",
        "encoding_robustness_report.json":"Stage 4 three-encoding comparison",
        "sandbox_false_positive_report.json": "Stage 4 false-positive detection results",
        "read_only_expansion_report.json":"Stage 4 expanded probe read-only validation",
        "stage5_summary.md":              "Stage 5 compiled Markdown report",
        "metric_trust_ranking.png":       "Figure 1 — metric tier bar chart",
        "governance_sensitivity.png":     "Figure 2 — governance on/off comparison",
        "encoding_robustness.png":        "Figure 3 — three-encoding grouped bars",
        "calibrated_campaign_comparison.png": "Figure 4 — Cohen's d heatmap across campaigns",
        "ablation_effects.png":           "Figure 5 — |Cohen's d| ablation heatmap",
        "scenario_summary_table.md":      "Table 6 — calibrated campaign scenario means",
        "findings_summary_table.md":      "Table 7 — ranked findings condensed table",
    }
    return descriptions.get(name, "Stage 5 output file")


# ---------------------------------------------------------------------------
# Bundle builder
# ---------------------------------------------------------------------------

def _collect_files() -> List[Path]:
    """Collect all files to include in the bundle."""
    files: List[Path] = []

    # Top-level JSON/CSV reports
    for pat in ("*.json", "*.csv"):
        files.extend(_OUTPUT_ROOT.glob(pat))

    # Stage 5 figures
    fig_dir = _OUTPUT_ROOT / "figures_stage5"
    if fig_dir.exists():
        files.extend(fig_dir.glob("*.png"))
        files.extend(fig_dir.glob("*.csv"))
        files.extend(fig_dir.glob("*.md"))

    # calibrated_campaigns comparison report
    cc_dir = _OUTPUT_ROOT / "calibrated_campaigns"
    if cc_dir.exists():
        files.extend(cc_dir.glob("*.json"))
        files.extend(cc_dir.glob("*.csv"))

    # Stage 5 narrative report
    stage5_md = _REPO_ROOT / "reality_audit" / "reports" / "stage5_summary.md"
    if stage5_md.exists():
        files.append(stage5_md)

    # Deduplicate
    return list({p.resolve(): p for p in files}.values())


def build_replication_bundle(
    bundle_root: Path = _BUNDLE_ROOT,
    n_tests: int = 0,
) -> Path:
    """Build the replication bundle directory.

    Parameters
    ----------
    bundle_root : Path
        Destination directory (will be created).
    n_tests : int
        Total test count to embed in README.

    Returns
    -------
    Path to the bundle root directory.
    """
    bundle_root.mkdir(parents=True, exist_ok=True)
    reports_dir = bundle_root / "reports"
    figures_dir = bundle_root / "figures"
    reports_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files = _collect_files()
    manifest_entries: List[Dict[str, Any]] = []

    for src in files:
        # Route by extension / parent
        if src.suffix == ".png" or src.parent.name == "figures_stage5":
            if src.suffix in (".png", ".csv", ".md"):
                dest = figures_dir / src.name
            else:
                continue
        elif src.name.endswith(".md") and src.parent.name == "reports":
            dest = bundle_root / src.name
        else:
            dest = reports_dir / src.name

        try:
            shutil.copy2(src, dest)
        except (OSError, shutil.SameFileError):
            pass

        manifest_entries.append({
            "source": str(src.relative_to(_REPO_ROOT)),
            "bundle_path": str(dest.relative_to(bundle_root)),
            "description": _describe(src),
        })

    # Write README
    readme_path = bundle_root / "README.md"
    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.write(_README_CONTENT.format(timestamp=ts, n_tests=n_tests or "?"))

    # Write manifest
    manifest_path = bundle_root / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "stage": "Stage 5",
                "built": ts,
                "files": manifest_entries,
                "total_files": len(manifest_entries),
            },
            fh,
            indent=2,
        )

    print(f"Replication bundle written to: {bundle_root}")
    print(f"Total files included: {len(manifest_entries)}")
    return bundle_root


if __name__ == "__main__":
    build_replication_bundle()
