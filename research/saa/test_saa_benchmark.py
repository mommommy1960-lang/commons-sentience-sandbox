import csv
import tempfile
import unittest
from pathlib import Path

from saa_benchmark import evaluate


class BenchmarkTest(unittest.TestCase):
    def test_counts_and_missing_positive_class(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "intervals.csv"
            with path.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(("start_utc", "end_utc", "observed_hazard", "baseline_alert", "commons_alert"))
                writer.writerow(("2025-01-01T00:00:00Z", "2025-01-01T00:01:00Z", 1, 0, 1))
                writer.writerow(("2025-01-01T00:01:00Z", "2025-01-01T00:02:00Z", 0, 0, 1))
            result = evaluate(path)
            self.assertEqual(result["baseline"]["false_negative"], 1)
            self.assertEqual(result["commons"]["false_positive"], 1)
            self.assertEqual(result["commons"]["recall"], 1.0)


if __name__ == "__main__":
    unittest.main()
