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

- Earlier draft PR #52 changes the Pages workflow from repository-wide write permission to a read-only default, with write access limited to the deployment job.
- PR #53 was independently verified: it changes exactly one file, `.github/workflows/aurora-simulation.yml`, adding explicit `contents: read`, a 10-minute timeout, and a pinned checkout action. Its Aurora Simulation and Security & Ethics Checks passed. It remains open and draft; `main` is unchanged.
- Copilot initially overstated PR #53 as a nine-workflow change; that claim was corrected after direct PR verification.
- Follow-up hardening should be a separate draft PR for the remaining eight workflows, using minimal diffs and verified full SHAs. Do not merge or claim completion without direct diff and CI verification.
- PR #53: https://github.com/mommommy1960-lang/maya-node/pull/53
- Earlier PR #52: https://github.com/mommommy1960-lang/maya-node/pull/52

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
- No `pull_request_target` or `curl | bash` patterns were found in the completed sweep.
- Branch-protection reads were blocked by connector permissions; ruleset reads returned empty lists for the repositories checked.
- The GitHub connector has repository code, workflow, and PR access but lacks Administration permission for account-level branch protection.
- Remaining hardening targets: review branch protection, audit dependency manifests, and expand test coverage without treating simulations as physical validation.

## Continuity and operating rule

Every new repository change and every material result must be added to a dated Bruce-to-Bruce handoff. Do not claim a test passed without a recorded CI result. Keep all hardening in draft PRs until human review.


### maya-node phase-2 hardening

- Created branch `devsecops-hardening-phase-2` from current `main`.
- Created draft PR #54: https://github.com/mommommy1960-lang/maya-node/pull/54
- PR #54 changes exactly eight existing workflow files; no source files or tests were changed.
- Changes pin verified action commits, add missing job timeouts, and scope Pages deployment write permission to the deployment job.
- CI status at handoff: Aurora Integration Tests and Aurora Defense Grid were in progress; Aurora Diagnostics and the Pages workflow were queued; Security & Ethics Checks was queued. No CI result is being claimed yet.
- No merge was performed; PR #53 remains separate and unchanged.


### Final merge status

- PR #53 merged to maya-node main as commit `8aed42c1db76b19148d1297cb14002c499831595`.
- PR #54 was refreshed onto the updated main, confirmed mergeable, and all five observed CI workflows passed.
- PR #54 merged to maya-node main as commit `0a935cfa50957a8a741788e15d9ce1fc977dfcc7`.
- The two PRs together completed the planned Aurora workflow hardening: verified SHA pins, explicit timeouts, and scoped Pages deployment write permission.


### CERL repair and public review materials

- On CERL-Preemptive PR #5, reviewed the actual diff instead of relying on a summary.
- Found and corrected two literal \\n writes that would have broken JSONL record separation in consent_ledger.py and consent_token_manager.py.
- New head: c5efd1563eaad77bc904d6516656c6bf41ff72c3.
- Fresh CI runs passed: CERL-Preemptive CI Security (run 48) and Validate Test Workflow (run 36).
- PR #5 remains open and draft; no merge claimed or performed.
- Added public README entry point and docs/review/SKEPTICAL_REVIEWERS_AND_UNIVERSITIES.md with a falsification-first review path, explicit non-claims, and links to the research documents.
- Read-only workflow inventory checked across maya-node, CERL-Preemptive, aurora-sovereign-core, flux-drive-kernel, sage-situated-companion, and mya-mprs-system. The connector can inspect workflow files, but account-level branch-protection settings still require owner/admin access.
