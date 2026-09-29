"""Exploratory Fermi SAA crossing classification, never a radiation-safety claim.

Train on an earlier weekly spacecraft FITS file and evaluate on a later one.
Baseline: fixed circle centered at 25 S, 45 W, radius fit on training week.
Candidate: nearest-neighbor geographical map from the training week.
Both use the actual position in the test file: this is NOT advance forecasting.
NASA files: https://heasarc.gsfc.nasa.gov/FTP/fermi/data/lat/weekly/spacecraft/
"""

import argparse
import json

import numpy as np
from astropy.io import fits
from sklearn.neighbors import KNeighborsClassifier


def load(path):
    with fits.open(path) as hdus:
        table = hdus["SC_DATA"].data
        x = np.column_stack((table["LAT_GEO"], table["LON_GEO"]))
        y = np.asarray(table["IN_SAA"], dtype=bool)
        times = np.asarray(table["START"])
    return x, y, times


def circle_distance(x):
    # Approximate great-circle distance in radians, useful near this SAA region.
    lat, lon = np.radians(x[:, 0]), np.radians(x[:, 1])
    center_lat, center_lon = np.radians((-25, -45))
    delta = np.sin((lat - center_lat) / 2) ** 2 + np.cos(lat) * np.cos(center_lat) * np.sin((lon - center_lon) / 2) ** 2
    return 2 * np.arcsin(np.sqrt(np.clip(delta, 0, 1)))


def metrics(truth, predicted):
    tp = int(np.sum(truth & predicted))
    fn = int(np.sum(truth & ~predicted))
    fp = int(np.sum(~truth & predicted))
    tn = int(np.sum(~truth & ~predicted))
    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "recall": tp / (tp + fn) if tp + fn else None,
            "precision": tp / (tp + fp) if tp + fp else None,
            "false_alarm_rate": fp / (fp + tn) if fp + tn else None}


def replay(train_path, test_path):
    train_x, train_y, train_time = load(train_path)
    test_x, test_y, test_time = load(test_path)
    if max(train_time) >= min(test_time):
        raise ValueError("Training intervals must precede evaluation intervals")
    if not train_y.any() or not test_y.any():
        raise ValueError("IN_SAA contains no positive crossings in the selected weekly files; cannot benchmark this label")
    train_dist = circle_distance(train_x)
    # Lock radius from training week only. Grid in degrees, optimize F1.
    choices = np.radians(np.arange(5, 61, 0.5))
    def f1(radius):
        predicted = train_dist <= radius
        m = metrics(train_y, predicted)
        denominator = 2 * m["tp"] + m["fp"] + m["fn"]
        return 2 * m["tp"] / denominator if denominator else 0
    radius = max(choices, key=f1)
    baseline = circle_distance(test_x) <= radius
    candidate = KNeighborsClassifier(n_neighbors=31, metric="haversine", weights="distance")
    candidate.fit(np.radians(train_x), train_y)
    mapped = candidate.predict(np.radians(test_x)).astype(bool)
    return {"train_intervals": len(train_y), "test_intervals": len(test_y),
            "test_saa_intervals": int(test_y.sum()),
            "baseline_circle_radius_degrees": round(float(np.degrees(radius)), 1),
            "baseline": metrics(test_y, baseline), "prior_week_map": metrics(test_y, mapped),
            "limitations": "IN_SAA is an operational crossing flag, not radiation dose or component errors; both methods use test-time coordinates and cannot establish forecast lead time, protection, or superiority over NASA/ESA tools."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("earlier_week_fits")
    parser.add_argument("later_week_fits")
    args = parser.parse_args()
    print(json.dumps(replay(args.earlier_week_fits, args.later_week_fits), indent=2))
