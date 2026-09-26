# Reality Audit — IceCube Response and Provenance Audit

**Date:** 2026-09-10  
**Status:** Internal correction / Stage 16 input-quality audit  
**Decision:** the legacy 37-row IceCube CSV and conclusions derived from it are quarantined from scientific inference pending replacement with validated official input.

## Why this audit exists

The 100,000-case falsification battery showed that detector acceptance can manufacture spectacular anisotropy when an analysis compares a biased detector against the wrong isotropic null. The immediate follow-through was therefore: **show us the detector response.**

Before building that correction, source provenance was checked. That check found a more basic problem.

## 1. Provenance failure in the repository's legacy 37-row file

Current legacy file:

`data/real/icecube_hese_events.csv`

Several rows disagree materially with published properties of the actual 3-year HESE events. Examples:

| Event | Repository row | Published HESE value |
|---|---|---|
| 3 | RA 127.93, Dec -31.21, 78.8 TeV, **shower** | RA 127.9, Dec -31.2, 78.7 TeV, **track** |
| 5 | RA 110.63, Dec **-7.69**, 71.4 TeV, shower | RA 110.6, Dec **-0.4**, 71.4 TeV, track |
| 8 | RA **178.87**, Dec **-6.88**, 28.9 TeV, shower | RA **182.4**, Dec **-21.2**, 32.6 TeV, track |
| 13 | RA **91.01**, Dec **14.08**, 253.3 TeV, shower | RA **67.9**, Dec **40.3**, 253 TeV, track |
| 18 | RA **86.88**, Dec **-3.91**, 41.0 TeV, track | RA **345.6**, Dec **-24.8**, 31.5 TeV, track |
| 23 | RA **344.92**, Dec **-16.25**, 82.0 TeV, shower | RA **208.7**, Dec **-13.2**, 82.2 TeV, track |
| 37 | RA **124.54**, Dec **-72.09**, 30.7 TeV, shower | RA **167.3**, Dec **+20.7**, 30.8 TeV, track |

These are not rounding differences. They change hemisphere membership, sky position, topology, and sometimes energy.

### Consequence

The earlier Reality Audit result based on this file — including the `10 north / 27 south` count and the associated ~0.76% exact 50/50 binomial result — is now classified:

**DEPRECATED / INVALID INPUT PROVENANCE**

It must not be used as evidence for physical anisotropy, simulation-like structure, or any other external scientific claim.

The file is preserved for provenance/history; it is not silently deleted.

## 2. What the actual IceCube publication says

The IceCube Collaboration's 3-year HESE paper, *Physical Review Letters* 113, 101101 (2014), reports 37 candidate events over 988 days and explicitly states that the data are **consistent with isotropic arrival directions**.

That does not prove perfect isotropy. It does mean our prior simple hemisphere result was already in tension with the collaboration's response-aware scientific interpretation and therefore demanded input/provenance review before any excitement.

## 3. The correct public response-rich dataset exists

IceCube's official 7.5-year HESE public release provides:

- **102 real data events** in `HESE_data.json`;
- reconstructed deposited energy, morphology, zenith, and double-cascade length;
- large Monte Carlo files split across `HESE_mc_truth.json`, `HESE_mc_observable.json`, and `HESE_mc_flux.json`;
- true/reconstructed zenith and energy;
- neutrino flavor / interaction information;
- `weightOverFluxOverLivetime`;
- atmospheric pion/kaon/prompt flux information;
- atmospheric self-veto corrections;
- atmospheric-muon weights;
- detector-systematic corrections through supplied spline machinery.

IceCube's own `data_loader.py` applies the analysis energy and double-cascade-length cuts. Its `weighter.py` combines astrophysical, atmospheric-neutrino, atmospheric-muon, self-veto, and detector-systematic terms. Its effective-area example computes response from the MC weights rather than assuming equal raw north/south acceptance.

This is the correct family of inputs for the next Reality Audit IceCube null.

## 4. Sanity check from the official 7.5-year data file

As a sanity check only, the published 102-event `HESE_data.json` reconstructed zenith values were converted to declination using the South-Pole geometry:

