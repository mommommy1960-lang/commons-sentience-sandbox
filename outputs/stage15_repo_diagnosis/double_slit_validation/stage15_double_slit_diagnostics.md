# Double-Slit Diagnostics Summary

Generated: 2026-04-22T02:45:43.366857Z

## Scientific Framing

Controlled computational benchmark reproducing expected behavior under encoded physical assumptions; not a standalone discovery claim.

## Mode Metrics

| Mode | Visibility | Interference Detected | Regime | Alpha | Peaks | Troughs |
|---|---:|---|---|---:|---:|---:|
| coherent | 0.9122 | True | coherent | 0.0000 | 10 | 10 |
| decohered | 0.4072 | True | classicalized | 0.7000 | 8 | 8 |
| measurement | 0.0110 | False | classicalized | 1.0000 | 0 | 0 |

## Distribution Comparisons

- Visibility drop (coherent -> decohered): 0.5050
- Visibility drop (coherent -> measurement): 0.9012
- L1 distance (coherent vs decohered): 0.2227
- L1 distance (coherent vs measurement): 0.3182
- JS divergence (coherent vs decohered): 0.0759
- JS divergence (coherent vs measurement): 0.1281

## Expectation Checks

- coherent_interference_present: PASS
- decohered_visibility_reduced: PASS
- measurement_visibility_strongly_suppressed: PASS
- measurement_below_coherent: PASS

Overall expectation status: **PASS**

## Limitations

- This is a 1-D benchmark with encoded decoherence/measurement assumptions.
- It does not model full laboratory detector dynamics or full quantum measurement theory.
- It does not prove observer-caused collapse or that reality is a simulation.

## Benchmark Readiness

`ready`
