"""
replay_session.py — Command-line turn-by-turn replay for saved simulation sessions.

Usage:
    python replay_session.py --list
    python replay_session.py --session <session_id>
    python replay_session.py --session <session_id> --auto --delay 1.5
    python replay_session.py --session <session_id> --turn 10
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from session_manager import get_session_dir, list_sessions

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_csv(path: Path) -> list[dict]:
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return []


def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def _display_turn(
    turn_row: dict,
    interactions: list[dict],
    total_turns: int,
    agents_data: dict,
) -> None:
    """Print a single turn's state to the terminal."""
    turn_num = turn_row.get("turn", "?")
    print(f"\n{'=' * 65}")
    print(f"  TURN {turn_num} / {total_turns}")
    print(f"{'=' * 65}")
    print(f"  Room (Sentinel)    : {turn_row.get('room', '—')}")
    print(f"  Action             : {turn_row.get('action', '—')}")
    print(f"  Event Type         : {turn_row.get('event_type', '—')}")
    print(f"  Urgency            : {float(turn_row.get('urgency', 0)):.3f}")
    print(f"  Trust              : {float(turn_row.get('trust', 0)):.3f}")
    print(f"  Contradiction P.   : {float(turn_row.get('contradiction_pressure', 0)):.3f}")
    print(f"  Recovery           : {float(turn_row.get('recovery', 0)):.3f}")
    if "trust_in_Aster" in turn_row:
        print(f"  Trust in Aster     : {float(turn_row.get('trust_in_Aster', 0)):.3f}")

    # Show any interactions that happened this turn
    turn_str = str(turn_num)
    turn_interactions = [ix for ix in interactions if str(ix.get("turn")) == turn_str]
    for ix in turn_interactions:
        outcome = ix.get("outcome", "")
        badge = "✅" if outcome == "cooperated" else "⚡"
        print(
            f"\n  {badge} Interaction: {ix.get('interaction_type', '')} "
            f"({ix.get('initiator', '')} ↔ {ix.get('respondent', '')})"
        )
        print(f"     Room     : {ix.get('room', '—')}")
        print(f"     Outcome  : {outcome}")
        if ix.get("conflict_point"):
            cp = ix["conflict_point"]
            print(f"     Conflict : {cp[:90]}{'…' if len(cp) > 90 else ''}")
        print(
            f"     Δ Trust  : {ix.get('trust_delta_i_to_r', '')} / "
            f"{ix.get('trust_delta_r_to_i', '')}"
        )
        if ix.get("narrative"):
            narr = ix["narrative"]
            print(f"     Narrative: {narr[:100]}{'…' if len(narr) > 100 else ''}")


def _display_header(session_dir: Path) -> tuple[list[dict], list[dict], dict, int]:
    """Print session header and return (state_history, interaction_log, agents_data, total_turns)."""
    meta = _load_json(session_dir / "session_metadata.json")
    state_history = _load_csv(session_dir / "state_history.csv")
    interaction_log = _load_csv(session_dir / "interaction_log.csv")
    multi_state = _load_json(session_dir / "multi_agent_state.json")
    agents_data = multi_state.get("agents", {})
    total_turns = len(state_history)

    print(f"\n{'=' * 65}")
    print(f"  Commons Sentience Sandbox — Session Replay")
    print(f"{'=' * 65}")
    print(f"  Session : {meta.get('session_id', session_dir.name)}")
    print(f"  Created : {meta.get('created_at', 'unknown')[:19]}")
    print(f"  Version : {meta.get('simulation_version', 'unknown')}")
    print(f"  Agents  : {', '.join(meta.get('agent_names', []))}")
    print(f"  Turns   : {total_turns}")

    summary = meta.get("summary", {})
    if summary:
        print(f"\n  Summary metrics:")
        print(f"    Sentinel trust in Queen : {summary.get('sentinel_trust_in_queen', '—')}")
        print(f"    Aster trust in Queen    : {summary.get('aster_trust_in_queen', '—')}")
        print(f"    Mutual trust (S→A)      : {summary.get('mutual_trust_sentinel_aster', '—')}")
        print(f"    Sentinel reflections    : {summary.get('sentinel_reflections', '—')}")
        print(f"    Aster reflections       : {summary.get('aster_reflections', '—')}")
        print(f"    Cooperation events      : {summary.get('cooperation_events', '—')}")
        print(f"    Conflict events         : {summary.get('conflict_events', '—')}")

    return state_history, interaction_log, agents_data, total_turns


# ---------------------------------------------------------------------------
# Replay modes
# ---------------------------------------------------------------------------


def replay_interactive(
    session_dir: Path,
    auto: bool = False,
    delay: float = 1.0,
    start_turn: int = 1,
) -> None:
    """Run interactive (key-press) or auto replay of a session."""
    state_history, interaction_log, agents_data, total_turns = _display_header(session_dir)

    if not state_history:
        print("\n  No state_history.csv found in session.")
        return

    idx = max(0, min(start_turn - 1, len(state_history) - 1))

    while 0 <= idx < len(state_history):
        row = state_history[idx]
        _display_turn(row, interaction_log, total_turns, agents_data)

        if auto:
            time.sleep(delay)
            idx += 1
        else:
            print(
                f"\n  [Enter/n] next  [p] prev  [t <n>] jump  [q] quit : ",
                end="",
                flush=True,
            )
            try:
                cmd = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n  Replay interrupted.")
                break

            if cmd in ("", "n"):
                idx += 1
            elif cmd == "p":
                idx = max(0, idx - 1)
            elif cmd == "q":
                break
            elif cmd.startswith("t "):
                try:
                    target = int(cmd[2:]) - 1
                    idx = max(0, min(target, len(state_history) - 1))
                except ValueError:
                    pass

    print("\n  Replay complete.\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_list() -> None:
    sessions = list_sessions()
    if not sessions:
        print(
            "\n  No saved sessions found.\n"
            "  Run `python run_sim.py` to create one.\n"
        )
        return
    print(
        f"\n  {'ID':<40} {'Created':<22} {'Turns':<7} {'Version'}"
    )
    print(f"  {'-' * 82}")
    for s in sessions:
        print(
            f"  {s['session_id']:<40} "
            f"{s.get('created_at', '')[:19]:<22} "
            f"{s.get('total_turns', ''):<7} "
            f"{s.get('simulation_version', '')}"
        )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="replay_session.py",
        description="Replay a saved Commons Sentience Sandbox session turn by turn.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python replay_session.py --list
  python replay_session.py --session 20260315_213200_default
  python replay_session.py --session 20260315_213200_default --auto --delay 1.5
  python replay_session.py --session 20260315_213200_default --turn 10
        """,
    )
    parser.add_argument(
        "--list", action="store_true", help="List all saved sessions and exit"
    )
    parser.add_argument("--session", type=str, help="Session ID to replay")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-play without waiting for key presses",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds between turns in auto mode (default: 1.0)",
    )
    parser.add_argument(
        "--turn",
        type=int,
        default=1,
        help="Turn number to start replay from (default: 1)",
    )

    args = parser.parse_args()

    if args.list:
        _cmd_list()
        return

    if not args.session:
        parser.print_help()
        sys.exit(0)

    session_dir = get_session_dir(args.session)
    if session_dir is None:
        print(f"\n  Session '{args.session}' not found.")
        print("  Run `python replay_session.py --list` to see available sessions.\n")
        sys.exit(1)

    replay_interactive(
        session_dir,
        auto=args.auto,
        delay=args.delay,
        start_turn=args.turn,
    )


if __name__ == "__main__":
    main()
