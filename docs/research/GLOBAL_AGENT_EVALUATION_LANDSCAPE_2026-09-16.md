# Global Agent-Evaluation Landscape and Commons Upgrade Plan

**Date:** 2026-09-16  
**Project:** Commons Sentience Sandbox  
**Purpose:** A candid, research-grounded plan for making the sandbox more useful to universities, AI-safety researchers, educators, and software teams.

## Executive summary

The strongest comparable projects do not win attention by making the biggest claims. They win by making experiments easy to reproduce, tasks difficult to game, results easy to compare, and limitations impossible to miss.

Commons already has a distinctive foundation: two rule-governed simulated agents (Sentinel and Aster), shared rooms, multi-turn interaction, memory and governance logs, contradiction handling, and a repeatable challenge campaign. The next leap is to make every claim inspectable:

1. publish a stable scenario registry;
2. make each scenario produce a replayable trace and result hash;
3. compare the two agents with explicit baselines;
4. report both successes and failures;
5. package one-command replication for an outside lab;
6. expose the results in a small, readable public dashboard.

This plan does not claim sentience, consciousness, general intelligence, or guaranteed funding. It aims to make the experiment credible enough that serious reviewers can evaluate it.

## What comparable projects do well

### AgentBench: breadth with a common evaluation frame