`declination = degrees(recoZenith) - 90`.

Observed raw file:

- 102 events
- 40 north
- 62 south
- raw north fraction: **39.22%**

Applying the official example loader's default reconstructed deposited-energy range of 60 TeV to 10 PeV leaves:

- 60 events
- 21 north
- 39 south
- raw north fraction: **35.0%**

**Important:** this observed fraction is NOT the detector exposure model. It contains astrophysical sky realization, backgrounds, response, cuts, and statistical fluctuation. It is included only to demonstrate why a raw 50/50 hemisphere assumption is unsafe.

For the old `10 north / 27 south` count, the exact lower-tail probability changes from about 0.00382 at pNorth=0.50 to about 0.2008 at pNorth=0.35. A separate 100,000-draw sensitivity run at n=37, pNorth=0.35 produced about **20.082%** with 10 or fewer northern events.

Again, pNorth=0.35 is not being claimed as IceCube's true acceptance. It is a sensitivity demonstration motivated by the official observed 60-event subset.

## 5. Response-model gate added to Reality Audit

A new module, `reality_audit/data_analysis/icecube_response_audit.py`, now:

1. audits the legacy CSV against published HESE track-event anchors;
2. marks it `UNTRUSTED_LEGACY_INPUT` when anchors disagree;
3. converts South-Pole zenith to declination explicitly;
4. summarizes official `HESE_data.json` without pretending observed counts are detector exposure;
5. calculates exact binomial sensitivity across alternative acceptance assumptions;
6. refuses to call an IceCube analysis `response-informed` unless all three official MC inputs are present and contain the required response fields.

Tests lock this behavior so later work cannot quietly turn the old file back into scientific evidence.

## 6. What is still required for the real response-corrected rerun

A mission-grade rerun requires the complete official HESE MC release and its detector-systematic machinery. The three MC JSONs are large (together well over 100 MB) and the release uses detector-systematic interpolation splines / PHOTOSPLINE for the collaboration example fit.

This environment can inspect the official public repository and verify the data/response architecture, but it cannot reliably materialize and execute the complete large response package here. Therefore the audit does **not** invent a response curve.

The next executable stage, once those official files are available in the runner environment, is:

1. validate official source identity and required fields;
2. reproduce IceCube's selection cuts;
3. compute an expected reconstructed-zenith / declination acceptance distribution from weighted MC;
4. include astrophysical signal plus atmospheric-neutrino and muon background components with documented parameter choices;
5. propagate detector-systematic variations;
6. generate at least 100,000 acceptance-aware null catalogs;
7. rerun hemisphere and preferred-axis statistics;
8. apply map-domain / trial correction;
9. report the result whether it becomes more interesting or completely disappears.

## 7. Corrected evidence state

**Fermi:** weak after current exposure correction.  
**Swift:** null-like.  
**IceCube legacy 37-row Reality Audit result:** **DEPRECATED because the input file fails provenance.**  
**Official IceCube 3-year publication:** arrival directions consistent with isotropy.  
**Official IceCube 7.5-year response-rich release:** validated target for the replacement analysis; response-corrected Reality Audit result not yet executed.

Therefore the prior `partial_replication` narrative must not be strengthened using the old IceCube branch. Until the official response-rich rerun exists, the honest cross-catalog statement is:

> **No validated catalog-independent anisotropy signal has been established by Reality Audit.**

## Core lesson

The 100,000-run battery warned us that the camera can lie.

The next audit found something even more basic: **we had the wrong photograph in one of the folders.**

That is exactly what Reality Audit is supposed to catch.

**Reality first. Provenance first. Instrument response before anomaly.**

### Primary sources

- IceCube Collaboration, *Observation of High-Energy Astrophysical Neutrinos in Three Years of IceCube Data*, Phys. Rev. Lett. 113, 101101 (2014), DOI 10.1103/PhysRevLett.113.101101.
- IceCube Collaboration, HESE 7.5-year data release, DOI 10.21234/4EQJ-BB17.
- Public response repository: `icecube/HESE-7-year-data-release`.
