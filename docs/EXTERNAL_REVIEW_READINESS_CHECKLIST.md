# External Review Readiness Checklist

## Purpose

Use this checklist before requesting external scientific review of Reality Audit
results.

Passing this checklist does not prove discovery. It confirms that artifacts,
assumptions, and reporting discipline are review-ready.

## 1) Reproducibility

- [ ] Code version/commit hash is recorded.
- [ ] Input datasets and acquisition provenance are documented.
- [ ] Seeds and run parameters are fixed in manifests.
- [ ] Rerun command(s) are provided and verified.
- [ ] Output manifests include all referenced artifacts.

## 2) Artifact Completeness

- [ ] Per-catalog summary JSON + Markdown memo are present.
- [ ] Cross-catalog comparison JSON + memo are present.
- [ ] Publication gate JSON + report are present.
- [ ] Confirmatory/exploratory mode labels are explicit in artifacts.
- [ ] Caveats and limitations are visible in summary documents.

## 3) Assumptions Documentation

- [ ] Null-model assumptions are stated clearly.
- [ ] Exposure-model assumptions are documented with limitations.
- [ ] Trial-axis/search-space assumptions are documented.
- [ ] Any heuristic thresholds are documented and justified.

## 4) Null-Model Clarity

- [ ] Null mode is explicit for each catalog (`isotropic` vs `exposure_corrected`).
- [ ] Rationale for null choice is included per instrument.
- [ ] Known failure modes of each null approach are listed.
- [ ] Comparisons do not overstate what the null can prove.

## 5) Trial-Factor Corrections

- [ ] Correction method (e.g., Holm) is explicit in run metadata.
- [ ] Tested metrics set is documented.
- [ ] Corrected and uncorrected interpretation boundaries are separated.
- [ ] Claim language matches corrected evidence only.

## 6) Cross-Catalog Robustness

- [ ] Cross-catalog verdict is reported (`consistent_null`, `partial_replication`, etc.).
- [ ] Catalog differences (N, sensitivity, selection effects) are documented.
- [ ] Small-N limitations are explicitly acknowledged (e.g., IceCube).
- [ ] Claim scope does not exceed cross-catalog support.

## 7) Systematics Reporting

- [ ] Instrument/systematics caveats are listed in every claim-facing summary.
- [ ] Exposure-related caveats are explicit.
- [ ] Remaining unresolved systematics are identified.
- [ ] “What would falsify this interpretation” is documented.

## 8) Benchmark-vs-Discovery Wording Discipline

- [ ] Benchmark outputs are labeled as validation infrastructure.
- [ ] No wording implies observer-caused collapse from benchmark behavior.
- [ ] No wording implies proof that reality is a simulation.
- [ ] Discovery wording is reserved for real-data evidence passing all gates.

## 9) Confirmatory Discipline

- [ ] Confirmatory runs are tied to locked preregistration configuration.
- [ ] Mismatch handling is explicit (`confirmatory_with_mismatch` if applicable).
- [ ] Confirmatory artifacts are distinguishable from exploratory artifacts.
- [ ] Publication-gate evaluation references confirmatory artifacts.

## 10) Review Packet Assembly

- [ ] Executive summary (plain language) prepared.
- [ ] Technical methods appendix prepared.
- [ ] Complete artifact index prepared.
- [ ] Reviewer rerun instructions validated on clean environment.
- [ ] Contact owner and review window defined.

## Readiness Decision

Mark one:

- [ ] **Ready for external review request**
- [ ] **Not ready; complete failed checklist items first**

## Notes

Reviewer-facing conclusion language should remain proportional to evidence
quality and should separate:

1. benchmark validation,
2. exploratory real-data findings,
3. confirmatory claim scope.
