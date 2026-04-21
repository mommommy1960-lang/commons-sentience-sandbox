# Reality Audit — Stage 8 Template: First Real-Catalog Results Package

## What Stage 8 Is For

Stage 8 is the first layer that ingests a real publicly available event catalog,
runs the Stage 7 preferred-axis / anisotropy analysis pipeline on it, and produces
a short internal memo for collaborators to review.

It does **not** constitute a scientific result on its own.  The outputs are a
starting point for systematic investigation, not evidence for any cosmological
or metaphysical claim.

---

## What File to Place in `data/real/`

Download one of the following catalogs and place it in `data/real/`:

| File name                        | Source                                | Notes                            |
|----------------------------------|---------------------------------------|----------------------------------|
| `fermi_lat_grb_catalog.csv`      | HEASARC / Fermi-LAT GRBs              | Recommended first target         |
| `swift_bat3_grb_catalog.csv`     | HEASARC / Swift BAT3 GRBs             | Alternative GRB catalog          |
| `icecube_hese_events.csv`        | IceCube HESE public data release      | Sub-TeV neutrino events          |

Any other CSV/TSV placed in `data/real/` will also be detected automatically
(as long as it is not named `example_event_catalog.csv`).

See `data/real/README_public_catalog_ingest.md` for column naming conventions
and download links.

---

## Which Command to Run

### Auto-detect (recommended):

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
    --auto-detect \
    --name stage8_real_first_results \
    --output-dir outputs/stage8_first_results/stage8_real_first_results \
    --null-repeats 100 \
    --axis-count 48 \
    --seed 42 \
    --plots \
    --save-normalized
```

### Manual input path:

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
    --input data/real/fermi_lat_grb_catalog.csv \
    --name stage8_fermi_lat \
    --output-dir outputs/stage8_first_results/stage8_fermi_lat \
    --null-repeats 100 \
    --axis-count 48 \
    --seed 42 \
    --plots \
    --save-normalized
```

### Convenience runner (auto-detect, minimal flags):

```bash
python scripts/run_stage8_first_results.py
```

---

## What Outputs to Expect

All outputs land under `outputs/stage8_first_results/<run_name>/`:

| File                                     | Description                                              |
|------------------------------------------|----------------------------------------------------------|
| `<name>_normalized_events.csv`           | Normalised catalog in pipeline schema (if --save-normalized) |
| `<name>_summary.json`                    | Full structured results JSON                             |
| `<name>_results.csv`                     | One-row CSV summary for aggregation                      |
| `<name>_summary.md`                      | Stage 7 Markdown summary                                 |
| `<name>_sky_plot.png`                    | Sky position scatter plot (if --plots)                   |
| `<name>_null_comparison.png`             | Metric vs null comparison bar chart (if --plots)         |
| `<name>_axis_scan.png`                   | Per-axis score plot (if --plots)                         |
| `<name>_memo.md`                         | **Stage 8 first-results internal memo**                  |
| `<name>_stage8_manifest.json`            | Full artifact manifest                                   |

---

## How Collaborators Should Read the Memo

The memo (`<name>_memo.md`) is a ~1–2 page internal document structured as:

1. **What was run** — catalog, event count, analysis parameters
2. **Coverage** — events with position, instrument labels, time span
3. **Key metrics table** — four observed statistics and their percentile ranks vs the isotropic null
4. **Interpretation** — tier classification and plain-language summary
5. **What this does NOT prove** — explicit disclaimers
6. **Current limitations** — known gaps in the method
7. **Recommended next upgrades** — what to do before claiming a result

Read the memo alongside the `_summary.json` for full numeric detail.

---

## What Would Count as an Interesting Result

An *interesting* result is one where:

- The preferred-axis percentile is ≥ 0.97 (top 3% vs isotropic null), **and**
- The pattern persists across two or more independent catalogs, **and**
- A plausible instrumental / selection-effects explanation has been evaluated
  and found insufficient to explain the magnitude of the deviation.

A single-catalog run with `axis_percentile ≥ 0.97` is *interesting* but not
yet *significant* in a scientific sense.

---

## What Would Still Be Insufficient for a Claim

Even a strong result from Stage 8 would be insufficient without:

1. **Exposure-map correction** — the null model must reflect actual sky coverage,
   not just uniform isotropy.
2. **Trial-factor adjustment** — four metrics are tested simultaneously; a
   Bonferroni or permutation correction is needed.
3. **Pre-registration** — the hypothesis and analysis plan must be filed before
   unblinding results.
4. **Multi-catalog replication** — at least one independent catalog must show
   a consistent pattern.
5. **Systematic-effects audit** — instrument pointing biases, spectral selection
   effects, and epoch-dependent efficiency must be characterised.

---

*This template is part of the commons-sentience-sandbox Stage 8 artifact layer.
It is an internal guide, not a scientific claim.*
