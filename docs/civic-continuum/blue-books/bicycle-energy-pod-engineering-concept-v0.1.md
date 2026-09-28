# Bicycle Energy Pod

## Retrofit Energy-Recovery System — Engineering Concept v0.1

**Date:** September 26, 2026  
**Project status:** Concept design; prototype not yet built or validated

## Purpose

Create a removable system for ordinary and electric bicycles that converts rider-supplied or recoverable mechanical energy into stored electrical energy. The device is intended to power bicycle lights, safety electronics, USB devices, and—where the bicycle and local rules permit—limited electric assistance.

This system does not create free energy. Electrical generation produces resistance. The useful design goal is to recover energy during braking and downhill travel, or allow the rider to intentionally generate extra power.

## Historical basis

Traditional bottle and hub dynamos use wheel motion to power bicycle lights. Faster wheel rotation generally produces more electrical power, so older unregulated lamps could appear brighter as the bicycle accelerated. Modern dynamo lighting remains available; battery-powered LED systems became common largely because they are inexpensive, efficient, and easy to install.

## Proposed product

**Working name:** Bicycle Energy Pod (BEP)

The retrofit system consists of:

1. A generator integrated into a compatible hub, friction roller, or crank module.
2. A rectifier and charge controller.
3. A small protected battery and/or supercapacitor buffer.
4. A handlebar control and status display.
5. Regulated outputs for lighting, USB-C power, and optional low-power assistance.
6. Speed, temperature, voltage, current, and braking sensors.
7. A protected reserve bank for emergency lighting or limited assistance.

## Operating modes

| Mode | Energy source | Intended use |
|---|---|---|
| Coast | None | Generator disengaged or minimized to reduce drag |
| Regenerative braking | Bicycle kinetic energy | Slow the bicycle while recovering part of the energy |
| Downhill recovery | Gravity and controlled speed | Charge while limiting downhill acceleration |
| Pedal charging | Intentional rider effort | Generate power for storage or accessories |
| Stationary generation | Rider pedaling on a stand | Emergency or off-grid charging |
| Assist | Stored electrical energy | Limited propulsion assistance on compatible systems |
| Reserve boost | Energy intentionally held in reserve | Emergency assistance when the main e-bike battery is low |

## Recommended architecture

```text
Wheel or crank
    -> generator
    -> rectifier / motor controller
    -> current and voltage protection
    -> supercapacitor buffer
    -> protected battery pack
    -> regulated accessory outputs
    -> optional motor-assist output
```

### Why use a buffer

Braking creates short bursts of power. A supercapacitor can absorb those bursts quickly, after which the controller can transfer energy to the battery at a safe rate. A battery-only prototype may be simpler, but it must limit charge current and protect against overvoltage, overheating, and overcharge.

## First prototype: accessory-power version

The safest first prototype should avoid propulsion and prove the energy path at low power.

### Prototype components

- Commercial bicycle dynamo or reversible direct-drive hub motor
- Matching rectifier or regenerative controller
- Fuse and disconnect switch
- Protected low-voltage storage pack or supercapacitor module
- DC-DC converter with regulated lighting output
- Weather-resistant enclosure and connectors
- Voltage, current, temperature, wheel-speed, and braking data logger
- Handlebar mode switch and visible charge indicator

### First outputs

- Front and rear LED lighting
- Turn indicators or brake light
- Emergency USB output
- Location or safety sensor power

## LED lighting plus dynamo recovery

The LED lighting system and generator operate together. Efficient LEDs receive regulated power from storage, while the generator replenishes storage during braking, downhill recovery, stationary pedaling, or deliberate pedal charging. A safety reserve keeps enough energy for front and rear lights even when propulsion assistance is unavailable.

## Emergency Reserve Boost

Reserve Boost holds recovered energy separately from the ordinary e-bike battery allocation. The rider activates it with a guarded handlebar button when the main battery is nearly depleted.

### Required behavior

1. Reserve energy remains unused during ordinary assistance unless the rider explicitly enables it.
2. Safety lighting has first priority; propulsion cannot consume the protected lighting reserve.
3. The display reports reserve energy in watt-hours and gives a conservative estimate of remaining assist time or distance.
4. The system may display an equivalent battery increase only when it knows the main battery's usable capacity and state of charge.
5. Reserve Boost stops automatically at its safe minimum voltage or temperature limit.
6. The rider can dedicate all remaining reserve energy to safety lighting.

The amount of assistance depends on how much energy was actually recovered. A small dynamo reserve may provide only brief assistance; restoring multiple battery-indicator bars requires a correspondingly large amount of stored energy. The prototype must measure this result rather than promise a fixed number of bars.

## Control rules

1. Default to low-drag coast mode.
2. Enable generation during braking, downhill recovery, stationary charging, or deliberate rider selection.
3. Stop charging at the storage system's voltage or temperature limit.
4. Maintain ordinary mechanical brakes; regenerative braking must never be the only braking system.
5. Fail safely to coast mode when the controller, sensor, or storage system faults.
6. Prevent assist while charging from the same rider input; otherwise the system wastes energy in a loop.
7. Log input power, stored power, output power, temperature, speed, and time.
8. Preserve a configurable minimum lighting reserve before allowing propulsion boost.

## Energy accounting

Mechanical input power is approximately:

\[
P_{mechanical}=\tau\omega
\]

where \(\tau\) is torque and \(\omega\) is rotational speed.

Electrical output is:

\[
P_{electrical}=VI
\]

where \(V\) is voltage and \(I\) is current.

Overall recovery efficiency is:

\[
\eta=\frac{E_{stored}}{E_{mechanical\ input}}
\]

The measured stored energy must always be lower than the mechanical energy supplied because the generator, electronics, wiring, and storage system all have losses.

## Validation plan

### Bench test

1. Spin the generator at controlled speeds.
2. Measure torque, revolutions per minute, voltage, current, and temperature.
3. Confirm overvoltage, overcurrent, and thermal shutdown behavior.
4. Compare mechanical input energy with electrical energy delivered and stored.

### Bicycle test

1. Establish a no-generator coast-down baseline.
2. Repeat with the generator disengaged.
3. Repeat at several generation settings.
4. Measure stopping distance using mechanical brakes alone and combined braking.
5. Test controlled downhill recovery without exceeding safe storage limits.
6. Test wet conditions only after enclosure and braking safety are validated.

### Success criteria for v0.1

- No interference with steering, wheels, chain, or mechanical brakes
- Safe shutdown on electrical or thermal faults
- Measurable stored energy with a complete energy ledger
- Predictable added resistance at each generation setting
- Useful regulated lighting output
- Weather-resistant mounting and strain-relieved wiring

## Risks requiring engineering review

- Battery fire or cell damage from uncontrolled regenerative current
- Reduced or unpredictable braking performance
- Wheel, fork, frame, or mount failure
- Cable entanglement
- Water ingress and corrosion
- Excessive downhill speed or storage overvoltage
- Local vehicle-class rules if propulsion assistance is added

## Development sequence

1. Build and test the low-power bench rig.
2. Add accessory lighting and data logging.
3. Install on a stationary bicycle stand.
4. Conduct controlled low-speed bicycle testing.
5. Add supercapacitor buffering if braking bursts exceed battery limits.
6. Evaluate a direct-drive hub version for regenerative braking.
7. Consider propulsion assistance only after braking, electrical, structural, and regulatory review.

## Honest product claim

The Bicycle Energy Pod is a retrofit bicycle energy-management system. It captures otherwise wasted braking or downhill energy and converts intentional rider effort into stored electricity for accessories and compatible assistance. It reduces waste; it does not generate energy without a physical source.