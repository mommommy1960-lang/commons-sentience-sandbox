# First Real Experiment Plan — Experiment 1

> **Date:** 2026-04-19  
> **Status:** Planning phase — no real data fetched yet  
> **Prerequisite completed:** Full real-data analysis readiness layer built and tested  
> **Next action:** Choose dataset and write formal analysis plan (see Section 5)

---

## 1. Candidate First Real Questions

All three candidate questions are data-analysis-only. They require no custom hardware.  
They use publicly available, archived datasets.  
They are designed to be clearly falsifiable.

### 1.1 Preferred Sky Axis (Cosmic-Ray Anisotropy)

**Question:** Do ultra-high-energy cosmic rays arrive preferentially from a particular sky direction?

- **Null hypothesis:** Arrival directions are isotropic (uniform on sky).
- **Alternative hypothesis:** A dipole or quadrupole component is statistically detectable.
- **Primary statistic:** Spherical harmonic power at l=1 and/or l=2.
- **Detection threshold:** p < 3×10⁻⁷ (~5σ) after multiple-comparison correction.
- **Registry entry:** `cosmic_ray_anisotropy_v1`
- **Mock pipeline:** `mock_cosmic_ray_pipeline.py` — ✅ tested

### 1.2 Astrophysical Timing Delay

**Question:** Is there a systematic energy-dependent delay in photon arrival times from astrophysical transients?

- **Null hypothesis:** No energy-dependent delay (arrival time independent of photon energy).
- **Alternative hypothesis:** A linear slope Δt = κ × E × D is detectable (Lorentz-invariance violation signature).
- **Primary statistic:** OLS slope of timing residual vs. energy × distance.
- **Detection threshold:** p < 3×10⁻⁷ after look-elsewhere correction.
- **Registry entry:** `astrophysical_timing_delay_v1`
- **Mock pipeline:** `mock_timing_pipeline.py` — ✅ tested

### 1.3 CMB Multipole Alignment

**Question:** Is the CMB low-multipole power distribution statistically consistent with isotropy?

- **Null hypothesis:** CMB a_lm coefficients are isotropically distributed (no preferred axis).
- **Alternative hypothesis:** Anomalous alignment of l=2 and l=3 multipoles ("axis of evil" signal).
- **Primary statistic:** Multipole alignment statistic for l=2 and l=3.
- **Detection threshold:** p < 3×10⁻⁷.
- **Registry entry:** `cmb_axis_alignment_v1`
- **Mock pipeline:** To be built (analogous to cosmic ray pipeline).

**Recommended first target: 1.2 (Timing delay from Fermi-LAT GRBs).** See Section 6.

---

## 2. Public Datasets Needed (Later — Do Not Fetch Yet)

