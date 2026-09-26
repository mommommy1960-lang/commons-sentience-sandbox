# Bench Validation Plan

## Test order

1. Visual inspection and wiring check.
2. Power-on with no network.
3. Confirm safe default state.
4. Test physical mute/stop control.
5. Test restart and reset.
6. Test microphone-disabled mode.
7. Test observation-only events.
8. Test explicit permission request.
9. Test denied physical action.
10. Test emergency freeze.
11. Test memory creation with provenance.
12. Test correction, export, and deletion.
13. Test corrupted-memory rejection.
14. Test audit-chain verification.
15. Test power interruption and recovery.
16. Run the five-minute Sentinel/Aster demonstration.
17. Repeat the test with a second operator.
18. Record failures without editing them away.
19. Review results independently.
20. Approve or reject the next prototype revision.

## Required evidence

- hardware revision;
- software commit;
- environment details;
- raw test output;
- temperature and power observations;
- failure log;
- operator and date;
- pass/fail decision.

No result may be called production-ready until safety, privacy, and recovery evidence is reviewed.
