# REALITY AUDIT – STAGE 14 TEMPLATE

## Purpose

This template documents the Stage 14 confirmatory-reruns pattern.  Use it when
you need to:
- Lock a preregistration plan and run confirmatory analysis
- Resolve publication-gate failures related to preregistration metadata
- Produce a gate report showing `CANDIDATE_FIRST_RESULTS_NOTE` or better

---

## Stage 14 Workflow

```
configs/preregistered_anisotropy_plan.json
    └─── _locked: true  (set once, never change after first confirmatory run)

scripts/run_stage14_confirmatory_reruns.py    (all 3 catalogs → confirmatory summaries)
    └─── outputs/stage14_confirmatory/{fermi,swift,icecube}/*_summary.json

scripts/run_stage14_confirmatory_comparison.py  (build comparison → evaluate gate)
    └─── outputs/stage14_confirmatory/gate/
             stage14_confirmatory_gate_publication_gate_report.md
             stage14_confirmatory_gate_manifest.json
```

---

## Step 1: Lock the Preregistration Plan

**Do this exactly once, before the first confirmatory run.**

```python
import json, hashlib

with open("configs/preregistered_anisotropy_plan.json") as f:
    plan = json.load(f)

plan["_locked"] = True
plan["preregistration_metadata"]["registration_date"] = "YYYY-MM-DD"
plan["preregistration_metadata"]["first_confirmatory_run_date"] = "YYYY-MM-DD"
plan["preregistration_metadata"]["plan_hash_sha256"] = None  # compute below on null plan

canonical = json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
h = hashlib.sha256(canonical.encode()).hexdigest()
plan["preregistration_metadata"]["plan_hash_sha256"] = h

with open("configs/preregistered_anisotropy_plan.json", "w") as f:
    json.dump(plan, f, indent=2)
    f.write("\n")
```

Commit: `git add configs/preregistered_anisotropy_plan.json && git commit -m "Lock preregistration plan"`

---

## Step 2: Run Confirmatory Reruns

```bash
python scripts/run_stage14_confirmatory_reruns.py \
    --null-repeats 500 \
    --axis-count 192 \
    --seed 42
```

Outputs go to `outputs/stage14_confirmatory/{fermi,swift,icecube}/`.

---

## Step 3: Run Comparison and Gate

```bash
python scripts/run_stage14_confirmatory_comparison.py
```

Expected verdict: `CANDIDATE_FIRST_RESULTS_NOTE` (all required gates pass).

---

## Key Gate Requirements for `CANDIDATE_FIRST_RESULTS_NOTE`

| Gate | Requirement |
|------|-------------|
| `prereg_present` | Any catalog has `preregistration_hash` in metadata |
| `prereg_locked` | Any catalog has `preregistration_locked: true` |
| `trial_correction_applied` | Any catalog has `trial_correction_method != "none"` |
| `at_least_two_catalogs` | Comparison includes ≥2 catalogs |
| `null_model_appropriate` | Fermi/Swift use `exposure_corrected`, IceCube uses `isotropic` |
| `replication_status_labeled` | Comparison has a `consistency_verdict` |
| `systematics_documented` | Comparison memo has caveats |
| `output_artifacts_complete` | Summary JSON and comparison present |
| `comparison_memo_present` | Comparison interpretation present |
| `no_metaphysical_language` | No unsupported claims in interpretation |

---

## Required Gate States After Stage 14

```
prereg_present             PASS  ← was failing in Stage 13
prereg_locked              PASS  ← was failing in Stage 13
trial_correction_applied   PASS  ← was failing in Stage 13
external_review_pending    FAIL  ← informational; expected; OK
```

---

## Notes

- **Never modify** `configs/preregistered_anisotropy_plan.json` after the first
  confirmatory run.  A post-hoc modification invalidates the plan hash and
  converts confirmatory results to exploratory.
- IceCube HESE (N≈37) is always treated as exploratory regardless of its signal
  tier — see `interpretation_guardrails` in the plan JSON.
- The `external_review_pending` gate will remain `FAIL` until an independent
  scientific reviewer has evaluated the methodology.
