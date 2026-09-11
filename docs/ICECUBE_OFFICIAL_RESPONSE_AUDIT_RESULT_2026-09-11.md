# IceCube Official HESE Response Audit Result — 2026-09-11

## Decision

**The hemisphere candidate is killed at the response-informed intermediate gate.**

For the official IceCube HESE 7.5-year public release, the frozen 60 TeV–10 PeV
selection contains 60 events: 21 reconstructed north and 39 reconstructed south.
The official public Monte Carlo, weighted with the exact best-fit flux/background
values used by IceCube's supplied example (but without PHOTOSPLINE detector
corrections), predicts a north fraction of 0.4094. The exact two-sided binomial
probability is 0.3623. A 100,000-catalog Monte Carlo lower-tail check gives 0.2111.
This is not anomalous.

This result replaces no collaboration likelihood and makes no ontological claim.
The quarantined legacy 10-north / 27-south result remains invalid because its input
provenance failed.

## What was executed

- Official release: DOI `10.21234/4EQJ-BB17`
- Official release Git commit: `2d1ed03a7fd1529e780149fef0e0135c0a57bcb0`
- Reality Audit executable commit: `cefa988fdfda0570951d993dbeba2a8d978d896e`
- Selected official MC events: 736,814
- Null catalogs per component diagnostic: 100,000
- Random seed: `20260910`
- Random generator: Python `random.Random` (MT19937)
- Result artifact SHA-256: `0b00bd27040278f987a4fa21085bbb67ee62f65989723815cd4d134f8084e572`
- Focused tests: 8 passed

All four official input Git blob SHA-1 values match the pinned source manifest.
The JSON result additionally records byte counts and SHA-256 digests.

## Frozen selection and conventions

- Reconstructed deposited energy: 60,000 GeV through 10,000,000 GeV, inclusive.
- Double-cascade reconstructed length: 10 m through 1,000 m, inclusive.
- The length cut applies only to reconstructed morphology 2, matching the supplied
  IceCube loader.
- At the South Pole, reconstructed declination is `degrees(zenith) - 90`; north is
  therefore `recoZenith >= pi/2`.
- Neutrino/antineutrino weighting follows the official convention: positive
  `primaryType` receives `nunubar_ratio`, negative receives `2 - nunubar_ratio`.

## Primary response-aware result

| Quantity | Value |
|---|---:|
| Observed total | 60 |
| Observed north | 21 |
| Observed south | 39 |
| Observed north fraction | 0.3500 |
| Expected north fraction, nominal mixture | 0.4094 |
| Exact lower-tail probability | 0.2113 |
| Exact two-sided probability | 0.3623 |
| Monte Carlo lower-tail probability | 0.2111 |

The nominal mixture hemisphere count is the single primary diagnostic, so no
multiple-testing correction is applied to that one result.

## Nuisance sensitivity

One-at-a-time flux/background stresses use the official HESE example's prior
centres and one-standard-deviation bounds where available. Prompt normalization is
also switched from the example best fit of zero to one as a conservative stress.
These are sensitivity attacks, not a nuisance posterior or refit.

Across the 13 nominal/varied scenarios:

- expected north fraction: 0.3949 to 0.4218;
- exact two-sided probability: 0.2966 to 0.5116.

No tested flux/background nuisance variation makes the observed hemisphere count
unusual. Exploratory component-only tests are explicitly marked exploratory and
receive Holm family-wise-error adjustment. Component-only incompatibilities are
not anomaly evidence because the observed sample is a mixture, not a pure
atmospheric component.

## Preferred-axis boundary

**Not computable from this public release.** The official observed and Monte Carlo
JSON files contain reconstructed zenith but no azimuth or right ascension. A
free-axis sky scan cannot be reconstructed from declination alone. No coordinates
were invented, no preferred-axis statistic was reported, and no axis-scan trial
factor was fabricated.

## Remaining limitation

The exact IceCube detector-systematic correction requires the collaboration's
PHOTOSPLINE library and supplied spline tables. The spline tables are present, but
PHOTOSPLINE could not be built in the current runtime because CMake is absent and
there is no published `photospline` Python package available from pip. This is a
clearly bounded tooling limitation. It does not rescue the candidate: the
available official-MC response and flux/background stress tests already place the
hemisphere observation comfortably inside the null range.

## Promotion decision

`KILLED_RESPONSE_INFORMED_INTERMEDIATE`

Do not promote this candidate. Preserve the negative result. A future full spline
run may refine the response estimate, but it is not justified as a search for a
desired conclusion. A scientifically higher-value next action is to preregister a
test on a dataset that publishes sufficient directional coordinates and response
information for the intended statistic.
