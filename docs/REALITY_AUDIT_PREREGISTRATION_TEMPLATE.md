# Reality Audit — Pre-Registration Template

## Purpose

This template explains when and how to lock an analysis plan before running
a confirmatory test in the public anisotropy pipeline.  Fill in all sections
and store as `configs/preregistered_anisotropy_plan.json` before executing
any run intended for a first-results note.

---

## Why Pre-Registration Matters

Exploratory analyses are vulnerable to researcher degrees of freedom:
- Choosing the null model after seeing preliminary results can inflate false-positive rates.
- Selecting the threshold after seeing percentile outputs is equivalent to p-hacking.
- Adding or dropping catalogs after observing results biases cross-catalog comparisons.

Pre-registration forces you to specify all of these choices **before** looking
at any confirmatory result.  It does not restrict hypothesis generation — it
only distinguishes *exploratory* from *confirmatory*.

---

## Machine-Readable Plan Fields

See `configs/preregistered_anisotropy_plan.json` for the actual plan.  Key fields:

| Field | Description |
|-------|-------------|
| `hypothesis.name` | Short identifier for the hypothesis |
| `hypothesis.null_hypothesis` | Explicit null hypothesis statement |
| `target_catalogs` | List of catalogs, roles, and null-mode choices |
| `primary_statistics` | Statistics used for confirmatory inference |
| `secondary_statistics` | Exploratory statistics (not used for discovery claims) |
| `null_model.primary` | Default null model (`isotropic` or `exposure_corrected`) |
| `null_model.null_repeats` | Null ensemble size (minimum 500 for confirmatory) |
| `axis_scan.axis_count` | Number of trial axes (192 for confirmatory, 48 for screening) |
| `thresholds.exclusion_percentile` | Single-metric threshold for "notable deviation" |
| `thresholds.discovery_percentile` | Single-metric threshold for "discovery-level" |
| `multiple_testing_correction.method` | `holm` or `bonferroni` (recommended: `holm`) |
| `interpretation_guardrails` | Required caveats for interpreting results |
| `preregistration_metadata._locked` | Set to `true` before first confirmatory run |

---

## Step-by-Step Usage

### 1. Decide what you are testing

Edit `configs/preregistered_anisotropy_plan.json`.  Fill in:
- `hypothesis.name` and `hypothesis.description`
- `target_catalogs` — which catalogs, in what role (primary / replication)
- `primary_statistics` — exactly which statistics count for the test
- `null_model` parameters
- `thresholds`

### 2. Lock the plan

Set `"_locked": true` in the plan BEFORE running.

Compute the plan hash to detect future modifications:
```python
from reality_audit.data_analysis.preregistration import load_preregistration_plan, compute_plan_hash
plan = load_preregistration_plan()
print(compute_plan_hash(plan))
```
Store the hash string in `preregistration_metadata.plan_hash_sha256`.

### 3. Run with the plan

```bash
python reality_audit/data_analysis/run_stage8_first_results.py \
  --input data/real/fermi_lat_grb_catalog.csv \
  --name stage_confirmatory_fermi \
  --null-mode exposure_corrected \
  --null-repeats 500 \
  --axis-count 192 \
  --preregistration-plan configs/preregistered_anisotropy_plan.json
```

The run metadata in the output summary JSON will record:
- `preregistration.hypothesis_name`
- `preregistration.plan_hash_sha256`
- `preregistration.locked`

### 4. Do NOT modify the plan after running

If you modify the plan after running it, re-run from scratch and label the
results clearly as exploratory.

---

## What Counts as a Confirmatory Run

A run is confirmatory if and only if:
1. The plan was locked (`_locked: true`) before execution.
2. The plan hash matches the stored hash in the run metadata.
3. All three catalogs listed in the plan were available and run.
4. No threshold parameters were changed between locking and running.
5. Results were not pre-screened on a subset of null repeats.

---

## Interpretation Guardrails (from plan)

These apply to all results from this pipeline:

1. A statistically significant anisotropy is NOT evidence for any specific
   physical mechanism without independent theoretical motivation.
2. Small catalogs (N < 100) are underpowered.  IceCube HESE (N≈37) results
   are exploratory regardless of percentile.
3. Instrument acceptance correction is approximate; surviving signals must
   be checked against detailed instrument-response Monte Carlo.
4. Do NOT report percentiles as p-values.  Empirical null resolution floor
   is ≈1/null_repeats.
5. Pre-trial significance does not account for researcher degrees of freedom;
   only results using the pre-registered plan are confirmatory.

---

## What Still Blocks a Publishable Claim

Even after locking this plan and running confirmatory analyses:

| Blocker | Description |
|---------|-------------|
| True exposure maps | Fermi FSSC FITS exposure maps needed (not declination proxy) |
| Third catalog | A third independent catalog must replicate the signal |
| Detailed systematics | Instrument-response Monte Carlo needed |
| Theory link | A physical mechanism with a priori prediction is needed |
| Independent review | External scientific review is required before publication |
