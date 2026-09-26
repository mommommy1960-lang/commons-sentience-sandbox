#!/usr/bin/env python3
"""Pierre Auger UHECR rotational-symmetry screening test.

This is a conservative screening analysis aimed at one class of simulation-
hypothesis-adjacent prediction discussed by Beane, Davoudi & Savage (2014):
rotational-symmetry breaking in the highest-energy cosmic-ray arrival
distribution under a cubic-lattice scenario.

This script does NOT test 'the simulation hypothesis' in general. It tests
whether the public Auger highest-energy catalog shows unexpected right-
ascension harmonic structure under a uniform-RA null, with an explicit
look-elsewhere correction across predeclared energy subsets and harmonics.

The Auger surface detector has approximately uniform exposure in right
ascension at full efficiency, which makes RA harmonics a useful first screen.
Publication-grade work should still incorporate the collaboration's detailed
exposure corrections and a full spherical/cubic-symmetry statistic.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import urllib.request
from pathlib import Path

import numpy as np

CATALOG_URL = "https://opendata.auger.org/catalog/list/auger_catalogSD.csv"
NS = (20, 40, 60, 109)
HARMONICS = (1, 2, 3, 4, 6)


def _download_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8-sig")


def _parse_energy(value: str) -> float:
    # Public catalog values may look like '86±7'.
    value = value.strip()
    for sep in ("±", "+/-", "+-"):
        if sep in value:
            value = value.split(sep, 1)[0]
    return float(value)


def load_catalog(url: str = CATALOG_URL) -> list[dict]:
    text = _download_text(url)
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for raw in reader:
        norm = {str(k).strip().lower().replace(" ", "_"): v for k, v in raw.items() if k is not None}

        def first(*names):
            for name in names:
                if name in norm and str(norm[name]).strip() != "":
                    return norm[name]
            return None

        energy = first("energy_(eev)", "energy", "energy_eev")
        ra = first("α_(deg)", "alpha_(deg)", "ra", "alpha", "α")
        dec = first("δ_(deg)", "delta_(deg)", "dec", "delta", "δ")
        if energy is None or ra is None or dec is None:
            # Fallback by position for the current catalog schema:
            vals = list(raw.values())
            if len(vals) < 8:
                continue
            energy, dec, ra = vals[3], vals[6], vals[7]
        rows.append({
            "energy_eev": _parse_energy(str(energy)),
            "ra_deg": float(ra),
            "dec_deg": float(dec),
        })
    if len(rows) != 109:
        raise RuntimeError(f"Expected 109 catalog events, got {len(rows)}; schema/source may have changed")
    return rows


def harmonic_amplitude(ra_rad: np.ndarray, m: int) -> float:
    return float(np.abs(np.mean(np.exp(1j * m * ra_rad))))


def rayleigh_tail_approx(n: int, amplitude: np.ndarray | float) -> np.ndarray | float:
    return np.exp(-n * np.asarray(amplitude) ** 2)


def run(rows: list[dict], repeats: int, seed: int) -> dict:
    energies = np.array([r["energy_eev"] for r in rows], dtype=float)
    ra = np.deg2rad(np.array([r["ra_deg"] for r in rows], dtype=float))
    order = np.argsort(-energies)

    tests = []
    for n in NS:
        idx = order[:n]
        for m in HARMONICS:
            amp = harmonic_amplitude(ra[idx], m)
            p_approx = float(rayleigh_tail_approx(n, amp))
            tests.append({"n_highest_energy": n, "harmonic_m": m, "amplitude": amp, "p_approx": p_approx})

    # Joint look-elsewhere calibration. We preserve the nested energy subsets
    # within each simulated sky so correlations across N and m are retained.
    rng = np.random.default_rng(seed)
    min_p = np.ones(repeats, dtype=float)
    chunk = 5000
    done = 0
    while done < repeats:
        b = min(chunk, repeats - done)
        sim = rng.uniform(0.0, 2.0 * math.pi, size=(b, len(rows)))
        local_min = np.ones(b, dtype=float)
        for n in NS:
            idx = order[:n]
            for m in HARMONICS:
                amp = np.abs(np.mean(np.exp(1j * m * sim[:, idx]), axis=1))
                p = rayleigh_tail_approx(n, amp)
                local_min = np.minimum(local_min, p)
        min_p[done:done+b] = local_min
        done += b

    observed_min_p = min(t["p_approx"] for t in tests)
    global_p = float((1 + np.sum(min_p <= observed_min_p)) / (repeats + 1))
    best = min(tests, key=lambda t: t["p_approx"])

    return {
        "source": CATALOG_URL,
        "source_event_count": len(rows),
        "predeclared_energy_subsets": list(NS),
        "predeclared_ra_harmonics": list(HARMONICS),
        "monte_carlo_repeats": repeats,
        "seed": seed,
        "best_single_screen": best,
        "global_look_elsewhere_p": global_p,
        "all_tests": tests,
        "interpretation": (
            "Screen only. A low global p would justify a fuller exposure-aware spherical/cubic analysis; "
            "it would not establish a simulation ontology."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument("--output", default="outputs/auger_uhecr_lattice_screen_100k.json")
    args = parser.parse_args()
    result = run(load_catalog(), args.repeats, args.seed)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
