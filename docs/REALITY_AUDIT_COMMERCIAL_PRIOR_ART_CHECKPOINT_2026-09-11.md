# Reality Audit Commercial Prior-Art Checkpoint

Date: 2026-09-11

Product framing: **Reality Audit — a falsification-first research assurance
engine.**

Founder and principal human author: **Mya P. Brown**, ORCID
`0009-0009-6346-405X`.

## Executive decision

`PRODUCT_WEDGE_PLAUSIBLE__EXCLUSIVITY_NOT_PROVEN__FTO_NOT_CLEARED`

Reality Audit may be sellable as an integrated research-assurance workflow and
service. The present search does **not** support claiming that experiment tracking,
provenance, data validation, workflow versioning, anomaly detection, adversarial
testing, or signed/verification records were invented here.

No responsible search can prove that nobody anywhere previously conceived an
idea. Patentability and freedom to operate are different questions. This document
is a documented engineering search, not a legal opinion, patentability opinion,
or guarantee against litigation.

## Feature comparison checkpoint

Legend: `Y` = documented core function; `P` = partial/adjacent; `N/F` = not found
in the reviewed core documentation, not proof of absence.

| Capability | Reality Audit target | MLflow | W&B | DVC | Great Expectations |
|---|---:|---:|---:|---:|---:|
| Parameters, metrics, artifacts, code/run identity | Y | Y | Y | P | P |
| Dataset/artifact versioning and lineage | Y | P | Y | Y | P |
| Declarative data-quality expectations | Y | N/F | N/F | N/F | Y |
| Claim and assumption registry | Y | N/F | N/F | N/F | N/F |
| Mandatory ordinary/baseline reproduction | Y | N/F | N/F | N/F | N/F |
| Adversarial systematics attack plan | Y | N/F | N/F | N/F | N/F |
| Synthetic fault/signal injection gate | Y | N/F | N/F | N/F | N/F |
| Detector/measurement response gate | Y | N/F | N/F | N/F | N/F |
| Response-aware null generation | Y | N/F | N/F | N/F | N/F |
| Multiple-testing/trial-factor gate | Y | N/F | N/F | N/F | N/F |
| Frozen/preregistered decision rule | Y | N/F | N/F | N/F | N/F |
| Independent replication requirement | Y | N/F | N/F | N/F | N/F |
| Promotion state machine for scientific claims | Y | N/F | N/F | N/F | N/F |
| First-class preserved negative result | Y | P | P | P | P |
| Signed evidence bundle | Target | N/F | P | N/F | P |

The `N/F` entries are search findings limited to the reviewed product documentation.
They must never be rewritten as categorical claims that a competitor lacks a
feature across every edition, integration, patent, or unpublished implementation.

## Concrete prior-art and freedom-to-operate flags

1. **MLflow Tracking** documents logging parameters, code versions, metrics,
   datasets, models, and artifacts; it provides APIs, search, storage, comparison,
   and traceability. Source: `https://mlflow.org/docs/latest/ml/tracking/`.
2. **Weights & Biases Experiments** documents metrics, hyperparameters, system
   metrics, model artifacts, dashboards, reproduction, registries, reports, and
   automations. Source: `https://docs.wandb.ai/models/track`.
3. **DVC** is established prior art around data/model versioning and reproducible
   pipelines. Source: `https://doc.dvc.org/`.
4. **Great Expectations** is established prior art around declarative data
   validation, validation definitions/checkpoints, and stored validation results.
   Source: `https://docs.greatexpectations.io/`.
5. **US 11,042,523 B2**, “Data curation system with version control for workflow
   states and provenance,” has priority claims reaching back to 2014. Any claim
   broadly covering versioned workflow state plus provenance is high risk.
   Source: `https://patents.google.com/patent/US11042523B2/en`.
6. **US 12,316,655 B1**, “Cyber resilience agentic mesh,” includes autonomous
   operations and tokens representing proof/verification of operations. Any broad
   “agent performs attacks and emits proof token” claim needs claim-by-claim legal
   review. Source: `https://patents.google.com/patent/US12316655B1/en`.
7. General anomaly detection, software fault injection, statistical null testing,
   red teaming, regulated validation, audit trails, and digital signatures are
   crowded prior-art areas and cannot individually support a first-ever claim.

## What may still differentiate

The presently supportable differentiation hypothesis is the enforced composition:

`claim -> assumptions -> provenance gate -> ordinary baseline -> adversarial`
`systematics -> synthetic fault injection -> response model -> null generation ->`
`trial control -> replication gate -> promotion state -> preserved negative result`

Potential commercial moats that do not require pretending the MIT-licensed core is
retroactively proprietary:

- domain-specific audit packs and response-model adapters;
- enterprise connectors and regulated-workflow integrations;
- implementation know-how for constructing hostile tests;
- signed evidence-bundle service and verification infrastructure, subject to FTO;
- curated failure-mode libraries;
- independent review network and reputation;
- brand/trademark;
- hosted workflow, access controls, and support;
- private customer configurations and proprietary adapters developed later.

## Sellable now versus not ready

### Defensibly sellable now

**Reality Audit Claim Stress Test**, a scoped human-led service:

1. customer supplies one scientific, technical, or AI-performance claim;
2. Reality Audit produces a claim/assumption/provenance map;
3. one ordinary baseline reproduction is attempted;
4. one adversarial or synthetic fault-injection test is executed;
5. the customer receives an evidence bundle and promotion/kill decision;
6. limitations and negative results remain explicit.

This sells skilled analysis and a repeatable process. It does not require claiming
exclusive ownership of experiment tracking or scientific falsification.

### Not ready to claim

- “first proof machine”;
- “nobody has created this before”;
- guaranteed discovery;
- guaranteed regulatory compliance;
- guaranteed freedom from infringement or lawsuits;
- autonomous software that safely breaks arbitrary third-party systems;
- patent exclusivity over the already published MIT implementation.

## Mandatory pre-market gates

1. Fix a precise product specification and architecture; slogans cannot be
   searched for infringement.
2. Build a claim chart against the independent claims of the identified patents
   and newly discovered families.
3. Search USPTO Patent Center, Google Patents, WIPO Patentscope, EPO Espacenet,
   papers, theses, repositories, archived product pages, and commercial products.
4. Audit all dependencies, datasets, model weights, examples, and copied text for
   license compatibility and attribution.
5. Have qualified patent counsel perform an actual freedom-to-operate review before
   making legal assurances or investing heavily in a patent filing.
6. Market only verified capabilities and preserve the evidence supporting every
   comparative claim.

## Next build decision

Build the smallest sellable layer as a **claim-stress-test CLI plus signed evidence
bundle schema**, while treating cryptographic signing as implementation work and
not presumed novelty. Test it first on the two preserved negative-result cases:
IceCube HESE and Pierre Auger. A product that faithfully kills its founder's own
preferred hypotheses demonstrates the value proposition better than a fabricated
discovery.
