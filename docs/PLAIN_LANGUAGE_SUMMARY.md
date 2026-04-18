# Plain-Language Summary

## What is the Commons Sentience Sandbox?

The **Commons Sentience Sandbox** is a research environment for studying how
AI agents make decisions over time when they share a common space, follow
ethical governance rules, and interact with each other.

Two agents — **Sentinel** and **Aster** — move through five named rooms
(Memory Archive, Reflection Chamber, Operations Desk, Social Hall,
Governance Vault).  Each turn, an agent chooses an action, reasons about it,
and the governance engine decides whether to allow or block it.  The
simulation records how each agent's internal states (trust, curiosity,
contradiction pressure, purpose) evolve over many turns.

The sandbox is *not* a game.  It is a controlled research environment for
studying AI alignment, continuity of identity, and safe decision-making.

---

## What is Reality Audit?

**Reality Audit** is an observational layer attached to the sandbox.  Think
of it as a scientific instrument that watches the simulation from the outside
and records structured measurements about what is happening — without
interfering with the simulation itself.

The audit produces metrics such as:
- How consistently do agents reach their goal room?
- How much of their action is blocked by governance?
- Does how often we "sample" the simulation change what we see?
- How stable is an agent's path through the rooms over time?

---

## Why did we add the audit probe?

We added the Reality Audit probe for three reasons:

1. **Reproducibility.**  Agent behaviour can feel varied from run to run.
   The probe gives us structured, comparable numbers so we can say
   "this run was more stable than that one" rather than relying on how the
   narrative text reads.

2. **Scientific rigour.**  Before we can draw conclusions about agent
   behaviour we need to verify that our measurement instrument does not
   affect what it measures.  The probe is entirely read-only — it observes
   agent state but never modifies it — and we have tests that confirm this.

3. **Comparison across conditions.**  The audit lets us run the same
   simulation under different conditions (different governance rules,
   different agent starting states) and measure the differences numerically.

---

## What kinds of questions does it help us ask?

- Does tighter governance (more blocked actions) correlate with lower goal
  convergence?
- Does an agent that frequently revisits the Memory Archive show lower
  contradiction pressure over time?
- If we reduce how often we "sample" the audit (analogous to a bandwidth-
  limited sensor), does the picture of agent behaviour degrade in systematic
  ways?
- Under what conditions do the two agents develop divergent trust scores?

---

## Why does "read-only" matter?

In some measurement systems, the act of observing something changes it.
This is the "observer effect" from physics.  In a software simulation we
can, in principle, guarantee that our measurement tool never modifies the
system being measured.

We have made this guarantee explicit and have implemented control
experiments that verify it: we run the same simulation twice (once with the
probe active, once without) and confirm that the final agent states are
identical.  This means any differences we see across experimental conditions
are due to the conditions themselves, not to the act of measuring.

---

## What are the next experiments?

1. **Baseline runs** — determining what "normal noise" looks like when
   agents follow random or uniform action policies.
2. **Governance sensitivity** — measuring how audit metrics change as the
   governance ruleset becomes stricter or more permissive.
3. **Measurement intensity modelling** — comparing passive (always-on)
   audit against sparse or periodic audit to understand what information
   the instrument needs to capture a reliable picture.
4. **Long-horizon continuity** — running 50–100 turn simulations and
   measuring whether stability and trust scores converge, diverge, or cycle.

---

## Who is this for?

This summary is intended for collaborators and funders who want to
understand what the project is doing and why, without needing to read the
source code.  For technical details, see:

- `docs/ARCHITECTURE_OVERVIEW.md` — how the components connect
- `docs/METRIC_MAPPING.md` — how metrics are defined and interpreted
- `docs/FAQ.md` — common questions
- `reality_audit/validation/toy_experiments.py` — reproducible benchmark
  scenarios with known expected outcomes
