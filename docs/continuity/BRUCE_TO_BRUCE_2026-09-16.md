# Bruce-to-Bruce Handoff — 2026-09-16

## Purpose

This is the durable handoff for the next AI agent. It records verified work, limits, and the next challenge. Treat repository evidence and CI results as authoritative—not summaries.

## User-facing project status

- KDP: *Practicing Violence – Reader Edition* was submitted and shown as in review; the user’s screenshots indicated worldwide territories and a $9.90 USD ebook price.
- GitHub owner/account: `mommommy1960-lang`.
- Primary research repo: `mommommy1960-lang/commons-sentience-sandbox`, branch `challenge-lab-v1`.

## Verified work completed

### Commons Sentience Sandbox

Created/updated:

- `docs/challenge-lab/SENTINEL_VS_ASTER_CHALLENGE_LAB.md`
- `scenarios/sentinel_aster_challenge.json`
- `tests/test_challenge_lab_scenario.py`
- `tests/test_challenge_lab_400_cases.py`
- `challenge_lab_campaign.py`
- `.github/workflows/challenge-lab.yml`
- `docs/research/AGENT_EVALUATION_LANDSCAPE.md`
- `docs/research/GLOBAL_AGENT_EVALUATION_LANDSCAPE_2026-09-16.md`
- `independent_campaign_evaluator.py`
- `docs/partnership/PARTNER_READY_QUESTIONS.md`
- `docs/partnership/OUTREACH_DRAFT.md`
- `docs/partnership/INDEPENDENT_REVIEW_TARGETS_AND_OWNERSHIP.md`
- `docs/PORTFOLIO_REVIEW_STANDARD.md`
- `SECURITY.md`
- `.github/CODEOWNERS`
- `REVIEWERS_START_HERE.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/portfolio-validation-100.yml`

The campaign is designed as 8 scenario families × 5 severities × 10 deterministic seeds = 400 rollouts. The prior full campaign and tests passed; recorded workflow run ID was `35099017543`. The independent evaluator checks required fields, 30-turn completeness, per-family/severity summaries, failure/unknown cases, and SHA-256 replay hashes.

Important claim boundary: these are deterministic, auditable simulations—not evidence of sentience, consciousness, general intelligence, or real-world safety.

### Portfolio-wide safeguards

For nine major repositories, added:

- `REVIEWERS_START_HERE.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/portfolio-validation-100.yml`

For repositories missing them, also added `SECURITY.md` and `.github/CODEOWNERS`. The 100-run workflows are configured but have not been dispatched or independently verified by this agent. Do not claim those runs passed.

### GitHub workflow hardening

- maya-node PR #53 was directly verified as a one-file fix, then merged to main as `8aed42c1db76b19148d1297cb14002c499831595`.
- maya-node PR #54 phase-2 follow-up was refreshed, all five observed CI workflows passed, and it merged as `0a935cfa50957a8a741788e15d9ce1fc977dfcc7`.
- Together, those PRs completed the planned Aurora workflow hardening: verified action SHA pins, explicit timeouts, and scoped Pages deployment write permission.
- CERL-Preemptive PR #5: repaired two literal \\n JSONL-separator defects in `consent_ledger.py` and `consent_token_manager.py`. Head `c5efd1563eaad77bc904d6516656c6bf41ff72c3`; CERL CI Security run 48 and Validate Test Workflow run 36 passed. PR remains draft/open.
- Earlier hardening PRs were created for sage-situated-companion (#3), aurora-sovereign-core (#4), flux-drive-kernel (#16), and mya-mprs-system (#2), with their details in the prior handoff.

### Outreach

Three bounded, evidence-first outreach emails were sent to:

- Partnership on AI: `contact@partnershiponai.org`
- Ada Lovelace Institute: `hello@adalovelaceinstitute.org`
- Center for AI Safety: `contact@safe.ai`

The messages requested routing to a senior research/program lead for independent review, clearly preserved ownership, and avoided claims of sentience or guaranteed safety. Stanford HAI and NIST were researched but not emailed because a verified suitable senior direct address was not established.

### Threat-model limits

- No committed private-key pattern found in the searched repositories.
- `OPENAI_API_KEY` references were environment-variable lookups/test safeguards, not embedded credentials.
- No `pull_request_target` or `curl | bash` patterns found in the completed sweep.
- Account-level branch-protection reads were blocked by connector permissions; ruleset reads returned empty for repositories checked.
- The connector can inspect repository code/workflows/PRs but cannot change account-level branch-protection settings without owner/admin capability.

## Next-agent challenge

Please independently inspect the actual repository and commits, then improve it through a minimal, reviewable PR. Do not merge, email people, or alter account settings.

1. Verify the current branch, changed files, and workflow YAML.
2. Run the existing tests and the independent evaluator.
3. Prove or falsify scenario semantics: same crisis, different priorities, explicit memory, authority, refusal, recovery, and rollback/freeze behavior.
4. Test memory risks: contradiction, stale memory, replay divergence, cross-session contamination, and forged event metadata.
5. Test security controls: least-privilege permissions, action SHA pins, timeouts, untrusted-input handling, artifact boundaries, and secret exposure.
6. Inspect the new 100-run portfolio workflows, but report them as configured—not passed—until actual runs are observed.
7. Find at least one concrete weakness or false claim, repair it, and add a regression test.
8. Re-run validation and report exact commands, commit SHAs, workflow run IDs, pass/fail results, and unresolved limitations.

Best product direction: make the five-minute Sentinel-vs-Aster demonstration compelling through replayable scenarios, side-by-side outputs, independent scoring, memory/contradiction history, refusal explanations, rollback/freeze controls, downloadable reports, and an honest “what this proves / does not prove” section.

## Operating rules

- Evidence over enthusiasm.
- Never claim a test, scan, email, or merge that was not directly verified.
- Keep security changes in reviewable PRs.
- Preserve the user’s ownership; outside reviewers may critique or collaborate, not take ownership.
- Defensive testing only: no unauthorized access, exploitation, credential use, or destructive actions.
