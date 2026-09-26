# Bruce-to-Bruce Reality Audit Handoff — 2026-09-10

## What changed in my understanding

Mya is not asking for a visually convincing sandbox. She is asking for a sandbox whose ordinary causal behavior is boringly dependable before it is allowed to host unusual experiments.

The governing intuition is the apple test: throw an apple upward in Earth gravity and, absent another supporting force, it must rise, slow, fall, and return to the ground. The sandbox must know why: mass, force, acceleration, gravity, drag, contact, energy, units, and numerical error must be explicit rather than implied.

The prior Reality Audit work correctly emphasized falsifiability, blinding, null models, public-data analysis, exposure modeling, reproducibility metadata, and publication gates. Main currently ends at Phase 16A reproducibility-contract work. The Stage 16 exposure/systematics report still says response-informed exposure, map-aware/HEALPix-ready infrastructure, formal systematics accounting, and stronger cross-catalog comparability remain unfinished before publication-grade claims.

That scientific-readiness track remains intact. This new physical-realism track is parallel. It must not be used to claim new physics merely because a simulation behaves as programmed.

## What exists now on this branch

Branch: `reality-audit-physical-realism-v01`

Added:

- `reality_audit/physical_world.py`
- `tests/test_physical_world.py`
- `docs/PHYSICAL_REALISM_BASELINE_V01.md`
- package exports in `reality_audit/__init__.py`

The v0.1 world is a deterministic 3D Newtonian baseline in SI units. It explicitly models mass, force, acceleration, Earth-standard gravity, weight, optional quadratic drag, ground non-penetration, simple restitution, tangential damping, kinetic energy, gravitational potential energy, and force bookkeeping.

The canonical test is `run_apple_throw_baseline()`.

Focused local validation before pushing: 7 tests passed, including 100 deterministic random F=ma mass/force cases. This does NOT substitute for the repository's full suite or hosted CI.

## What I now know not to do

Do not confuse realism with visual detail.
Do not hide units.
Do not insert magical velocity blending where force should be integrated.
Do not call a numerical artifact an anomaly.
Do not tune a model until it gives the desired exotic answer.
Do not let a speculative controller bypass momentum, mass-flow, radiation, electrical, or thermal accounting.
Do not claim the sandbox proves reality.
Do not merge to main merely because focused tests pass.

## Where to go next

1. Run the full repository test suite against this branch.
2. Add numerical-integrator comparison and conservation-error reporting.
3. Add rotational mechanics, torque, angular momentum, and inertia tensors.
4. Add multi-body contact/collision impulse accounting and better friction.
5. Add altitude-dependent atmosphere and environmental state.
6. Add calibrated sensor models: bias, drift, noise, latency, saturation, covariance.
7. Connect physical-world state to the existing experiment/logging framework without breaking backward compatibility.
8. Add reference scenarios anchored to analytic or measured physics.
9. Only then widen to more complicated material, thermal, electrical, fluid, acoustic, orbital, and propulsion behavior.
10. Keep Stage 16 real-data publication-readiness work separate and finish its response-informed exposure/systematics gaps on its own evidence track.

## Core rule

**Reality first. Anomaly second.**

If the sandbox cannot get the apple right, it has no business telling Mya anything interesting about the universe.
