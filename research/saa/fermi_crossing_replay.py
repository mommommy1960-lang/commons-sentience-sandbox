"""Exploratory Fermi GBM SAA crossing classification, never a radiation-safety claim.

Train on an earlier daily GBM position-history FITS file and evaluate on a later one.
Baseline: fixed circle centered at 25 S, 45 W, radius fit on training day.
Candidate: nearest-neighbor geographical map from the training day.
Both use the actual position in the test file: this is NOT advance forecasting.
NASA files: https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/daily/
"""

import argparse
import json

import numpy as np
from astropy.io import fits
from matplotlib.path import Path
from sklearn.neighbors import KNeighborsClassifier

# Public NASA ACROSS Fermi GBM SAA polygon as viewed 2026-09-29;
# https://app.across.sciencecloud.nasa.gov/observatories/Fermi
# Coordinates are (longitude, latitude). This snapshot may not represent
# the exact operational contour in January 2025.
NASA_ACROSS_POLYGON = [(33.9, -30), (24.5, -22.6), (-18.6, 2.5),
                       (-25.7, 5.2), (-36, 5.2), (-42, 4.6),
                       (-58.8, 0.7), (-93.1, -8.6), (-97.5, -9.9),
                       (-98.5, -12.5), (-92.1, -21.7), (-86.1, -30)]


def load(path):
    with fits.open(path) as hdus:
        table = hdus["GLAST POS HIST"].data
        # 30-second sampling keeps the spatial model lightweight.
        x = np.column_stack((table["SC_LAT"][::30], table["SC_LON"][::30]))
        # GBM longitudes are 0..360; the published contour uses -180..180.
        x[:, 1] = (x[:, 1] + 180) % 360 - 180
        # Fermi GBM public data tools define bit 0x02 as the SAA state.
        y = (np.asarray(table["FLAGS"][::30], dtype=np.int64) & 0x02) != 0
        times = np.asarray(table["SCLK_UTC"][::30])
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
    # Daily GBM files include a brief overlap at UTC midnight. Discard the
    # overlap from training so no evaluation timestamp enters the fit.
    keep = train_time < min(test_time)
    train_x, train_y, train_time = train_x[keep], train_y[keep], train_time[keep]
    if not len(train_time) or max(train_time) >= min(test_time):
        raise ValueError("Training intervals must precede evaluation intervals")
    if not train_y.any() or not test_y.any():
        raise ValueError("GBM flags contain no positive SAA crossings in the selected files")
    train_dist = circle_distance(train_x)
    # Lock radius from training day only. Grid in degrees, optimize F1.
    choices = np.radians(np.arange(5, 61, 0.5))
    def f1(radius):
        predicted = train_dist <= radius
        m = metrics(train_y, predicted)
        denominator = 2 * m["tp"] + m["fp"] + m["fn"]
        return 2 * m["tp"] / denominator if denominator else 0
    radius = max(choices, key=f1)
    baseline = circle_distance(test_x) <= radius
    nasa_published_contour = Path(NASA_ACROSS_POLYGON).contains_points(test_x[:, [1, 0]])
    candidate = KNeighborsClassifier(n_neighbors=31, metric="haversine", weights="distance")
    candidate.fit(np.radians(train_x), train_y)
    mapped = candidate.predict(np.radians(test_x)).astype(bool)
    return {"train_intervals": len(train_y), "test_intervals": len(test_y),
            "test_saa_intervals": int(test_y.sum()),
            "baseline_circle_radius_degrees": round(float(np.degrees(radius)), 1),
            "baseline": metrics(test_y, baseline),
            "nasa_across_published_polygon_snapshot": metrics(test_y, nasa_published_contour),
            "prior_day_map": metrics(test_y, mapped),
            "limitations": "GBM SAA is an operational crossing flag, not radiation dose or component errors; both methods use test-time coordinates and cannot establish forecast lead time, protection, or superiority over NASA/ESA tools."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("earlier_day_fits")
    parser.add_argument("later_day_fits")
    args = parser.parse_args()
    print(json.dumps(replay(args.earlier_day_fits, args.later_day_fits), indent=2))