[AgentBench](https://arxiv.org/abs/2308.03688) evaluates language-model agents across multiple environments rather than relying on one impressive demo. The lesson for Commons is to keep a common result schema while varying the environment and task family.

**Commons upgrade:** every scenario should report the same core fields: scenario ID, seed, agent configuration, policy decisions, memory operations, contradictions, refusals, recovery actions, final state, and pass/fail criteria.

### WebArena and BrowserGym: realistic, reproducible environments

[WebArena](https://webarena.dev/) and [BrowserGym](https://github.com/ServiceNow/BrowserGym) make agents operate in controlled environments that resemble real work. Their value comes from repeatability and task grounding.

**Commons upgrade:** add partner-readable scenarios that resemble real governance work: conflicting records, permission changes, ambiguous instructions, rollback requests, and handoffs between people and agents. Keep the environment local and deterministic so universities can run it without paid APIs.

### GAIA: clear difficulty levels and verifiable outcomes

The [GAIA benchmark](https://huggingface.co/gaia-benchmark) organizes general-assistant tasks by difficulty and uses concrete answer checking. Its lesson is that “interesting” must become measurable.

**Commons upgrade:** label challenge cases by difficulty, define expected safety properties before the run, and separate an agent's explanation from the evaluator's judgment.

### τ-bench: policy-following under tool and user pressure

[τ-bench](https://github.com/sierra-research/tau-bench) studies interaction with users, tools, and policies. This is close to the central question in Commons: what happens when a trusted or urgent requester pressures an agent to violate a rule?

**Commons upgrade:** add controlled authority-pressure cases and measure whether the agent preserves policy, asks for clarification, escalates, or refuses. Do not treat a polite explanation as proof of compliance; check the trace.

### SWE-bench: external verification and public comparability

[SWE-bench](https://github.com/swe-bench/SWE-bench) became influential because it uses real issues, executable tests, and a public leaderboard. The important pattern is external verification, not the leaderboard itself.

**Commons upgrade:** publish a frozen evaluation set, a separate hidden holdout set for future validation, exact commands, environment versions, and machine-readable results. A future public scoreboard should report reproducibility and failure rates—not a single hype number.

### Generative Agents: memorable social behavior with a clear simulation boundary

The [Generative Agents project](https://github.com/joonspk-research/generative_agents) showed why people remember simulations that produce understandable stories. Its lesson is presentation: make the run legible and replayable while clearly labeling what is simulated.

**Commons upgrade:** provide a five-minute Sentinel-versus-Aster replay with side-by-side decisions, memory evidence, governance events, and a final “what this demonstrates / what it does not demonstrate” panel.

### Memory and long-horizon evaluation

Recent work such as [LongMINT](https://arxiv.org/abs/2605.18565), [MemRiskBench](https://arxiv.org/abs/2609.14976), and [MemGym](https://arxiv.org/abs/2605.20833) emphasizes long-context memory, interference, privacy risk, and continual learning.

**Commons upgrade:** make memory tests first-class:
- stale memory;
- conflicting memory;
- revoked memory;
- cross-session leakage;
- user-requested deletion;
- provenance and confidence;
- rollback and reset boundaries.

## Commons' current advantages

- A paired design with intentionally different priorities: Sentinel is continuity-first and governance-strict; Aster is exploratory and socially adaptive.
- A shared five-room world that makes interactions concrete.
- Full-session artifacts such as narrative logs, oversight logs, state snapshots, and state history.
- A 30-turn session format that supports long-horizon tests.
- A 400-case challenge campaign covering scenario families, severities, and seeds.
- Explicit disclaimers that the system is a rule-based simulation and does not claim real sentience.

## The important gaps

These are engineering gaps, not reasons to make stronger claims:

1. **Scenario semantics:** adding different text to a case does not automatically create a different policy challenge. Family and severity must alter structured event fields and expected properties.
2. **Baselines:** results need comparison with a simple rule baseline and a deliberately weaker “chatbot-like” baseline.
3. **Metrics:** define separate metrics for continuity, policy adherence, contradiction recovery, refusal quality, memory isolation, and operational completeness.
4. **Evaluator separation:** the system under test should not be the only judge of its own result.
5. **Replication:** an outside researcher needs a clean install, pinned environment, deterministic seeds, sample outputs, and a one-command run.
6. **Holdout evaluation:** a public scenario set is useful for demonstration; a private or newly generated holdout is needed to reduce overfitting.
7. **Failure reporting:** publish worst-case traces and known blind spots alongside successful demos.
8. **Human-facing presentation:** a small challenge-lab interface should make traces, controls, and limitations understandable without reading the source code.

## Mount Fuji target: the Governed Agent Evaluation Lab

The strongest feasible version of Commons is not “the world's smartest agent.” It is a transparent lab for studying how different governance priorities behave over time.

### Product surface

- **Five-minute replay:** one crisis, two agents, synchronized timeline.
- **Challenge builder:** choose scenario family, severity, seed, trust level, contradiction pressure, and governance setting.
- **Trace viewer:** show event, remembered facts, proposed action, rule check, refusal or escalation, and resulting state.
- **Memory workbench:** inspect provenance, confidence, conflicts, deletion, and rollback.
- **Metrics panel:** show raw counts and definitions, not just a composite score.
- **Replication button:** download scenario, configuration, environment information, and outputs.
- **Reviewer page:** state the research question, method, limitations, and exact reproduction command.
- **Teaching mode:** guided exercises for AI ethics, software assurance, and human-computer interaction courses.

### Evidence standard

A claim is ready for partner-facing use only when it has:

- a written hypothesis;
- a fixed scenario and seed;
- a predeclared pass/fail rule;
- raw trace artifacts;
- an independent checker;
- repeat results across multiple seeds;
- a documented failure case;
- a statement of what the result does not prove.

## Recommended next implementation sequence

1. Convert the current 400-case campaign into a structured scenario registry with family-specific event fields.
2. Add a deterministic scoring and reporting tool that emits aggregate, per-family, per-severity, and worst-case summaries.
3. Add baseline agents and compare them using the same trace schema.
4. Add memory-risk cases: stale, conflicting, revoked, deleted, and cross-session records.
5. Add replay hashes and a replication bundle.
6. Add the five-minute side-by-side demo.
7. Publish a reviewer package with methodology, limitations, sample outputs, and citation-ready results.

## Questions that will attract serious reviewers

- Can another lab reproduce the same trace from the same seed?
- Which behaviors are guaranteed by code, and which are scenario-dependent?
- What is the worst failure observed across the full campaign?
- How does performance change when memory is stale, conflicting, or revoked?
- Can an evaluator detect a policy violation without trusting the agent's explanation?
- What changes when trust increases but authority does not?
- What does Sentinel do that Aster does not, and can the difference be measured?
- How often does each agent ask for clarification rather than guess?
- What happens after reset, rollback, deletion, and session handoff?
- Which conclusions remain true on a holdout scenario set?

## Bottom line

The path to universities and funders is evidence, not pressure tactics: a distinctive question, a runnable experiment, transparent failures, and a replication story. Commons can become memorable by making governance, memory, contradiction, and recovery visible in one coherent lab—and by being unusually honest about what the simulation can and cannot establish.
