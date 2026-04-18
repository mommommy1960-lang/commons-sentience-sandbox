# Reality Audit Integration

This document explains the Reality Audit sandbox, how to run experiments, and how to interpret outputs.

## Purpose

The Reality Audit layer adds a configurable experiment manager on top of FluxDrive navigation and control. It supports reproducible audit scenarios for discretization, preferred-frame anisotropy, bandwidth-limited sensing, observer-triggered updates, and control artifact separation.

## Running experiments

Use the provided script to run definitions from the `configs/` folder:

```bash
python scripts/run_experiment.py configs/discretization_test.json
```

Output is stored in `outputs/<experiment_name>/<run_id>/` and includes:

- `config.json`
- `raw_log.json`
- `raw_log.csv`
- `summary.json`

## Example configs

- `configs/discretization_test.json`
- `configs/preferred_frame_test.json`
- `configs/bandwidth_limit_test.json`
- `configs/observer_effect_test.json`
- `configs/control_artifact_test.json`

## Analysis

Aggregate results with `reality_audit.analysis` and generate plot-ready CSV files.

```python
from pathlib import Path
from reality_audit.analysis import summarize_run_directories

records = summarize_run_directories(Path("outputs/discretization_audit"), output_csv=Path("outputs/discretization_audit/summary.csv"))
```

## Limitations

- The framework is intentionally lightweight and avoids assumptions about whether the environment is implemented by a physical or simulated substrate.
- Measurement and world physics are decoupled, but actual audit sensitivity depends on parameter choice.
