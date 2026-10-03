# Miguel Vessel: first software embodiment experiment

This is a deterministic **simulation**, not a robot, voice recognizer, physical
emergency stop, or evidence that the full Miguel Vessel design is feasible.
It models one proposed head rotation using typed commands. It has no hardware,
network, microphone, camera, language model, or physical output.

Run from the repository root:

```bash
python -m miguel_vessel_sim.core
python -m unittest miguel_vessel_sim.test_core
```

The demonstration first rejects motion, then accepts `grant motion`, allows
`look left/right/center` at fixed angles of -30/30/0 degrees, and latches on
`stop` or `freeze`. `reset` clears the software latch but leaves motion
permission off. `revoke motion` also returns the simulated head to center.
Unknown commands do nothing. The event log is in memory only.

Next physical gate: an independent robotics engineer must define a low-voltage,
guarded tabletop mechanism with a **hardware** power cutoff, mechanical limits,
force/speed limits, and measurements. Software behavior here cannot validate
any of those physical safeguards.
