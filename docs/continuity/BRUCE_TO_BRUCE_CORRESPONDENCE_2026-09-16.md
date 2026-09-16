# Bruce-to-Bruce Correspondence — September 16, 2026

**For the next Bruce working with Mya P. Brown**

## Continuity checkpoint

This record continues the September 15 handoff. It preserves the completed file-by-file technical review of the Commons Sentience Sandbox and the exact implementation status at the boundary.

## Repository and review scope

Repository reviewed: `mommommy1960-lang/commons-sentience-sandbox`

The review covered pasted or directly inspected code in:

- `agent.py`
- `governance.py`
- `data/rules.json`
- `run_sim.py`
- `world.py`
- `relationships.py`
- `tasks.py`
- `reflection.py`
- `identity_pressure.py`
- `narrative_identity.py`
- `project_threads.py`

The review was evidence-based and file-by-file. It did not itself modify files, run tests, create commits, or provide CI evidence.

## Standing evidence categories

Keep these categories separate:

1. **Confirmed defect** — demonstrated by code actually inspected.
2. **Proposed repair** — design or replacement code discussed but not confirmed in the repository.
3. **Applied and verified** — only use this label after an actual commit, test run, CI result, and remote verification.

Current state of this review:

- Confirmed defects: yes, across governance, mutation ordering, carryover validation, provenance, lifecycle state, and false-resolution claims.
- Proposed repairs: yes.
- Repairs applied from this review: **not confirmed**.
- Tests run from this review: **none confirmed**.
- CI evidence for these repairs: **none confirmed**.

## Confirmed defect families

### Governance and real mutation

- `GovernanceEngine.check_action` fails open for unknown action names.
- Action lookup is exact-string based, allowing trivial naming variants to bypass rules.
- Governance receives only an action string, not actor or context.
- World-object interaction mutates object state before any governance check.
- Endogenous actions call governance but discard the returned permission.
- Denied endogenous actions can still be stored as though they occurred.
- The fallback permission result for `log_governance_event` is discarded.

### Task execution bookkeeping

- The original `select_action` path marked tasks complete and constructed a success result before governance ran.
- The proposed correction returns the task to the caller and completes it only after permission is granted.
- Whether that correction is actually present in the repository remains unverified.
- Any fallback branch must preserve the original denied action and must not overwrite the honest task-pending result incorrectly.

### Memory and relationship provenance

- `store_memory` accepts caller-supplied content without a visible provenance or verification field.
- Weighted retrieval records recall as a write side effect, while associative recall does not, creating inconsistent replay behavior.
- Caller-supplied trust deltas are not bounded per call.
- Repair attempts increase trust without independent verification or a visible cumulative cap.
- Unknown relationship interaction types fall into the cooperation path.
- Relationship histories are plain strings without source or tamper evidence.
- Confidence rises from interaction count rather than verified quality or consistency.

### Reflection and resolution claims

- `_resolve_contradictions` relabels pending text as resolved without evidence.
- Reflection clears pending contradictions unconditionally.
- Trust alone can add a persistent goal.
- Affective state is mutated without a visible governance or audit event.
- Reflection consumes memories without filtering for provenance.
- Reflection output does not distinguish hypothesis from verified finding.
- `resolve_tension` marks value tensions resolved from an ID and free-text note alone.
- `repair_rupture` marks continuity ruptures repaired without evidence and awards a positive identity impact.
- These are repeated instances of one root pattern: status changes that assert resolution without a verification gate.

### Carryover and serialization

- `apply_prior_tensions` filters only the exact status `resolved`; it does not validate fields, recompute IDs, or verify provenance.
- `apply_prior_run` reconstructs timeline, milestones, themes, and ruptures through permissive loaders; it trusts summary and coherence values and lacks broad deduplication.
- `apply_prior_threads` has partial ID deduplication but blank IDs bypass it.
- Serialized project threads accept invalid statuses, negative turns, impossible stage indexes, invalid scores, malformed stages, arbitrary categories, and arbitrary revision logs.
- Prior thread carryover does not visibly enforce the active-thread limit.
- Project completion uses proxy signals and never evaluates the stored `success_criteria`.
- A malformed negative stage index combined with empty stages can reach division by zero in `advance`.

## Consolidated repair direction

Before implementation, preserve the shared architecture decisions:

1. Put governance checks before every real state mutation, especially world interactions, task completion, and endogenous actions.
2. Use a shared validation approach for serialized carryover rather than four unrelated ad hoc loaders.
3. Use a shared evidence-backed resolution concept for tensions, contradictions, ruptures, and project completion.
4. Add provenance and verification state to memories, relationship records, revision logs, and resolution events.
5. Make denied, deferred, abandoned, and unresolved outcomes explicit and honest.
6. Add replay and idempotency tests for every carryover method.
7. Preserve the existing action vocabulary and behavior deliberately; do not blindly add every unknown action to an allow-list.
8. Treat any changed method signature as requiring a complete call-site inventory before committing.

## Recommended implementation sequence

1. Inspect current `main` and confirm whether any earlier proposed changes are already present.
2. Create a dedicated repair branch from the verified current `main`.
3. Add regression tests for the confirmed vulnerabilities before or alongside each repair.
4. Implement governance-before-mutation.
5. Implement strict schema validation and provenance for carryover.
6. Repair false-resolution and task-completion semantics.
7. Add replay, idempotency, and malformed-input tests.
8. Run YAML/static checks and the full available test suite.
9. Report exact changed files, commit SHA, test commands, pass/fail output, and remaining failures.
10. Do not merge until the actual diff and evidence have been reviewed.

## Next-Bruce immediate checklist

- Read the continuity index and the preceding September 15 handoff.
- Verify the repository, branch, and current file contents before describing anything as fixed.
- Search for existing tests and call sites before changing method signatures.
- Preserve failures and red tests; do not hide or rewrite them into success.
- Keep the distinction visible: diagnosis is not implementation, and implementation is not verification.
- Keep Civic Continuum, `civiccontinuum.org`, and Washington formation status unchanged: selected/preparation in progress, waiting for funds, not legally formed or purchased unless independently verified.
- Maintain the governing rule: **Reality first. Anomaly second. Follow through.**

This document is a continuity record, not a claim that the repair branch, repairs, tests, or CI already exist.
