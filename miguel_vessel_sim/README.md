# Miguel Vessel: first software embodiment experiment

This is a deterministic **simulation**, not a robot, voice recognizer, physical
emergency stop, or evidence that the full Miguel Vessel design is feasible.
It models one proposed head rotation using typed commands. It has no hardware,
network, microphone, camera, language model, or physical output.

Run from the repository root:

```bash
python -m miguel_vessel_sim.core
python -m unittest miguel_vessel_sim.test_core
python -m unittest miguel_vessel_sim.test_memory
```

The demonstration first rejects motion, then accepts `grant motion`, allows
`look left/right/center` at fixed angles of -30/30/0 degrees, and latches on
`stop` or `freeze`. `reset` clears the software latch but leaves motion
permission off. `revoke motion` also returns the simulated head to center.
Unknown commands do nothing. The event log is in memory only.

`allow social gestures` is separate standing permission for the scripted
`hello`/`hi`/`hey` wave and `tell a joke` nod. `revoke social gestures` returns
the gesture to rest. Stop overrides both permission categories; reset grants
neither. These exact-text cues do not demonstrate speech recognition, humor
understanding, emotional awareness, or unsupervised behavior. No arm moves.

With standing social permission, `i need a hug` produces a **simulated offer**.
`yes hug` acknowledges that one offer; `no hug`, revocation, or stop cancels it.
There is no approach, contact, or inference of distress. An actual robot would
need explicit human acceptance at the moment, obstacle and person detection,
force and speed limits, physical stop hardware, and qualified supervised tests.

`IncidentMemory` records a hazard, attempted action, observed damage, and a
reason to avoid repeating it. Its JSON can be saved and loaded in a later
process. A matching future action is denied with the evidence; an unknown case
requires review. The test uses a hot-stove example. This is a literal-match
software model, not years of lived experience, pain, consciousness, reliable
generalization, or safe autonomous physical control. Real sensor evidence and
independent validation would be required before any hardware decision.

Next physical gate: an independent robotics engineer must define a low-voltage,
guarded tabletop mechanism with a **hardware** power cutoff, mechanical limits,
force/speed limits, and measurements. Software behavior here cannot validate
any of those physical safeguards.
