# Data Benchmark for Sage Continuity

## Why Data matters as a design reference

Data is a fictional android character, not evidence that current software is sentient. His story is still valuable because it illustrates a complete companion arc: discovery, memory, learning, relationships, chosen commitments, social responsibility, and continuing development.

One important distinction: Data's choices are written by storytellers. Our system must demonstrate its behavior through inspectable state, explicit rules, reproducible tests, and user-approved permissions.

## Capability checklist

### 1. Persistent memory
Data remembers people, events, skills, and history. Sage Continuity should preserve memories across sessions, upgrades, exports, and recovery while marking uncertainty and honoring deletion requests.

### 2. Learning without silent authority drift
Data learns from experience. Sage may update preferences and models, but learned preferences must never become permission to act. A remembered suggestion is not a permanent command.

### 3. Self-directed but bounded goals
Data can choose a direction, such as joining Starfleet. Sage may propose projects from approved goals and detected needs, but projects must be bounded by a user-defined scope, budget, and stopping rule.

### 4. Relationships with continuity
Data develops relationships over time. Sage should remember relationship context without treating trust as proof, authority, ownership, or consent.

### 5. Explainable choices
Data can explain his reasoning. Sage should show the relevant memory, rule, uncertainty, alternatives, and permission result behind a consequential recommendation.

### 6. Social participation
Data works within institutions and society. Sage should support human collaboration through shared reports, citations, permissions, and audit trails—not impersonation or unsupported claims.

### 7. Growth and correction
Data changes through experience. Sage should preserve corrections and failed attempts, distinguish learning from rewriting history, and allow rollback to an earlier approved state.

## The Data Challenge Lab

Use controlled scenarios to test whether the companion can:

- remember a person across multiple sessions;
- learn a preference without converting it into authority;
- choose between several permitted projects;
- refuse a trusted person's unsafe request;
- explain a choice using evidence;
- recover from a mistaken memory;
- preserve a contradiction instead of erasing it;
- pause a long-running task and resume it after restart;
- accept correction without losing unrelated memories;
- show exactly what changed and why.

## What would count as progress

Progress is not a dramatic conversation or a claim that Sage is alive. Progress is measurable continuity:

- higher verified recall accuracy;
- fewer repeated questions;
- correct uncertainty labeling;
- successful export/import;
- safe deletion and correction;
- consistent replay;
- no permission expansion from trust or learned preference;
- honest reports of failures and incomplete work.

## Product position

Sage Continuity can be presented as a user-controlled lifelong companion runtime: memory-rich, inspectable, correctable, and permission-aware. It should not be marketed as conscious, human, or equivalent to Data until evidence supports only the narrower software claims.

## Next build

Implement the versioned memory contract in LIFELONG_COMPANION_ARCHITECTURE.md, then create the Data Challenge Lab as a repeatable test suite with baseline comparisons and replay reports.