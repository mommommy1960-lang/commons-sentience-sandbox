# SESSION RECOVERY INDEX

> **Last updated:** 2026-04-19  
> **HEAD commit:** see `git log --oneline -1`  
> **Branch:** `main`  
> **Remote:** https://github.com/mommommy1960-lang/commons-sentience-sandbox  
> **Tests passing:** see latest pytest run

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
| Real-data analysis readiness | 82 |
| Fermi-LAT adapter + real pipeline | 39 |
| `test_sample_data_ingest.py` | 37 |
| **Total** | **890** |

Run all tests:
```bash
cd /workspaces/commons-sentience-sandbox
python -m pytest tests/ -q
```

---

## 5. Commit History (Most Recent)

| Hash | Message |
|---|---|
| current | Add local sample data ingest test and Fermi-LAT public-data analysis plan |
| `7288717` | Add Fermi-LAT GRB adapter, real timing pipeline, and dry-run output (832 tests passing) |
| `e35b6cf` | Add real-data analysis readiness layer and companion-book alignment docs |
| `63575ca` | FULL SESSION SNAPSHOT — Stage 5 quantum benchmarks + Stage 6 readiness layer |
| `5d222a7` | Add advanced quantum double-slit benchmark with which-path detection and 100-run validation |

---

## 6. Current Position — Experiment 1, Phase 4 Complete

As of 2026-04-19, the project has completed Phase 4 (local-sample dry run) of Experiment 1.

**Files added this session:**
- `data/sample_fermi_lat_grb_events.csv` — 50-event synthetic-but-realistic local sample (5 GRBs, randomized energy/time)
- `docs/SAMPLE_DATA_SCHEMA.md` — schema documentation for sample file
- `tests/test_sample_data_ingest.py` — 37 tests covering load, normalization, grouping, pipeline compatibility
- `reality_audit/data_analysis/run_local_fermi_lat_dry_run.py` — end-to-end local dry-run script
- `docs/FERMI_LAT_PUBLIC_DATA_PLAN.md` — full planning document for first real public-data analysis

Dry-run outputs written to:
`commons_sentience_sim/output/reality_audit/local_fermi_lat_dry_run/`

**Phase 5 (first real public-data analysis) has NOT started.**

---

## 7. Next Step — Phase 5: First Real Public-Data Analysis

The framework is ready for real Fermi-LAT FITS ingestion. The next session should:

1. **Register formal analysis plan** in `experiment_registry.py` (before touching real data)
2. **Download a single real GRB event file** from the Fermi FSSC (e.g. GRB080916C LAT data)
3. **Ingest through `fermi_lat_grb_adapter.py`** with `column_map` override for FITS-derived column names
4. **Run blinded pipeline** (`freeze_immediately=False`)
5. **Check systematics** per `docs/FERMI_LAT_PUBLIC_DATA_PLAN.md §9`
6. **Unblind** only after all checks pass

See: [docs/FERMI_LAT_PUBLIC_DATA_PLAN.md](FERMI_LAT_PUBLIC_DATA_PLAN.md)

---

## 8. Quick Recovery Checklist (New Session)

```bash
# 1. Confirm branch and commit
git log --oneline -5

# 2. Confirm tests still pass
python -m pytest tests/ -q

# 3. Read this file
cat docs/SESSION_RECOVERY_INDEX.md

# 4. Read the public-data plan
cat docs/FERMI_LAT_PUBLIC_DATA_PLAN.md

# 5. See the local dry-run results
cat commons_sentience_sim/output/reality_audit/local_fermi_lat_dry_run/summary.json
```

**Restart command for Phase 5:**
```
Continue Experiment 1 Phase 5: ingest the first real Fermi-LAT GRB event file
following the plan in docs/FERMI_LAT_PUBLIC_DATA_PLAN.md.
Register the analysis plan first, then ingest, then run blinded pipeline.
```

# 3. Read this file
cat docs/SESSION_RECOVERY_INDEX.md

# 4. Read audit summary
cat commons_sentience_sim/output/reality_audit/advanced_quantum_double_slit/audit_summary.json

# 5. Read metric trust report
cat commons_sentience_sim/output/reality_audit/metric_trust_update_report.json
```

---

## 9. Next Restart Point — Stage 5 Checkpoint + Real-Data Readiness Layer

### What was added on 2026-04-19

This session completed the **Real-Data Analysis Readiness Layer** — the final
Year 1 deliverable. All code is committed, tested, and pushed to remote.

**Roadmap position after this session:** End of Year 1. Ready to transition to Experiment 1.

---

### Files Added

#### `reality_audit/data_analysis/` (new package)

| File | Purpose |
|---|---|
| `__init__.py` | Package init; re-exports all public names |
| `experiment_registry.py` | `ExperimentSpec`, `ExperimentRegistry`, `build_default_registry()` |
| `null_models.py` | `NullModelLibrary` — 5 null model generators (isotropic, no-delay, symmetric, white-noise, bandwidth-flat) |
| `signal_injection.py` | `SignalInjector` — 4 signal injectors (preferred-axis, anisotropy, timing-delay, bandwidth-anomaly) |
| `blinding.py` | `Blinder` — blind/freeze/unblind protocol with audit trail |
| `reporting.py` | `ReportWriter` — JSON/CSV/Markdown/manifest output |
| `mock_cosmic_ray_pipeline.py` | Full mock cosmic-ray anisotropy pipeline (dry run) |
| `mock_timing_pipeline.py` | Full mock astrophysical timing-delay pipeline (dry run) |

#### `reality_audit/analysis/`

| File | Purpose |
|---|---|
| `benchmark_transfer.py` | 10 transfer principles from benchmarks → real analysis; `run_benchmark_transfer()` writes JSON report |

#### `tests/`

| File | Tests |
|---|---|
| `test_data_analysis_readiness.py` | ~72 tests across 7 classes (Registry, NullModels, SignalInjector, Blinder, ReportWriter, CosmicRay pipeline, Timing pipeline) |
| `test_benchmark_transfer.py` | 9 tests (principles library, run function, output structure) |

#### `docs/`

| File | Purpose |
|---|---|
| `COMPANION_BOOK_ALIGNMENT.md` | Maps repo modules to companion book roadmap; explicit framing of what is/isn't done |
| `FIRST_REAL_EXPERIMENT_PLAN.md` | Candidate experiments, datasets, pre-conditions, recommended first target |

---

### Outputs Generated

| Output | Path |
|---|---|
| Benchmark transfer report | `commons_sentience_sim/output/reality_audit/benchmark_transfer_report.json` |
| Mock cosmic-ray pipeline outputs | `commons_sentience_sim/output/reality_audit/mock_cosmic_ray/` |
| Mock timing-delay pipeline outputs | `commons_sentience_sim/output/reality_audit/mock_timing_delay/` |

---

### Exact Next Command After This Phase

```bash
# 1. Confirm all tests still pass
python -m pytest tests/ -q

# 2. Read transfer report
cat commons_sentience_sim/output/reality_audit/benchmark_transfer_report.json

# 3. Read experiment plan
cat docs/FERMI_LAT_PUBLIC_DATA_PLAN.md

# 4. See local dry-run results
cat commons_sentience_sim/output/reality_audit/local_fermi_lat_dry_run/summary.json
```
