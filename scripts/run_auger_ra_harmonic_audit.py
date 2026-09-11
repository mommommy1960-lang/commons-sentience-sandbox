#!/usr/bin/env python3
"""Preregistered response-preserving RA harmonic audit for Auger Open Data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path

THRESHOLDS_EEV = (2.5, 4.0, 8.0, 16.0, 32.0)
SEED = 20260911
EXPECTED_ARCHIVE_SHA256 = "0499fb34d4d2bd968b1704ebc4cccace361b4841482994d2b4701816de18d8bd"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def load_sd1500(path: Path) -> list[dict]:
    rows = []
    seen = set()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            sdid = row.get("sdid", "")
            if not sdid or sdid in seen:
                continue
            seen.add(sdid)
            try:
                ra = float(row["sd_ra"])
                theta = float(row["sd_theta"])
                energy = float(row["sd_energy"])
                selected = int(row["sd1500"]) == 1
            except (KeyError, TypeError, ValueError):
                continue
            if not selected or theta > 60.0:
                continue
            if not all(math.isfinite(x) for x in (ra, theta, energy)):
                continue
            rows.append({"sdid": sdid, "ra_deg": ra % 360.0, "theta_deg": theta, "energy_eev": energy})
    return rows


def harmonic(ra_degrees: list[float]) -> dict:
    if not ra_degrees:
        return {"n": 0, "amplitude": None, "phase_deg": None}
    angles = [math.radians(x) for x in ra_degrees]
    c = sum(math.cos(x) for x in angles) / len(angles)
    s = sum(math.sin(x) for x in angles) / len(angles)
    return {
        "n": len(angles),
        "amplitude": math.hypot(c, s),
        "phase_deg": math.degrees(math.atan2(s, c)) % 360.0,
    }


def simulate_null_amplitudes(counts: list[int], repeats: int, seed: int) -> list[list[float]]:
    """Nested threshold nulls using one uniform-RA sequence per catalog."""
    import numpy as np

    rng = np.random.Generator(np.random.MT19937(seed))
    result = [[] for _ in counts]
    max_count = max(counts)
    # Bound peak memory while moving billions of trigonometric operations into
    # compiled NumPy loops. Every row remains one complete nested null catalog.
    for start in range(0, repeats, 256):
        size = min(256, repeats - start)
        angles = rng.random((size, max_count)) * (2.0 * math.pi)
        cs = np.cumsum(np.cos(angles), axis=1)
        ss = np.cumsum(np.sin(angles), axis=1)
        for i, count in enumerate(counts):
            amplitudes = np.hypot(cs[:, count - 1], ss[:, count - 1]) / count
            result[i].extend(amplitudes.tolist())
    return result


def empirical_upper(value: float, null: list[float]) -> float:
    return (1 + sum(x >= value for x in null)) / (len(null) + 1)


def global_min_p(observed_p: list[float], nulls: list[list[float]]) -> float:
    repeats = len(nulls[0])
    sorted_nulls = [sorted(values) for values in nulls]
    import bisect

    null_minima = []
    for i in range(repeats):
        ps = []
        for values, ordered in zip(nulls, sorted_nulls):
            # Upper-tail rank including the catalog itself.
            greater_equal = repeats - bisect.bisect_left(ordered, values[i])
            ps.append(greater_equal / repeats)
        null_minima.append(min(ps))
    observed_min = min(observed_p)
    return (1 + sum(p <= observed_min for p in null_minima)) / (repeats + 1)


def synthetic_calibration() -> dict:
    uniform = [i * 360.0 / 360 for i in range(360)]
    injected = [0.0] * 90 + uniform
    return {"uniform": harmonic(uniform), "injected_ra0": harmonic(injected)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--repeats", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output", default="outputs/auger_ra_harmonic/auger_ra_harmonic_100k.json")
    args = parser.parse_args()

    archive = Path(args.archive)
    archive_hash = sha256(archive)
    if archive_hash != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError(f"Auger archive provenance failure: {archive_hash}")

    rows = load_sd1500(Path(args.csv))
    # Sort descending so every threshold is a prefix and null catalogs preserve nesting.
    rows.sort(key=lambda row: row["energy_eev"], reverse=True)
    observed = []
    counts = []
    for threshold in THRESHOLDS_EEV:
        selected = [row["ra_deg"] for row in rows if row["energy_eev"] >= threshold]
        summary = harmonic(selected)
        summary["threshold_eev"] = threshold
        observed.append(summary)
        counts.append(summary["n"])
    if not counts or min(counts) == 0:
        raise RuntimeError("At least one frozen threshold has no selected events")

    nulls = simulate_null_amplitudes(counts, args.repeats, args.seed)
    local_ps = []
    for summary, null in zip(observed, nulls):
        p = empirical_upper(summary["amplitude"], null)
        summary["local_p"] = p
        summary["bonferroni_p"] = min(1.0, p * len(THRESHOLDS_EEV))
        local_ps.append(p)
    global_p = global_min_p(local_ps, nulls)

    result = {
        "decision": "NO_PROMOTION" if global_p > 0.01 else "PROVISIONAL_RESIDUAL_SYSTEMATICS_REQUIRED",
        "claim_boundary": "RA first-harmonic calibration; not simulation ontology and not unrestricted preferred-axis scan",
        "source": {"doi": "10.5281/zenodo.10488964", "archive_sha256": archive_hash, "csv_sha256": sha256(Path(args.csv))},
        "execution": {"revision": revision(), "seed": args.seed, "null_catalogs": args.repeats, "random_generator": "numpy.random.MT19937", "python": platform.python_version()},
        "selection": {"array": "SD1500 vertical", "zenith_max_deg": 60.0, "thresholds_eev": list(THRESHOLDS_EEV), "deduplicate": "first row per sdid"},
        "synthetic_calibration": synthetic_calibration(),
        "observed_tests": observed,
        "global_family_p": global_p,
        "limitations": [
            "Public 10% sample, not the full Auger dataset.",
            "RA scrambling assumes uniform sidereal exposure and preserves observed declination and energy structure.",
            "Previously published Auger anisotropy means a positive result may reproduce established science.",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
