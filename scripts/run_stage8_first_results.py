"""
Convenience runner for Stage 8 first real-catalog results.

Auto-detects a real catalog from data/real/ and runs the full Stage 8
first-results workflow.  If no real catalog is present, prints
instructional text and exits cleanly.

Usage
-----
    python scripts/run_stage8_first_results.py
"""
import os
import sys

# Resolve repo root regardless of cwd
_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from reality_audit.data_analysis.stage8_first_results import (
    discover_real_catalog,
    run_stage8_first_results,
    build_stage8_status_summary,
    _KNOWN_CATALOG_FILES,
)


def main() -> int:
    print("[Stage 8] Auto-detecting real catalog in data/real/ ...")
    discovery = discover_real_catalog()

    if not discovery["usable"]:
        supported = "\n  ".join(k["filename"] for k in _KNOWN_CATALOG_FILES)
        print(
            "\nNo real catalog found in data/real/.\n"
            "\nTo run Stage 8, place one of the following files there:\n"
            f"  {supported}\n"
            "\nSee data/real/README_public_catalog_ingest.md for download instructions.\n"
        )
        return 0  # Graceful exit; not an error condition for the convenience runner

    input_path = discovery["detected_path"]
    label      = discovery["detected_catalog_label"]
    name       = f"stage8_{label}"
    output_dir = os.path.join(_REPO_ROOT, "outputs", "stage8_first_results", name)

    print(f"[Stage 8] Found: {input_path}")
    print(f"[Stage 8] Running workflow: name={name!r} -> {output_dir}")

    bundle = run_stage8_first_results(
        input_path=input_path,
        output_dir=output_dir,
        name=name,
        null_repeats=100,
        axis_count=48,
        seed=42,
        plots=True,
        save_normalized=True,
    )

    status = build_stage8_status_summary(bundle)
    sig    = bundle.get("study_results", {}).get("signal_evaluation", {})

    print()
    print("=" * 60)
    print("  STAGE 8 CONVENIENCE RUNNER — SUMMARY")
    print("=" * 60)
    print(f"  Catalog   : {bundle.get('catalog_label')}")
    print(f"  Events    : {bundle.get('event_count')}")
    print(f"  Tier      : {sig.get('tier', 'unknown')}")
    print(f"  Max pct   : {sig.get('max_percentile', 0.0):.4f}")
    print(f"  Output    : {output_dir}")
    print(f"  Memo      : {bundle.get('memo_path')}")
    print("=" * 60)
    print()
    print("NOTE: This is an internal first-results package, not a scientific claim.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
