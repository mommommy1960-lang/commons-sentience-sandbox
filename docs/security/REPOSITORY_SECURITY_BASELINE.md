# Repository Security Baseline

This checklist is the minimum security posture for Civic Continuum work.

## Repository settings to verify in GitHub

- Two-factor authentication enabled for the owner account.
- GitHub Actions restricted to approved actions where practical.
- Pull requests required before merging to main.
- At least one approving review required.
- Stale approvals dismissed after new commits.
- Force pushes and branch deletion disabled on main.
- CODEOWNERS review required.
- Secret scanning and push protection enabled where available.
- No long-lived personal access tokens in workflows.
- Secrets limited to the repository and environment that needs them.

## Code-level requirements

- Default-deny or explicit pause for unknown external operations.
- Permission checks before every state-changing operation.
- Independent emergency freeze.
- Provenance for memory and carryover records.
- Replay and audit-chain verification.
- Idempotent restore.
- No self-modifying governance rules.
- No autonomous network expansion.
- No claims of sentience, personhood, production safety, or physical capability without evidence.

## Current evidence boundary

This document is a required baseline, not a report that the settings above are enabled. Settings must be checked in the GitHub UI or API and recorded with date and evidence.
