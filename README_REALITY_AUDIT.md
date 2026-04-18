# Reality Audit Sandbox for FluxDrive

This package provides a modular experiment framework for auditing simulation behavior in the FluxDrive environment. It focuses on reproducible audits of discretization, anisotropy, bandwidth limits, observer-triggered state changes, and control artifact separation.

## Features

- Modular world modes: `continuous_baseline`, `discrete_grid`, `anisotropic_preferred_axis`, `bandwidth_limited`, `observer_triggered_updates`, `noisy_quantized_measurement`
- Common controller API for proportional, PID, and future predictive controllers
- Structured experiment orchestration from JSON/YAML definitions
- Structured logging of raw time series, metrics, and experiment metadata
- Analysis utilities for aggregating and comparing run results

## Getting Started

### Run an experiment

```bash
python scripts/run_experiment.py configs/discretization_test.json
```

### Example Configs

Example definitions live under `configs/` and include:

- `discretization_test.json`
- `preferred_frame_test.json`
- `bandwidth_limit_test.json`
- `observer_effect_test.json`
- `control_artifact_test.json`

### Output Structure

Each experiment run writes output into `outputs/<experiment_name>/<run_id>/` containing:

- `config.json`
- `raw_log.json`
- `raw_log.csv`
- `summary.json`

## Analysis

Use `reality_audit.analysis` to aggregate and compare metrics across runs:

```python
from pathlib import Path
from reality_audit.analysis import summarize_run_directories

records = summarize_run_directories(Path("outputs/discretization_audit"), output_csv=Path("outputs/discretization_audit/summary.csv"))
```

## Notes

- Experiments are reproducible from explicit seeds and configuration files.
- The measurement suite is designed to keep physics, control, and sensing layers separate.
- The framework is intentionally agnostic to whether the environment is "real" or simulated.
