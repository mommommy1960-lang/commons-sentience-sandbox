import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

def load_summary(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))

def aggregate_summaries(directories: Iterable[Path]) -> List[Dict]:
    aggregated = []
    for directory in directories:
        summary_path = directory / "summary.json"
        if not summary_path.exists():
            continue
        summary = load_summary(summary_path)
        if "results" in summary:
            aggregated.extend(summary["results"])
        else:
            aggregated.append(summary)
    return aggregated

def compare_controller_performance(runs: List[Dict], metric: str) -> List[Dict]:
    result = []
    for run in runs:
        metrics = run.get("metrics", {})
        if metric in metrics:
            result.append({
                "run_id": run.get("run_id"),
                "controller": run.get("controller"),
                "world_mode": run.get("world_mode"),
                "seed": run.get("seed"),
                metric: metrics[metric],
            })
    return result

def write_comparison_csv(records: List[Dict], output_path: Path) -> None:
    if not records:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted(records[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)

def find_run_directories(root: Path) -> List[Path]:
    return [child for child in root.iterdir() if child.is_dir()]

def summarize_run_directories(root: Path, output_csv: Optional[Path] = None) -> List[Dict]:
    directories = find_run_directories(root)
    records = aggregate_summaries(directories)
    if output_csv is not None:
        write_comparison_csv(records, output_csv)
    return records
