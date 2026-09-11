#!/usr/bin/env python3
"""Run the frozen Fermi 2FLGC photon-timing v2 primary test."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from astropy.io import fits
from scipy.stats import rankdata


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/fermi_2flgc_photon_timing_v2.json"
CATALOG = ROOT / "data/real/fermi_2flgc_official/fermilgrb_heasarc_2022.tbl"
QUERY_DIR = ROOT / "data/real/fermi_2flgc_official/target_queries"
OUTPUT = ROOT / "outputs/fermi_2flgc/fermi_2flgc_timing_v2_100k.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_catalog(path: Path) -> dict[str, dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = [value.strip() for value in lines[1].strip("|").split("|")]
    records = {}
    for line in lines:
        if line.startswith("|GRB"):
            values = [value.strip() for value in line.strip("|").split("|")]
            record = dict(zip(header, values))
            records[record["name"]] = record
    return records


def ra_deg(value: str) -> float:
    h, m, s = map(float, value.split())
    return 15.0 * (h + m / 60.0 + s / 3600.0)


def dec_deg(value: str) -> float:
    sign = -1.0 if value.startswith("-") else 1.0
    d, m, s = map(float, value.lstrip("+-").split())
    return sign * (d + m / 60.0 + s / 3600.0)


def angular_sep_deg(ra1, dec1, ra2: float, dec2: float):
    ra1 = np.deg2rad(ra1)
    dec1 = np.deg2rad(dec1)
    ra2 = np.deg2rad(ra2)
    dec2 = np.deg2rad(dec2)
    cosine = np.sin(dec1) * np.sin(dec2) + np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2)
    return np.rad2deg(np.arccos(np.clip(cosine, -1.0, 1.0)))


def centered_ranks(values: np.ndarray) -> np.ndarray:
    ranks = rankdata(values, method="average")
    return ranks - ranks.mean()


def correlation(x: np.ndarray, y: np.ndarray) -> float:
    denom = np.sqrt(np.dot(x, x) * np.dot(y, y))
    return float(np.dot(x, y) / denom) if denom else 0.0


def run() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    catalog = read_catalog(CATALOG)
    selection = config["event_selection"]
    groups = []
    source_rows = []
    catalog_fits = ROOT / "data/real/fermi_2flgc_official/fermilgrb_heasarc_2022.fits"
    input_files = {
        str(CATALOG.relative_to(ROOT)): sha256(CATALOG),
        str(catalog_fits.relative_to(ROOT)): sha256(catalog_fits),
    }

    for source in config["targets"]:
        record = catalog[source]
        event_file = next(QUERY_DIR.glob(f"{source}_*EV00.fits"))
        spacecraft_file = next(QUERY_DIR.glob(f"{source}_*SC00.fits"))
        input_files[str(event_file.relative_to(ROOT))] = sha256(event_file)
        input_files[str(spacecraft_file.relative_to(ROOT))] = sha256(spacecraft_file)
        with fits.open(event_file, memmap=False) as hdus:
            events = hdus["EVENTS"].data
            dt = np.asarray(events["TIME"], dtype=float) - float(record["trigger_met"])
            energy = np.asarray(events["ENERGY"], dtype=float)
            zenith = np.asarray(events["ZENITH_ANGLE"], dtype=float)
            sep = angular_sep_deg(
                np.asarray(events["RA"], dtype=float),
                np.asarray(events["DEC"], dtype=float),
                ra_deg(record["ra"]),
                dec_deg(record["dec"]),
            )
            mask = (
                (dt >= selection["analysis_time_start_trigger_relative_s"])
                & (dt <= selection["analysis_time_stop_trigger_relative_s"])
                & (energy >= selection["energy_min_mev"])
                & (zenith <= selection["zenith_max_deg"])
                & (sep <= selection["angular_separation_max_deg"])
            )
            selected_t = dt[mask]
            selected_e = energy[mask]
        if len(selected_t) >= selection["minimum_events_per_grb"]:
            groups.append((centered_ranks(np.log10(selected_e)), centered_ranks(selected_t)))
        source_rows.append({
            "source": source,
            "redshift": float(record["redshift"]),
            "query_rows": int(len(events)),
            "selected_rows": int(mask.sum()),
            "included": bool(mask.sum() >= selection["minimum_events_per_grb"]),
        })

    total = sum(len(x) for x, _ in groups)
    if len(groups) < selection["minimum_grbs"] or total < selection["minimum_total_events"]:
        status = "STOP_INSUFFICIENT_EVENTS"
        observed = None
        p_value = None
        exceedances = None
    else:
        x = np.concatenate([pair[0] for pair in groups])
        y = np.concatenate([pair[1] for pair in groups])
        observed = correlation(x, y)
        n_null = int(config["null"]["catalogs"])
        rng = np.random.default_rng(int(config["null"]["seed"]))
        exceedances = 0
        for _ in range(n_null):
            xp = np.concatenate([rng.permutation(pair[0]) for pair in groups])
            if abs(correlation(xp, y)) >= abs(observed):
                exceedances += 1
        p_value = (exceedances + 1) / (n_null + 1)
        status = "NO_PROMOTION" if p_value >= 0.05 else "RESIDUAL_REQUIRES_SYSTEMATICS"

    result = {
        "schema_version": "1.0",
        "experiment_name": config["experiment_name"],
        "status": status,
        "config_sha256": sha256(CONFIG),
        "analysis_script_sha256": sha256(Path(__file__)),
        "code_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "catalog_original_rows": sum(r["time"] < "2018-08-04" for r in catalog.values()),
        "catalog_total_rows": len(catalog),
        "published_fact_reproduction": {
            "original_rows_expected_186": sum(r["time"] < "2018-08-04" for r in catalog.values()) == 186,
            "original_lle_detected": sum(
                int(r["lle_bbbd_sig_detected"] or 0) == 1 and r["time"] < "2018-08-04"
                for r in catalog.values()
            ),
            "original_lat_detected_su_tsinput_positive": sum(
                float(r["su_tsinput"] or 0) > 0 and r["time"] < "2018-08-04"
                for r in catalog.values()
            ),
        },
        "sources": source_rows,
        "included_sources": len(groups),
        "selected_events": total,
        "observed_statistic": observed,
        "null_catalogs": int(config["null"]["catalogs"]),
        "seed": int(config["null"]["seed"]),
        "null_exceedances": exceedances,
        "plus_one_two_sided_p": p_value,
        "input_sha256": input_files,
        "interpretation": "This result is not evidence for simulation ontology. Promotion is forbidden without the response, systematic, trial-control, and independent-replication gates in the frozen configuration.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    print(json.dumps(run(), indent=2))