| Experiment | Dataset | Source | Notes |
|---|---|---|---|
| Cosmic-ray anisotropy | Pierre Auger Observatory public event list | [auger.org/data](https://www.auger.org/data) | Public data releases available |
| Timing delay | Fermi-LAT GRB photon catalog | [fermi.gsfc.nasa.gov](https://fermi.gsfc.nasa.gov/ssc/data/) | Standard public archive |
| CMB alignment | Planck legacy maps (PR3/PR4) | [pla.esac.esa.int](https://pla.esac.esa.int/) | Public FITS maps |

**Do not download until:**
1. Analysis plan is written and frozen in `ExperimentRegistry`
2. Blinder is configured with blind_keys
3. Full mock-pipeline dry run passes all tests

---

## 3. Software Modules Already Ready

| Module | Purpose | Status |
|---|---|---|
| `ExperimentRegistry` | Register and track analysis plan | ✅ Ready |
| `NullModelLibrary` | Generate null-hypothesis synthetic events | ✅ Ready |
| `SignalInjector` | Inject known signals for recovery test | ✅ Ready |
| `Blinder` | Blind/unblind result channels | ✅ Ready |
| `ReportWriter` | Structured JSON/CSV/Markdown output | ✅ Ready |
| `mock_cosmic_ray_pipeline` | Full mock anisotropy pipeline | ✅ Ready |
| `mock_timing_pipeline` | Full mock timing-delay pipeline | ✅ Ready |
| `benchmark_transfer.py` | Audit principles transferred to real analysis | ✅ Ready |
| pytest suite | 720/720 passing | ✅ Ready |

---

## 4. What Still Needs to Be Built Before Touching Real Data

### Required before Experiment 1 begins

1. **Ingestion adapter** — a module in `reality_audit/adapters/` that:
   - reads the real dataset file (FITS, CSV, or JSON) without modifying it
   - returns events in the standard format expected by the analysis pipeline
   - is itself tested on a synthetic dataset of matching format

2. **Analysis plan document** — a formal written plan specifying:
   - exact dataset to be used (version, access date, checksum)
   - exact preprocessing steps (cuts, quality filters)
   - exact primary statistic and threshold
   - list of secondary statistics
   - what counts as positive evidence vs. null result

3. **Pre-registration step** — freeze the analysis plan in `ExperimentRegistry` before accessing signal channels in data

4. **Format validation tests** — tests that the ingestion adapter produces output matching the mock pipeline's expected format

### Nice-to-have (second iteration)

- Systematic uncertainty estimation module
- Cross-validation against independent subsamples
- Sensitivity scaling study (power as a function of N)

---

## 5. Dry Run vs. Real Analysis

| | Dry run | Real analysis |
|---|---|---|
| Data source | Synthetic (NullModelLibrary) | Real public dataset |
| Signal | Injected (known ground truth) | Unknown; blinded |
| Analysis plan | Frozen before run | Frozen before data access |
| Results | Validated against known answer | Compared to null distribution |
| Blinding | Immediate unblind (for validation) | Unblind only after freeze |
| Publication eligible | No | Yes (if blinding discipline followed) |

**Rule:** A dry run succeeds if and only if:
1. The pipeline detects a 1σ injected signal (recovery test passes)
2. The pipeline correctly retains null on a pure-null dataset (p > 0.05)
3. All tests pass

Only after a successful dry run may the real-data ingestion adapter be built.

---

## 6. Recommended First Target and Rationale

**Recommended: Fermi-LAT timing delay (Experiment 1.2)**

Reasons:

1. **Cleanest null model.** The no-delay null is a single-parameter model with well-understood noise (Gaussian timing offsets). Less ambiguous than sky-direction isotropy which depends on detector exposure map.

2. **Published sensitivity.** The Fermi-LAT collaboration and independent groups have published LIV timing-delay analyses. We can cross-check our pipeline against published results on the same public data.

3. **Tractable dataset size.** Fermi-LAT GRB catalog contains ~350 well-characterized bursts. Manageable for a first run.

4. **Mock pipeline already validated.** `mock_timing_pipeline.py` is tested and matches the real-analysis structure exactly.

5. **Clear falsifiability.** A null result is as informative as a positive result. Both are publishable.

**Recommended first step:**
```python
# In the next session:
from reality_audit.data_analysis.experiment_registry import build_default_registry
registry = build_default_registry()
spec = registry.get("astrophysical_timing_delay_v1")
# Write formal analysis plan → freeze before data access
```

---

## 7. Protocol Checklist — Before Any Real Data Is Touched

- [ ] Full pytest suite passes (720+ tests, 0 failures)
- [ ] Analysis plan written and signed off
- [ ] `ExperimentRegistry` entry frozen (blinding_status confirmed)
- [ ] Ingestion adapter built and tested on synthetic data
- [ ] Mock dry run passes (recovery + null retention)
- [ ] Dataset checksum recorded
- [ ] Output directory created and empty
- [ ] `ReportWriter` configured

Only after all boxes are checked: load the dataset.
