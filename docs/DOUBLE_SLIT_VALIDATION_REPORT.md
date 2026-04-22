# Double Slit Validation Report

## Purpose

This report documents what the `double_slit_sim` module actually does, how it
implements coherence/decoherence/measurement modes, and what conclusions are
and are not justified.

Primary module:
- `reality_audit/data_analysis/double_slit_sim.py`

Companion CLI:
- `reality_audit/data_analysis/run_double_slit.py`

This is a computational benchmark model. It is not a laboratory quantum
experiment and does not establish claims about ontology.

## Model Definition

The simulator builds a 1-D screen intensity profile from a mixed model:

1. Coherent two-slit term (fringes present)
2. Classical incoherent sum term (fringes suppressed)
3. Weighted blend controlled by an effective decoherence parameter

### Core ingredients

- Wavelength: $\lambda$
- Slit separation: $d$
- Slit width: $a$
- Screen distance: $L$
- Screen coordinate: $x$

Derived terms:

$$
\theta = \arctan(x/L), \quad
\beta = \frac{k a \sin\theta}{2}, \quad
\delta = \frac{k d \sin\theta}{2}, \quad
k = \frac{2\pi}{\lambda}
$$

Envelope and coherent/interference form used in code:

$$
I_{\text{coherent}}(x) = 4\,\mathrm{sinc}^2(\beta)\cos^2(\delta)
$$

Classicalized (incoherent) reference:

$$
I_{\text{classical}}(x) = 2\,\mathrm{sinc}^2(\beta)
$$

Mixed output:

$$
I_{\text{mixed}}(x) = (1-\alpha)I_{\text{coherent}}(x) + \alpha I_{\text{classical}}(x)
$$

with $\alpha \in [0,1]$ after clipping.

## Coherence Parameter, Decoherence Model, and Measurement Toggle

The implementation computes:

- `coherence_decoherence = 1 - coherence`
- `measurement_addend = 1.0` if `measurement_on=True`, else `0.0`
- `alpha = clip(coherence_decoherence + decoherence_strength + measurement_addend, 0, 1)`

Interpretation:

- `coherence=1.0`, `decoherence_strength=0`, `measurement_on=False` gives
  $\alpha=0$ (maximal modeled coherence).
- Larger `decoherence_strength` increases $\alpha$ and suppresses fringes.
- `measurement_on=True` forces $\alpha \to 1$ (full classicalized blend).

## How Interference Is Suppressed (Algorithmic View)

Suppression is explicit, not emergent from a microscopic detector model:

1. Compute coherent pattern $I_{\text{coherent}}$.
2. Compute classical reference $I_{\text{classical}}$.
3. Mix by $\alpha$.
4. Normalize to peak 1.
5. Compute visibility:

$$
V = \frac{I_{\max}-I_{\min}}{I_{\max}+I_{\min}}
$$

As $\alpha$ increases, the oscillatory contribution from $\cos^2(\delta)$ is
progressively down-weighted, so fringe contrast decreases and $V$ falls.

The module classifies interference with a threshold:

- `interference_detected = (visibility > 0.15)`

## Mode Expectations

- Coherent mode: high visibility, interference detected.
- Decohered mode: reduced visibility relative to coherent mode.
- Measurement mode: visibility strongly reduced and usually below threshold.

These are benchmark expectations checked in tests.

## Modeled Behavior vs Emergent Behavior

Modeled behavior (hard-coded by design):

- The exact blending equation for coherence/decoherence.
- Measurement toggle forcing $\alpha$ to 1 through additive clipping.
- Regime labels (`coherent`, `partially_decohered`, `classicalized`).

Emergent behavior (output from the model equations and sampling):

- Specific numeric visibility values for a parameter set.
- Hit-position histograms sampled from the intensity distribution.
- Sensitivity of visibility to geometry/noise parameter changes.

In short: the benchmark intentionally enforces qualitative physics-inspired
trends; it does not claim to derive collapse from first principles.

## Why This Does NOT Prove Observer-Caused Collapse

This implementation does not model a conscious observer, laboratory apparatus
dynamics, detector back-action at microscopic detail, or full quantum
measurement theory. Instead, it introduces a controllable classicalization
parameter (`alpha`) and a measurement toggle that algorithmically increases that
parameter.

Therefore:

- It validates analysis behavior under known synthetic regimes.
- It does not prove that observation causes physical wavefunction collapse.
- It does not prove that reality is a simulation.

## Current Validation Status

Existing tests already verify expected trend behavior in this repository, such
as:

- coherent visibility > decohered visibility,
- measurement mode suppresses visibility below the interference threshold,
- coherent mode reports interference while measurement mode does not.

Stage 15 extension adds a dedicated diagnostics runner and validation tests to
make these checks easier to reproduce and share.

## Practical Use in the Reality Audit Program

Use this module as a calibration benchmark for analysis/reporting logic, not as
a source of external scientific claims. It is useful for proving that the
pipeline can discriminate high-contrast, reduced-contrast, and suppressed
interference regimes in a controlled setting.
