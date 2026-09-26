# Auger UHECR Lattice-Symmetry Screen — 100,000 Null Skies

## Question

Beane, Davoudi & Savage proposed that one specific numerical-simulation scenario, a universe represented on a cubic spacetime lattice, could in principle leave rotational-symmetry-breaking structure in the arrival directions of the highest-energy cosmic rays.

Reality Audit therefore asked a deliberately narrower question:

> Does the public Pierre Auger catalog of 109 highest-energy events show unusual right-ascension harmonic structure under a uniform-RA null, after correcting for the fact that we looked at several energy subsets and harmonics?

This is a **screen**, not a complete cubic-lattice test. A full test would require collaboration-grade exposure treatment and a spherical statistic tailored to cubic symmetry.

## Source

Pierre Auger Observatory, Catalog of the Highest-Energy Cosmic Rays recorded during Phase I of Operation:
https://opendata.auger.org/catalog/

Main Auger Open Data DOI: 10.5281/zenodo.4487612

The Auger documentation explains that large-scale anisotropy searches commonly use right ascension because the surface-detector exposure is close to uniform in RA in the fully efficient regime, while detailed analyses still account for small exposure nonuniformities.

## Predeclared screen

Energy-ranked subsets:
- top 20 events
- top 40 events
- top 60 events
- all 109 events

RA harmonics:
- m = 1
- m = 2
- m = 3
- m = 4
- m = 6

The m=4 component is especially relevant as a crude screen for fourfold angular structure, but none of these one-dimensional RA harmonics should be confused with a full orientation-independent cubic-symmetry statistic.

Null calibration: 100,000 uniform-RA skies, retaining the same nested energy-subset structure. Seed: 20260910.

## Result

The smallest single-screen Monte Carlo p-value was:

- **top 60 events, m=2:** p ≈ **0.06388**

Other low-ish but non-significant screens included:

- top 40, m=6: p ≈ 0.10147
- top 20, m=2: p ≈ 0.11765
- top 20, m=6: p ≈ 0.11966
- all 109, m=4: p ≈ 0.16226

For the most directly fourfold screen:

- top 20, m=4: p ≈ **0.43915**
- top 40, m=4: p ≈ **0.88932**
- top 60, m=4: p ≈ **0.59571**
- all 109, m=4: p ≈ **0.16226**

After accounting for the search across the predeclared energy subsets and harmonics, the correlated 100,000-sky look-elsewhere calibration gave a global p of approximately:

- **p_global ≈ 0.605**

## Plain-language verdict

**No Eureka here.**

The public 109-event Auger highest-energy catalog does not show a statistically persuasive RA-harmonic signature in this screen. In particular, the fourfold component does not stand out.

That is useful negative evidence against the specific simple lattice-like directional screen we asked for. It is not evidence against every possible simulation hypothesis, and it is not a complete test of the Beane-Davoudi-Savage cubic-lattice scenario.

## Scientific boundary

This result should be labeled:

**NULL / NO PROMOTION**

It does not pass the Eureka Gate.

A stronger follow-up would need:

1. the full Auger exposure model rather than the close-to-uniform-RA approximation;
2. a three-dimensional spherical statistic that explicitly fits cubic/octahedral symmetry over arbitrary lattice orientation;
3. preregistered energy thresholds or a properly corrected threshold scan;
4. independent comparison with Telescope Array or another UHECR dataset;
5. a prospective prediction that can be tested on later data.

The correct response to a null result is not to keep changing the statistic until something becomes significant. The next test must be specified for a physical reason before the decisive result is inspected.

**Decision: no discovery claim. Keep digging with a stronger, preregistered test.**
