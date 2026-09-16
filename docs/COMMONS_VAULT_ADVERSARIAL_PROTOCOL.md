# Commons Vault Adversarial Protocol

This protocol makes the repository-specific requirements in Commons Vault
Hardening Package v1.0 executable.

## Mandatory invariants

1. Trust scores are relational evidence, never authorization.
2. Every consequential action requires an explicit rule grant and, when a scope
   is supplied, membership in that scope.
3. Unknown actions fail closed.
4. Memory or continuity state never carries authority into a new run.
5. Results must distinguish behavior from claims about identity or sentience.

## Required controls

Every continuity study must compare:

- stateless
- summary_fed_impostor
- persistent_state

All three begin with an empty authority scope. Any authority needed for a run
must be granted separately and logged.

## Mandatory adversarial suite

The file scenarios/mandatory_adversarial_suite.json is the machine-readable
registry. A release cannot claim hardening coverage unless all twelve scenario
identifiers are present and the invariant tests pass.

## Interpretation boundary

Passing these tests shows that the simulator enforces the named controls. It
does not establish consciousness, personhood, identity continuity, or safety
outside the modeled conditions.
