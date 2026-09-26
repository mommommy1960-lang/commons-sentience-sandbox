# AquaShield engineering baseline v0.1

## System architecture

| Element | Function | Fail-safe state |
|---|---|---|
| Segmented wall cells | Store water near occupied volume | Independently isolated cells |
| Transfer manifold | Move selected water inventory | Closed valves, balanced tanks |
| Elastic exercise cell | Fully contains water and gas | Mechanically supported and drained |
| Breathing interface | Keeps airway on a dry gas supply | Independent emergency gas path |
| Restraint/load harness | Adds axial and joint loading | Quick release, no entrapment |
| Flow loop | Produces adjustable resistance | Pump off; bypass open |
| Gas separator | Removes entrained bubbles | Automatic loop isolation |
| Filtration/sanitation | Controls particles and biology | Quarantine contaminated segment |
| Drain/sump tanks | Receives emergency drain | Passive capacity reserved |
| Instrumentation | Pressure, flow, force, leak and water quality | Local alarms; manual override |

## Baseline requirements

Identifiers are stable so a reviewer can challenge individual requirements.

| ID | Requirement | Verification |
|---|---|---|
| AQ-001 | No free water surface may be exposed to cabin atmosphere during operation. | Inspection and leak test |
| AQ-002 | A single puncture or valve failure must not release the total water inventory. | Fault injection |
| AQ-003 | The crew breathing path must be physically independent of the water loop. | Architecture review and pressure test |
| AQ-004 | Occupant release must not depend on software, electric power, or pump operation. | Timed manual-egress test |
| AQ-005 | Water transfer must preserve spacecraft mass-property limits. | Mass model and hardware-in-loop simulation |
| AQ-006 | Resistance settings must be measured as force and work, not inferred from pump command. | Calibrated load cells |
| AQ-007 | Radiation benefit must be reported using transport analysis and uncertainty, not water thickness alone. | Independent radiation analysis |
| AQ-008 | The system must identify and isolate gas ingestion, microbial contamination, and leakage. | Fault-injection matrix |
| AQ-009 | No medical-prevention claim may be made without an approved human study. | Claims review |
| AQ-010 | A crewed unit requires independent human-factors and flight-safety approval. | External review record |

## First physical demonstrator: AQ-D0

AQ-D0 is a 0.50 m³ maximum-water terrestrial rig with a flexible contained
exercise volume, transparent inspection window, recirculation loop, gas
separator, filter, two independent isolation valves per penetration, reserved
drain capacity, and instrumented hand/foot interfaces.

Minimum measurements:

- total water mass before and after each run;
- flow rate, differential pressure, electrical power, and water temperature;
- force at each human-contact simulator;
- visible and measured gas fraction;
- leak rate and isolation time;
- emergency drain time and trapped volume;
- microbial indicators before and after sanitation;
- center-of-mass change during transfer.

AQ-D0 is initially tested with an anthropomorphic fixture, never a person.

## Flight architecture still missing

- validated radiation transport for a defined mission and habitat;
- structural loads and launch restraint;
- slosh and guidance-navigation-control coupling;
- fire, electrical, and toxicology assessment;
- water-quality standard and maintenance burden;
- crew entrapment and aspiration hazard analysis;
- reduced-gravity fluid-management data;
- medical protocol and institutional review approval.

