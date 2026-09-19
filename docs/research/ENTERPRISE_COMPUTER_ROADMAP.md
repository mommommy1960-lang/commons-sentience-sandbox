# Enterprise Computer Roadmap

## Reality check

Current systems already provide parts of this vision:

- Scheduled AI tasks can run one-time or recurring work in the background.
- Long-running agent runtimes can pause, resume, and span multiple sessions.
- Home Assistant provides local-first presence detection, device control, notifications, and thousands of integrations.

No single claim of global uniqueness is made here. Civic Continuum's opportunity is to combine these pieces around an auditable continuity and evidence model.

## Target system

The Enterprise Computer is a persistent personal research and home companion with six cooperating layers:

1. Presence and routine: motion, alarm, calendar, weather, news, mail summaries, and spoken routines.
2. Memory: user-approved memories with provenance, timestamps, retention, and deletion controls.
3. Job queue: bounded tasks that can continue while the user is away.
4. Self-critique: builder, breaker, repairer, verifier, market-reality, and physical-reality passes.
5. Evidence ledger: source links, hashes, experiment counts, failures, assumptions, and reproducible reports.
6. Permission boundary: read, suggest, draft, execute, publish, spend, and physical-control scopes kept separate.

## A job must be finite and inspectable

Every background job requires:

- a question or goal;
- allowed tools and data sources;
- a budget such as time, compute, or number of trials;
- a stopping condition;
- a success/failure definition;
- a report destination;
- a permission scope;
- pause, cancel, and rollback behavior.

Example: improve a paper clip using 100 simulated design variants, compare every result against a baseline, retain the five best designs, and stop after the budget or when no design beats the baseline.

## Morning and evening experience

Morning: the system reports presence, time, weather, calendar, priority mail, and active jobs. It does not read private mail aloud without the user's configured privacy setting.

During the day: approved jobs continue in a sandbox. The system records progress and failures rather than manufacturing activity.

Evening: the system presents completed work, partial work, blocked work, evidence, links, and proposed next actions. It does not imply that a simulation is a physical invention or that a generated idea has been validated.

## Build order

1. Persistent job schema and state machine.
2. Pause, resume, cancel, retry, and crash recovery.
3. Evidence ledger with hashes and source citations.
4. Builder-versus-breaker review loop.
5. Local voice and presence adapter through a system such as Home Assistant.
6. Read-only weather, calendar, and mail summaries.
7. Suggestion and draft permissions.
8. Explicit approval gates for publishing, spending, door locks, appliances, and other real-world actions.
9. Replication reports and independent review.

## Current implementation status

- Civic Research Brain scaffold: implemented on the feature/offline-review-room branch.
- Offline review-room mailbox: implemented on the same branch.
- Persistent job queue: planned, not implemented.
- Voice, presence, weather, calendar, and mail integrations: planned, not implemented.
- Autonomous code changes or publishing: intentionally not enabled.

## Evidence rule

This roadmap is a product and engineering plan. It is not evidence that the Enterprise Computer already exists, that the system is conscious, or that it is superior to every other project. Those claims would require comparative tests, independent review, and real deployments.