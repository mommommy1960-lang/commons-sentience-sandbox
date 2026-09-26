# Reality Audit Physical Realism Baseline v0.1

## Purpose

This is the first conservative reality-anchor layer for the Reality Audit sandbox. The goal is simple: before the sandbox is asked to evaluate unusual, emergent, or speculative behavior, it must reproduce ordinary physical causality in a transparent, testable way.

This track runs in parallel with the Stage 16 real-data / exposure-modeling work. It does not replace the Stage 16 publication-readiness roadmap and it does not constitute experimental evidence about the physical universe.

## What v0.1 models

All quantities use SI units.

- 3D position and velocity
- mass
- Newtonian force and acceleration (`F = ma`)
- Earth-standard gravitational acceleration by default (`9.80665 m/s^2` downward)
- weight (`m g`)
- optional quadratic aerodynamic drag
- ground non-penetration
- simple restitution / bounce
- simple tangential damping at ground contact
- kinetic energy
- gravitational potential energy relative to the contact plane
- explicit force bookkeeping for gravity, drag, external force, normal force, and net force

The numerical integrator is semi-implicit Euler. It is intentionally simple and auditable.

## Canonical reality-anchor: the apple test

`run_apple_throw_baseline()` encodes the ordinary proposition that motivated this track:

> Throw an apple upward in Earth gravity and, absent another supporting force, it rises, slows, reaches an apex, falls, and returns to the ground.

With drag disabled, the simulation is checked against the analytic vacuum results:

- apex height: `v0^2 / (2 g)`
- round-trip flight time: `2 v0 / g`

With drag enabled, the simulated apex must be lower than the vacuum apex for the same launch state.

This test is intentionally boring. Boring is the point. A sandbox that cannot get the apple right has no business being trusted with exotic conclusions.

## Current test contract

The first test file verifies:

1. weight equals mass times gravitational acceleration;
2. free-fall acceleration is independent of mass when drag is disabled;
3. applied force produces `a = F / m` when gravity is disabled;
4. a resting body does not fall through the ground plane;
5. an upward-thrown apple returns to the ground and agrees closely with analytic vacuum apex and flight time;
6. drag lowers the apple's apex relative to vacuum;
7. 100 deterministic random mass/force cases satisfy `F = ma`.

## What this does NOT model yet

v0.1 is not a high-fidelity digital twin of Earth. It does not yet include:

- rotational rigid-body dynamics / torque / inertia tensors
- multi-body collision resolution
- static vs kinetic friction models
- deformable bodies or fracture
- fluids, buoyancy, turbulence, or CFD
- thermodynamics / heat transfer
- electromagnetism
- acoustics
- orbital mechanics / nonuniform gravity fields
- relativistic dynamics
- quantum dynamics
- material constitutive models
- detailed atmosphere varying with altitude, humidity, temperature, or weather
- numerical uncertainty budgets across integrators

Those belong in later layers and must be added one class of physics at a time with analytic, laboratory, or authoritative benchmark anchors.

## Design rule going forward

**Reality first, anomaly second.**

Every new physical subsystem should ship with:

- units and sign conventions;
- conservation / balance laws where applicable;
- at least one analytic or canonical benchmark;
- failure tolerances;
- deterministic replay;
- explicit model limits;
- provenance for constants and assumptions;
- tests that try to falsify the implementation rather than merely demonstrate it runs.

The sandbox is not allowed to call a behavior anomalous until ordinary-model error, numerical error, sensor/model artifacts, and known physical explanations have been bounded well enough for the claim being considered.

## Next realism layers

The highest-value next additions are:

1. rotational mechanics and torque;
2. multi-body contact and collision impulse accounting;
3. improved friction and constraints;
4. atmosphere model plus drag as a function of altitude / density;
5. thermal and electrical energy ledgers;
6. sensor models with calibration, bias, drift, noise, latency, saturation, and covariance;
7. propulsion bookkeeping that closes force, momentum, mass flow, radiation momentum, electrical power, and thermal paths;
8. numerical-integrator comparison and uncertainty ledger;
9. reference scenarios tied to measured or analytic Earth physics.

The physical realism track should remain bounded and falsifiable. Passing a sandbox benchmark proves the implementation matches that benchmark within tolerance. It does not prove a novel physical effect exists in reality.
