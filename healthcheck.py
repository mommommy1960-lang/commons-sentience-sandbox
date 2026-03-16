"""
healthcheck.py — Health check for Commons Sentience Sandbox v1.0.

Verifies that the repository is correctly set up and all components are working.
Run this before your first simulation or after upgrading.

Usage
-----
  python healthcheck.py
  python healthcheck.py --verbose
"""
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Result collector
# ---------------------------------------------------------------------------

_PASS = "\u2705"
_FAIL = "\u274c"
_WARN = "\u26a0\ufe0f"

results: list[tuple[str, bool, str]] = []  # (label, ok, detail)


def check(label: str, ok: bool, detail: str = "") -> bool:
    results.append((label, ok, detail))
    return ok


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_python_version() -> None:
    major, minor = sys.version_info[:2]
    ok = major == 3 and minor >= 9
    check(
        "Python version >= 3.9",
        ok,
        f"Python {major}.{minor}" + ("" if ok else " — upgrade required"),
    )


def check_required_files() -> None:
    required = [
        "run_sim.py",
        "evaluation.py",
        "session_manager.py",
        "scenario_designer.py",
        "experiment_config.py",
        "run_experiments.py",
        "replay_session.py",
        "compare_sessions.py",
        "plot_state.py",
        "dashboard.py",
        "requirements.txt",
        "README.md",
        "RELEASE_NOTES_v1.md",
        "quickstart.py",
    ]
    for fname in required:
        p = ROOT / fname
        check(f"File exists: {fname}", p.exists(), str(p) if not p.exists() else "")


def check_data_files() -> None:
    data_dir = ROOT / "commons_sentience_sim" / "data"
    required_data = ["rooms.json", "rules.json", "scenario_events.json"]
    for fname in required_data:
        p = data_dir / fname
        ok = p.exists()
        check(f"Data file: data/{fname}", ok, "" if ok else f"Missing: {p}")
        if ok:
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                check(f"  JSON valid: data/{fname}", False, str(e))


def check_experiment_configs() -> None:
    exp_dir = ROOT / "experiments"
    if not exp_dir.exists():
        check("experiments/ directory exists", False, str(exp_dir))
        return
    check("experiments/ directory exists", True)
    configs = list(exp_dir.glob("*.json"))
    check(
        f"Experiment configs present ({len(configs)} found)",
        len(configs) >= 1,
        ", ".join(p.name for p in configs),
    )
    for p in configs:
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            check(f"  JSON valid: experiments/{p.name}", False, str(e))


def check_scenarios() -> None:
    try:
        from scenario_designer import list_available_scenarios, validate_scenario, load_scenario
    except ImportError as e:
        check("scenario_designer importable", False, str(e))
        return
    check("scenario_designer importable", True)

    scenarios = list_available_scenarios()
    check(
        f"Scenarios discoverable ({len(scenarios)} found)",
        len(scenarios) >= 1,
        ", ".join(s["name"] for s in scenarios),
    )
    for s in scenarios:
        p = Path(s["path"])
        data = load_scenario(p)
        issues = validate_scenario(data)
        check(
            f"  Scenario valid: {s['name']}",
            not issues,
            "; ".join(issues) if issues else "",
        )


def check_output_directory() -> None:
    out_dir = ROOT / "commons_sentience_sim" / "output"
    check("Output directory exists", out_dir.exists(), str(out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)


def check_sessions_directory() -> None:
    sess_dir = ROOT / "sessions"
    check("sessions/ directory exists", sess_dir.exists(), str(sess_dir))
    sess_dir.mkdir(parents=True, exist_ok=True)


def check_python_imports() -> None:
    modules = [
        ("json", "json (stdlib)"),
        ("csv", "csv (stdlib)"),
        ("pathlib", "pathlib (stdlib)"),
        ("datetime", "datetime (stdlib)"),
        ("matplotlib", "matplotlib"),
    ]
    for mod_name, label in modules:
        try:
            importlib.import_module(mod_name)
            check(f"Import: {label}", True)
        except ImportError:
            check(f"Import: {label}", False, f"pip install {mod_name}")

    # streamlit is optional (only needed for dashboard)
    try:
        importlib.import_module("streamlit")
        check("Import: streamlit (dashboard)", True)
    except ImportError:
        check("Import: streamlit (dashboard)", False, "pip install streamlit  [optional, for dashboard]")


def check_core_modules() -> None:
    core_modules = [
        "commons_sentience_sim.core.agent",
        "commons_sentience_sim.core.memory",
        "commons_sentience_sim.core.governance",
        "commons_sentience_sim.core.reflection",
        "commons_sentience_sim.core.relationships",
        "commons_sentience_sim.core.values",
        "commons_sentience_sim.core.world",
        "commons_sentience_sim.core.tasks",
    ]
    sys.path.insert(0, str(ROOT))
    for mod in core_modules:
        try:
            importlib.import_module(mod)
            check(f"Core module: {mod.split('.')[-1]}", True)
        except Exception as e:
            check(f"Core module: {mod.split('.')[-1]}", False, str(e))


def check_existing_output() -> None:
    out_dir = ROOT / "commons_sentience_sim" / "output"
    key_outputs = [
        ("multi_agent_state.json", True),
        ("evaluation_report.json", True),
        ("narrative_log.md", False),
        ("state_history.csv", False),
    ]
    for fname, required in key_outputs:
        p = out_dir / fname
        if required:
            check(f"Output exists: {fname}", p.exists(), "Run python run_sim.py to generate" if not p.exists() else "")
        elif p.exists():
            check(f"Output exists: {fname}", True, "")
        # skip optional outputs that are absent


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(verbose: bool) -> int:
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    total = len(results)

    print()
    print("=" * 60)
    print("  Commons Sentience Sandbox v1.0 — Health Check")
    print("=" * 60)

    for label, ok, detail in results:
        if not ok or verbose:
            icon = _PASS if ok else _FAIL
            line = f"  {icon}  {label}"
            if detail and not ok:
                line += f"\n       {detail}"
            print(line)

    print()
    if failed == 0:
        print(f"  {_PASS}  All {total} checks passed.")
    else:
        print(f"  {_FAIL}  {failed} of {total} checks failed — see details above.")
    print("=" * 60)
    print()
    return 0 if failed == 0 else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Health check for Commons Sentience Sandbox v1.0"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all checks, not just failures",
    )
    args = parser.parse_args()

    check_python_version()
    check_required_files()
    check_data_files()
    check_experiment_configs()
    check_scenarios()
    check_output_directory()
    check_sessions_directory()
    check_python_imports()
    check_core_modules()
    check_existing_output()

    return print_summary(args.verbose)


if __name__ == "__main__":
    sys.exit(main())
