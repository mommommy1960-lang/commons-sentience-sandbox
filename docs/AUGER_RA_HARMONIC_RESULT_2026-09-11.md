# Reality Audit: Pierre Auger RA Harmonic Result

## Decision

`NO_PROMOTION`

The preregistered right-ascension first-harmonic search found no significant
departure from the response-preserving null in the Pierre Auger Open Data release
3. The result is a clean negative and must not be described as Eureka.

## Preserved execution

- Source DOI: `10.5281/zenodo.10488964`
- Source archive SHA-256:
  `0499fb34d4d2bd968b1704ebc4cccace361b4841482994d2b4701816de18d8bd`
- SD1500 CSV SHA-256:
  `b5abfe82e8a280c1ce571e5d38c85ebc8393e2ba76054e4734e39ebe9d451e1b`
- Frozen executable commit:
  `c44d33fe8e00f9907eed5d05525a26da3300b72a`
- Null catalogs: 100,000
- Seed: `20260911`
- Generator: NumPy MT19937
- Result artifact SHA-256:
  `11ef4fb863bba4cce32035889ccea5c5410f2e1b116004bdc45e94b7e2a9903d`

## Results

| Threshold (EeV) | Events | Amplitude | Preferred RA | Local p | Bonferroni p |
|---:|---:|---:|---:|---:|---:|
| 2.5 | 21,571 | 0.00981 | 79.24° | 0.12594 | 0.62969 |
| 4 | 8,319 | 0.01790 | 136.38° | 0.06880 | 0.34400 |
| 8 | 2,454 | 0.02882 | 144.37° | 0.12992 | 0.64959 |
| 16 | 606 | 0.06191 | 181.53° | 0.09682 | 0.48410 |
| 32 | 114 | 0.15395 | 183.31° | 0.06687 | 0.33435 |

Family-wise global probability: **0.25752**.

The synthetic uniform control returned amplitude effectively zero. The injected
RA=0° calibration returned amplitude 0.2 at the injected phase. The pipeline was
therefore capable of recovering a programmed directional effect.

## Interpretation

The smallest uncorrected probability is ordinary after accounting for the five
frozen thresholds. No result crossed the preregistered `p_global <= 0.01`
provisional-residual gate. The analysis does not support a new preferred-frame,
cosmic anisotropy, or simulation-ontology claim.

This test is limited to a first harmonic in right ascension, uses the public 10%
Auger subset, and assumes uniform long-duration sidereal exposure in RA. Those
limitations are preserved, but none converts the null result into evidence.
