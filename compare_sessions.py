"""
compare_sessions.py — Compare two saved Commons Sentience Sandbox sessions.

Usage:
    python compare_sessions.py --session-a <id> --session-b <id>
    python compare_sessions.py --session-a <id> --session-b <id> --markdown
    python compare_sessions.py --list
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from session_manager import (
    SESSIONS_DIR,
    compare_sessions,
    list_sessions,
)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _print_comparison(report: dict) -> None:
    """Pretty-print a comparison report to the terminal."""
    print(f"\n{'=' * 65}")
    print(f"  SESSION COMPARISON REPORT")
    print(f"{'=' * 65}")
    print(f"  Session A : {report['session_a']}  (v{report.get('session_a_version', '?')})")
    print(f"  Session B : {report['session_b']}  (v{report.get('session_b_version', '?')})")
    print(f"  Generated : {report['generated_at'][:19]}")

    comp = report.get("comparison", {})

    # Config comparison
    cfg_cmp = comp.get("config", {})
    if cfg_cmp:
        exp_a = cfg_cmp.get("session_a_experiment", "—")
        exp_b = cfg_cmp.get("session_b_experiment", "—")
        same = cfg_cmp.get("same_config", False)
        print(f"\n  EXPERIMENT CONFIGS")
        print(f"  {'Session A config':<50} {exp_a}")
        print(f"  {'Session B config':<50} {exp_b}")
        if same:
            print(f"  {'Same config':<50} Yes — differences are run-to-run variation")
        else:
            print(f"  {'Same config':<50} No — score differences may reflect config changes")
        param_diffs = cfg_cmp.get("parameter_differences", {})
        if param_diffs:
            print(f"\n  Parameter differences:")
            print(f"  {'Parameter':<50} {'Session A':>12} {'Session B':>12}")
            print(f"  {'-' * 76}")
            for k, v in param_diffs.items():
                label = k.replace("_", " ").title()
                print(f"  {label:<50} {str(v['session_a']):>12} {str(v['session_b']):>12}")

    def _section(title: str, data: dict, fmt: str = ".4f") -> None:
        print(f"\n  {title}")
        print(f"  {'Metric':<50} {'Session A':>10} {'Session B':>10} {'Δ':>10}")
        print(f"  {'-' * 82}")
        for key, val in data.items():
            label = key.replace("_", " ").title()
            va = val["session_a"]
            vb = val["session_b"]
            delta = val["delta"]
            if fmt == ".4f":
                print(
                    f"  {label:<50} {va:>10.4f} {vb:>10.4f} {delta:>+10.4f}"
                )
            else:
                print(
                    f"  {label:<50} {va:>10} {vb:>10} {delta:>+10}"
                )

    _section("FINAL TRUST VALUES", comp.get("trust_final", {}), fmt=".4f")
    _section("REFLECTIONS", comp.get("reflections", {}), fmt="d")
    _section("INTERACTIONS", comp.get("interactions", {}), fmt="d")
    _section(
        "FINAL CONTRADICTION PRESSURE",
        comp.get("contradiction_pressure", {}),
        fmt=".4f",
    )

    state_history = comp.get("state_history", {})
    if state_history:
        print(f"\n  STATE HISTORY (Sentinel final row)")
        print(
            f"  {'Metric':<50} {'Session A':>10} {'Session B':>10} {'Δ':>10}"
        )
        print(f"  {'-' * 82}")
        for key, val in state_history.items():
            if not isinstance(val, dict):
                continue
            label = key.replace("_", " ").title()
            va = val["session_a"]
            vb = val["session_b"]
            delta = val["delta"]
            print(
                f"  {label:<50} {va:>10.4f} {vb:>10.4f} {delta:>+10.4f}"
            )

    # Evaluation score comparison
    eval_cmp = comp.get("evaluation", {})
    if eval_cmp:
        print(f"\n  EVALUATION SCORES")
        overall = eval_cmp.get("overall", {})
        if overall:
            print(
                f"  {'Overall Score':<50} "
                f"{overall.get('session_a', 0):>10.1f} "
                f"{overall.get('session_b', 0):>10.1f} "
                f"{overall.get('delta', 0):>+10.1f}"
            )
            print(f"  Better overall: {overall.get('better', '—').replace('session_', 'Session ')}")
        cat_cmp = eval_cmp.get("categories", {})
        if cat_cmp:
            print(f"\n  {'Category':<50} {'Session A':>10} {'Session B':>10} {'Δ':>10} {'Better':>12}")
            print(f"  {'-' * 95}")
            for cat_key, cat_val in cat_cmp.items():
                label = cat_key.replace("_", " ").title()
                print(
                    f"  {label:<50} "
                    f"{cat_val.get('session_a', 0):>10.1f} "
                    f"{cat_val.get('session_b', 0):>10.1f} "
                    f"{cat_val.get('delta', 0):>+10.1f} "
                    f"{cat_val.get('better', '—').replace('session_', 'S'):>12}"
                )
        if eval_cmp.get("largest_gap_category"):
            print(
                f"\n  Largest gap: {eval_cmp['largest_gap_category'].replace('_', ' ').title()} "
                f"(delta={eval_cmp.get('largest_gap_delta', 0):+.1f})"
            )

    print()


def _write_markdown(report: dict, output_path: Path) -> None:
    """Write a markdown comparison report."""
    comp = report.get("comparison", {})

    def _md_table(data: dict, fmt_float: bool = True) -> list[str]:
        rows = ["| Metric | Session A | Session B | Δ |", "|--------|-----------|-----------|---|"]
        for key, val in data.items():
            label = key.replace("_", " ").title()
            va = val["session_a"]
            vb = val["session_b"]
            delta = val["delta"]
            if fmt_float:
                rows.append(
                    f"| {label} | {va:.4f} | {vb:.4f} | {delta:+.4f} |"
                )
            else:
                rows.append(f"| {label} | {va} | {vb} | {delta:+d} |")
        return rows

    lines = [
        "# Session Comparison Report",
        "",
        f"**Session A:** `{report['session_a']}` (v{report.get('session_a_version', '?')})",
        f"**Session B:** `{report['session_b']}` (v{report.get('session_b_version', '?')})",
        f"**Generated:** {report['generated_at'][:19]}",
        "",
        "---",
        "",
    ]

    # Config comparison section
    cfg_cmp = comp.get("config", {})
    if cfg_cmp:
        lines += [
            "## Experiment Configs",
            "",
            f"- Session A: **{cfg_cmp.get('session_a_experiment', '—')}**",
            f"- Session B: **{cfg_cmp.get('session_b_experiment', '—')}**",
            f"- Same config: {'Yes' if cfg_cmp.get('same_config') else 'No'}",
        ]
        param_diffs = cfg_cmp.get("parameter_differences", {})
        if param_diffs:
            lines += [
                "",
                "**Parameter differences:**",
                "",
                "| Parameter | Session A | Session B |",
                "|---|---|---|",
            ]
            for k, v in param_diffs.items():
                label = k.replace("_", " ").title()
                lines.append(f"| {label} | {v['session_a']} | {v['session_b']} |")
        lines += ["", "---", ""]

    lines += [
        "## Final Trust Values",
        "",
    ]
    lines += _md_table(comp.get("trust_final", {}))

    lines += ["", "## Reflections", ""]
    lines += _md_table(comp.get("reflections", {}), fmt_float=False)

    lines += ["", "## Interactions", ""]
    lines += _md_table(comp.get("interactions", {}), fmt_float=False)

    lines += ["", "## Final Contradiction Pressure", ""]
    lines += _md_table(comp.get("contradiction_pressure", {}))

    state_history = comp.get("state_history", {})
    if state_history:
        hist_data = {k: v for k, v in state_history.items() if isinstance(v, dict)}
        if hist_data:
            lines += ["", "## State History — Sentinel Final Row", ""]
            lines += _md_table(hist_data)

    eval_cmp = comp.get("evaluation", {})
    if eval_cmp:
        lines += ["", "## Evaluation Score Comparison", ""]
        overall = eval_cmp.get("overall", {})
        if overall:
            lines += [
                "| | Session A | Session B | Delta | Better |",
                "|---|---|---|---|---|",
                f"| Overall Score | {overall.get('session_a', 0):.1f} | "
                f"{overall.get('session_b', 0):.1f} | "
                f"{overall.get('delta', 0):+.1f} | "
                f"{overall.get('better', '').replace('session_', 'Session ')} |",
            ]
        cat_cmp = eval_cmp.get("categories", {})
        if cat_cmp:
            lines += [
                "",
                "### Category Scores",
                "",
                "| Category | Session A | Session B | Delta | Better |",
                "|---|---|---|---|---|",
            ]
            for cat_key, cat_val in cat_cmp.items():
                label = cat_key.replace("_", " ").title()
                lines.append(
                    f"| {label} | {cat_val.get('session_a', 0):.1f} | "
                    f"{cat_val.get('session_b', 0):.1f} | "
                    f"{cat_val.get('delta', 0):+.1f} | "
                    f"{cat_val.get('better', '').replace('session_', 'Session ')} |"
                )
        if eval_cmp.get("largest_gap_category"):
            lines += [
                "",
                f"**Largest gap:** {eval_cmp['largest_gap_category'].replace('_', ' ').title()}"
                f" (delta = {eval_cmp.get('largest_gap_delta', 0):+.1f})",
            ]

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Markdown report → {output_path}")


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
        prog="compare_sessions.py",
        description="Compare two saved Commons Sentience Sandbox sessions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compare_sessions.py --list
  python compare_sessions.py --session-a 20260315_A --session-b 20260315_B
  python compare_sessions.py --session-a 20260315_A --session-b 20260315_B --markdown
        """,
    )
    parser.add_argument("--list", action="store_true", help="List all saved sessions")
    parser.add_argument("--session-a", type=str, help="ID of session A")
    parser.add_argument("--session-b", type=str, help="ID of session B")
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Write a markdown comparison report to sessions/",
    )

    args = parser.parse_args()

    if args.list:
        _cmd_list()
        return

    if not args.session_a or not args.session_b:
        parser.print_help()
        sys.exit(0)

    print(
        f"\n  Comparing:\n    A: {args.session_a}\n    B: {args.session_b}"
    )

    report = compare_sessions(args.session_a, args.session_b)
    _print_comparison(report)

    json_path = (
        SESSIONS_DIR / f"comparison_{args.session_a}_vs_{args.session_b}.json"
    )
    print(f"  JSON report → {json_path}")

    if args.markdown:
        md_path = (
            SESSIONS_DIR / f"comparison_{args.session_a}_vs_{args.session_b}.md"
        )
        _write_markdown(report, md_path)


if __name__ == "__main__":
    main()
