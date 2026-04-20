# Companion Book Alignment

> **Date:** 2026-04-19  
> **Repository:** commons-sentience-sandbox  
> **Branch:** main  
> **Status:** Pre-physical-experiment phase — methodology and benchmark validation complete

---

## 1. Where the Project Currently Sits in the Companion Roadmap

The companion book describes a multi-year research programme progressing through:

```
Year 0: Conceptual framing + probe design
Year 1: Simulation validation + software infrastructure + pre-experiment methodology
Year 2: Experiment 1 — data-analysis-only program (public datasets)
Year 3: Experiment 2 — optical-cavity hardware
Year 4: Experiment 3 — interferometer hardware
Year 5+: Experiment 4 — mesoscopic coherence lab
```

**Current position: Late Year 1.**

All Year 1 methodology work described in the companion is now implemented and tested. The project is **at the transition point** from simulation/validation into real-data work. No physical experiments have been run. No real public datasets have been ingested.

---

## 2. Completed Repo Modules — Year 1 Methods Work

The following modules directly implement the Year 1 methods described in the companion book.

### 2.1 Audit Framework (Stages 1–4)

| Companion section | Repo module | Status |
|---|---|---|
| Probe design — passive, non-perturbing | `reality_audit/adapters/sim_probe.py` | ✅ Complete |
| Agent behavioral audit methodology | `reality_audit/` (full framework) | ✅ Complete |
| Governance condition ablation | `reality_audit/analysis/aggregate_experiments.py` | ✅ Complete |
| Metric trust ranking | `reality_audit/analysis/update_metric_trust.py` | ✅ Complete |
| Long-horizon stability testing | `reality_audit/benchmarks/` + Stage 6 suite | ✅ Complete |
| Probe-impact validation (Stage 6) | `reality_audit/analysis/plot_stage6.py` + reports | ✅ Complete |

### 2.2 Classical and Quantum Benchmarks (Stage 5)

| Companion section | Repo module | Status |
|---|---|---|
| Wave double-slit benchmark | `reality_audit/benchmarks/double_slit.py` | ✅ Complete |
| Quantum double-slit with decoherence | `reality_audit/benchmarks/quantum_double_slit.py` | ✅ Complete |
| Entangled which-path / eraser | `reality_audit/benchmarks/advanced_quantum_double_slit.py` | ✅ Complete |
| Complementarity V² + D² = 1 | `reality_audit/analysis/advanced_quantum_metrics.py` | ✅ Complete |
| 100-run stability validation | `reality_audit/benchmarks/advanced_quantum_runner.py` | ✅ Complete |

**Test count:** 720/720 passing.

### 2.3 Real-Data Analysis Readiness Layer (Year 1 — final phase)

| Companion section | Repo module | Status |
|---|---|---|
| Pre-analysis plan discipline | `reality_audit/data_analysis/experiment_registry.py` | ✅ Complete |
| Null model library | `reality_audit/data_analysis/null_models.py` | ✅ Complete |
| Signal injection framework | `reality_audit/data_analysis/signal_injection.py` | ✅ Complete |
| Blinding protocol | `reality_audit/data_analysis/blinding.py` | ✅ Complete |
| Structured reporting | `reality_audit/data_analysis/reporting.py` | ✅ Complete |
| Cosmic-ray anisotropy mock pipeline | `reality_audit/data_analysis/mock_cosmic_ray_pipeline.py` | ✅ Complete |
| Timing-delay mock pipeline | `reality_audit/data_analysis/mock_timing_pipeline.py` | ✅ Complete |
| Benchmark-to-method transfer audit | `reality_audit/analysis/benchmark_transfer.py` | ✅ Complete |

---

## 3. Companion Experiments — Future Work Status

### Experiment 1 — Data-Analysis-Only Program (Year 2)

