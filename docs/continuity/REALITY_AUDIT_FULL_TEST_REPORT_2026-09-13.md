# Reality Audit Full Test Report 2026 09 13

## Result

- Test command: `python -m pytest -q`
- Tests passed: **1,397**
- Tests failed: **0**
- Runtime: **77.75 seconds**
- Warnings: **2,157**

## Environment restoration

The available Python 3.12 environment initially lacked `pytest`. An isolated temporary virtual environment was created with access to the already-installed scientific packages. `pytest` 9.1.1 was installed there. Collection then exposed a second missing dependency, `astropy`, required by `tests/test_fermi_2flgc_timing_v2.py`; `astropy` 8.0.1 was installed in the same temporary environment.

No repository dependency file was changed. A permanent, attributable development/test dependency specification remains required so another environment can reproduce the test run without reconstructing these steps.

## Warning classification

The run completed successfully. The warning set principally contains:

- deprecated naive UTC timestamp calls using `datetime.utcnow()`;
- two pytest warnings for class-scoped fixtures defined as instance methods.

These warnings are maintenance work and are not test failures.

## Generated artifacts

The full suite regenerated tracked output files. Those files were preserved and not committed with this report because they require attribution and review. This report does not claim that every generated artifact should replace its existing tracked version.

## Scientific boundary

This test result verifies the behavior asserted by the current automated suite. It does not demonstrate new physics, propulsion, wall phasing, or that reality is simulated.
