# SESSION RECOVERY INDEX

> **Last updated:** 2026-04-18  
> **HEAD commit:** `63575ca` — FULL SESSION SNAPSHOT  
> **Branch:** `main`  
> **Remote:** https://github.com/mommommy1960-lang/commons-sentience-sandbox  
> **Tests passing:** 720 / 720

---

## 1. What Was Built

### Audit Framework (Stages 1–4)
- `reality_audit/` — core framework for running, scoring, and auditing agent experiments
- `reality_audit/adapters/sim_probe.py` — read-only probe verification (sandbox-native)
- `reality_audit/adapters/room_distance.py` — room-distance adapter
- Full pipeline: campaigns → raw logs → findings → governance

### Stage 5 — Double-Slit Benchmarks
| Benchmark | Key file | Runner |
|---|---|---|
| Wave double-slit | `reality_audit/benchmarks/double_slit.py` | `double_slit_runner.py` |
| Quantum double-slit (decoherence) | `reality_audit/benchmarks/quantum_double_slit.py` | `quantum_double_slit_runner.py` |
| Advanced quantum (entanglement + eraser) | `reality_audit/benchmarks/advanced_quantum_double_slit.py` | `advanced_quantum_runner.py` |

**Physics model (advanced quantum):**
- State: `|Ψ⟩ = (1/√2)(|L⟩|d_L⟩ + |R⟩|d_R⟩)`
- Marginal: `P(y) = ½(|A_L|²+|A_R|²) + s·Re(A_L·A_R*)` where `s = ⟨d_L|d_R⟩`
- Complementarity: `V_th = s`, `D = √(1−s²)`, **`V²+D²=1` (exact)**
- Conditions: ONE_SLIT, TWO_SLIT_COHERENT, TWO_SLIT_PARTIAL, TWO_SLIT_WHICH_PATH, ERASER_PLUS, ERASER_MINUS

**100-run stability (n=20 000, n_bins=200, seed=42):**
- coherent: mean V_th = 0.9991, CV = 0.000000
- which_path: mean V_th = 0.2711, CV = 0.000000
- AUDIT_PASSED (Q1–Q4 all PASS)

### Stage 6 — Long-Horizon + Probe-Impact Testing
- Long-horizon runs in `commons_sentience_sim/output/reality_audit/stage6_long_horizon/`
- Probe-impact test: `commons_sentience_sim/output/reality_audit/stage6_probe_impact_report.json`
- Figures: `commons_sentience_sim/output/reality_audit/figures_stage6/`

### Metric Trust Updates
- Report: `commons_sentience_sim/output/reality_audit/metric_trust_update_report.json`
- Calibration: `commons_sentience_sim/output/reality_audit/metric_calibration_report.json`

### Analysis Modules (`reality_audit/analysis/`)
| File | Purpose |
|---|---|
| `advanced_quantum_audit.py` | Q1–Q4 audit for advanced quantum |
| `advanced_quantum_metrics.py` | fringe_visibility, V/D complementarity, eraser recovery |
| `plot_advanced_quantum.py` | 8-figure visualization suite |
| `quantum_benchmark_audit.py` | Quantum double-slit audit |
| `update_metric_trust.py` | Metric trust update pipeline |
| `aggregate_experiments.py` | Cross-experiment aggregation |

---

## 2. Where Outputs Live

All outputs are under:
```
commons_sentience_sim/output/reality_audit/
```

Key subdirectories:

| Directory | Contents |
|---|---|
| `advanced_quantum_double_slit/` | Full advanced quantum run: JSON, CSV, 8 figures |
| `advanced_quantum_double_slit/figures/` | 8 PNGs (one_slit, coherent, which_path, eraser±, overlap_sweep, V-vs-D, 100-run stability) |
| `quantum_double_slit/` | Quantum double-slit decoherence run |
| `double_slit/` | Wave double-slit run |
| `stage6_probe_impact/` | Probe-impact test raw data |
| `stage6_long_horizon/` | Long-horizon stability data |
| `figures_stage5/` | Stage 5 aggregate figures |
| `figures_stage6/` | Stage 6 figures |
| `replication_bundle/` | Full replication package |

---

## 3. Key Reports

| Report | Path |
|---|---|
| Probe-impact report | `commons_sentience_sim/output/reality_audit/stage6_probe_impact_report.json` |
| Quantum double-slit audit | `commons_sentience_sim/output/reality_audit/quantum_double_slit/` |
| Advanced quantum audit | `commons_sentience_sim/output/reality_audit/advanced_quantum_double_slit/audit_summary.json` |
| Advanced quantum comparison | `commons_sentience_sim/output/reality_audit/advanced_quantum_double_slit/audit_comparison_report.json` |
| Advanced quantum aggregate | `commons_sentience_sim/output/reality_audit/advanced_quantum_double_slit/aggregate_summary.json` |
| Metric trust update | `commons_sentience_sim/output/reality_audit/metric_trust_update_report.json` |
| Metric calibration | `commons_sentience_sim/output/reality_audit/metric_calibration_report.json` |
| Governance interpretation | `commons_sentience_sim/output/reality_audit/governance_interpretation_report.json` |
| Findings ranked | `commons_sentience_sim/output/reality_audit/findings_ranked.json` |

---

## 4. Test Suite

| Module | Tests |
|---|---|
| Prior (Stages 1–6) | 629 |
| `test_advanced_quantum_double_slit.py` | 35 |
| `test_advanced_quantum_metrics.py` | 28 |
| `test_advanced_quantum_runner.py` | 14 |
| `test_advanced_quantum_audit.py` | 14 |
| `test_plot_advanced_quantum.py` | 12 |
| **Total** | **720** |

Run all tests:
```bash
cd /workspaces/commons-sentience-sandbox
python -m pytest tests/ -q
```

---

## 5. Commit History (Most Recent)

| Hash | Message |
|---|---|
| `63575ca` | FULL SESSION SNAPSHOT — Stage 5 quantum benchmarks + Stage 6 readiness layer |
| `5d222a7` | Add advanced quantum double-slit benchmark with which-path detection and 100-run validation |
| `376e736` | Add quantum double-slit benchmark with decoherence and audit integration |
| `17cb26f` | Add double-slit benchmark for observer-sensitive audit validation |
| `76bd8a7` | Stage 6 probe impact test |

---

## 6. Next Step — Real-Data Analysis Pipelines (Experiment 1)

The framework is ready for real-data ingestion. The next session should:

1. **Define Experiment 1:** choose a public dataset (e.g. EEG, fMRI, behavioural time-series)
2. **Build ingestion adapter** in `reality_audit/adapters/` that reads the dataset and emits the standard campaign format
3. **Wire to audit pipeline:** reuse `reality_audit/analysis/aggregate_experiments.py` and audit modules
4. **Validate with mock data first** (utilities in `reality_audit/benchmarks/` for reference)
5. **Register findings** in `commons_sentience_sim/output/reality_audit/findings_ranked.json`

The mock pipeline scaffolding lives in `reality_audit/` — extend, don't replace.

---

## 7. Quick Recovery Checklist (New Session)

```bash
# 1. Confirm branch and commit
git log --oneline -5

# 2. Confirm tests still pass
python -m pytest tests/ -q

# 3. Read this file
cat docs/SESSION_RECOVERY_INDEX.md

# 4. Read audit summary
cat commons_sentience_sim/output/reality_audit/advanced_quantum_double_slit/audit_summary.json

# 5. Read metric trust report
cat commons_sentience_sim/output/reality_audit/metric_trust_update_report.json
```
