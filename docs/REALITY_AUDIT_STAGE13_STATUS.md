# Reality Audit Stage 13 Status

## Stage Goal

Stage 13 builds the publication-readiness gating layer for the Reality Audit
public anisotropy program. It formalizes a checklist for when results can be
circulated, packages the current three-catalog evidence state, and classifies
output-directory clutter from deliverables.

---

## Roadmap Alignment

Stage 13 addresses the next natural question after three-catalog comparison and
IceCube robustness diagnostics (Stage 12): Are the current results ready to
circulate, even internally?

The Operational Companion roadmap emphasis that applies here:
- Analysis-locking and preregistration must be verified before any confirmatory claim.
- Replication across instruments is required, not just observed.
- Known systematics must be documented.
- Exploratory and confirmatory labels must be explicit.

Stage 13 mechanizes these checks so future pipeline runs can be evaluated
automatically without manual review of every metadata field.

---

## Implemented Capabilities

| Capability | Status | Notes |
|---|---|---|
| Publication gate checklist JSON | COMPLETE | `configs/publication_gate_checklist.json` |
| Publication gate documentation | COMPLETE | `docs/REALITY_AUDIT_PUBLICATION_GATE.md` |
| `publication_gate.py` module | COMPLETE | Load/evaluate/write gate reports |
| `first_results_package.py` module | COMPLETE | Collect/package/brief current state |
| `output_hygiene.py` module | COMPLETE | Classify outputs directory; no auto-delete |
| Stage 13 runner CLI | COMPLETE | `run_stage13_publication_gate.py` |
| Scripts convenience wrapper | COMPLETE | `scripts/run_stage13_publication_gate.py` |
| Stage 13 tests | COMPLETE | 15 tests passed |

---

## Why Publication Gating Matters Now

After three catalogs and a robustness check, the natural temptation is to
circulate results informally. The gate makes the required conditions explicit:

1. Preregistration must be locked before confirmatory runs.
2. Multiple-testing correction must be applied.
3. At least two independent catalogs must be compared.
4. A replication verdict must be present.
5. Caveats must be documented.
6. No metaphysical language is permitted.

Without a formal gate, these conditions can be silently violated under pressure
to report results quickly.

---

## Current Evidence State (Stage 13 Gate Evaluation)

### Gate verdict: NOT_READY

**This is the honest and correct diagnosis.**

| Gate | Status | Detail |
|---|---|---|
| `prereg_present` | FAIL | Stage 9 Fermi/Swift runs predate preregistration feature |
| `prereg_locked` | FAIL | No locked plan in any used run |
| `trial_correction_applied` | FAIL | Stage 9 runs predate trial correction feature |
| `at_least_two_catalogs` | PASS | 3 catalogs present |
| `replication_status_labeled` | PASS | `partial_replication` |
| `systematics_documented` | PASS | 5 caveats documented |
| `output_artifacts_complete` | PASS | All tiers and verdict present |
| `comparison_memo_present` | PASS | Interpretation text present |
| `no_metaphysical_language` | PASS | No violations detected |
| `icecube_small_n_acknowledged` | PASS | Caveat present |

These are genuine technical mismatches, not enforcement errors.
The path to `internally_reviewable` is:
1. Rerun Fermi, Swift, and IceCube with `--preregistration-plan configs/preregistered_anisotropy_plan.json`
   and `--run-mode preregistered_confirmatory`.
2. Lock the plan (`_locked: true`) before those confirmatory reruns.
3. Confirm trial-factor correction is applied (`correction_method != none`) in the new runs.
4. Rerun Stage 13 gate against those new summaries.

---

## What the Output Hygiene Report Found

| Category | Count |
|---|---|
| deliverable | 65 |
| smoke / exploratory | 46 |
| benchmark / synthetic | 104 |
| legacy (pre-Stage-8) | 104 |
| unknown | 2 |
| transient plots | 0 |

Key recommendations (no files deleted):
- Smoke directories (`*_smoke`) can be added to `.gitignore` to prevent accidental staging.
- Legacy outputs (`discretization_audit`, `observer_effect_audit`, `preferred_frame_audit`) are
  pre-Stage-8 and unrelated to the current anisotropy deliverable.
- Benchmark and synthetic outputs are supporting evidence but not primary deliverables.

---

## Next Likely Step After Stage 13

Stage 14 (planned):
1. Lock the preregistration plan.
2. Re-run all three catalogs with `--run-mode preregistered_confirmatory`.
3. Re-run Stage 13 gate on the new confirmatory outputs.
4. Produce a Stage 14 readiness report that reaches `internally_reviewable` or
   `candidate_first_results_note`.
5. Prepare a candidate internal first-results note document.

---

## Final Validation

- `python -m pytest tests/test_stage13_publication_gate.py -v`: 15 passed
- `python -m pytest tests/test_catalog_comparison.py tests/test_stage8_first_results.py tests/test_stage12_icecube_diagnostics.py tests/test_stage13_publication_gate.py -v`: **73 passed**
- `python reality_audit/data_analysis/run_stage13_publication_gate.py`: OK, verdict NOT_READY (correct)
- `python scripts/run_stage13_publication_gate.py`: OK, same verdict
