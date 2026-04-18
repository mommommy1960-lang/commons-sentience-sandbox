import argparse
from pathlib import Path

from reality_audit.experiment import ExperimentConfig, ExperimentRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Reality Audit experiment.")
    parser.add_argument("config", type=Path, help="Path to experiment JSON or YAML config.")
    args = parser.parse_args()

    config = ExperimentConfig.load(args.config)
    print(f"[reality_audit] Experiment : {config.name}")
    print(f"[reality_audit] World mode : {config.world_mode}")
    print(f"[reality_audit] Controllers: {config.controllers}")
    print(f"[reality_audit] Seeds      : {config.seeds}")
    print(f"[reality_audit] Duration   : {config.duration}s  dt={config.dt}")
    print()
    runner = ExperimentRunner(config)
    results = runner.run()
    summary_path = Path(config.output_dir) / config.name / "summary.json"
    print()
    print(f"[reality_audit] Done. {len(results)} run(s) completed.")
    print(f"[reality_audit] Summary    : {summary_path}")


if __name__ == "__main__":
    main()
