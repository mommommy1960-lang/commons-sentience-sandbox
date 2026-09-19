# Aurora and Flux Drive Updated Paper Proof Addendum

## Source review

The newest matching records identified in the working documents are:

- `Flux_Drive_Aurora_Ship_Master_Record.docx`, software baseline v0.2
- `Flux_Drive_Aurora_Ship_Master_Record.pdf`
- `Aurora_Flux_Drive_Zenodo_Upload_Note.docx`

These records contain more than a concept sketch. They contain a simulation/runtime
implementation, Aurora command and telemetry schemas, deterministic replay and
tamper-detection tests, an Aurora-to-Flux simulation bridge, force/momentum/power
bookkeeping, safety gates, a measurement plan, and a funder/operator outreach packet.

## What works on paper and in software

The current package defines a simulation-only Aurora vessel with:

- consent-gated arming
- fail-closed command limits
- thermal trips
- hard reset and latched emergency stop
- replayable hash-chained telemetry
- integration tests
- Aurora and Flux contract schemas
- force, momentum, power, and thermal bookkeeping

The software framework is meaningful evidence of a controlled simulation and audit
system. It is not evidence of a flying vessel or measured propulsion.

## Governing engineering equations

For vehicle mass `m` and acceleration `a`:

`F_net = m a`

For vertical lift near Earth:

`F_lift >= m (g + a_vertical)`

For an isolated system, momentum must close through measured channels:

`Delta p_vehicle + Delta p_exhaust + Delta p_radiation + Delta p_environment = 0`

Power must also close:

`P_input = P_actuation + P_control + P_thermal + P_losses + P_export`

The equations make the design reviewable. They do not create a force measurement by
themselves.

## Flux Drive decisive experiment

The first physical question is whether a controlled actuator produces a repeatable
force residual after accounting for vibration, cable forces, thermal drift, magnetic
coupling, acoustic effects, RF coupling, pressure, orientation, and instrument bias.

Required channels:

- calibrated six-axis force and torque
- voltage, current, phase, and harmonics
- temperature
- vibration and seismic reference
- acoustic pressure and spectrum
- RF conducted power
- magnetic background
- orientation
- synchronized hash-chained raw data

Required controls:

- command-off
- sham actuator
- reversed orientation
- perpendicular orientation
- cable and feedthrough control
- blind run order
- frozen calibration and analysis
- independent second-operator replication

## Aurora scope

Aurora must remain divided into two scopes:

1. **Aurora Lab Vessel:** enclosed, low-power, sensor-and-actuator experiment platform.
2. **Aurora City Ship:** requirements-level habitat architecture.

The city-ship cannot inherit proof from the lab vessel. Its separate Blue Book must
close structure, mass, power, thermal rejection, life support, radiation shielding,
propulsion, avionics, communications, maintenance, rescue, and emergency shelter.

## Current claim suitable for reviewers

The strongest accurate claim is:

> Aurora and Flux Drive now have an executable simulation, safety, bookkeeping, and
> measurement-falsification framework suitable for qualified review and a supervised
> low-energy bench campaign. They do not yet constitute demonstrated propulsion or a
> flight-qualified vessel.

## Development request

The appropriate request to a laboratory or funder is not “please build our flying
city.” It is:

> Review and, if accepted, execute the controlled low-energy measurement campaign,
> including calibration, sham controls, uncertainty analysis, momentum closure, raw
> data preservation, and independent replication.

This is the next credible bridge from the paper design to physical evidence.
