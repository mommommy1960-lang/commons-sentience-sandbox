#!/usr/bin/env python3
"""Response-informed IceCube HESE hemisphere diagnostic using official public MC.

This is an intermediate Stage 16 diagnostic, not a publication-grade IceCube
analysis. It uses IceCube's public 7.5-year data/MC arrays and the same basic
reconstructed energy/double-cascade-length cuts as their example loader.

It deliberately does NOT claim full collaboration-likelihood reproduction:
detector-systematic PHOTOSPLINE corrections and a fitted nuisance-parameter
posterior are not applied here. The output labels that limitation explicitly.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

BASE = "https://raw.githubusercontent.com/icecube/HESE-7-year-data-release/main/HESE-7-year-data-release/resources/data"
FILES = {
    "data": "HESE_data.json",
    "observable": "HESE_mc_observable.json",
    "flux": "HESE_mc_flux.json",
    "truth": "HESE_mc_truth.json",
}


def _download(name: str, cache: Path) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    filename = FILES[name]
    path = cache / filename
    if not path.exists():
        urllib.request.urlretrieve(f"{BASE}/{filename}", path)
    return path


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _selected_indices(payload: dict, emin=60_000.0, emax=10_000_000.0) -> List[int]:
    energies = payload["recoDepositedEnergy"]
    morph = payload["recoMorphology"]
    lengths = payload["recoLength"]
    out = []
    for i, (energy, topology, length) in enumerate(zip(energies, morph, lengths)):
        energy = float(energy)
        if not (emin <= energy <= emax):
            continue
        if int(topology) == 2:
            try:
                length_value = float(length)
            except (TypeError, ValueError):
                continue
            if math.isnan(length_value) or not (10.0 <= length_value <= 1000.0):
                continue
        out.append(i)
    return out


def _north(reco_zenith_rad: float) -> bool:
    # At the South Pole, dec = degrees(zenith) - 90.
    return float(reco_zenith_rad) >= math.pi / 2.0


def _fraction(weights: Iterable[Tuple[bool, float]]) -> dict:
    north = 0.0
    south = 0.0
    for is_north, weight in weights:
        if not math.isfinite(weight) or weight < 0:
            continue
        if is_north:
            north += weight
        else:
            south += weight
    total = north + south
    return {
        "north_weight": north,
        "south_weight": south,
        "north_fraction": (north / total) if total else None,
        "total_weight": total,
    }


def _flux_power_law(energy: float, norm: float, gamma: float, pivot: float) -> float:
    return norm * (energy / pivot) ** (-gamma)


def _component_weights(mc: dict, indices: List[int], params: dict) -> Dict[str, dict]:
    astro = []
    conv = []
    prompt = []
    muon = []
    total = []

    for i in indices:
        energy = float(mc["primaryEnergy"][i])
        zen = float(mc["recoZenith"][i])
        nflag = _north(zen)
        base = float(mc["weightOverFluxOverLivetime"][i])

        astro_flux = (
            _flux_power_law(energy, params["astro_norm"], params["astro_gamma"], 1.0e5)
            * 1.0e-18 / 6.0
        )
        astro_w = base * astro_flux

        tilt_conv = _flux_power_law(
            energy, params["conv_norm"], params["cr_delta_gamma"], 2020.0
        )
        conv_flux = (
            float(mc["pionFlux"][i]) + params["kpi_ratio"] * float(mc["kaonFlux"][i])
        ) * tilt_conv
        conv_w = base * conv_flux * float(mc["conventionalSelfVetoCorrection"][i])

        tilt_prompt = _flux_power_law(
            energy, params["prompt_norm"], params["cr_delta_gamma"], 7887.0
        )
        prompt_flux = float(mc["promptFlux"][i]) * tilt_prompt
        prompt_w = base * prompt_flux * float(mc["promptSelfVetoCorrection"][i])

        muon_w = params["muon_norm"] * float(mc["muonWeightOverLivetime"][i])
        total_w = astro_w + conv_w + prompt_w + muon_w

        astro.append((nflag, astro_w))
        conv.append((nflag, conv_w))
        prompt.append((nflag, prompt_w))
        muon.append((nflag, muon_w))
        total.append((nflag, total_w))

    return {
        "astrophysical": _fraction(astro),
        "conventional_atmospheric_nu": _fraction(conv),
        "prompt_atmospheric_nu": _fraction(prompt),
        "atmospheric_muon": _fraction(muon),
        "nominal_mixture_no_spline_systematics": _fraction(total),
    }


def _binomial_lower_tail(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p**i * (1.0-p)**(n-i) for i in range(k+1))


def _binomial_exact_two_sided(k: int, n: int, p: float) -> float:
    pk = math.comb(n, k) * p**k * (1-p)**(n-k)
    total = 0.0
    for i in range(n+1):
        pi = math.comb(n, i) * p**i * (1-p)**(n-i)
        if pi <= pk + 1e-15:
            total += pi
    return min(1.0, total)


def _mc_tail(k: int, n: int, p: float, repeats: int, seed: int) -> float:
    rng = random.Random(seed)
    hits = 0
    for _ in range(repeats):
        north = sum(rng.random() < p for _ in range(n))
        if north <= k:
            hits += 1
    return hits / repeats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default=".cache/icecube_hese_7yr")
    parser.add_argument("--output", default="outputs/icecube_response_audit/official_mc_response_100k.json")
    parser.add_argument("--repeats", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20260910)
    args = parser.parse_args()

    cache = Path(args.cache)
    paths = {name: _download(name, cache) for name in FILES}
    data = _load_json(paths["data"])
    mc = {}
    for key in ("observable", "flux", "truth"):
        mc.update(_load_json(paths[key]))

    required = {
        "primaryEnergy", "recoDepositedEnergy", "recoZenith", "recoLength", "recoMorphology",
        "weightOverFluxOverLivetime", "muonWeightOverLivetime", "pionFlux", "kaonFlux", "promptFlux",
        "conventionalSelfVetoCorrection", "promptSelfVetoCorrection",
    }
    missing = sorted(required - set(mc))
    if missing:
        raise RuntimeError(f"Official MC package missing required fields: {missing}")

    data_idx = _selected_indices(data)
    data_north = sum(_north(data["recoZenith"][i]) for i in data_idx)
    data_n = len(data_idx)

    mc_idx = _selected_indices(mc)
    # Intermediate response diagnostic. Astro best-fit central values are from
    # Phys. Rev. D 104, 022002. Background/systematic nuisance parameters here
    # remain nominal, not refitted.
    params = {
        "astro_gamma": 2.87,
        "astro_norm": 6.37,
        "conv_norm": 1.0,
        "prompt_norm": 1.0,
        "muon_norm": 1.0,
        "kpi_ratio": 1.0,
        "cr_delta_gamma": -0.05,
    }
    components = _component_weights(mc, mc_idx, params)

    tests = {}
    for name, summary in components.items():
        p = summary["north_fraction"]
        if p is None:
            continue
        tests[name] = {
            "expected_north_fraction": p,
            "observed_north": data_north,
            "observed_total": data_n,
            "lower_tail_exact": _binomial_lower_tail(data_north, data_n, p),
            "two_sided_exact": _binomial_exact_two_sided(data_north, data_n, p),
            "lower_tail_monte_carlo": _mc_tail(data_north, data_n, p, args.repeats, args.seed),
            "monte_carlo_repeats": args.repeats,
        }

    result = {
        "source": "IceCube HESE 7.5-year public release, DOI 10.21234/4EQJ-BB17",
        "analysis_reference": "PhysRevD.104.022002",
        "selection": {
            "reco_deposited_energy_gev": [60_000.0, 10_000_000.0],
            "double_cascade_length_m": [10.0, 1000.0],
        },
        "observed_selected": {
            "n": data_n,
            "north": data_north,
            "south": data_n - data_north,
            "north_fraction": data_north / data_n if data_n else None,
        },
        "mc_selected_count": len(mc_idx),
        "parameters": params,
        "component_response": components,
        "hemisphere_tests": tests,
        "quality_tier": "RESPONSE_INFORMED_INTERMEDIATE_NOT_PUBLICATION_GRADE",
        "limitations": [
            "Uses official MC response weights and official basic cuts, but does not apply PHOTOSPLINE detector-systematic corrections.",
            "Astrophysical central values are fixed; atmospheric and detector nuisance parameters are not refitted to this dataset.",
            "A hemisphere count compresses directional/energy information and is not the collaboration likelihood.",
            "This diagnostic must not be described as an IceCube discovery test or as evidence for simulation ontology.",
        ],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
