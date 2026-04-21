# Reality Audit — Stage 9 Status

## What Stage 8 Found

Stage 8 ran the Fermi GBM GRB catalog (3000 events, 2008–2026) through the
Stage 7 anisotropy pipeline using a **uniform isotropic null** model.

Results vs isotropic null:
- Hemisphere imbalance: −0.412 → **100th percentile** (top 0%, strongest signal tier)
- Preferred-axis score: 0.246 → **100th percentile**
- Energy–time Pearson r: 0.020 → 71st percentile (not significant)
- Temporal clustering: 0.970 → 0th percentile (low, not anomalous high)
- **Signal tier: `strong_anomaly_like_deviation`**

### Why Stage 8 was misleading

The Fermi GBM has strongly **non-uniform sky coverage**:
- Earth occultation removes a significant fraction of the sky from any single observation.
- GBM triggers systematically favour events near the spacecraft orientation.
- There is known galactic latitude bias in the trigger catalogue.

An isotropic null expects events uniformly on the whole sphere.  Fermi GBM
does not observe uniformly.  The large hemisphere imbalance (−0.41) almost
certainly reflects the detector's sky-coverage pattern, not a genuine
cosmological anisotropy.

**Conclusion from Stage 8:** The strong anomaly result was an artefact of an
inadequate null model, not a signal.

---

## Stage 9: What It Adds

Stage 9 replaces the isotropic null with an **empirical sky-acceptance proxy**
built from the observed catalog itself.

### Method

1. Bin the observed events on a 24×12 RA×Dec grid (15°/bin).
2. Normalise bin counts to a probability distribution, with a small floor
   weight per cell to avoid zero-probability zones.
3. Sample null event positions from this distribution instead of uniformly.

### What this tests

"Is the pattern in the data stronger than the pattern expected from *the
observed sky coverage itself*?"

If hemisphere imbalance and preferred-axis score drop to non-significant
percentiles under the exposure-corrected null, it means those signals were
indeed driven by coverage geometry and not by any additional structure.

If any metric remains anomalous even under the corrected null, it would be
a more credible hypothesis-generating signal.

---

## Stage 9 Capability Checklist

| Component                               | Status   |
|-----------------------------------------|----------|
| `exposure_corrected_nulls.py` module    | COMPLETE |
| `null_mode` parameter in study pipeline | COMPLETE |
| `null_mode` CLI flag (`--null-mode`)    | COMPLETE |
| Stage 9 Fermi run (exposure_corrected)  | COMPLETE |
| Stage 9 isotropic comparison run        | COMPLETE |
| Stage-by-stage comparison               | COMPLETE |
| Tests for exposure null module          | COMPLETE |
| `docs/REALITY_AUDIT_STAGE9_STATUS.md`   | COMPLETE |
| `docs/REALITY_AUDIT_STAGE9_TEMPLATE.md` | COMPLETE |
| README Stage 9 section                  | COMPLETE |

---

## Why This Is Still Not a Publication-Grade Correction

The Stage 9 empirical correction is an **internal robustness upgrade**, not a
final instrument-response model.

| Limitation | Impact |
|------------|--------|
| Map built from data under test | Absorbs both acceptance and signal; conservative but not independent |
| 24×12 bin resolution | 15°/bin; cannot resolve fine-scale acceptance variation |
| No time-varying acceptance | Fermi pointing changes with orbit; single static map is approximate |
| No trigger efficiency model | Spectral/fluence-dependent trigger rate not modelled |
| No Earth-limb geometry | Exact Earth-limb position at each trigger time not used |

**Result:** If the exposure-corrected null shows no anomaly, that tells us
the Stage 8 result was acceptance-driven.  If it still shows an anomaly, a
more accurate instrument-response-weighted null is needed before any claim.

---

## Next Stage Priorities (Stage 10)

1. **Instrument-response-weighted null** — use the published Fermi GBM
   sky-exposure FITS maps (available from the FSSC) to weight the null
   correctly without contaminating it with the signal.
2. **HEALPix-based preferred-axis scan** — NSIDE ≥ 8 (~768 axes) for
   finer preferred-axis resolution.
3. **Multi-catalog cross-matching** — repeat on Swift BAT GRB catalog and
   check for cross-instrument consistency.
4. **Pre-registration** — file analysis plan before unblinding next dataset.
5. **Trial-factor correction** — Bonferroni or permutation correction across
   the four simultaneously tested metrics.

---

*Last updated: 2026-04-21*
