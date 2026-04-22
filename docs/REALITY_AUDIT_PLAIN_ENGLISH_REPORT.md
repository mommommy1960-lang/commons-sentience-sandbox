# Reality Audit: Plain-English Report

## What this repository is

Commons Sentience Sandbox is a research codebase with two connected parts:

- a simulation sandbox used to test analysis methods in controlled settings,
- a staged Reality Audit workflow used to analyze public astrophysics catalogs
  with explicit guardrails.

The central idea is disciplined testing, not dramatic interpretation.

## Mission hierarchy (important)

1. Primary mission: defensible real-data anomaly-analysis infrastructure.
2. Secondary support: simulation/benchmark tools that validate methods.
3. Future expansion: owned-lab precision experiments only after software and
  analysis maturity.

## What the Reality Audit is

The Reality Audit is a narrow, method-first analysis program. It asks whether
sky-position pattern signals survive proper controls, replication, and
confirmatory discipline.

It is designed to reduce false confidence by requiring:

- declared null models,
- cross-catalog comparison,
- preregistration + confirmatory reruns,
- publication-readiness gate checks,
- explicit caveats in every memo.

## What the double-slit environment is doing

The double-slit environment is a controlled simulation benchmark inside this
repository. It creates three modes on purpose:

- coherent mode (clear interference fringes),
- decohered mode (fringes reduced),
- measurement-on mode (fringes strongly suppressed).

In plain terms, the code blends a wave-like pattern with a classical pattern
using an internal "decoherence" control. Turning measurement on pushes that
blend toward the classical side.

What this confirms: the implementation reproduces the expected transition from
high-contrast interference to reduced contrast to strong suppression under the
encoded decoherence/measurement assumptions.

What this does not confirm: an independent physical discovery. The benchmark
does not prove observer-caused collapse and does not prove that reality is a
simulation.

Why this matters: it gives the team a known, testable environment where the
pipeline should react in predictable ways. If the analysis cannot separate
these three modes in simulation, it should not be trusted on public-catalog
data.

Important boundary: this is still a model benchmark, not a laboratory proof.
It does not prove observer-caused collapse and does not prove reality is a
simulation.

Role in this project: this benchmark is supporting infrastructure for method
validation. It does not define the repository's main scientific mission.

## What the simulation sandbox is

The simulation sandbox is a broader controlled environment used for structured
experiments, logging, and stress tests. It helps validate analysis logic before
interpreting public-catalog outputs.

## What the public anisotropy pipeline is doing

The public anisotropy pipeline:

- ingests and normalizes public event catalogs,
- computes directional metrics (including preferred-axis and hemisphere
  imbalance),
- compares observed values against null ensembles,
- writes reproducible JSON/Markdown artifacts.

Later stages add exposure-aware null handling, cross-catalog comparison,
trial-factor correction, and publication gating.

## What preregistration, confirmatory reruns, and publication gate mean

- Preregistration: lock analysis choices before confirmatory interpretation.
- Confirmatory reruns: rerun with locked settings so results are auditable.
- Publication gate: a checklist that prevents circulation when required
  safeguards are missing.

These controls are meant to keep claims proportional to evidence.

## What the repository can do now

As of Stage 14 completion and Stage 15 diagnosis support, the repository can:

- run reproducible catalog analyses for Fermi, Swift, and IceCube,
- compare multi-catalog outcomes with explicit verdict labels,
- record preregistration metadata in confirmatory runs,
- evaluate publication readiness with machine-readable gate reports,
- generate plain-English internal reporting artifacts.

## What it has found so far

Current confirmatory-era snapshot:

- publication gate verdict: `candidate_first_results_note`,
- cross-catalog verdict: `partial_replication`,
- Fermi: weak anomaly-like tier,
- Swift: no anomaly detected,
- IceCube: strong anomaly-like tier with small sample size.

Interpretation: evidence is mixed and still compatible with instrument or
selection effects.

## What this does NOT prove

It does not prove:

- a universal anisotropy signal,
- metaphysical conclusions,
- that reality is a simulation,
- readiness for external claims without independent review.

## What should happen next

Near-term upgrades should prioritize:

1. stronger exposure and instrument-response systematics controls,
2. HEALPix-grade spatial analysis infrastructure,
3. larger independent datasets and replication power,
4. continued locked-plan confirmatory discipline,
5. external methodological review before wider circulation.

## Bottom line

The project is currently strong at careful internal first-results reporting and
weak at discovery-level certainty. The correct posture remains: test, replicate,
gate, then escalate only when evidence quality materially improves.
