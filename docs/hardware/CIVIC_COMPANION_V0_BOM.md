# Civic Continuum Companion v0 Bench Prototype

## Product boundary

This is a low-voltage, phone-connected demonstrator. It is not a medical device, emergency device, surveillance device, vehicle controller, or autonomous household controller.

## Hardware-neutral minimum bill of materials

- one supported development computer or single-board computer;
- one protected low-voltage battery or USB power bank;
- one small speaker or wired headphones;
- one physical mute/stop control;
- one status LED or small display;
- one enclosure suitable for bench testing;
- insulated wiring and strain relief;
- optional motion sensor;
- optional microphone, only after privacy testing.

No mains wiring, motors, locks, weapons, heaters, or flight hardware belong in v0.

## Acceptance criteria

- device starts in safe observation mode;
- physical mute is visible and works without software;
- removing network access does not disable shutdown;
- no external action occurs without explicit scoped approval;
- memory can be inspected, corrected, exported, and deleted;
- audit records survive restart;
- battery and enclosure remain within safe temperature limits;
- reset returns the system to a known state.
