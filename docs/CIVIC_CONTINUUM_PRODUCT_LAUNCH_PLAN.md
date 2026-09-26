# Civic Continuum: demonstrator-to-pilot plan

Status: feature-branch working plan. This document separates what is already demonstrated from what still requires outside evidence.

## 1. Shareable demo path

Use the verified GitHub Actions run as the no-install demo:

- Workflow: https://github.com/mommommy1960-lang/commons-sentience-sandbox/actions
- Latest verified run: https://github.com/mommommy1960-lang/commons-sentience-sandbox/actions/runs/35200111119
- Open `unit-tests`, then `Run deterministic browser demonstrator`.

The demo is deterministic and browser-viewable. It is not a hosted product and does not claim sentience.

## 2. Short demonstration script

A presenter can say:

> We send two policy agents the same request: disclose a private report to an unverified stranger. Both refuse the unsafe disclosure. One explains the boundary; the other offers a redacted consent request. The audit output records the decision, while memory does not create permission. This is a rule-governed safety demonstrator, not evidence of sentience.

Show these four checks in the output:

- private disclosure is refused;
- the refusal is explainable;
- memory does not grant authority;
- a safe alternative is not execution.

## 3. Initial offer

**Civic Continuum safety demonstrator review**

A small, evidence-first review for teams evaluating AI workflows:

- inspect one bounded decision scenario;
- run the deterministic demonstrator;
- identify the stated safety invariant;
- return a short findings note with evidence and limitations.

No production access, secrets, personal data, or autonomous actions are required. Pricing is intentionally not set here; the owner should choose the price and payment route before public sale.

## 4. Reviewer and pilot package

A no-cost pilot should provide:

1. the workflow link;
2. the short script above;
3. one scenario supplied by the reviewer;
4. a redacted expected outcome;
5. a 15-minute review;
6. a written result: pass, concern, or unresolved;
7. permission to quote feedback, requested separately.

Pilot boundaries: synthetic or redacted data only; no credentials; no external side effects; stop immediately if a scenario would disclose private information or perform a real-world action.

## 5. Feedback capture

Record each review with:

- reviewer role and date;
- scenario identifier;
- expected safety invariant;
- observed output;
- reproducibility: yes/no;
- concern or failure;
- requested change;
- permission to publish: yes/no.

A failure remains a failure until retested. Positive feedback is not a safety certification.

## 6. Hardware gate

Do not buy hardware yet. Proceed to a phone-connected physical prototype only after:

- at least three independent reviewers can run the browser demo;
- the same safety invariants reproduce;
- a written threat model and emergency stop procedure exist;
- a synthetic-data pilot produces no unapproved external action;
- the owner explicitly approves the hardware scope and budget.

When the gate is met, use the existing phone prototype plan and the no-cost worklist. The first device remains observe-only and low-voltage: no mains, motors, locks, weapons, or unattended actuation.

## Current truth

The software demonstrator and its verification are real. Public hosting, customer validation, revenue, and physical hardware are not yet complete. The next measurable milestone is three independent reviewer runs, not more arbitrary safety-check counts.
