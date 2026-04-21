# Reality Audit — Stage 8 Status

## Stage 7: COMPLETE

The Stage 7 public-data anisotropy track is fully implemented and validated.
See `docs/REALITY_AUDIT_STAGE7_STATUS.md`.

Capabilities delivered in Stage 7:
- Public event catalog ingestion (`public_event_catalogs.py`)
- 48-axis preferred-axis scan (`public_anisotropy_study.py`)
- Isotropic null ensemble (100 repeats by default)
- Empirical percentile-rank signal evaluation
- TIER classification: none / weak / moderate / strong
- Full CLI (`run_public_anisotropy_study.py`)
- Benchmark, convenience script, tests (36/36 passing)

---

## Stage 8: Objective

**Goal:** Accept one manually placed real public catalog and produce a
reproducible internal first-results package including:

1. Normalised event CSV
2. Full Stage 7 anisotropy analysis artifacts
3. Internal first-results memo (Markdown)
4. Stage 8 artifact manifest

The Stage 8 layer is intentionally thin — it orchestrates the Stage 7 pipeline,
adds auto-detection of real catalog files, and adds the memo.

### Capability checklist

| Component                            | Status   |
|--------------------------------------|----------|
| `stage8_first_results.py` module     | COMPLETE |
| `run_stage8_first_results.py` CLI    | COMPLETE |
| `scripts/run_stage8_first_results.py`| COMPLETE |
| `tests/test_stage8_first_results.py` | COMPLETE |
| `docs/REALITY_AUDIT_STAGE8_TEMPLATE.md` | COMPLETE |
| `docs/REALITY_AUDIT_STAGE8_STATUS.md`| COMPLETE |
| README Stage 8 section               | COMPLETE |

---

## Flagship Hypothesis

**Preferred-axis / directional anisotropy** is the primary metric of interest:

> Does the spatial distribution of extragalactic events show a statistically
> significant preferred axis, beyond what is expected from an isotropic sky?

The preferred-axis score is the maximum |mean cos-projection| of event unit
vectors over 48 trial axes.  It is compared to an isotropic null ensemble
via empirical percentile rank.

Secondary metrics:
- Hemisphere imbalance (north–south fraction difference)
- Energy–time Pearson r
- Temporal clustering score

---

## What Remains Before a Publishable First-Results Note

The following gaps must be addressed before any external publication or
pre-print:

| Gap                              | Required action                                                     |
|----------------------------------|---------------------------------------------------------------------|
| Exposure-map null                | Replace isotropic null with acceptance-weighted sky coverage map    |
| Finer axis scan                  | HEALPix NSIDE ≥ 8 (~768–3072 axes) for sharper sensitivity         |
| Trial-factor correction          | Bonferroni or permutation correction across 4 simultaneously tested metrics |
| Pre-registration                 | File hypothesis and analysis plan before unblinding real results    |
| Multi-catalog replication        | Run on ≥2 independent catalogs; check for consistency              |
| Systematic-effects audit         | Characterise instrument pointing, spectral selection, epoch effects |

Until these are addressed, all Stage 8 outputs are **internal first-results
artifacts only** — not a publishable or citable result.

---

## Next Stage Priorities (Stage 9)

1. Exposure-map-corrected null model
2. HEALPix-based preferred-axis scan
3. Multi-catalog cross-matching module
4. Pre-registration workflow
5. Trial-factor correction module

---

*Last updated: 2026-04-21*
