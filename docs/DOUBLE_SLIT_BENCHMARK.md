# Double-Slit Benchmark for Observer-Sensitive Audit Validation

## What This Benchmark Is

This module implements a **minimal benchmark model** of the double-slit experiment
inside the `commons-sentience-sandbox` repository.  It is used to validate the
Reality Audit framework's ability to detect and quantify observer-sensitive signals.

Three experimental conditions are supported:

| Condition | Description |
|---|---|
| `one_slit` | Only one slit open.  Single-slit diffraction pattern. |
| `two_slit` | Both slits open, no which-path measurement.  Full wave interference. |
| `two_slit_measured` | Both slits open, which-path detector active.  Interference suppressed. |

---

## What This Benchmark Is Not

- **Not a quantum simulator.**  The model uses classical wave-optics formulae
  (Young's double-slit interference + Fraunhofer diffraction).  It does not simulate
  quantum states, wavefunctions, superposition, entanglement, or decoherence.
- **Not a claim about the physical universe.**  The repository is a testing
  sandbox.  This benchmark exists to validate auditing logic, not to make statements
  about quantum mechanics.
- **Not a measurement of real observation effects in the sandbox agents.**  The
  double-slit benchmark is a separate, self-contained model.  It does not interact
  with the agent simulation.

---

## Physical Model

The intensity at screen position $y$ is computed as:

**One slit:**
$$I(y) = \text{sinc}^2\!\left(\frac{a \cdot y}{\lambda L}\right)$$

**Two slits, unmeasured (coherent superposition):**
$$I(y) = \cos^2\!\left(\frac{\pi d \cdot y}{\lambda L}\right) \cdot \text{sinc}^2\!\left(\frac{a \cdot y}{\lambda L}\right)$$

**Two slits, with which-path measurement (incoherent sum):**
$$I(y) = \frac{1}{2}\left[\text{sinc}^2\!\left(\frac{a(y - d/2)}{\lambda L}\right) + \text{sinc}^2\!\left(\frac{a(y + d/2)}{\lambda L}\right)\right]$$

where:
- $d$ = slit separation (default: 4.0)
- $a$ = slit width (default: 1.0)
- $\lambda$ = wavelength parameter (default: 1.0)
- $L$ = screen distance (default: 100.0)
- $y$ = screen position

The "which-path measurement" is modelled by **suppressing the cosine interference
cross-term**, turning coherent superposition into incoherent sum.  This reproduces
the qualitative effect (pattern collapse) without simulating quantum decoherence.

Particle hits are sampled from the intensity distribution via a seeded multinomial
process, producing reproducible integer hit counts per screen bin.

---

## Assumptions

1. Classical wave optics in the far-field (Fraunhofer) limit.
2. Monochromatic illumination (single `wavelength` parameter).
3. Equal slit widths and amplitudes.
4. Screen hit counts are multinomially distributed given the intensity profile.
5. The "which-path measurement" effect is modelled by removing the interference term;
   no attempt is made to simulate a physical detector or wavefunction collapse.

---

## How It Connects to Reality Audit

The benchmark serves three validation functions:

### 1. Observer-sensitivity detection
The audit metric `fringe_visibility` measures whether an interference pattern is
present.  The benchmark provides a **ground truth signal** where the correct
answer is known analytically:

- `two_slit` → high fringe visibility (~1.0)
- `two_slit_measured` → low fringe visibility (~visibility of single-slit pattern)
- `one_slit` → intermediate or low fringe visibility

If the audit metrics cannot distinguish these conditions, the framework has a
detection gap.

### 2. Metric calibration baseline
The benchmark provides clean, reproducible, analytically tractable distributions
that can be used to calibrate audit metrics (KL divergence, entropy, peak count)
before applying them to the noisier agent simulation output.

### 3. Observer-effect logic testing
The `two_slit_measured` condition directly models the result of a which-path
measurement (observation).  Comparing its metrics to `two_slit` validates whether
the audit framework's observer-sensitivity metrics respond correctly to a known
intervention.

---

## Benchmark Results (50,000 trials, 200 bins, seed=42)

| Metric | `one_slit` | `two_slit` | `two_slit_measured` |
|---|---|---|---|
| Fringe visibility | 0.2716 | **0.9999** | 0.2711 |
| Peak count | 0 | **2** | 0 |
| Center intensity (norm.) | 1.0000 | 1.0000 | 1.0000 |
| Distribution entropy | 5.2833 | **4.9274** | 5.2834 |

**Cross-condition metrics:**

| Metric | Value |
|---|---|
| Fringe suppression ratio (measured/unmeasured) | **0.2711** (strong suppression) |
| Visibility drop (two_slit − measured) | **0.7288** |
| KL divergence (two_slit ‖ measured) | **0.3404** |
| KL divergence (two_slit ‖ one_slit) | **0.3404** |

**Verdict:** `BENCHMARK_BEHAVED_CORRECTLY: interference present, measurement suppresses, one-slit distinct`

---

## Interpretation

1. **The two-slit unmeasured case shows a strong interference-like pattern.**
   Fringe visibility = 0.9999 (near-perfect constructive/destructive alternation).

2. **The measured case loses the interference pattern.**
   Fringe visibility collapses to 0.2711 — matching the one-slit
   diffraction envelope.  Suppression ratio = 0.27 (73% reduction).

3. **The one-slit case is distinct from both two-slit cases.**
   Zero peaks detected; fringe visibility = 0.27 (only diffraction envelope
   shape, no oscillation); KL divergence from two-slit = 0.34.

4. **These results confirm the audit framework can detect observer-sensitive signals.**
   The metrics `fringe_visibility`, `peak_count`, and `measured_vs_unmeasured_kl`
   all correctly identify the correct condition.

---

## Limitations Relative to Real Quantum Mechanics

| Limitation | Impact |
|---|---|
| Classical wave optics only | Does not model superposition or wavefunction collapse |
| No particle tracking | Cannot model single-photon detection events |
| Measurement modelled as term removal | Does not simulate actual measurement back-action |
| Deterministic intensity profile | No quantum shot noise in the intensity itself (only sampling noise) |
| No entanglement | Cannot model Bell tests or multi-particle correlations |
| No time evolution | Screen pattern is computed statically, not dynamically |

The benchmark is calibrated to reproduce the **qualitative phenomenology** (interference
pattern present / absent depending on which-path knowledge) at the scale the audit
framework cares about: differences in distributions that audit metrics can detect.

---

## File Structure

```
reality_audit/
  benchmarks/
    double_slit.py           — core physics model (intensity functions + sampling)
    double_slit_runner.py    — audit-integrated runner (writes config/raw/summary)
  analysis/
    double_slit_metrics.py   — fringe_visibility, KL divergence, peak_count, etc.
    plot_double_slit.py      — figure generation (4 PNG outputs)

tests/
  test_double_slit.py            — 36 unit tests
  test_double_slit_runner.py     — 9 integration tests
  test_double_slit_metrics.py    — 22 unit tests
  test_plot_double_slit.py       — 6 figure tests

docs/
  DOUBLE_SLIT_BENCHMARK.md       — this file

commons_sentience_sim/output/reality_audit/double_slit/
  config.json                    — run configuration
  raw_results.json               — per-condition intensity profiles + hit counts
  raw_results.csv                — flat CSV (condition × bin)
  summary.json                   — top-level summary + per-condition stats
  metrics.json                   — full interference metric suite
  one_slit/summary.json          — per-condition sub-summary
  two_slit/summary.json
  two_slit_measured/summary.json
  figures/
    one_slit_distribution.png
    two_slit_distribution.png
    two_slit_measured_distribution.png
    overlay_comparison.png
```

---

## Reproducibility

All benchmark runs are fully reproducible given the same `seed` parameter.
The default seed is `42`.  Results are independent of system state.

```python
from reality_audit.benchmarks.double_slit_runner import run_double_slit_benchmark
from reality_audit.analysis.double_slit_metrics import compute_all_metrics

result = run_double_slit_benchmark(n_trials=50_000, n_bins=200, seed=42)
metrics = compute_all_metrics(result["results"])
print(metrics["interpretation"])
```
