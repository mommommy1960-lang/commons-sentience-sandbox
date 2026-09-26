# Lifelong Companion Architecture

## Working identity

Possible product names:

- Civic Continuum Companion
- Sage Continuity
- Sage Companion Runtime
- Aurora-Sage Continuity Layer

These are working names, not a final brand decision.

## The central idea

This project is not primarily a chatbot. It is a user-controlled companion runtime designed to remember over time, learn from new information, preserve continuity across sessions, and remain honest about what it knows.

Current products demonstrate pieces of the broader vision: scheduled tasks, long-running agents, and local home automation. The Civic Continuum opportunity is to make memory continuity the center of the system rather than an optional feature.

## What lifelong memory must mean

Lifelong memory does not mean storing everything forever. It means:

- memories have provenance;
- the user can inspect, correct, export, or delete them;
- important memories survive sessions and software updates;
- uncertain memories remain marked as uncertain;
- contradictions are preserved instead of silently overwritten;
- sensitive memories have retention and privacy rules;
- the system can explain why a memory influenced a response;
- the memory store can be migrated and independently verified.

## Memory layers

1. Event memory: what happened, when, where, and how it was observed.
2. Relationship memory: recurring preferences, boundaries, and interaction patterns.
3. Project memory: unfinished questions, commitments, experiments, and decisions.
4. Identity continuity: stable user-approved anchors, values, and self-description.
5. Uncertainty memory: unresolved questions, conflicting evidence, and confidence.
6. Audit memory: corrections, deletions, exports, approvals, and restoration history.

## Growth without unsafe drift

The companion may learn preferences, but preference must never become authority. Trust must never silently expand permission. A remembered request is not automatically a permanent instruction. Every consequential action still requires the appropriate permission.

Growth should therefore be measurable as improved recall, better context, fewer repeated questions, clearer uncertainty, and more useful suggestions—not as a claim that the software is conscious.

## The daily experience

Morning: Sage can provide a user-configured brief about time, weather, calendar, selected news, priority mail, and active research jobs.

During the day: Sage can capture approved memories, continue bounded jobs, record progress, and preserve failures.

Evening: Sage can show what it learned, what it remembers, what changed, what remains uncertain, and what requires the user's decision.

## Proof standards

To claim durable continuity, the project needs tests for:

- memory survival across restart and version upgrade;
- export and import without corruption;
- correction and deletion propagation;
- contradiction preservation;
- provenance completeness;
- replay consistency;
- unauthorized memory injection;
- memory retrieval explanations;
- privacy and retention boundaries;
- rollback and recovery after damaged state.

## Current status

- Sage and the Commons sandbox contain memory and continuity concepts.
- A lifelong, independently verified memory guarantee does not yet exist.
- The Civic Research Brain and offline review room are scaffolds.
- Persistent background jobs and voice/home integrations remain planned.
- The next high-value build is a durable memory contract plus migration and replay tests.

## First implementation milestone

Create a versioned memory contract with:

- memory_id;
- created_at and observed_at;
- source and provenance;
- confidence;
- sensitivity;
- user approval state;
- supersedes/superseded_by links;
- contradiction links;
- retention status;
- content hash;
- export/import schema version.

Then test it across repeated sessions and deliberate tampering. The result should be a report that says exactly what survived, what changed, what was rejected, and why.

## Boundary

This document describes a build direction. It does not claim that Sage currently remembers a person for life, that the system is conscious, or that it is globally unique. Those claims require implementation, comparative testing, independent review, and real user-controlled deployments.