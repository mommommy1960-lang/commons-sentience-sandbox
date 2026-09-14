# Quantum Double-Slit 100k Sampling Audit — 2026-09-10

## Purpose

This experiment asks a deliberately narrow question: when the existing quantum-style two-path benchmark generates finite Born-rule samples, do 100,000-event samples behave like the probability distributions the benchmark itself specifies?

It is an implementation / sampling calibration test. It is **not** an ontology detector. A successful result does not show that physical reality is simulated and does not establish new physics.

## Workload

- 100,000 sampled detection events per condition per seed
- 2 primary conditions: coherent and fully decohered
- 10 deterministic seeds: 0 through 9
- 2,000,000 total sampled detection events
- Existing benchmark geometry and probability equations retained

The replay used the repository's documented probability equations and the same seeded Python CDF-sampling algorithm as `born_sample()`.

## Reference profiles

- Coherent fringe visibility: approximately **0.9990665**
- Fully decohered fringe visibility: approximately **0.2710655**
- Existing repository audit already classifies this coherent/decohered distinction as a PASS and reports monotonic loss of visibility with increasing decoherence.

## 100k finite-sampling results

Across the 10 seeds:

### Coherent samples

- mean chi-square / degree of freedom: **0.98494**
- standard deviation of chi-square / degree of freedom: **0.12492**
- range: **0.77039 to 1.21551**
- mean L1 distance from expected probability profile: **0.03130**
- maximum L1 distance: **0.03446**
- every sampled coherent dataset preferred the coherent probability model over the decohered model by log likelihood
- smallest coherent-model log-likelihood advantage observed: **33,366.64**

### Decohered samples

- mean chi-square / degree of freedom: **1.02166**
- standard deviation of chi-square / degree of freedom: **0.09885**
- range: **0.90014 to 1.17616**
- mean L1 distance from expected probability profile: **0.03600**
- maximum L1 distance: **0.03866**
- every sampled decohered dataset preferred the decohered probability model over the coherent model by log likelihood
- smallest decohered-model log-likelihood advantage observed: **71,597.24**

For seed 0 specifically, using a conventional chi-square goodness-of-fit calculation over the 200 screen bins:

- coherent: chi-square ≈ **191.17** for 199 degrees of freedom, p ≈ **0.642**
- decohered: chi-square ≈ **184.30** for 199 degrees of freedom, p ≈ **0.765**

These values do not show a systematic residual against the distributions the benchmark was programmed to sample.

## Partial-decoherence check at 100,000 events

Using gamma values 0, 0.25, 0.50, 0.75, and 1.00, the programmed reference fringe visibility decreases as expected:

- gamma 0.00: **0.99907**
- gamma 0.25: **0.83782**
- gamma 0.50: **0.66058**
- gamma 0.75: **0.46755**
- gamma 1.00: **0.27107**

The 100,000-event samples at each point remained statistically consistent with their respective programmed distributions in the independent replay.

## Interpretation

The interesting result is methodological, not metaphysical.

The benchmark is behaving like the quantum-style model it was designed to implement. Increasing the number of detection events makes the sampled histogram converge more tightly toward the programmed Born-rule distribution. Coherent and decohered conditions remain decisively distinguishable, and the decoherence trend remains orderly.

That means the benchmark is useful as a **calibration instrument for Reality Audit**: it can be handed a known interference/decoherence structure and recover it reliably.

It does **not** mean the universe is a computer simulation. The benchmark is software running equations chosen by us. Repeating those equations 100,000 or 100,000,000 times cannot by itself turn their successful implementation into evidence about the ontology of the external universe.

To investigate simulation-like hypotheses scientifically, Reality Audit must use real observational data and preregister specific departures from ordinary physics or known measurement systematics that would count as evidence: for example reproducible preferred-direction structure, discretization signatures, unexplained bandwidth-like limits, timing residuals, or other effects that survive exposure correction, calibration, null models, multiple-testing controls, and independent replication.

## Bottom line

**No simulation-of-reality signal was found by this 100k sampling audit.**

What was found is something we need first: a stable benchmark that reproduces the behavior it claims to reproduce.

Reality first. Anomaly second.
