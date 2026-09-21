# AquaShield calculations and trade study

These equations check scale and internal consistency. They do not establish
flight safety or medical benefit.

## Water shielding mass

For water density `rho`, covered area `A`, and average thickness `t`:

`m = rho A t` and `sigma = rho t`.

Using `rho = 1000 kg/m^3`:

| Thickness | Areal density | Water mass over 10 m² |
|---:|---:|---:|
| 0.05 m | 50 kg/m² (5 g/cm²) | 500 kg |
| 0.10 m | 100 kg/m² (10 g/cm²) | 1,000 kg |
| 0.20 m | 200 kg/m² (20 g/cm²) | 2,000 kg |

The table is a mass calculation, not a dose-reduction prediction.

## Why a full-size flooded room is not the baseline

A cylindrical water volume of radius 1.5 m and length 3.0 m contains
`pi r^2 L = 21.2 m^3`, or about **21,200 kg of water**. Dedicated launch mass at
that scale is not credible for an early demonstrator. AquaShield therefore uses
existing mission water where possible, a smaller elastic cell, and partial
filling rather than assuming a permanently flooded room.

## Adjustable resistance estimate

A first-order drag estimate is

`F = 0.5 rho Cd Ap v^2`,

where `Cd` is drag coefficient, `Ap` projected area, and `v` relative water
speed. For `Cd=1`, `Ap=0.10 m²`:

| Water speed | Estimated force |
|---:|---:|
| 0.25 m/s | 3.1 N |
| 0.50 m/s | 12.5 N |
| 1.00 m/s | 50.0 N |

Actual limb loading is unsteady and posture-dependent; calibrated force sensors
must replace this estimate in testing.

## Pump and drain checks

Ideal hydraulic power is `P_h = delta_p Q`; electrical input is
`P_e = delta_p Q / eta`. At 40 kPa, 0.010 m³/s, and 60% efficiency, estimated
electrical power is 667 W before thermal-control overhead.

Drain time is `T = V/Q`. Draining 0.50 m³ at 0.025 m³/s takes 20 seconds in the
ideal volume-balance calculation. Real plumbing losses, deformation, trapped
water, valve time, and loss of power must be tested.

## Acceptance criteria for the paper model

- Mass calculations close within 0.5%.
- Energy calculations state efficiency and rejected heat.
- No dose claim is derived only from areal density.
- No exercise claim is derived only from drag force.
- All numerical assumptions are inputs in the public calculator.

