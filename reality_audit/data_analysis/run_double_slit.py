"""
run_double_slit.py
==================
CLI entrypoint for the double-slit simulation benchmark.

Usage example
-------------
    python -m reality_audit.data_analysis.run_double_slit \\
        --wavelength 500e-9 \\
        --slit-separation 1e-4 \\
        --num-particles 10000 \\
        --seed 42 \\
        --output-dir outputs/double_slit/coherent \\
        --name coherent_run

All outputs are written under ``--output-dir``:
    <name>_report.json      — structured JSON summary
    <name>_intensity.csv    — screen positions + normalised intensity
    <name>_summary.md       — human-readable Markdown summary
    <name>_plot.png         — intensity + hit-histogram figure
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from reality_audit.data_analysis.double_slit_sim import (
    run_double_slit_sim,
    write_all_artifacts,
)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run the double-slit simulation and write audit artifacts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--wavelength", type=float, default=500e-9,
                   help="Particle/photon wavelength in metres.")
    p.add_argument("--slit-separation", type=float, default=1e-4,
                   help="Centre-to-centre slit spacing in metres.")
    p.add_argument("--slit-width", type=float, default=2e-5,
                   help="Individual slit width in metres.")
    p.add_argument("--screen-distance", type=float, default=1.0,
                   help="Slit-to-screen distance in metres.")
    p.add_argument("--num-particles", type=int, default=5000,
                   help="Number of particle hits to sample.")
    p.add_argument("--screen-points", type=int, default=500,
                   help="Number of discrete positions on the screen.")
    p.add_argument("--coherence", type=float, default=1.0,
                   help="Coherence factor [0, 1]. 1 = fully coherent.")
    p.add_argument("--decoherence-strength", type=float, default=0.0,
                   help="Extra decoherence towards classical pattern [0, 1].")
    p.add_argument("--measurement-on", action="store_true",
                   help="Enable which-path measurement (forces fully classical output).")
    p.add_argument("--noise-level", type=float, default=0.0,
                   help="Fractional additive noise on intensity.")
    p.add_argument("--seed", type=int, default=None,
                   help="RNG seed for reproducibility.")
    p.add_argument("--output-dir", type=str, default="outputs/double_slit",
                   help="Directory where artifacts are written.")
    p.add_argument("--name", type=str, default="double_slit",
                   help="Artifact name prefix.")
    p.add_argument("--config", type=str, default=None,
                   help="Optional path to a JSON config file. CLI flags override config values.")
    return p


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # -----------------------------------------------------------------------
    # Merge optional JSON config (CLI flags have precedence)
    # -----------------------------------------------------------------------
    config: dict = {}
    if args.config:
        cfg_path = Path(args.config)
        if not cfg_path.exists():
            print(f"[run_double_slit] ERROR: config file not found: {cfg_path}", file=sys.stderr)
            sys.exit(1)
        with open(cfg_path) as f:
            config = json.load(f)

    def _cfg(key: str, default):
        """Return CLI value if set (not equal to parser default), else config value."""
        return config.get(key, default)

    # Build simulation kwargs — CLI args take priority over config file
    sim_kwargs = {
        "wavelength":          args.wavelength if args.wavelength != 500e-9 else _cfg("wavelength", 500e-9),
        "slit_separation":     args.slit_separation if args.slit_separation != 1e-4 else _cfg("slit_separation", 1e-4),
        "slit_width":          args.slit_width if args.slit_width != 2e-5 else _cfg("slit_width", 2e-5),
        "screen_distance":     args.screen_distance if args.screen_distance != 1.0 else _cfg("screen_distance", 1.0),
        "num_particles":       args.num_particles if args.num_particles != 5000 else _cfg("num_particles", 5000),
        "screen_points":       args.screen_points if args.screen_points != 500 else _cfg("screen_points", 500),
        "coherence":           args.coherence if args.coherence != 1.0 else _cfg("coherence", 1.0),
        "decoherence_strength": args.decoherence_strength if args.decoherence_strength != 0.0 else _cfg("decoherence_strength", 0.0),
        "measurement_on":      args.measurement_on or _cfg("measurement_on", False),
        "noise_level":         args.noise_level if args.noise_level != 0.0 else _cfg("noise_level", 0.0),
        "seed":                args.seed if args.seed is not None else _cfg("seed", None),
    }

    output_dir = args.output_dir if args.output_dir != "outputs/double_slit" else _cfg("output_dir", "outputs/double_slit")
    name       = args.name       if args.name       != "double_slit"          else _cfg("name", "double_slit")

    # -----------------------------------------------------------------------
    # Run simulation
    # -----------------------------------------------------------------------
    print("[run_double_slit] Running simulation …")
    result = run_double_slit_sim(**sim_kwargs)

    # -----------------------------------------------------------------------
    # Write artifacts
    # -----------------------------------------------------------------------
    paths = write_all_artifacts(result, output_dir, name)

    # -----------------------------------------------------------------------
    # Terminal summary
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  DOUBLE-SLIT SIMULATION RESULTS")
    print("=" * 60)
    print(f"  Run ID             : {result['run_id']}")
    print(f"  Timestamp          : {result['timestamp']}")
    print(f"  Regime             : {result['regime'].upper()}")
    print(f"  Visibility         : {result['visibility']:.4f}")
    print(f"  Coherence score    : {result['coherence_score']:.4f}")
    print(f"  Interference       : {'YES' if result['interference_detected'] else 'NO'}")
    print(f"  Alpha (effective)  : {result['summary_stats']['alpha_effective']:.4f}")
    print(f"  Num hits sampled   : {result['summary_stats']['num_hits']:,}")
    print(f"  measurement_on     : {sim_kwargs['measurement_on']}")
    print(f"  decoherence_strength: {sim_kwargs['decoherence_strength']}")
    print()
    print("  ARTIFACTS:")
    for artifact_type, path in paths.items():
        print(f"    {artifact_type:10s} : {path}")
    print("=" * 60)
    print()
    print("  NOTE: This is a computational simulation. It does not")
    print("  by itself constitute evidence that reality is a simulation.")
    print("=" * 60)


if __name__ == "__main__":
    main()
