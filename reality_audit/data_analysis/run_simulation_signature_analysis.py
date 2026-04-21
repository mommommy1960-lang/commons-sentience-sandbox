"""
run_simulation_signature_analysis.py
=====================================
CLI entry point for the simulation-signature analysis pipeline.

Usage examples
--------------
# Baseline null analysis:
python reality_audit/data_analysis/run_simulation_signature_analysis.py \\
  --input data/real/example_event_catalog.csv \\
  --name baseline_run \\
  --output-dir outputs/simulation_signature/baseline \\
  --null-mode isotropic --null-repeats 25 --seed 42 --plots

# Preferred-axis injection test:
python reality_audit/data_analysis/run_simulation_signature_analysis.py \\
  --input data/real/example_event_catalog.csv \\
  --name axis_run \\
  --output-dir outputs/simulation_signature/axis \\
  --null-mode isotropic --null-repeats 25 \\
  --inject-anomaly preferred_axis --anomaly-strength 0.5 --seed 42 --plots

# Load config instead of individual flags:
python reality_audit/data_analysis/run_simulation_signature_analysis.py \\
  --config configs/simulation_signature_baseline.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure package root is on the path when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from reality_audit.data_analysis.simulation_signature_analysis import (
    analyze_event_dataset,
    evaluate_signal_strength,
    generate_null_events,
    inject_synthetic_anomaly,
    load_event_dataset,
    standardize_events,
    write_analysis_artifacts,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Simulation-signature anomaly analysis pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input",           default=None, help="Path to event CSV or JSON")
    p.add_argument("--config",          default=None, help="Path to JSON config file")
    p.add_argument("--output-dir",      default="outputs/simulation_signature/run", dest="output_dir")
    p.add_argument("--name",            default="analysis")
    p.add_argument("--null-mode",       default="isotropic",
                   choices=["isotropic", "shuffled_time"], dest="null_mode")
    p.add_argument("--null-repeats",    default=25, type=int, dest="null_repeats")
    p.add_argument("--inject-anomaly",  default=None,
                   choices=["preferred_axis", "energy_dependent_delay", "clustered_arrivals"],
                   dest="inject_anomaly")
    p.add_argument("--anomaly-strength", default=0.5, type=float, dest="anomaly_strength")
    p.add_argument("--seed",             default=None, type=int)
    p.add_argument("--plots",            action="store_true", default=False)
    p.add_argument("--save-normalized",  action="store_true", default=False,
                   dest="save_normalized",
                   help="Save standardized event list as CSV")
    return p


def _load_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _merge_config(args: argparse.Namespace, cfg: dict) -> argparse.Namespace:
    """Layer config values under CLI args (CLI always wins)."""
    defaults = {
        "input":           cfg.get("input_path"),
        "output_dir":      cfg.get("output_dir"),
        "null_mode":       cfg.get("null_mode", "isotropic"),
        "null_repeats":    cfg.get("null_repeats", 25),
        "inject_anomaly":  cfg.get("anomaly_type"),
        "anomaly_strength":cfg.get("anomaly_strength", 0.5),
        "seed":            cfg.get("seed"),
        "plots":           cfg.get("plots_enabled", False),
    }
    for attr, val in defaults.items():
        if getattr(args, attr, None) is None and val is not None:
            setattr(args, attr, val)
    return args


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # --- load config if provided ---
    if args.config:
        cfg = _load_config(args.config)
        args = _merge_config(args, cfg)

    if not args.input:
        parser.error("--input is required (or provide it via --config)")

    print(f"[run_simulation_signature_analysis] Starting: {args.name}")
    print(f"  Input:      {args.input}")
    print(f"  Output dir: {args.output_dir}")
    print(f"  Null mode:  {args.null_mode} x{args.null_repeats}")
    print(f"  Injection:  {args.inject_anomaly or 'none'}")
    print(f"  Seed:       {args.seed}")

    # === 1. Load ===
    raw = load_event_dataset(args.input)
    print(f"  Loaded {len(raw)} raw records")

    # === 2. Standardize ===
    events = standardize_events(raw)
    print(f"  Standardized {len(events)} events")

    # === 3. Optionally save normalized ===
    if args.save_normalized:
        import csv as _csv
        os.makedirs(args.output_dir, exist_ok=True)
        norm_path = os.path.join(args.output_dir, f"{args.name}_normalized.csv")
        safe_events = [
            {k: v for k, v in e.items()
             if not k.startswith("_") or k == "_b_proxy"}
            for e in events
        ]
        if safe_events:
            with open(norm_path, "w", newline="") as f:
                writer = _csv.DictWriter(f, fieldnames=list(safe_events[0].keys()))
                writer.writeheader()
                writer.writerows(safe_events)
            print(f"  Saved normalized events to {norm_path}")

    # === 4. Generate null ===
    null_events = generate_null_events(events, mode=args.null_mode, seed=args.seed)
    print(f"  Generated {len(null_events)} null events (mode={args.null_mode})")

    # === 5. Optional anomaly injection ===
    analysis_events = events
    if args.inject_anomaly:
        analysis_events = inject_synthetic_anomaly(
            events,
            anomaly_type=args.inject_anomaly,
            strength=args.anomaly_strength,
            seed=args.seed,
        )
        print(f"  Injected anomaly: {args.inject_anomaly} (strength={args.anomaly_strength})")

    # === 6. Analyze ===
    config_dict = {
        "null_mode":    args.null_mode,
        "null_repeats": args.null_repeats,
        "seed":         args.seed,
    }
    results = analyze_event_dataset(
        analysis_events,
        reference_events=null_events,
        config=config_dict,
        null_repeats=args.null_repeats,
        seed=args.seed,
    )

    # === 7. Evaluate ===
    signal_eval = evaluate_signal_strength(results)

    # === 8. Save artifacts ===
    manifest = write_analysis_artifacts(
        results=results,
        signal_eval=signal_eval,
        events=analysis_events,
        null_events=null_events,
        output_dir=args.output_dir,
        name=args.name,
        plots_enabled=args.plots,
        config=config_dict,
    )

    # === 9. Terminal summary ===
    print()
    print("=" * 60)
    print(f"  RESULT: {signal_eval['tier']}")
    print(f"  Max percentile vs null: {signal_eval['max_percentile']:.3f}")
    print(f"  {signal_eval['summary']}")
    print()
    print("  Artifacts written:")
    for kind, path in manifest.items():
        print(f"    [{kind}] {path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
