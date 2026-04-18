# Quantum Double-Slit Benchmark

## Overview

This benchmark implements a **quantum-style two-path interferometer** using
complex probability amplitudes and Born-rule sampling.  It is an upgrade over
the classical wave-optics benchmark (`double_slit.py`) and is designed to
validate observer-sensitive auditing logic in the Reality Audit framework.

---

## What It Is

The quantum double-slit benchmark:

- Uses **complex Fraunhofer amplitudes** — each slit contributes a complex
  number `A(y)` whose magnitude encodes the single-slit diffraction envelope
  and whose phase encodes the path-length difference.
- Models **density-matrix decoherence** via a parameter γ ∈ [0, 1] that
  continuously interpolates between a fully coherent pure state (γ=0) and a
  maximally mixed, which-path-measured state (γ=1).
- Samples screen hit counts using the **Born rule** (seeded multinomial
  sampling), enabling empirical fringe visibility measurement.
- Is fully reproducible: every run is seeded, outputs are written to JSON/CSV,
  and all figures are regenerated from raw data.

---

## What It Is Not

> This section is required for honest framing.

- **Not a quantum computer simulation.** The model has a two-dimensional
  path Hilbert space (left slit, right slit). No exponential cost occurs.
- **Not a simulation of the physical universe.** This is a mathematical model
  of Fraunhofer diffraction + Born-rule sampling — a classical computation
  that produces quantum-consistent statistics.
- **Not using Lindblad dynamics.** Decoherence is phenomenological (a
  γ-weighted mixture of the coherent and incoherent probability densities),
  not derived from coupling to an environment.
- **Not modelling measurement back-action.** The detector is a passive classical
  screen; no state collapse is simulated step-by-step.
- **Not a validation of quantum mechanics.** The benchmark validates the audit
  framework, not the laws of physics.

---

## Physics Formulation

### Complex amplitudes (Fraunhofer far-field)

Each slit at transverse position `y_slit` contributes amplitude at screen
point `y`:

```
A(y, y_slit) = sinc( a · (y - y_slit) / (λL) ) · exp( i · 2π · y_slit · y / (λL) )
```

Where:
- `a` = slit width
- `λ` = wavelength parameter
- `L` = slit-to-screen distance
- sinc(x) = sin(πx)/(πx), sinc(0) = 1

### Coherent superposition (γ = 0)

Without which-path information:

```
Ψ(y) = A_L(y) + A_R(y)
P(y) = |Ψ(y)|²
```

This recovers the standard Young's double-slit interference pattern:

```
P(y) ≈ 4 · sinc²(a·y/(λL)) · cos²(π·d·y/(λL))
```

where `d` = slit separation.

### Density-matrix decoherence

Partial decoherence interpolates via:

```
P(y) = |A_L|² + |A_R|² + 2·(1-γ)·Re(A_L · A_R*)
```

| γ value | Physical interpretation                  | Fringe visibility |
|---------|-------------------------------------------|-------------------|
| 0.0     | Fully coherent (pure state)               | ~1.0             |
| 0–1     | Partial decoherence (mixed state)         | decreasing        |
| 1.0     | Fully decohered (which-path, incoherent) | ~0.27 (envelope) |

### Born-rule sampling

Screen hits are drawn from the normalised probability distribution using
seeded multinomial sampling (inverse-CDF method over `n_trials` particles).

---

## Benchmark Parameters

| Parameter        | Default value | Description                    |
|------------------|---------------|-------------------------------|
| `n_trials`       | 50 000        | Number of sampling events      |
| `slit_separation`| 4.0           | Distance between slit centres  |
| `slit_width`     | 1.0           | Single-slit width parameter    |
| `wavelength`     | 1.0           | Wavelength equivalent          |
| `screen_distance`| 100.0         | Distance to screen             |
| `screen_width`   | ±40.0         | Half-width of screen           |
| `n_bins`         | 200           | Screen discretisation          |
| `seed`           | 42            | Reproducibility seed           |
| `partial_gammas` | [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0] | Decoherence sweep |

---

## Concrete Results (seed=42, n=50 000)

| Condition             | Fringe visibility |
|-----------------------|------------------|
| one_slit              | 0.2716           |
| two_slit_coherent     | **0.9991**       |
| two_slit_decohered    | 0.2711           |

### Decoherence sweep

