# Reality Audit — Stage 5 Replication Bundle

**Date built:** 2026-04-18T00:56:02Z
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

Expected: 267+ tests passing.

## Key findings reference

See `figures/findings_summary_table.md` and `docs/STAGE5_FINDINGS.md`.

## Metric trust quick reference

See `figures/scenario_summary_table.md` and `docs/METRIC_TRUST_RANKING.md`.

## Limitations

See `docs/EXPERIMENTAL_LIMITATIONS.md`.
