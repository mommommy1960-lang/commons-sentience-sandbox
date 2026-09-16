# Commons Portfolio Review Standard

**Owner:** Mya P. Brown / Commons Initiative  
**Status:** Evidence-first working standard

## Core rule

A repository may describe a behavior as **demonstrated** only when a reviewer can reproduce it from a stated version, command, input, and expected result.

Use these labels consistently:

- **Demonstrated:** executed and supported by preserved evidence;
- **Tested in simulation:** verified only inside a model or local harness;
- **Prototype:** partial implementation requiring further validation;
- **Proposed:** design or hypothesis not yet implemented;
- **Speculative:** concept requiring foundational evidence.

## Required controls

Every repository should maintain:

1. SECURITY.md for private vulnerability reporting and secret handling;
2. .github/CODEOWNERS routing sensitive changes to the owner;
3. REVIEWERS_START_HERE.md explaining scope and evidence limits;
4. a pinned, reproducible test command;
5. tests for normal, boundary, failure, reset, and rollback behavior;
6. a record of known failures and unresolved risks;
7. provenance for external data, dependencies, and generated artifacts;
8. a clear ownership and collaboration boundary.

## Review gates

Before a public release or partner claim, check:

- Can a clean checkout run the documented test?
- Are all required dependencies and versions stated?
- Are security-sensitive workflows least-privileged?
- Are secrets excluded from history and logs?
- Can a reviewer distinguish the agent's explanation from the evaluator's verdict?
- Are failed cases preserved rather than silently removed?
- Does the result survive repeated seeds or inputs?
- Are simulation, prototype, and physical claims separated?
- Does the public copy avoid guaranteed outcomes, endorsement claims, or inflated comparisons?

## Collaboration boundary

External reviewers receive only the minimum access needed for a defined task. Review does not transfer copyright, patent rights, trademarks, repository administration, exclusive licenses, commercial rights, or publication control.

Any expanded collaboration requires a separate written agreement.

## Incident response

When a problem is found:

1. preserve the evidence;
2. restrict or revoke affected access;
3. reproduce in a controlled environment;
4. fix the narrowest root cause;
5. add a regression test;
6. record the failure and correction;
7. communicate only verified facts.

## Public presentation

The front page should answer, in order:

1. What is this?
2. Who is it for?
3. What can I run in five minutes?
4. What is measured?
5. What failed?
6. How can I reproduce it?
7. What does it not prove?
8. How can I request a bounded review?

The strongest competitive advantage is inspectability: outside researchers can challenge the work, reproduce it, and verify who owns it.
