# Programmable Fiber-Optic Vehicle Surface — Engineering Blue Book v1

**Owner:** Mya P. Brown, Civic Continuum  
**Status:** paper-stage feasibility specification  
**Evidence level:** ordinary-physics architecture; no tested coupon, vehicle installation, certification, or road approval  
**Public disclosure:** sanitized engineering brief; protected geometry, fabrication drawings, supplier terms, and patent-sensitive implementation details excluded

## 1. Claim boundary

This project proposes a removable, programmable illuminated surface made from flexible optical or light-distribution elements mounted over a stationary curved panel. It does not presently establish a road-legal vehicle body display, optical camouflage, structural body replacement, autonomous signaling system, or certified lighting device.

The first defensible result is a 600 mm by 600 mm stationary coupon that demonstrates controlled appearance, bounded power and temperature, environmental sealing, fault-safe shutdown, and repairable modular construction.

## 2. Product decomposition

The concept is separated into three layers:

- **AURORA VISAGE:** the visible non-structural appearance layer.
- **CHROMASKIN:** the removable illuminated optical panel or textile-like laminate.
- **AURORA SURFACE OS:** the bounded controller, diagnostics, content policy, and fault-state logic.

These names describe system roles. They do not imply validated performance.

## 3. Ordinary physical mechanism

The baseline architecture uses established components:

1. a non-structural flexible substrate;
2. side-emitting polymer optical fibers or distributed light guides;
3. edge-coupled RGB or RGBW LED sources;
4. local optical mixing/diffusion;
5. segmented driver electronics;
6. temperature and current sensing;
7. a sealed low-voltage harness;
8. a controller that defaults to a dark or fixed compliant state on fault.

Photonic fibers below roughly 300 micrometers have been woven into flexible display textiles in published research. This supports material plausibility, not automotive durability or certification.

The first coupon does not need high-resolution video. It needs independently addressable zones capable of repeatable color and intensity states.

## 4. Optical model

For one illuminated segment, a first-order guided-power model is

[
P_{mathrm{out}}(L)=eta_c P_{mathrm{LED}}e^{-alpha L},
]

where:

- (P_{mathrm{LED}}) is optical power produced by the source,
- (eta_c) is coupling efficiency,
- (alpha) is the effective attenuation coefficient,
- (L) is the optical path length.

A deliberately side-emitting fiber distributes part of the guided light over length. If the effective extraction coefficient is (eta), the emitted power per unit length is approximated by

[
q(x)=etaeta_cP_{mathrm{LED}}e^{-(alpha+eta)x}.
]

Uniform appearance cannot be assumed. It must be designed by controlling source injection, fiber spacing, extraction treatment, reflectors, diffusers, and segment length. Coupon acceptance therefore uses measured luminance uniformity:

[
U_L=rac{L_{min}}{L_{mathrm{avg}}},
]

reported with the full luminance map. The initial engineering target is (U_Lge 0.70) within each intended uniform zone; this is a design target, not a claimed measured value.

Color error is measured rather than judged by eye. For commanded and measured color coordinates, the report records a standard color difference such as (Delta E_{00}). The exact acceptance threshold is frozen before testing.

## 5. Electrical and energy model

For (N) independently driven channels,

[
P_{mathrm{elec}}=sum_{i=1}^{N}V_iI_i+P_{mathrm{controller}}+P_{mathrm{conversion}}.
]

The optical-wall-plug efficiency is

[
eta_{mathrm{wall}}=rac{P_{mathrm{visible,out}}}{P_{mathrm{elec}}}.
]

The coupon power budget must include drivers, conversion losses, controller consumption, sensors, and wiring—not LEDs alone.

For a battery or vehicle supply, energy over a duty cycle is

[
E=int_0^T P_{mathrm{elec}}(t),dt.
]

Road-vehicle integration is excluded until the load can be evaluated against the vehicle electrical architecture, electromagnetic compatibility, protected circuit routing, and fail-safe power isolation.

## 6. Thermal model

Nearly all electrical power not emitted as useful external light eventually becomes heat. A conservative steady-state balance is

[
P_{mathrm{heat}}=P_{mathrm{elec}}-P_{mathrm{visible,out}},
]

and a first thermal estimate is

[
Delta T approx P_{mathrm{heat}}R_{	heta,mathrm{system}}.
]

Because solar loading can dominate electronics heat, the coupon test also uses

[
P_{mathrm{solar,abs}}=alpha_sGA,
]

