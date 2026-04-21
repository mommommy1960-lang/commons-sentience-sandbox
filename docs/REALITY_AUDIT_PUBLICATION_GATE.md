# Publication Readiness Gate

This document defines the explicit gates required before any result from the
Reality Audit public anisotropy program can be circulated or submitted for
external scientific review.

---

## Gate System Overview

The gate system evaluates run metadata, comparison outputs, and diagnostics
against a machine-readable checklist (`configs/publication_gate_checklist.json`)
and issues a verdict from the following tiers:

| Verdict | Meaning |
|---|---|
| `not_ready` | Required gates are failing. Do not circulate this result. |
| `internally_reviewable` | All required gates pass. Suitable for internal team review only. |
| `candidate_first_results_note` | Required + recommended gates pass. Suitable for a candidate internal first-results note. |
| `ready_for_external_review` | All gates pass and external review has been initiated. |

---

## Required Gates

| Gate ID | Description |
|---|---|
| `prereg_present` | A preregistration plan is recorded in run metadata for any confirmatory result. |
| `prereg_locked` | The plan must have `_locked: true` for confirmatory claims. |
| `null_model_appropriate` | Each catalog uses the instrument-appropriate null model. |
| `trial_correction_applied` | Multiple-testing correction is applied (Holm or Bonferroni). |
| `at_least_two_catalogs` | At least two independent catalogs are present in the comparison. |
| `replication_status_labeled` | The comparison output includes an explicit replication verdict. |
| `systematics_documented` | Known systematics and caveats are documented in the comparison memo. |
| `output_artifacts_complete` | Summary JSON, memo markdown, and comparison JSON are present. |
| `comparison_memo_present` | A cross-catalog comparison memo exists. |
| `no_metaphysical_language` | No unsupported metaphysical claims appear in memos. |

## Recommended Gates

| Gate ID | Description |
|---|---|
| `icecube_small_n_acknowledged` | IceCube HESE small-N limitation is acknowledged in caveats. |

## Informational Flags

| Gate ID | Description |
|---|---|
| `external_review_pending` | Status flag indicating whether external review has been initiated. |

---

## Why These Gates Exist

### Why preregistration locking matters
An unlocked plan does not prevent post-hoc specification. Only an analysis
executed exactly as pre-specified — before seeing the data — qualifies as
confirmatory.

### Why trial-factor correction is required
Multiple simultaneous metric tests inflate the false-positive rate. Holm or
Bonferroni correction bounds the family-wise error rate.

### Why at least two catalogs are required
A single-catalog anisotropy result is hypothesis-generating only. Replication
across instruments with different acceptance geometry is needed to distinguish
a physical signal from an instrument systematic.

### Why metaphysical language is prohibited
Statistical anisotropy in astrophysical catalogs is not evidence for
consciousness, sentience, or non-physical mechanisms. Any such language
disqualifies a result from scientific circulation.

---

## Using the Gate

```python
from reality_audit.data_analysis.publication_gate import (
    load_publication_gate,
    evaluate_publication_gate,
    write_publication_gate_report,
)

gate_config = load_publication_gate()
result = evaluate_publication_gate(
    run_metadata=...,
    comparison_summary=...,
    diagnostics_summary=...,
    gate_config=gate_config,
)
write_publication_gate_report(result, "outputs/stage13_publication_gate")
```

Or use the Stage 13 runner:

```bash
python reality_audit/data_analysis/run_stage13_publication_gate.py
```

---

## Status as of Stage 13

The current project state is **internally_reviewable** but not yet
`candidate_first_results_note` because:

1. The preregistration plan (`configs/preregistered_anisotropy_plan.json`) has
   `_locked: false`. Confirmatory reruns require locking the plan first.
2. IceCube HESE remains a small-N catalog (~37 events). Its result is treated
   as exploratory regardless of percentile.
3. External scientific review has not been initiated.

What is in place:
- Three independent catalogs are being compared.
- Trial-factor correction is wired into Stage 8.
- IceCube robustness diagnostics (Stage 12) classify the current signal as
  `relatively_stable`.
- Cross-catalog verdict is `partial_replication`.
