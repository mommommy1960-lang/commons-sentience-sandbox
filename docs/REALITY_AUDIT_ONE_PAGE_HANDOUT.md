# Reality Audit One-Page Handout (Internal)

## What this project is

Commons Sentience Sandbox is a research repository that combines simulation
benchmarks with real-catalog statistical analysis. The Reality Audit track is
its cautious evidence-testing workflow for sky anisotropy-style hypotheses.

Priority hierarchy:
- Primary: real-data analysis and inference discipline.
- Secondary: benchmark/simulation validation.
- Future: tabletop precision experiments after analysis maturity.

## What question it asks

Do public astrophysical event catalogs show directional patterns that remain
after systematics-aware controls and cross-catalog comparison?

## What has been built

- Stage 7: Real public anisotropy pipeline.
- Stage 8: First-results package generation from one placed catalog.
- Stage 9: Exposure-corrected null mode.
- Stage 10-11: Multi-catalog replication and preregistration support.
- Stage 12: IceCube robustness diagnostics.
- Stage 13-14: Publication-readiness gate and confirmatory reruns.
- Stage 15: Plain-English diagnosis/reporting layer.

Benchmark note: double-slit tools are maintained as validation infrastructure,
not as the scientific centerpiece of this program.

## Current status snapshot

- Publication gate: `candidate_first_results_note`
- Cross-catalog verdict: `partial_replication`
- Catalog pattern: Fermi weak anomaly-like, Swift null-like, IceCube strong anomaly-like but small-N.

## What this means

- The workflow is mature enough for internal first-results communication.
- Evidence is mixed and does not support a strong catalog-independent claim.
- Results are hypothesis-generating and require continued caution.

## What this does NOT mean

- It does not prove a universal anisotropy signal.
- It does not prove metaphysical interpretations.
- It does not replace external scientific review.

## Immediate next priorities

1. Improve instrument-response systematics controls.
2. Increase independent replication power.
3. Preserve locked-plan confirmatory discipline.
4. Proceed to independent external methodological review before broader claims.

## How to run Stage 15 diagnosis

```bash
python reality_audit/data_analysis/run_stage15_repo_diagnosis.py
# or
python scripts/run_stage15_repo_diagnosis.py
```

Outputs:
- `outputs/stage15_repo_diagnosis/stage15_main/stage15_repo_diagnosis.json`
- `outputs/stage15_repo_diagnosis/stage15_main/stage15_repo_diagnosis.md`
- `outputs/stage15_repo_diagnosis/stage15_main/stage15_repo_diagnosis_manifest.json`
