#!/usr/bin/env python3
"""Civic Research Brain: a transparent self-critique work-loop scaffold.

This is an orchestration tool, not a conscious system and not an autonomous
model. It creates explicit work phases so a coordinator can repeatedly
build, challenge, repair, verify, and document an idea.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

PHASES = (
    ("builder", "What improvement or experiment should we propose?"),
    ("breaker", "How could the proposal fail, mislead, or be unsafe?"),
    ("repairer", "What smallest repair addresses the strongest failure?"),
    ("verifier", "What exact test or evidence would distinguish success from failure?"),
    ("market_reality", "Who needs this, and what evidence shows they would pay or adopt it?"),
    ("physical_reality", "What must be measured in the real world before making a physical claim?"),
)

def create_session(args: argparse.Namespace) -> None:
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    session = {
        "session_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "question": args.question,
        "status": "OPEN",
        "reality_rule": "Reality first. Anomaly second. Follow through.",
        "evidence_status": "No execution or external validation is implied.",
        "phases": [
            {"name": name, "prompt": prompt, "status": "PENDING", "response": ""}
            for name, prompt in PHASES
        ],
    }
    path = root / "session.json"
    path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    print(path)

def show_prompts(args: argparse.Namespace) -> None:
    session = json.loads(Path(args.session).read_text(encoding="utf-8"))
    print(f"Question: {session['question']}")
    for index, phase in enumerate(session["phases"], start=1):
        print(f"{index}. [{phase['name']}] {phase['prompt']}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Transparent Civic Research Brain loop")
    sub = parser.add_subparsers(required=True)
    create = sub.add_parser("create")
    create.add_argument("--question", required=True)
    create.add_argument("--output", default="research-room")
    create.set_defaults(func=create_session)
    prompts = sub.add_parser("prompts")
    prompts.add_argument("--session", default="research-room/session.json")
    prompts.set_defaults(func=show_prompts)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()