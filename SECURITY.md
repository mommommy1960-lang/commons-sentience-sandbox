# Security Policy

## Scope

This repository contains simulation, research, and safety-orchestration code. It is not a production autonomous-agent or physical-device control system.

## Report a vulnerability

Do not publish credentials, private memories, exploit details, or personal data in a public issue. Use GitHub's private security advisory/reporting flow when available. If that channel is unavailable, contact the repository owner privately through a verified account channel.

Include:

- affected path and commit;
- reproducible steps;
- expected and observed behavior;
- impact;
- a safe mitigation, if known.

## Non-negotiable safety boundaries

- Unknown operations must not gain authority by default.
- Trust, affection, familiarity, urgency, memory, or identity never expand permissions.
- Physical effects, external messages, account actions, purchases, doors, vehicles, microphones, and cameras require a separate explicit scope.
- Self-destruction, disabling safety, harm to living beings, and weaponization are prohibited.
- Emergency freeze must take precedence over normal work.
- Audit records must preserve denials and failures honestly.
- No secret, token, API key, private memory, or personal data belongs in source control.

## Release gate

Before merging security-sensitive changes, require:

1. review of the exact diff;
2. unit and integration tests;
3. static/YAML validation;
4. audit of changed permissions and external effects;
5. confirmation that secrets are not present;
6. documented remaining failures;
7. human approval.

This policy describes required controls. It does not claim that repository settings, branch protection, CI, or production deployment are currently compliant.
