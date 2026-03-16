"""
quickstart.py — Friendly entry point for Commons Sentience Sandbox v1.0.

This script:
  1. Checks required directories and dependencies
  2. Prints the main commands for getting started
  3. Optionally runs a baseline simulation
  4. Optionally launches the dashboard

Usage
-----
  python quickstart.py                 # print commands and check setup
  python quickstart.py --run           # also run a baseline simulation
  python quickstart.py --dashboard     # also launch the dashboard
  python quickstart.py --run --dashboard
"""
from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BOLD = "\033[1m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_RESET = "\033[0m"


def _h(text: str) -> str:
    return f"{_BOLD}{_CYAN}{text}{_RESET}"


def _ok(text: str) -> str:
    return f"{_GREEN}\u2705  {text}{_RESET}"


def _warn(text: str) -> str:
    return f"{_YELLOW}\u26a0\ufe0f  {text}{_RESET}"


def _err(text: str) -> str:
    return f"{_RED}\u274c  {text}{_RESET}"


def _print_banner() -> None:
    print()
    print(_h("=" * 62))
    print(_h("  Commons Sentience Sandbox v1.0"))
    print(_h("  Research platform for continuity-governed simulated agents"))
    print(_h("=" * 62))
    print()
    print("  This is NOT a real AI — no sentience is claimed.")
    print("  It is intended for experimentation, evaluation, replay,")
    print("  session comparison, and scenario authoring research.")
    print()


# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------

def _check_deps() -> bool:
    print(_h("Checking dependencies..."))

    python_ok = sys.version_info >= (3, 9)
    if python_ok:
        print(_ok(f"Python {sys.version_info.major}.{sys.version_info.minor}"))
    else:
        print(_err(f"Python {sys.version_info.major}.{sys.version_info.minor} — Python 3.9+ required"))

    for pkg, friendly in [("matplotlib", "matplotlib"), ("streamlit", "streamlit (dashboard)")]:
        try:
            importlib.import_module(pkg)
            print(_ok(friendly))
        except ImportError:
            if pkg == "streamlit":
                print(_warn(f"{friendly} not installed — dashboard will not work. Run: pip install streamlit"))
            else:
                print(_err(f"{friendly} not installed. Run: pip install {pkg}"))
                return False

    # Ensure output dirs
    (ROOT / "commons_sentience_sim" / "output").mkdir(parents=True, exist_ok=True)
    (ROOT / "sessions").mkdir(parents=True, exist_ok=True)
    (ROOT / "experiments" / "results").mkdir(parents=True, exist_ok=True)
    print(_ok("Required directories exist"))
    print()
    return python_ok


# ---------------------------------------------------------------------------
# Command reference
# ---------------------------------------------------------------------------

def _print_commands() -> None:
    print(_h("Quick Reference — Main Commands"))
    print()

    sections = [
        ("Run a simulation", [
            ("Basic run (30 turns, baseline)", "python run_sim.py"),
            ("Named session", "python run_sim.py --name my_run"),
            ("With experiment config", "python run_sim.py --config high_trust"),
            ("With authored scenario", "python run_sim.py --scenario trust_crisis"),
            ("Config + scenario", "python run_sim.py --config strict_governance --scenario rapid_contradiction"),
        ]),
        ("Scenarios (authoring)", [
            ("List all scenarios", "python scenario_designer.py list"),
            ("Show scenario details", "python scenario_designer.py show --scenario trust_crisis"),
            ("Create new scenario", "python scenario_designer.py new --name my_scenario"),
            ("Validate all scenarios", "python scenario_designer.py validate"),
        ]),
        ("Sessions (replay & compare)", [
            ("List saved sessions", "python replay_session.py --list"),
            ("Replay a session", "python replay_session.py --session <session_id>"),
            ("Compare two sessions", "python compare_sessions.py --session-a <id> --session-b <id>"),
        ]),
        ("Experiments (batch runs)", [
            ("Run all experiment configs", "python run_experiments.py"),
            ("Run selected configs", "python run_experiments.py --configs baseline high_trust"),
            ("Run configs N times each", "python run_experiments.py --repeat 3"),
        ]),
        ("Visualisation & dashboard", [
            ("Plot latest state", "python plot_state.py"),
            ("Launch dashboard", "streamlit run dashboard.py"),
        ]),
        ("Maintenance", [
            ("Health check", "python healthcheck.py"),
            ("Health check (verbose)", "python healthcheck.py --verbose"),
            ("This quickstart", "python quickstart.py"),
        ]),
    ]

    for section_title, commands in sections:
        print(f"  {_BOLD}{section_title}{_RESET}")
        for desc, cmd in commands:
            print(f"    {_CYAN}{cmd}{_RESET}")
            print(f"      # {desc}")
        print()


# ---------------------------------------------------------------------------
# Optional: run a baseline simulation
# ---------------------------------------------------------------------------

def _run_baseline() -> bool:
    print(_h("Running baseline simulation..."))
    print("  python run_sim.py --name quickstart_baseline")
    print()
    result = subprocess.run(
        [sys.executable, str(ROOT / "run_sim.py"), "--name", "quickstart_baseline"],
        cwd=str(ROOT),
    )
    print()
    if result.returncode == 0:
        print(_ok("Baseline simulation completed successfully."))
    else:
        print(_err("Baseline simulation failed. Check the output above for errors."))
    print()
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Optional: launch dashboard
# ---------------------------------------------------------------------------

def _launch_dashboard() -> None:
    print(_h("Launching dashboard..."))
    print("  streamlit run dashboard.py")
    print()
    try:
        subprocess.run(
            ["streamlit", "run", str(ROOT / "dashboard.py")],
            cwd=str(ROOT),
        )
    except FileNotFoundError:
        print(_err("streamlit not found. Install it with: pip install streamlit"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quickstart for Commons Sentience Sandbox v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run a baseline simulation after checking setup.",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the Streamlit dashboard after checking setup.",
    )
    args = parser.parse_args()

    _print_banner()
    deps_ok = _check_deps()
    _print_commands()

    if not deps_ok:
        print(_err("Fix dependency issues above before running simulations."))
        print("  pip install -r requirements.txt")
        print()
        return 1

    if args.run:
        sim_ok = _run_baseline()
        if not sim_ok:
            return 1

    if args.dashboard:
        _launch_dashboard()

    if not args.run and not args.dashboard:
        print("  " + _BOLD + "Ready to go!" + _RESET + " Run:")
        print(f"    {_CYAN}python run_sim.py{_RESET}  — to start your first simulation")
        print(f"    {_CYAN}python quickstart.py --run{_RESET}  — to run and verify now")
        print(f"    {_CYAN}python healthcheck.py{_RESET}  — for a full health check")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