**Target:** Public cosmic-ray, astrophysical timing, or CMB datasets.  
**Status:** Architecture ready. Ingestion adapters not yet built. No real data fetched.  
**What was built this session:** Mock pipelines, experiment registry, blinding layer — the full structural skeleton.  
**What remains:** Ingestion adapter for real dataset; real-data dry run; analysis plan sign-off.

See: [docs/FIRST_REAL_EXPERIMENT_PLAN.md](FIRST_REAL_EXPERIMENT_PLAN.md)

---

### Experiment 2 — Optical-Cavity Hardware (Year 3)

**Status:** Not started.  
**Prerequisite:** Experiment 1 complete and reviewed. Hardware procurement not begun.  
**Companion requirement:** Coherence measurement protocol; cavity characterisation; integration with audit framework.  
**Repo work needed:** Hardware adapter; cavity simulation benchmark; alignment with blinding protocol.

---

### Experiment 3 — Interferometer Hardware (Year 4)

**Status:** Not started.  
**Prerequisite:** Experiments 1 and 2 reviewed.  
**Companion requirement:** Phase-sensitive measurement; vibration isolation characterisation; full blind analysis plan.  
**Repo work needed:** Interferometer simulation benchmark; signal-extraction module; cross-channel blinding.

---

### Experiment 4 — Mesoscopic Coherence Lab (Year 5+)

**Status:** Conceptual — not started.  
**Prerequisite:** All prior experiments reviewed and published.  
**Companion requirement:** Full quantum-state characterisation; advanced decoherence modelling.  
**Repo work needed:** Extensions to advanced quantum benchmark; hardware-in-the-loop adapter.

---

## 4. What Is Needed Before Each Experiment

### Before Experiment 1 (real data-analysis-only)

- [ ] Choose first real dataset (Auger, Fermi-LAT, or Planck — see FIRST_REAL_EXPERIMENT_PLAN.md)
- [ ] Write and sign off formal analysis plan (freeze before data access)
- [ ] Build ingestion adapter in `reality_audit/adapters/`
- [ ] Run full dry-run on synthetic data matching real-dataset format
- [ ] Confirm all mock-pipeline tests pass
- [ ] Obtain and stage public dataset (read-only)
- [ ] Run analysis; report via ReportWriter
- [ ] Unblind; document in registry

### Before Experiment 2 (optical-cavity hardware)

- [ ] Experiment 1 reviewed internally
- [ ] Hardware specification finalized
- [ ] Cavity simulation benchmark implemented
- [ ] Probe-is-read-only contract extended to hardware interface

### Before Experiment 3 (interferometer)

- [ ] Experiments 1–2 reviewed
- [ ] Phase-measurement pipeline implemented and validated
- [ ] Noise floor characterised

### Before Experiment 4 (mesoscopic)

- [ ] All prior experiments reviewed
- [ ] Advanced decoherence model validated against hardware data
- [ ] Full quantum state tomography pipeline

---

## 5. Explicit Framing — What This Repo Work Is and Is Not

### What this repo work IS

- A rigorous software methodology built before touching real data
- Benchmark-validated analysis infrastructure
- A documented audit trail of design decisions
- A reproducible foundation for future experiments

### What this repo work IS NOT

- A physical experiment
- A real-data analysis
- Evidence for or against any physical hypothesis
- A replacement for the hardware experiments described in the companion

**The benchmark results (e.g. AUDIT_PASSED for advanced quantum double-slit) are**
**statements about the software pipeline, not about physical reality.**  
They confirm that the analysis tools behave correctly on synthetic data with known ground truth.  
They do not confirm any hypothesis about the physical world.

This distinction must be maintained in all publications and communications.

---

## 6. Quick Reference — Current Outputs

