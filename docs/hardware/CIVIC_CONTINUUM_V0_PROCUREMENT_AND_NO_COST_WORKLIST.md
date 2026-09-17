# Civic Continuum v0 Procurement and No-Cost Worklist

## Status

- Phone prototype plan: CI-verified in run #150.
- Latest verified plan commit: `56be9d46`.
- This checklist records needs; it is not an order or spending authorization.
- No purchase is required to continue the software work.

## Priority 0 — use what is already available

Before buying anything, inventory:

- Android phone or tablet already available;
- existing USB cable and charger or power bank;
- wired headphones or an existing small speaker;
- a physical object that can serve as a clearly labeled manual stop control during
  supervised bench tests;
- a clean table and a well-ventilated, non-flammable test area;
- notebook or phone camera for dated test records.

Do not connect mains wiring, motors, locks, heaters, vehicle controls, weapons, or
unverified battery assemblies.

## Priority 1 — minimum low-voltage bench items

When funds are available, obtain only the smallest safe set:

- protected USB power bank or other certified low-voltage supply;
- small USB or wired speaker/headphones;
- clearly labeled physical mute/stop control;
- simple status LED or small display;
- insulated low-voltage wiring, connectors, and strain relief;
- non-conductive bench enclosure;
- optional motion sensor only after the observe-only tests pass.

The first build does not need a camera, microphone, motor, lock, relay, mains adapter,
or custom battery pack.

## Priority 2 — only after acceptance evidence

Consider, only after the first bench gate passes:

- a supported development computer or single-board computer;
- a separately approved microphone with a physical privacy disconnect;
- a separately approved enclosure revision;
- a second identical setup for independent replication.

## No-money work available now

1. Run the demonstrator and save its JSON report.
2. Inventory existing phone, tablet, cables, headphones, power bank, and safe workspace.
3. Draft the privacy notice and consent boundary.
4. Create the test-recording template with date, commit, operator, raw output,
   failures, and pass/fail decision.
5. Practice the five-minute demo in observe-only mode.
6. Review the product and bench-validation documents.
7. Identify one trusted second operator for later supervised replication.
8. Do not collect another person's data or enable sensors yet.

## Purchase gate

Before any purchase or sensor activation, confirm:

- item is low-voltage and certified;
- physical stop remains independent of software;
- no external actuation is included;
- privacy mode and data deletion are testable;
- the item fits the documented acceptance criteria;
- Mya approves the exact item and price.

## Definition of done for v0

The prototype is not called complete until safe boot, physical stop, network-loss
shutdown, permission denial, emergency freeze, memory provenance, export, deletion,
audit verification, power/temperature observation, and second-operator repetition
are all recorded as evidence.
