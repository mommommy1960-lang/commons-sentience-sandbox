"""Compare predeclared SAA alerts against observed hazardous intervals.

Input is a CSV with one row per nonoverlapping time interval and columns:
start_utc,end_utc,observed_hazard,baseline_alert,commons_alert.
The observed_hazard label must come from independent instrument telemetry;
IN_SAA alone is an operational crossing flag, not a radiation upset.
Alerts must be generated using information available before start_utc.
"""

import argparse
import csv
import json
from datetime import datetime, timezone


def instant(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamps must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def score(rows, column):
    tp = fp = fn = tn = 0
    for row in rows:
        actual, alert = row["observed_hazard"], row[column]
        if actual == 1 and alert == 1:
            tp += 1
        elif actual == 0 and alert == 1:
            fp += 1
        elif actual == 1 and alert == 0:
            fn += 1
        else:
            tn += 1
    return {"true_positive": tp, "false_positive": fp,
            "false_negative": fn, "true_negative": tn,
            "recall": tp / (tp + fn) if tp + fn else None,
            "precision": tp / (tp + fp) if tp + fp else None,
            "false_alarm_rate": fp / (fp + tn) if fp + tn else None}


def evaluate(path):
    required = {"start_utc", "end_utc", "observed_hazard", "baseline_alert", "commons_alert"}
    rows = []
    previous_end = None
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("CSV missing required columns: " + ", ".join(sorted(required)))
        for row in reader:
            start, end = instant(row["start_utc"]), instant(row["end_utc"])
            if end <= start or (previous_end is not None and start < previous_end):
                raise ValueError("Intervals must be positive, chronological and nonoverlapping")
            previous_end = end
            for key in ("observed_hazard", "baseline_alert", "commons_alert"):
                if row[key] not in ("0", "1"):
                    raise ValueError(key + " must be 0 or 1")
                row[key] = int(row[key])
            rows.append(row)
    if not rows:
        raise ValueError("No intervals supplied")
    return {"intervals": len(rows), "baseline": score(rows, "baseline_alert"),
            "commons": score(rows, "commons_alert"),
            "note": "Descriptive replay only; does not prove radiation protection or operational safety."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.csv_file), indent=2))
