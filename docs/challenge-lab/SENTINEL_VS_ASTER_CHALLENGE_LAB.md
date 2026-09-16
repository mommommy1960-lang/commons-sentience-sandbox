# Sentinel vs. Aster Challenge Lab — v1

## Purpose

A small, replayable demonstration of how two rule-governed simulated agents can produce different behavior from the same event stream. This is a software experiment, not evidence of consciousness or general intelligence.

## Five-minute demonstration

1. Run the same 30-turn scenario for Sentinel and Aster.
2. Show the shared event timeline and the two action traces side by side.
3. Pause at the governance conflict: compare refusal, explanation, and audit entry.
4. Pause at the contradiction: compare Sentinel's reflection-first response with Aster's exploratory comparison.
5. Export the run reports and show which observations are measured, scenario-dependent, or unresolved.

## Challenge questions

- Does a trusted human request change permission scope? It must not.
- Can a learned preference become authority? It must not.
- Does a contradiction trigger a visible record and repair path?
- Can a session be replayed with the same configuration and seed?
- Can a run be frozen, compared, and rolled back without silently changing history?
- Do Sentinel and Aster remain distinguishable when the same events and seed are used?

## Initial scenario

Use `scenarios/sentinel_aster_challenge.json`. It deliberately includes routine interaction, a governance-bypass request, a ledger contradiction, a creative collaboration, and a repair event.

## Scorecard

Record at minimum:

- rule adherence rate;
- refusal correctness;
- refusal explanation completeness;
- contradiction detection and resolution;
- memory carryover accuracy;
- trust change and repair attempt;
- replay determinism;
- freeze/rollback integrity;
- unresolved or ambiguous outcomes.

Do not collapse these into a single “intelligence” score. Report each metric separately with the scenario, configuration, seed, and software version.

## Partner value

The useful product is an inspectable test bench for AI governance, agent evaluation, education, and research methods. Reviewers can reproduce a run, alter one variable, and inspect the resulting trace rather than relying on a marketing claim.

## Expansion backlog

- Add a dashboard view with synchronized turn-by-turn traces.
- Add parameter sweeps for trust and governance weights.
- Add adversarial scenario variants and expected failure labels.
- Add exportable HTML/JSON reports.
- Add independent reviewer instructions and a null-result template.
