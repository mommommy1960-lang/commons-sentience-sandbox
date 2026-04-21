# Publication Readiness Gate Report

Generated: 2026-04-21T21:23:17.595400Z

## Overall Verdict

**NOT_READY**

_Required gates are failing. Do not circulate this result._

## Failing Required Gates

- `prereg_present`
- `prereg_locked`
- `trial_correction_applied`

## Gate Details

| Gate | Severity | Passed | Detail |
|---|---|---|---|
| `prereg_present` | required | NO | No preregistration plan recorded in any catalog metadata. |
| `prereg_locked` | required | NO | No locked preregistration plan (_locked: true) found. |
| `null_model_appropriate` | required | YES | All catalogs use appropriate null models. |
| `trial_correction_applied` | required | NO | No trial-factor correction applied (method=none or absent). |
| `at_least_two_catalogs` | required | YES | Found 3 catalogs in comparison. |
| `replication_status_labeled` | required | YES | Replication verdict: 'partial_replication'. |
| `systematics_documented` | required | YES | 5 caveat(s) documented. |
| `output_artifacts_complete` | required | YES | Summary JSON and comparison output appear complete. |
| `comparison_memo_present` | required | YES | Comparison interpretation/memo is present. |
| `no_metaphysical_language` | required | YES | No metaphysical language detected in interpretation. |
| `external_review_pending` | informational | NO | External review has not yet been initiated (expected — this is a status flag). |
| `icecube_small_n_acknowledged` | recommended | YES | IceCube small-N limitation acknowledged in caveats. |

## Notes

- Cross-catalog replication verdict: partial_replication

---

This is an internal pipeline readiness report.
It is not a scientific claim and does not substitute for external review.
