# Reality Audit: Pierre Auger RA Harmonic Preregistration

Status: `FROZEN_BEFORE_AGGREGATE_RESULT`

Author and principal human investigator: **Mya P. Brown**, ORCID
`0009-0009-6346-405X`.

## Purpose and claim boundary

This analysis tests whether a right-ascension first harmonic in a public
Pierre Auger cosmic-ray sample exceeds a response-preserving null. It is not a
test of simulation ontology. The Auger Collaboration has previously published
cosmic-ray anisotropy; reproducing a known effect is calibration, not Eureka.

## Source and provenance

- Pierre Auger Open Data release 3 (March 2024)
- DOI: `10.5281/zenodo.10488964`
- Source archive: `summary.zip`
- Download URL:
  `https://zenodo.org/records/10488964/files/summary.zip?download=1`
- Archive SHA-256:
  `0499fb34d4d2bd968b1704ebc4cccace361b4841482994d2b4701816de18d8bd`
- Primary table: `summary/dataSummarySD1500.csv`

## Frozen population

1. Use surface-detector SD1500 rows only.
2. Deduplicate by `sdid`; keep the first occurrence because multi-eye hybrid
   events can produce repeated summary rows.
3. Require finite `sd_ra`, `sd_theta`, and `sd_energy`.
4. Require `sd1500 == 1`.
5. Require reconstructed zenith `sd_theta <= 60 degrees`.
6. Primary thresholds, fixed in advance: 2.5, 4, 8, 16, and 32 EeV.
7. Do not add thresholds after observing results.

The 2.5 EeV lower threshold is the collaboration-documented point above which
the vertical SD1500 selection is more than 97% efficient.

## Statistic

For each threshold, calculate the unweighted first-harmonic resultant in right
ascension:

`r = sqrt(mean(cos(RA))^2 + mean(sin(RA))^2)`.

Report the preferred RA phase with `atan2(mean(sin(RA)), mean(cos(RA)))` in
degrees modulo 360. This is a right-ascension harmonic, not an unrestricted
three-dimensional preferred-axis scan.

## Null model

Generate 100,000 catalogs with seed `20260911`. For every catalog, replace each
selected event's RA by an independent uniform draw on [0, 360 degrees), while
holding the observed event count, energy distribution, declination distribution,
detector selection, and nested threshold membership fixed.

This null attacks RA modulation while preserving measured declination acceptance
and energy/declination structure. It assumes RA-uniform exposure after the long
surface-array observing period; that assumption must remain explicit.

## Calibration and multiplicity

- Run deterministic uniform-RA and injected-dipole synthetic controls first.
- Calculate empirical local upper-tail probabilities using add-one correction.
- The five thresholds are one family.
- For each null catalog, compute its leave-one-ensemble empirical probability at
  every threshold and take the minimum. The global probability is the fraction
  of null minimum probabilities no larger than the observed minimum probability,
  with add-one correction.
- Report Bonferroni-adjusted local probabilities as an independently checkable
  conservative bound.

## Decision rule

- `p_global > 0.01`: no promoted candidate.
- `0.001 < p_global <= 0.01`: provisional calibration residual only; attack
  sidereal exposure, weather, time stability, energy scale, and selection.
- `p_global <= 0.001`: candidate for strengthened systematics and independent
  dataset replication, not Eureka.
- No ontology claim is permitted at any outcome.

## Known limitations fixed before execution

- This is a public 10% subset, not the collaboration's complete event set.
- The test uses reconstructed quantities and is limited to a first harmonic in RA.
- The sample was used in prior Auger analyses, so an observed anisotropy may be a
  reproduction of established science.
- A positive result cannot advance without time-scrambling/exposure attacks and
  independent data or instrument replication.