where (alpha_s) is solar absorptance, (G) is incident solar irradiance, and (A) is exposed area.

The system must trip to a non-illuminated safe state before adhesive, fiber, coating, connector, or substrate temperature limits are approached. Trip and restart thresholds require hysteresis and must be recorded in the audit log.

## 7. Mechanical model

The display layer is non-structural and must not be credited with crash strength.

For a layer at distance (y) from a neutral bending axis with bend radius (R), the approximate bending strain is

[
arepsilon_b approx rac{y}{R}.
]

The maximum permitted curvature must be set from the weakest layer's allowable cyclic strain with a safety factor. Optical loss, delamination, conductor resistance, and visible uniformity are measured before and after bend cycling.

Thermal mismatch stress is screened using

[
arepsilon_{Delta T}=(alpha_1-alpha_2)Delta T,
]

where (alpha_1) and (alpha_2) are coefficients of thermal expansion for bonded layers. The coupon must demonstrate that its attachment and relief features prevent repeated temperature changes from concentrating strain at fibers, solder joints, and sealed penetrations.

## 8. Spatial resolution and viewing model

For zone pitch (p) viewed at distance (d), the angular pitch is approximately

[
	heta_papproxrac{p}{d}.
]

The design is not advertised as a conventional high-resolution display unless measured modulation, contrast, viewing angle, and pixel/zone crosstalk support that claim.

The first prototype is intentionally low-resolution. Its success criterion is controlled surface appearance and safe operation, not cinematic imagery.

## 9. Control and safety invariants

AURORA SURFACE OS must enforce:

- no content output until configuration, temperature sensors, current limits, and emergency stop pass self-test;
- loss of communication produces a dark or fixed preapproved state;
- no flashing pattern outside frozen stationary-test limits;
- no safety-signal color or behavior presented as a legal turn, stop, hazard, or emergency signal;
- watchdog reset cannot restore animation without a fresh authorized enable;
- every state command records actor, pattern identifier, brightness limit, timestamp, software version, and result;
- camera-based content generation is disabled in the first coupon;
- remote network control is excluded from the first coupon;
- moving-road mode does not exist in the first coupon firmware.

## 10. Failure-mode register

| Failure | Observable effect | Control | Stop condition |
| --- | --- | --- | --- |
| Fiber fracture or bend loss | dark line or nonuniform zone | bend-radius limit, strain relief, optical map | uniformity below frozen limit |
| LED or driver short | localized heat/current rise | channel fuse/current limit/thermal sensor | overcurrent or temperature trip |
| Controller crash | stale or uncontrolled appearance | independent watchdog and hard dark state | watchdog event |
| Water ingress | leakage, corrosion, optical haze | sealed coupon and moisture indication | insulation or visual failure |
| Adhesive delamination | lifting, flutter, optical distortion | peel/cycle testing and redundant retention | any propagation beyond frozen defect size |
| Harness fatigue | intermittent channel or arcing risk | flex relief, protected connector, continuity monitoring | continuity instability |
| Sensor failure | unsafe thermal blind spot | plausibility checks and redundant critical sensing | invalid sensor state |
| Unexpected flashing | distraction or seizure hazard | content-rate limiter and stationary controlled venue | rate-limit violation |
| Road-light confusion | misleading signal | no-road rule and regulatory review | any proposed moving-road use |

## 11. Coupon architecture

Minimum test article:

- active area: 600 mm × 600 mm;
- curved but stationary backing panel;
- non-structural removable optical laminate;
- low-voltage current-limited supply;
- independently fused or limited zones;
- at least two temperature-sensing locations near optical sources plus one ambient sensor;
- current and voltage logging;
- hardware emergency stop;
- physically disconnected network interface;
- transparent rear access for inspection;
- replaceable optical and driver modules.

No vehicle installation occurs during v1 testing.

## 12. Verification matrix

### CAL-00 — Instrument calibration

Calibrate electrical power, surface temperature, and luminance measurements. Record uncertainty, calibration date, range, resolution, and reference equipment.

### OPT-01 — Optical transfer

Sweep commanded intensity and color. Record electrical input, luminance map, spectral/color result, uniformity, crosstalk, and hysteresis.

### THM-01 — Thermal steady state

Operate worst-case approved stationary pattern until the prespecified thermal equilibrium rule is met. Pass only if all materials remain below their frozen limits with margin.

### THM-02 — Solar-plus-operation surrogate

