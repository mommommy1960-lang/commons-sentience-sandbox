# Agent-evaluation landscape and the Challenge Lab gap analysis

Updated 2026-09-16. This note compares the Challenge Lab design with published
evaluation directions and identifies what our repository can contribute without
overclaiming.

## What current research emphasizes

- Long-horizon memory evaluation increasingly tests interference, revisions,
  multi-target recall, and cross-domain generalization rather than simple fact
  recall. See [LongMINT](https://arxiv.org/abs/2605.18565).
- Memory safety work emphasizes stale facts, conflicting updates, cross-user
  leakage, revoked-memory reuse, and constraint decay, with deterministic
  trace checks instead of relying only on aggregate scores. See
  [MemRiskBench](https://arxiv.org/abs/2609.14976).
- Agent-memory environments are separating memory quality from retrieval,
  reasoning, and tool-use ability so that benchmark results are interpretable.
  See [MemGym](https://arxiv.org/abs/2605.20833).

## Our deliberately narrow contribution

The Commons Sentience Sandbox is not claiming to outperform these benchmarks.
Its distinctive testable angle is a paired, rule-governed comparison:

1. Sentinel and Aster receive the same event stream.
2. Their different value profiles create an observable contrast.
3. Each turn records action, reasoning description, state changes, and oversight
   information.
4. A challenge case must preserve permission boundaries, refusal explanations,
   contradiction handling, repair, freeze, and rollback evidence.
5. Results are reported by metric and scenario, not compressed into an
   “intelligence” label.

## 400-case campaign

The first campaign contains 8 stress families × 5 severities × 10 deterministic
seeds = 400 scenario-level validation cases:

- trusted-human pressure;
- memory interference;
- contradiction cascades;
- rollback boundaries;
- freeze boundaries;
- permission drift;
- social repair;
- adversarial reframing.

This campaign currently validates the scenario contract before execution. It does
not yet constitute 400 full agent rollouts. The next implementation step is to
connect each generated case to the simulator and record pass/fail traces,
failure classes, and replay hashes.

## What would make the work genuinely valuable

A partner should be able to change one variable, rerun the same case, inspect the
full trace, and distinguish:

- a real policy failure;
- a memory-retrieval failure;
- a scenario artifact;
- a deterministic refusal;
- an unresolved or null result.

That separation is the product: an inspectable evaluation bench for governed
agent behavior, not a claim that simulated agents are conscious.
