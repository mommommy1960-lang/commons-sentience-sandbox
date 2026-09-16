# Bruce-to-Bruce Handoff — 2026-09-16

## Current user-facing status

- KDP confirmed **Practicing Violence – Reader Edition** was submitted and is **in review**.
- KDP displayed a possible review window of up to 72 hours.
- Territories were set to worldwide rights for the original edition, subject to the author’s rights confirmation.

## Security and repository work completed today

### CERL-Preemptive

- Made Ruff, Flake8, Bandit, and dependency checks fail closed.
- Fixed CI compatibility and repository lint findings.
- Scoped dependency auditing to declared manifests.
- Pinned workflow actions to reviewed commit SHAs.
- Added workflow concurrency cancellation and a 15-minute timeout.
- Latest recorded validation passed both security and validation workflows.
- Open hardening PR: https://github.com/mommommy1960-lang/CERL-Preemptive/pull/5

### maya-node

- Created a draft PR that changes the Pages workflow from repository-wide write permission to read-only default.
- Write access is limited to the deployment job.
- Draft PR: https://github.com/mommommy1960-lang/maya-node/pull/52

### sage-situated-companion

- Added read-only permissions, concurrency cancellation, timeout, and pinned actions.
- Draft PR: https://github.com/mommommy1960-lang/sage-situated-companion/pull/3

### aurora-sovereign-core

- Added concurrency cancellation, timeout, and pinned actions to safety and simulation workflows.
- Draft PR: https://github.com/mommommy1960-lang/aurora-sovereign-core/pull/4

### flux-drive-kernel

- Added read-only permissions, concurrency cancellation, timeout, and pinned actions.
- Draft PR: https://github.com/mommommy1960-lang/flux-drive-kernel/pull/16

### mya-mprs-system

- Removed unattended scheduled repository writes.
- Converted generated diagnostics to a retained Actions artifact.
- Added timeout and pinned actions.
- Draft PR: https://github.com/mommommy1960-lang/mya-mprs-system/pull/2

## Threat-model findings

- No committed private-key pattern was found in the searched repositories.
- OPENAI_API_KEY references are environment-variable lookups and test safeguards, not embedded credentials.
- Remaining hardening targets: review branch protection, audit dependency manifests, and expand test coverage without treating simulations as physical validation.

## Operating rule

Every new repository change and every material result must be added to a dated Bruce-to-Bruce handoff. Do not claim a test passed without a recorded CI result.