| γ    | Fringe visibility |
|------|------------------|
| 0.00 | 0.9991           |
| 0.10 | 0.9364           |
| 0.25 | 0.8378           |
| 0.50 | 0.6606           |
| 0.75 | 0.4675           |
| 0.90 | 0.3520           |
| 1.00 | 0.2711           |

Visibility is **strictly monotone decreasing** with γ, as required by the
density-matrix decoherence model.

### Audit verdict: `AUDIT_PASSED`

| Audit question                                  | Result |
|-------------------------------------------------|--------|
| Q1: Can auditor distinguish coherent vs decohered? | PASS |
| Q2: Is partial decoherence trend detected?        | PASS |
| Q3: Is benchmark seed-stable?                     | PASS |

---

## Output Files

All outputs are written to:

```
commons_sentience_sim/output/reality_audit/quantum_double_slit/
├── config.json
├── raw_results.json
├── raw_results.csv
├── summary.json
├── decoherence_sweep.json
├── audit_summary.json
├── audit_comparison_report.json
├── one_slit/summary.json
├── two_slit_coherent/summary.json
├── two_slit_decohered/summary.json
├── decoherence_sweep/gamma_*/summary.json
├── one_slit_distribution.png
├── two_slit_coherent_distribution.png
├── two_slit_decohered_distribution.png
├── decoherence_sweep.png
├── overlay_comparison.png
└── visibility_vs_gamma.png
```

---

## Figures

1. **`one_slit_distribution.png`** — Single-slit sinc² diffraction envelope.
2. **`two_slit_coherent_distribution.png`** — Full fringe pattern with Born-rule samples.
3. **`two_slit_decohered_distribution.png`** — Incoherent sum; fringes suppressed to sinc² level.
4. **`decoherence_sweep.png`** — Probability profiles for each γ value (plasma colour scale).
5. **`overlay_comparison.png`** — All three main conditions overlaid.
6. **`visibility_vs_gamma.png`** — Fringe visibility as a function of γ (monotone decreasing).

---

## Module Structure

| Module                                                      | Purpose                               |
|-------------------------------------------------------------|---------------------------------------|
| `reality_audit/benchmarks/quantum_double_slit.py`           | Core physics model + Born sampling    |
| `reality_audit/benchmarks/quantum_double_slit_runner.py`    | Full audit-integrated benchmark run   |
| `reality_audit/analysis/quantum_double_slit_metrics.py`     | Fringe visibility, coherence metrics  |
| `reality_audit/analysis/plot_quantum_double_slit.py`        | Six figure generators                 |
| `reality_audit/analysis/quantum_benchmark_audit.py`         | Three audit questions + JSON reports  |
| `tests/test_quantum_double_slit.py`                         | 35 unit tests for core model          |
| `tests/test_quantum_double_slit_runner.py`                  | 14 tests for runner + output files    |
| `tests/test_quantum_double_slit_metrics.py`                 | 26 tests for metrics                  |
| `tests/test_plot_quantum_double_slit.py`                    | 11 tests for figure creation          |
| `tests/test_quantum_benchmark_audit.py`                     | 15 tests for audit integration        |

---

## Limitations

1. **Exact Fraunhofer (far-field) only.** No near-field (Fresnel) corrections.
2. **Independent bins.** No spatial correlations across screen bins.
3. **Phenomenological decoherence.** γ is a weighting parameter, not derived
   from a specific environment model (Lindblad, Redfield, etc.).
4. **Single-mode (monochromatic).** No wavelength distribution / coherence length.
5. **No multi-particle entanglement.** Single-particle statistics only.
6. **Constant slit illumination.** No spatial mode profile for the incoming beam.

---

## Comparison with Classical Wave Model

| Feature                    | `double_slit.py` (classical) | `quantum_double_slit.py` (quantum-style) |
|----------------------------|-----------------------------|-----------------------------------------|
| Amplitude representation   | Real intensity formula      | Complex numbers                          |
| Decoherence model          | None                        | Density-matrix γ parameter              |
| Sampling method            | Multinomial                 | Born-rule multinomial                   |
| Conditions                 | One, two-slit, measured     | One, coherent, decohered, partial-γ      |
| Decoherence sweep          | No                          | Yes (configurable γ values)              |
| Audit integration          | No                          | Yes (Q1, Q2, Q3)                         |
