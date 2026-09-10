# Eureka Gate and Product Positioning — 2026-09-10

## Scientific purpose

Reality Audit is not allowed to search until it finds a flattering answer. A candidate result may be promoted to **EUREKA CANDIDATE** only after it survives a fixed sequence of gates:

1. **Provenance gate** — input data and metadata are traceable to authoritative sources.
2. **Calibration gate** — the detector/analysis recovers known injected or known external signals and rejects null controls at expected rates.
3. **Ordinary-explanation gate** — instrument response, selection effects, exposure, background, numerical error, calibration drift, and known physics are modeled to the level required by the claim.
4. **Pre-registration gate** — hypothesis, statistic, thresholds, exclusions, and stopping rules are fixed before the decisive data are inspected.
5. **Multiplicity gate** — multiple testing / look-elsewhere effects are controlled.
6. **Robustness gate** — result persists across reasonable analysis choices and perturbations.
7. **Replication gate** — an independent dataset, instrument, or research group reproduces the predicted effect.
8. **Prediction gate** — the candidate model makes at least one new risky prediction that was not used to construct the model and that later succeeds.
9. **Audit gate** — code, data lineage, hashes, environment, and failure history are preserved so another investigator can recompute the result.

Passing all gates does **not** automatically prove an ontology such as “the universe is a simulation.” It means the evidence has earned promotion from anomaly to a serious candidate discovery requiring broader scientific review.

## Commercial positioning

The broad ideas of automated falsification, model checking, reproducibility, anomaly detection, and agentic hypothesis testing already exist in academic and commercial tools. Reality Audit should therefore not be marketed as “the first falsification engine.”

A defensible product position is narrower:

> **Reality Audit is an evidence-first falsification and contradiction-audit workflow that tries to kill a claim before it lets the claim graduate. It combines provenance quarantine, adversarial null testing, detector/systematics checks, repeated Monte Carlo stress testing, explicit failure-state preservation, and a human-readable promotion gate.**

The current public repository is MIT licensed. Existing published code can therefore be used, modified, distributed, sublicensed, or sold by others subject to the license notice. Commercial value should come from execution and service rather than an assumption of exclusivity over already-published code.

Possible sellable layers:

- hosted Reality Audit runs;
- fixed-price independent falsification reports;
- enterprise/private-data connectors;
- proprietary future modules developed outside the already-published MIT codebase;
- signed reproducibility/evidence packages;
- scientific or engineering red-team engagements;
- custom detector/systematics modeling;
- audit dashboards, workflow orchestration, and support;
- training and implementation services.

## Product rule

**Do not sell certainty. Sell disciplined attempts to destroy false certainty.**

A useful customer output is not merely PASS/FAIL. It is an evidence packet showing what was tested, what broke, what survived, what assumptions still dominate the result, and exactly what would be needed to promote the claim further.