| Output | Path |
|---|---|
| Advanced quantum audit | `commons_sentience_sim/output/reality_audit/advanced_quantum_double_slit/audit_summary.json` |
| Stage 6 probe-impact report | `commons_sentience_sim/output/reality_audit/stage6_probe_impact_report.json` |
| Metric trust update | `commons_sentience_sim/output/reality_audit/metric_trust_update_report.json` |
| Benchmark transfer report | `commons_sentience_sim/output/reality_audit/benchmark_transfer_report.json` |
| Experiment registry (default) | Built in memory via `build_default_registry()` |
| Local Fermi-LAT dry run | `commons_sentience_sim/output/reality_audit/local_fermi_lat_dry_run/` |
| Prior dry-run timing outputs | `commons_sentience_sim/output/reality_audit/dry_run_timing/` |

---

## 7. Current Exact Position on the Roadmap

> **Last updated:** 2026-04-19

### Programme track: Data-analysis-only (Year 2, Experiment 1)

We are partway through **Experiment 1, transitioning from Phase 3 readiness into Phase 4 local-sample validation**. The exact position is:

```
EXPERIMENT 1 — GRB TIMING-DELAY ANALYSIS (Fermi-LAT, public data)

  Phase 1 — Hypothesis definition              ✅ complete
  Phase 2 — Null model design                  ✅ complete
  Phase 3 — Infrastructure readiness           ✅ complete
    ├─ Signal injection framework              ✅
    ├─ Blinding protocol                       ✅
    ├─ Structured reporting                    ✅
    ├─ Mock cosmic-ray pipeline                ✅
    ├─ Mock timing-delay pipeline              ✅
    ├─ Fermi-LAT adapter (fermi_lat_grb_adapter.py)  ✅
    ├─ Real timing pipeline (real_timing_pipeline.py) ✅
    └─ Benchmark-to-method transfer audit      ✅
  Phase 4 — Local-sample dry run               ✅ complete
    ├─ Sample dataset (data/sample_fermi_lat_grb_events.csv)  ✅
    ├─ Schema documentation (docs/SAMPLE_DATA_SCHEMA.md)      ✅
    ├─ Sample ingest tests (tests/test_sample_data_ingest.py)  ✅
    ├─ Local end-to-end dry run script          ✅
    └─ Dry-run outputs generated                ✅
  Phase 5 — Real public-data analysis preparation  ✅ workflow ready; data NOT yet ingested
    ├─ Formal analysis registration frozen      ✅ fermi_lat_real_analysis_registration.json
    ├─ Strict public ingest layer               ✅ fermi_lat_public_ingest.py (28 tests)
    ├─ Blinded real-data runner                 ✅ run_fermi_lat_real_blinded.py (24 tests)
    ├─ QC and unblinding rules                  ✅ FERMI_LAT_REAL_DATA_QC_AND_UNBLINDING.md
    ├─ Download real Fermi-LAT data files       ⬜ NOT YET
    ├─ Run blinded pipeline on real data        ⬜ NOT YET
    └─ Human unblinding approval                ⬜ NOT YET
```

### What has NOT happened

- ❌ No real Fermi-LAT FITS data has been fetched or read
- ❌ No discovery or exclusion claim has been made
- ❌ No hardware has been involved
- ❌ The sandbox has not been rewritten or restructured
- ❌ No benchmark success has been overclaimed as physical proof
- ❌ The local dry-run p-value (synthetic data) has not been treated as science

### What we are about to enter

The next immediate step is downloading real Fermi-LAT event data and running the
blinded analysis with `run_fermi_lat_real_blinded.py`.  The registration is
already frozen.  See [docs/FERMI_LAT_PUBLIC_DATA_PLAN.md §11](FERMI_LAT_PUBLIC_DATA_PLAN.md)
for the exact blinding sequence.

### No steps have been skipped

The progression follows the companion-book sequence exactly:
- conceptual framing → simulation validation → software infrastructure
  → pre-analysis methodology → local dry-run
  → registration + blinded ingest workflow → real data access
Each phase was committed before the next was begun.
True public-data analysis has NOT begun until a real file is successfully ingested.
The local dry-run does not count as the public-data run.
