"""
run_double_slit_diagnostics.py
==============================
Stage 15/16 diagnostics runner for the double-slit benchmark module.

This runner executes three controlled benchmark modes:
1. coherent
2. decohered
3. measurement

It writes:
- per-mode artifacts via write_all_artifacts
- one diagnostics JSON summary
- one diagnostics Markdown summary
- one diagnostics manifest

Scientific framing:
This is a controlled computational benchmark that reproduces expected behavior
under encoded model assumptions. It is not a standalone discovery engine.
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import sys
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.double_slit_sim import run_double_slit_sim, write_all_artifacts

_DEFAULT_OUTPUT_DIR = os.path.join(
    "outputs", "stage15_repo_diagnosis", "double_slit_validation"
)


def _normalise_pdf(values: List[float]) -> List[float]:
    total = sum(values)
    if total <= 0.0:
        if not values:
            return []
        return [1.0 / len(values)] * len(values)
    return [max(0.0, v) / total for v in values]


def _l1_distance(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        n = min(len(a), len(b))
        a = a[:n]
        b = b[:n]
    return 0.5 * sum(abs(x - y) for x, y in zip(_normalise_pdf(a), _normalise_pdf(b)))


def _js_divergence(a: List[float], b: List[float], eps: float = 1e-12) -> float:
    if len(a) != len(b):
        n = min(len(a), len(b))
        a = a[:n]
        b = b[:n]
    pa = _normalise_pdf(a)
    pb = _normalise_pdf(b)
    m = [(x + y) / 2.0 for x, y in zip(pa, pb)]

    def _kl(p: List[float], q: List[float]) -> float:
        out = 0.0
        for pi, qi in zip(p, q):
            if pi <= 0.0:
                continue
            out += pi * math.log(pi / max(qi, eps), 2)
        return out

    return 0.5 * _kl(pa, m) + 0.5 * _kl(pb, m)


def _count_local_extrema(values: List[float]) -> Dict[str, int]:
    peaks = 0
    troughs = 0
    if len(values) < 3:
        return {"peak_count": 0, "trough_count": 0}
    for i in range(1, len(values) - 1):
        left = values[i - 1]
        mid = values[i]
        right = values[i + 1]
        if mid > left and mid > right:
            peaks += 1
        if mid < left and mid < right:
            troughs += 1
    return {"peak_count": peaks, "trough_count": troughs}


def _run_mode(
    mode_name: str,
    output_dir: str,
    seed: Optional[int],
    common_kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    if mode_name == "coherent":
        kwargs = {
            "coherence": 1.0,
            "decoherence_strength": 0.0,
            "measurement_on": False,
        }
    elif mode_name == "decohered":
        kwargs = {
            "coherence": 1.0,
            "decoherence_strength": 0.7,
            "measurement_on": False,
        }
    elif mode_name == "measurement":
        kwargs = {
            "coherence": 1.0,
            "decoherence_strength": 0.0,
            "measurement_on": True,
        }
    else:
        raise ValueError(f"Unknown mode: {mode_name}")

    run_seed = None if seed is None else seed + {"coherent": 0, "decohered": 1, "measurement": 2}[mode_name]
    result = run_double_slit_sim(seed=run_seed, **common_kwargs, **kwargs)

    mode_dir = os.path.join(output_dir, mode_name)
    artifact_paths = write_all_artifacts(result, mode_dir, name=f"double_slit_{mode_name}")

    intensity = result.get("intensity", [])
    extrema = _count_local_extrema(intensity)
    summary = {
        "mode": mode_name,
        "visibility": result.get("visibility"),
        "coherence_score": result.get("coherence_score"),
        "interference_detected": result.get("interference_detected"),
        "regime": result.get("regime"),
        "alpha_effective": result.get("summary_stats", {}).get("alpha_effective"),
        "max_intensity": max(intensity) if intensity else None,
        "min_intensity": min(intensity) if intensity else None,
        "intensity_range": (max(intensity) - min(intensity)) if intensity else None,
        "peak_count": extrema["peak_count"],
        "trough_count": extrema["trough_count"],
        "artifact_paths": artifact_paths,
        "raw": result,
    }
    return summary


def run_double_slit_diagnostics(
    output_dir: str,
    name: str = "stage15_double_slit_diagnostics",
    wavelength: float = 500e-9,
    slit_separation: float = 1e-4,
    slit_width: float = 2e-5,
    screen_distance: float = 1.0,
    num_particles: int = 5000,
    screen_points: int = 500,
    noise_level: float = 0.0,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)

    common_kwargs = {
        "wavelength": wavelength,
        "slit_separation": slit_separation,
        "slit_width": slit_width,
        "screen_distance": screen_distance,
        "num_particles": num_particles,
        "screen_points": screen_points,
        "noise_level": noise_level,
    }

    coherent = _run_mode("coherent", output_dir, seed, common_kwargs)
    decohered = _run_mode("decohered", output_dir, seed, common_kwargs)
    measurement = _run_mode("measurement", output_dir, seed, common_kwargs)

    i_c = coherent["raw"].get("intensity", [])
    i_d = decohered["raw"].get("intensity", [])
    i_m = measurement["raw"].get("intensity", [])

    comparisons = {
        "visibility_drop_coherent_to_decohered": coherent["visibility"] - decohered["visibility"],
        "visibility_drop_coherent_to_measurement": coherent["visibility"] - measurement["visibility"],
        "l1_distance_coherent_vs_decohered": _l1_distance(i_c, i_d),
        "l1_distance_coherent_vs_measurement": _l1_distance(i_c, i_m),
        "js_divergence_coherent_vs_decohered": _js_divergence(i_c, i_d),
        "js_divergence_coherent_vs_measurement": _js_divergence(i_c, i_m),
    }

    expectations = {
        "coherent_interference_present": bool(coherent["interference_detected"]),
        "decohered_visibility_reduced": decohered["visibility"] < coherent["visibility"],
        "measurement_visibility_strongly_suppressed": measurement["visibility"] < 0.2,
        "measurement_below_coherent": measurement["visibility"] < coherent["visibility"],
    }

    summary = {
        "stage": 15,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "name": name,
        "scientific_framing": (
            "Controlled computational benchmark reproducing expected behavior "
            "under encoded physical assumptions; not a standalone discovery claim."
        ),
        "parameters": common_kwargs | {"seed": seed},
        "modes": {
            "coherent": {k: v for k, v in coherent.items() if k != "raw"},
            "decohered": {k: v for k, v in decohered.items() if k != "raw"},
            "measurement": {k: v for k, v in measurement.items() if k != "raw"},
        },
        "comparisons": comparisons,
        "expectations": expectations,
        "expectations_pass": all(expectations.values()),
        "limitations": [
            "This is a 1-D benchmark with encoded decoherence/measurement assumptions.",
            "It does not model full laboratory detector dynamics or full quantum measurement theory.",
            "It does not prove observer-caused collapse or that reality is a simulation.",
        ],
        "benchmark_readiness": "ready" if all(expectations.values()) else "needs_review",
    }

    json_path = os.path.join(output_dir, f"{name}.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")

    md_path = os.path.join(output_dir, f"{name}.md")
    lines: List[str] = []
    lines.append("# Double-Slit Diagnostics Summary")
    lines.append("")
    lines.append(f"Generated: {summary['generated_at']}")
    lines.append("")
    lines.append("## Scientific Framing")
    lines.append("")
    lines.append(summary["scientific_framing"])
    lines.append("")
    lines.append("## Mode Metrics")
    lines.append("")
    lines.append("| Mode | Visibility | Interference Detected | Regime | Alpha | Peaks | Troughs |")
    lines.append("|---|---:|---|---|---:|---:|---:|")
    for mode in ("coherent", "decohered", "measurement"):
        m = summary["modes"][mode]
        lines.append(
            f"| {mode} | {m['visibility']:.4f} | {m['interference_detected']} | "
            f"{m['regime']} | {m['alpha_effective']:.4f} | {m['peak_count']} | {m['trough_count']} |"
        )
    lines.append("")
    lines.append("## Distribution Comparisons")
    lines.append("")
    c = summary["comparisons"]
    lines.append(f"- Visibility drop (coherent -> decohered): {c['visibility_drop_coherent_to_decohered']:.4f}")
    lines.append(f"- Visibility drop (coherent -> measurement): {c['visibility_drop_coherent_to_measurement']:.4f}")
    lines.append(f"- L1 distance (coherent vs decohered): {c['l1_distance_coherent_vs_decohered']:.4f}")
    lines.append(f"- L1 distance (coherent vs measurement): {c['l1_distance_coherent_vs_measurement']:.4f}")
    lines.append(f"- JS divergence (coherent vs decohered): {c['js_divergence_coherent_vs_decohered']:.4f}")
    lines.append(f"- JS divergence (coherent vs measurement): {c['js_divergence_coherent_vs_measurement']:.4f}")
    lines.append("")
    lines.append("## Expectation Checks")
    lines.append("")
    for key, value in summary["expectations"].items():
        lines.append(f"- {key}: {'PASS' if value else 'FAIL'}")
    lines.append("")
    lines.append(f"Overall expectation status: **{'PASS' if summary['expectations_pass'] else 'FAIL'}**")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    for item in summary["limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Benchmark Readiness")
    lines.append("")
    lines.append(f"`{summary['benchmark_readiness']}`")

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    manifest = {
        "stage": 15,
        "name": name,
        "generated_at": summary["generated_at"],
        "summary_json": json_path,
        "summary_md": md_path,
        "output_dir": output_dir,
        "benchmark_readiness": summary["benchmark_readiness"],
        "expectations_pass": summary["expectations_pass"],
    }
    manifest_path = os.path.join(output_dir, f"{name}_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    return {
        "summary": summary,
        "json_path": json_path,
        "md_path": md_path,
        "manifest_path": manifest_path,
    }


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run three-mode double-slit diagnostics and write benchmark summary artifacts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--output-dir", default=_DEFAULT_OUTPUT_DIR, help="Output directory.")
    p.add_argument("--name", default="stage15_double_slit_diagnostics", help="Output file prefix.")
    p.add_argument("--wavelength", type=float, default=500e-9)
    p.add_argument("--slit-separation", type=float, default=1e-4)
    p.add_argument("--slit-width", type=float, default=2e-5)
    p.add_argument("--screen-distance", type=float, default=1.0)
    p.add_argument("--num-particles", type=int, default=5000)
    p.add_argument("--screen-points", type=int, default=500)
    p.add_argument("--noise-level", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=42)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    output_dir = args.output_dir
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(_REPO_ROOT, output_dir)

    result = run_double_slit_diagnostics(
        output_dir=output_dir,
        name=args.name,
        wavelength=args.wavelength,
        slit_separation=args.slit_separation,
        slit_width=args.slit_width,
        screen_distance=args.screen_distance,
        num_particles=args.num_particles,
        screen_points=args.screen_points,
        noise_level=args.noise_level,
        seed=args.seed,
    )

    summary = result["summary"]
    print("=" * 66)
    print(" DOUBLE-SLIT VALIDATION DIAGNOSTICS")
    print("=" * 66)
    for mode in ("coherent", "decohered", "measurement"):
        m = summary["modes"][mode]
        print(
            f" {mode:<12} visibility={m['visibility']:.4f} "
            f"interference={m['interference_detected']} regime={m['regime']}"
        )
    print(f" Expectations pass : {summary['expectations_pass']}")
    print(f" Benchmark ready   : {summary['benchmark_readiness']}")
    print(f" JSON summary      : {result['json_path']}")
    print(f" Markdown summary  : {result['md_path']}")
    print(f" Manifest          : {result['manifest_path']}")
    print("=" * 66)
    return 0 if summary["expectations_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
