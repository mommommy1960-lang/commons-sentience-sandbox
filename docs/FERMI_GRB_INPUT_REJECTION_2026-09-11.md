# Fermi GRB Candidate Input Rejection — 2026-09-11

## Decision

`REJECT_INPUT__NO_SCIENTIFIC_RUN`

The repository file `data/real/fermi_lat_grb_catalog.csv` is not eligible for the
planned Fermi-LAT GRB timing analysis.

## Evidence

- File SHA-256:
  `8bd58b9fdf7bbc35da6ceae51a4469a6856ed585e6a895bc1bceea5b75cb165d`
- Rows: 3,000 events plus header.
- Instrument column identifies `Fermi-GBM`, not Fermi-LAT.
- No provenance sidecar exists.
- Authenticity tier: `UNVERIFIED`.
- Required timing-pipeline columns absent: `grb_name`, `energy_gev`, `redshift`,
  and `grb_t90_s`.
- Redshift-qualified sources: 0; minimum required: 5.
- 2,998 energy values fail the pipeline's declared GeV plausibility bounds,
  consistent with a unit/schema mismatch.

The pre-ingest validator returned `REJECT`. No timing slope, p-value, anomaly, or
ontology inference was calculated. Renaming columns or inventing a sidecar would
not repair provenance.

## Required replacement

Acquire photon-event data from the official Fermi Science Support Center/HEASARC,
retain the original FITS files and checksums, document the event selections and
instrument response, connect each GRB to a defensible redshift source, then freeze
the timing analysis before unblinding.
