import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable

class ExperimentLogger:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_config(self, config: Dict[str, Any]) -> None:
        with open(self.output_dir / "config.json", "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)

    def write_raw_log(self, records: Iterable[Dict[str, Any]], filename: str = "raw_log.json") -> None:
        with open(self.output_dir / filename, "w", encoding="utf-8") as handle:
            json.dump(list(records), handle, indent=2)

    def write_summary(self, summary: Dict[str, Any], filename: str = "summary.json") -> None:
        with open(self.output_dir / filename, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)

    def write_csv(self, records: Iterable[Dict[str, Any]], filename: str = "raw_log.csv") -> None:
        records = list(records)
        if not records:
            return
        with open(self.output_dir / filename, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