Apply a controlled radiant or environmental-chamber load representing the approved test envelope. Do not extrapolate beyond the measured envelope.

### MEC-01 — Bend cycling

Cycle the coupon between frozen radii. Re-measure optical attenuation, zone uniformity, insulation, and attachment integrity.

### ENV-01 — Water exposure

Use a defined spray or ingress procedure suitable for a non-certified engineering coupon. Never describe this as an IP rating unless an accredited test supports that rating.

### ENV-02 — Temperature cycling

Cycle between frozen non-destructive limits; inspect for condensation, delamination, optical shift, connector damage, and controller faults.

### EMC-01 — Pre-compliance emissions and immunity screen

Measure conducted and radiated behavior with qualified equipment before any vehicle connection. This is pre-compliance work, not certification.

### SAF-01 — Fault injection

Open sensors, short or overload one protected channel using a safe test fixture, interrupt communications, corrupt a command, and force a controller reset. The required result is a bounded dark/fixed state and retained audit evidence.

### HMI-01 — Visibility and distraction review

Test only in a controlled stationary setting. Measure luminance versus ambient condition, viewing angle, glare, flicker, and pattern transition rate. Include independent human-factors review before expanding content capability.

## 13. Data and acceptance discipline

Each test record contains:

- hardware and software revision;
- serialized coupon identifier;
- ambient conditions;
- calibrated instrument identifiers;
- raw time-series data;
- commanded state;
- measured output;
- uncertainty estimate;
- pass/fail rule frozen before the run;
- photographs of the test article;
- failures, repairs, and reruns without deletion.

A successful software replay is not a successful material test. A successful coupon is not a road-legal product.

## 14. Regulatory boundary

In the United States, vehicle lamps, reflective devices, and associated equipment are governed in part by Federal Motor Vehicle Safety Standard No. 108, codified at 49 CFR 571.108. Other federal, state, local, electromagnetic-compatibility, distraction, advertising, and vehicle-modification rules may apply. International deployment would also require market-specific type-approval review, including applicable UNECE lighting-installation rules.

Therefore:

- the first coupon is stationary and off-vehicle;
- moving-road animation is prohibited;
- required vehicle lamps and reflectors are not obscured, replaced, simulated, or controlled;
- any later parked-show demonstrator requires a qualified automotive lighting and compliance review;
- an OEM or certified modifier path is required before road integration.

## 15. Feasibility conclusion

The stationary coupon is feasible on paper because every functional block—LED source, polymer optical guide, flexible substrate, sensing, current limiting, thermal protection, environmental sealing, and bounded controller—uses ordinary known physics and available engineering methods.

The project is not yet validated because the coupled system has not demonstrated:

- required brightness and uniformity at acceptable power;
- thermal survival under combined internal and solar loads;
- durability under bend, vibration, moisture, ultraviolet exposure, and cleaning;
- electromagnetic compatibility;
- safe fault behavior;
- repairability and cost;
- regulatory acceptability for any vehicle use.

The correct next claim is: **a stationary, non-structural programmable optical-surface coupon is ready for detailed design review and bounded prototype planning.**

## 16. Stop/go gates

Proceed from paper to coupon only when:

1. materials and temperature limits are documented;
2. electrical protection and emergency stop are defined;
3. optical, thermal, mechanical, and fault acceptance criteria are frozen;
4. the work remains stationary and non-road;
5. cost and supplier terms are approved in writing;
6. no protected geometry is released before IP and NDA review.

Stop if the design requires structural-body credit, obscures regulated lighting, cannot enter a dark safe state, exceeds the frozen thermal envelope, creates uncontrolled flashing/glare, or depends on unverified camouflage or other unsupported claims.

## 17. Public technical references

- Sayed, Berzowska, and Skorobogatiy, *Jacquard-woven photonic bandgap fiber displays*, arXiv:1008.4096: https://arxiv.org/abs/1008.4096
- U.S. Federal Motor Vehicle Safety Standard No. 108, 49 CFR 571.108: https://www.ecfr.gov/current/title-49/subtitle-B/chapter-V/part-571/subpart-B/section-571.108
- UNECE vehicle-regulation framework and lighting-installation requirements must be checked against the destination market before any road-use design.
- The Aerospace Corporation Mission Assurance Baseline provides a useful general systems-assurance structure for requirements, validation, safety, reliability, interfaces, and transition planning: https://mab.aerospace.org/

These references support the engineering method and prior-art boundary. They do not establish novelty, patentability, certification, or tested performance.
