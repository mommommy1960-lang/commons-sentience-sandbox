"""
example_event_data.py
=====================
Generate a small synthetic example event catalog for testing and demonstration.

This data is ENTIRELY SYNTHETIC.  It does not represent real observations
from any instrument.  It is provided solely to make the simulation_signature_analysis
pipeline runnable out of the box.

Usage
-----
    python reality_audit/data_analysis/example_event_data.py

    # or from Python:
    from reality_audit.data_analysis.example_event_data import generate_example_event_dataset
    events = generate_example_event_dataset(n=500, seed=42)
"""

from __future__ import annotations

import csv
import math
import os
import random
from typing import Any, Dict, List, Optional


def generate_example_event_dataset(
    n: int = 300,
    seed: Optional[int] = 42,
    output_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Generate a list of synthetic astrophysical-style event records.

    Parameters
    ----------
    n           : number of events to generate
    seed        : RNG seed for reproducibility
    output_path : if provided, write CSV to this path

    Returns a list of dicts with keys:
      event_id, energy, arrival_time, ra, dec, instrument, epoch

    Energy is drawn log-uniformly from 0.1–100 GeV (illustrative scale).
    Arrival time is drawn uniformly from MJD 58000–59000 (illustrative).
    RA/Dec are drawn isotropically on the sphere.
    Instrument cycles over a small example set.
    """
    rng = random.Random(seed)
    instruments = ["EXAMPLE-A", "EXAMPLE-B", "EXAMPLE-C"]
    epochs      = ["epoch_1", "epoch_2", "epoch_3"]

    events: List[Dict[str, Any]] = []
    for i in range(n):
        # Isotropic sky position
        cos_dec = rng.uniform(-1.0, 1.0)
        dec     = math.degrees(math.asin(cos_dec))
        ra      = rng.uniform(0.0, 360.0)

        # Log-uniform energy 0.1–100 GeV
        log_e   = rng.uniform(math.log(0.1), math.log(100.0))
        energy  = math.exp(log_e)

        # Uniform arrival time MJD 58000–59000
        arrival_time = rng.uniform(58000.0, 59000.0)

        events.append({
            "event_id":    f"SYNTH_{i:05d}",
            "energy":      round(energy, 6),
            "arrival_time": round(arrival_time, 6),
            "ra":          round(ra, 6),
            "dec":         round(dec, 6),
            "instrument":  instruments[i % len(instruments)],
            "epoch":       epochs[i % len(epochs)],
        })

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fieldnames = ["event_id", "energy", "arrival_time", "ra", "dec",
                      "instrument", "epoch"]
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(events)

    return events


# ---------------------------------------------------------------------------
# CLI entry point: regenerate the sample data file on demand
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    out = "data/real/example_event_catalog.csv"
    rows = generate_example_event_dataset(n=300, seed=42, output_path=out)
    print(f"Wrote {len(rows)} synthetic example events to {out}")
    print("NOTE: This data is entirely synthetic and does not represent "
          "real observations.")
