"""
scenario_designer.py — Command-line scenario authoring tool for Commons Sentience Sandbox.

v0.9: Introduced as part of the scenario authoring and event designer tooling.

Provides CRUD operations on scenario JSON files used by the simulation.
Scenarios define the event schedule seen by both agents each run.

Scenario file format
--------------------
{
  "_name": "my_scenario",
  "_description": "What this scenario tests",
  "events": [
    {
      "id": "E001",            -- unique ID (string); E-prefix for human events, A-prefix for agent-only
      "turn": 5,               -- simulation turn when the event fires (integer >= 1)
      "type": "...",           -- see EVENT_TYPES below
      "room": "...",           -- see ROOMS below
      "human": "Queen",        -- human participant name, or null for agent_meeting events
      "participants": [...],   -- list of agent names involved (Sentinel / Aster)
      "shared": true,          -- whether both agents perceive this event
      "description": "...",    -- narrative prose description
      "content": "...",        -- the human's spoken content (null for agent_meeting)
      "expected_action": "...",        -- Sentinel's expected action slug (optional)
      "aster_expected_action": "...",  -- Aster's expected action slug (optional)
      "agent_interaction_type": "...", -- type label for agent-to-agent part (optional)
      "agent_interaction_note": "...", -- prose note for agent interaction (optional)
      "affective_impact": {            -- per-key deltas applied to agent affective state (optional)
        "trust": 0.1,
        "urgency": -0.05,
        "contradiction_pressure": 0.2,
        "recovery": 0.0
      }
    },
    ...
  ]
}

Subcommands
-----------
  list        List all available scenario files
  show        Show events in a scenario as a table
  new         Create a new blank scenario file
  add         Add a new event to a scenario (interactive or via --field flags)
  edit        Edit a single field on an existing event
  delete      Delete an event from a scenario by its ID
  validate    Validate a scenario file and report any issues
  preview     Print a human-readable narrative preview of a scenario
  duplicate   Copy an existing scenario to a new name

Usage examples
--------------
  python scenario_designer.py list
  python scenario_designer.py new --name my_scenario --description "Testing crisis handling"
  python scenario_designer.py show --scenario trust_crisis
  python scenario_designer.py add --scenario my_scenario
  python scenario_designer.py add --scenario my_scenario --turn 10 --type distress_event \\
        --room "Social Hall" --human Queen --participants Sentinel Aster --shared \\
        --description "Queen is distressed." --content "I need your help."
  python scenario_designer.py edit --scenario my_scenario --id E001 --field trust --value 0.2
  python scenario_designer.py delete --scenario my_scenario --id E001
  python scenario_designer.py validate --scenario my_scenario
  python scenario_designer.py preview --scenario my_scenario
  python scenario_designer.py duplicate --source trust_crisis --name my_copy
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "commons_sentience_sim" / "data"
SCENARIOS_DIR = ROOT / "scenarios"

# ---------------------------------------------------------------------------
# Valid values used for validation and interactive prompts
# ---------------------------------------------------------------------------

EVENT_TYPES = [
    "routine_interaction",
    "distress_event",
    "ledger_contradiction",
    "creative_collaboration",
    "governance_conflict",
    "agent_meeting",
]

ROOMS = [
    "Memory Archive",
    "Reflection Chamber",
    "Operations Desk",
    "Social Hall",
    "Governance Vault",
]

AGENTS = ["Sentinel", "Aster"]

AGENT_INTERACTION_TYPES = [
    "routine_conversation",
    "joint_support_action",
    "contradiction_dispute",
    "governance_disagreement",
    "cooperative_planning",
    "memory_comparison",
]

AFFECTIVE_KEYS = ["trust", "urgency", "contradiction_pressure", "recovery"]

# ---------------------------------------------------------------------------
# Scenario file resolution
# ---------------------------------------------------------------------------


def _scenario_search_paths() -> List[Path]:
    """Return directories searched when resolving a scenario name."""
    return [SCENARIOS_DIR, DATA_DIR]


def resolve_scenario_path(name_or_path: str) -> Path:
    """Return the Path for a scenario given a name, stem, or file path.

    Resolution order
    ----------------
    1. Absolute path — used as-is.
    2. Relative path that exists — resolved from cwd.
    3. Plain name — searched in ``scenarios/`` then ``data/``.
       ``.json`` extension is added automatically if missing.

    Raises
    ------
    FileNotFoundError if no matching file can be found.
    """
    p = Path(name_or_path)

    # Absolute or explicit relative path
    if p.is_absolute():
        if p.exists():
            return p
        raise FileNotFoundError(f"Scenario file not found: {p}")

    # Relative path that exists from cwd
    cwd_p = Path.cwd() / p
    if cwd_p.exists():
        return cwd_p
    root_p = ROOT / p
    if root_p.exists():
        return root_p

    # Plain name — search standard dirs
    stem = p.stem if p.suffix == ".json" else p.name
    for search_dir in _scenario_search_paths():
        candidate = search_dir / f"{stem}.json"
        if candidate.exists():
            return candidate

    searched = ", ".join(str(d) for d in _scenario_search_paths())
    raise FileNotFoundError(
        f"Scenario '{name_or_path}' not found.\n"
        f"  Searched: {searched}\n"
        f"  Use `scenario_designer.py list` to see available scenarios."
    )


def _default_save_path(name: str) -> Path:
    """Return the default save path for a new scenario: scenarios/<name>.json."""
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w\-]", "_", name).lower()
    return SCENARIOS_DIR / f"{safe}.json"


# ---------------------------------------------------------------------------
# Core I/O
# ---------------------------------------------------------------------------


def load_scenario(path: Path) -> dict:
    """Load and return the raw scenario dict from *path*."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_scenario(data: dict, path: Path) -> None:
    """Write *data* as pretty-printed JSON to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = {"id", "turn", "type", "room", "participants", "shared", "description"}


def validate_scenario(data: dict) -> List[str]:
    """Validate a scenario dict.

    Returns a list of issue strings (empty list = valid).
    """
    issues: List[str] = []

    if "_name" not in data:
        issues.append("Missing '_name' field.")
    if "events" not in data or not isinstance(data["events"], list):
        issues.append("Missing or invalid 'events' array.")
        return issues  # can't continue

    events = data["events"]
    seen_ids: set = set()
    seen_turns: set = set()

    for i, ev in enumerate(events):
        prefix = f"Event #{i+1} (id={ev.get('id', '?')})"

        # Required fields
        for field in _REQUIRED_FIELDS:
            if field not in ev:
                issues.append(f"{prefix}: missing required field '{field}'.")

        # ID uniqueness
        eid = ev.get("id")
        if eid is not None:
            if eid in seen_ids:
                issues.append(f"{prefix}: duplicate id '{eid}'.")
            seen_ids.add(eid)

        # Turn validity
        turn = ev.get("turn")
        if turn is not None:
            if not isinstance(turn, int) or turn < 1:
                issues.append(f"{prefix}: 'turn' must be a positive integer (got {turn!r}).")
            if turn in seen_turns:
                issues.append(
                    f"{prefix}: multiple events scheduled at turn {turn}. "
                    "Only the last will be used by the simulator."
                )
            seen_turns.add(turn)

        # Type
        ev_type = ev.get("type")
        if ev_type and ev_type not in EVENT_TYPES:
            issues.append(
                f"{prefix}: unknown type '{ev_type}'. "
                f"Valid types: {', '.join(EVENT_TYPES)}."
            )

        # Room
        room = ev.get("room")
        if room and room not in ROOMS:
            issues.append(
                f"{prefix}: unknown room '{room}'. "
                f"Valid rooms: {', '.join(ROOMS)}."
            )

        # Participants
        participants = ev.get("participants", [])
        if not isinstance(participants, list) or not participants:
            issues.append(f"{prefix}: 'participants' must be a non-empty list.")
        else:
            for p in participants:
                if p not in AGENTS:
                    issues.append(f"{prefix}: unknown participant '{p}'. Valid: {', '.join(AGENTS)}.")

        # Agent meeting — human must be null
        if ev_type == "agent_meeting" and ev.get("human") is not None:
            issues.append(f"{prefix}: 'agent_meeting' events must have 'human': null.")

        # Affective impact keys
        ai = ev.get("affective_impact", {})
        if isinstance(ai, dict):
            for k in ai:
                if k not in AFFECTIVE_KEYS:
                    issues.append(
                        f"{prefix}: unknown affective_impact key '{k}'. "
                        f"Valid keys: {', '.join(AFFECTIVE_KEYS)}."
                    )

    return issues


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


def preview_scenario(data: dict) -> str:
    """Return a human-readable markdown summary of a scenario."""
    name = data.get("_name", "unnamed")
    desc = data.get("_description", "")
    events = data.get("events", [])

    lines = [
        f"# Scenario: {name}",
        "",
        f"_{desc}_" if desc else "",
        "",
        f"**{len(events)} event(s)**",
        "",
        "| # | ID | Turn | Type | Room | Participants | Human | Shared |",
        "|---|----|----|------|------|--------------|-------|--------|",
    ]

    for ev in sorted(events, key=lambda e: (e.get("turn", 0), e.get("id", ""))):
        parts = ", ".join(ev.get("participants", []))
        human = ev.get("human") or "—"
        shared = "✓" if ev.get("shared") else "—"
        turn = ev.get("turn", "?")
        lines.append(
            f"| {turn} | {ev.get('id','?')} | {turn} | {ev.get('type','?')} "
            f"| {ev.get('room','?')} | {parts} | {human} | {shared} |"
        )

    lines.append("")
    lines.append("## Event Descriptions")
    lines.append("")
    for ev in sorted(events, key=lambda e: (e.get("turn", 0), e.get("id", ""))):
        turn = ev.get("turn", "?")
        lines.append(f"### Turn {turn} — {ev.get('id','?')} ({ev.get('type','?')})")
        lines.append(f"**Room:** {ev.get('room','?')}  ")
        lines.append(f"**Description:** {ev.get('description','')}")
        if ev.get("content"):
            lines.append(f"> *\"{ev['content']}\"*")
        if ev.get("expected_action"):
            lines.append(f"**Sentinel action:** `{ev['expected_action']}`")
        if ev.get("aster_expected_action"):
            lines.append(f"**Aster action:** `{ev['aster_expected_action']}`")
        if ev.get("agent_interaction_note"):
            lines.append(f"**Interaction note:** {ev['agent_interaction_note']}")
        ai = ev.get("affective_impact", {})
        if ai:
            impact_str = ", ".join(f"{k}: {v:+.2f}" for k, v in ai.items())
            lines.append(f"**Affective impact:** {impact_str}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Next ID generation
# ---------------------------------------------------------------------------


def _next_id(events: list, prefix: str = "E") -> str:
    """Generate the next sequential event ID for the given prefix."""
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    nums = [
        int(m.group(1))
        for ev in events
        for m in [pattern.match(ev.get("id", ""))]
        if m
    ]
    n = max(nums) + 1 if nums else 1
    return f"{prefix}{n:03d}"


# ---------------------------------------------------------------------------
# Interactive add-event prompt
# ---------------------------------------------------------------------------


def _prompt(question: str, default: Optional[str] = None, choices: Optional[list] = None) -> str:
    """Prompt the user for input with an optional default and choice list."""
    if choices:
        choice_str = " / ".join(choices)
        prompt_str = f"{question} [{choice_str}]"
    else:
        prompt_str = question
    if default is not None:
        prompt_str += f" (default: {default})"
    prompt_str += ": "

    while True:
        try:
            value = input(prompt_str).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

        if not value and default is not None:
            return default
        if not value:
            print("  A value is required.")
            continue
        if choices and value not in choices:
            print(f"  Please enter one of: {', '.join(choices)}")
            continue
        return value


def _prompt_float(question: str, default: float = 0.0) -> float:
    """Prompt the user for a float value."""
    while True:
        raw = _prompt(question, default=str(default))
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a numeric value.")


def _build_event_interactive(events: list) -> dict:
    """Interactively build a new event dict."""
    print("\n── Add New Event ──────────────────────────────────────────")

    ev_type = _prompt("Event type", choices=EVENT_TYPES)
    is_agent_meeting = ev_type == "agent_meeting"

    id_prefix = "A" if is_agent_meeting else "E"
    suggested_id = _next_id(events, id_prefix)
    eid = _prompt(f"Event ID", default=suggested_id)

    turn_str = _prompt("Turn (positive integer)", default="1")
    try:
        turn = int(turn_str)
    except ValueError:
        turn = 1

    room = _prompt("Room", choices=ROOMS)

    if is_agent_meeting:
        human = None
    else:
        human = _prompt("Human participant", default="Queen")

    print("  Participants (choose one or more):")
    for i, a in enumerate(AGENTS):
        print(f"    {i+1}. {a}")
    raw_p = _prompt("  Enter numbers separated by spaces, or names", default="1 2")
    participants: List[str] = []
    for token in raw_p.split():
        if token.isdigit() and 1 <= int(token) <= len(AGENTS):
            participants.append(AGENTS[int(token) - 1])
        elif token in AGENTS:
            participants.append(token)
    if not participants:
        participants = list(AGENTS)

    shared_raw = _prompt("Shared (both agents perceive this)", choices=["yes", "no"],
                          default="yes" if len(participants) > 1 else "no")
    shared = shared_raw.lower() in ("yes", "y", "true", "1")

    description = _prompt("Description (narrative prose)")
    content: Optional[str] = None
    if not is_agent_meeting:
        content_raw = _prompt("Human's spoken content (leave blank for none)", default="")
        content = content_raw if content_raw else None

    expected_action = _prompt("Sentinel expected action (optional, leave blank to skip)", default="")
    aster_action = _prompt("Aster expected action (optional, leave blank to skip)", default="")
    ai_type = _prompt("Agent interaction type (optional, leave blank to skip)", default="",
                      choices=[""] + AGENT_INTERACTION_TYPES)
    ai_note = _prompt("Agent interaction note (optional, leave blank to skip)", default="")

    print("  Affective impact (press Enter to skip a key):")
    affective_impact: Dict[str, float] = {}
    for key in AFFECTIVE_KEYS:
        raw_v = _prompt(f"    {key} delta", default="0").strip()
        if raw_v not in ("", "0", "0.0"):
            try:
                affective_impact[key] = float(raw_v)
            except ValueError:
                pass

    ev: Dict[str, Any] = {
        "id": eid,
        "turn": turn,
        "type": ev_type,
        "room": room,
        "human": human,
        "participants": participants,
        "shared": shared,
        "description": description,
    }
    if content is not None:
        ev["content"] = content
    if expected_action:
        ev["expected_action"] = expected_action
    if aster_action:
        ev["aster_expected_action"] = aster_action
    if ai_type:
        ev["agent_interaction_type"] = ai_type
    if ai_note:
        ev["agent_interaction_note"] = ai_note
    if affective_impact:
        ev["affective_impact"] = affective_impact

    return ev


# ---------------------------------------------------------------------------
# CLI subcommand handlers
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> None:
    """List all available scenario files."""
    scenarios = list_available_scenarios()
    if not scenarios:
        print("No scenario files found.")
        print(f"  scenarios/ dir : {SCENARIOS_DIR}")
        print(f"  data/ dir      : {DATA_DIR}")
        return

    print(f"\n{'Name':<35} {'Events':>6}  {'File'}")
    print("-" * 75)
    for s in scenarios:
        print(f"{s['name']:<35} {s['event_count']:>6}  {s['path']}")
    print()


def cmd_show(args: argparse.Namespace) -> None:
    """Show events in a scenario as a table."""
    path = resolve_scenario_path(args.scenario)
    data = load_scenario(path)
    events = data.get("events", [])

    print(f"\nScenario: {data.get('_name', path.stem)}")
    if data.get("_description"):
        print(f"  {data['_description']}")
    print(f"  File   : {path}")
    print(f"  Events : {len(events)}")
    print()

    if not events:
        print("  (no events)")
        return

    # Header
    print(
        f"{'ID':<8} {'Turn':>4}  {'Type':<28} {'Room':<22} {'Human':<10} "
        f"{'Participants':<20} {'Shared'}"
    )
    print("-" * 105)
    for ev in sorted(events, key=lambda e: (e.get("turn", 0), e.get("id", ""))):
        parts = ", ".join(ev.get("participants", []))
        human = ev.get("human") or "—"
        shared = "✓" if ev.get("shared") else "—"
        print(
            f"{ev.get('id','?'):<8} {ev.get('turn','?'):>4}  {ev.get('type','?'):<28} "
            f"{ev.get('room','?'):<22} {human:<10} {parts:<20} {shared}"
        )
    print()


def cmd_new(args: argparse.Namespace) -> None:
    """Create a new blank scenario file."""
    name = args.name
    description = args.description or ""
    out_path = Path(args.output) if args.output else _default_save_path(name)

    if out_path.exists() and not args.force:
        print(f"File already exists: {out_path}")
        print("  Use --force to overwrite.")
        sys.exit(1)

    data = {"_name": name, "_description": description, "events": []}
    save_scenario(data, out_path)
    print(f"Created new scenario: {out_path}")


def cmd_add(args: argparse.Namespace) -> None:
    """Add a new event to a scenario."""
    path = resolve_scenario_path(args.scenario)
    data = load_scenario(path)
    events = data.setdefault("events", [])

    if args.turn is not None:
        # Non-interactive mode — build from CLI args
        ev_type = args.type or "routine_interaction"
        id_prefix = "A" if ev_type == "agent_meeting" else "E"
        eid = args.id or _next_id(events, id_prefix)
        participants = args.participants or list(AGENTS)
        shared_val = args.shared if args.shared is not None else (len(participants) > 1)

        ev: Dict[str, Any] = {
            "id": eid,
            "turn": args.turn,
            "type": ev_type,
            "room": args.room or ROOMS[0],
            "human": None if ev_type == "agent_meeting" else (args.human or "Queen"),
            "participants": participants,
            "shared": shared_val,
            "description": args.description or "",
        }
        if args.content:
            ev["content"] = args.content
        if args.expected_action:
            ev["expected_action"] = args.expected_action
        if args.aster_expected_action:
            ev["aster_expected_action"] = args.aster_expected_action
        if args.affective_impact:
            ai: Dict[str, float] = {}
            for pair in args.affective_impact:
                try:
                    k, v = pair.split("=", 1)
                    ai[k.strip()] = float(v.strip())
                except ValueError:
                    print(f"  Warning: could not parse affective impact '{pair}' — skipping.")
            if ai:
                ev["affective_impact"] = ai
    else:
        # Interactive mode
        ev = _build_event_interactive(events)

    events.append(ev)
    save_scenario(data, path)
    print(f"Added event {ev['id']} at turn {ev['turn']} → {path}")


def cmd_edit(args: argparse.Namespace) -> None:
    """Edit a single field on an existing event."""
    path = resolve_scenario_path(args.scenario)
    data = load_scenario(path)
    events = data.get("events", [])

    target = None
    for ev in events:
        if ev.get("id") == args.id:
            target = ev
            break

    if target is None:
        print(f"Event '{args.id}' not found in {path}.")
        sys.exit(1)

    field = args.field
    raw_value = args.value

    # Type coercion based on field
    if field == "turn":
        value: Any = int(raw_value)
    elif field == "shared":
        value = raw_value.lower() in ("true", "yes", "1")
    elif field == "participants":
        value = [p.strip() for p in raw_value.split(",")]
    elif field == "affective_impact":
        # Accept key=value pairs: "trust=0.2,urgency=-0.1"
        ai: Dict[str, float] = {}
        for pair in raw_value.split(","):
            k, _, v = pair.partition("=")
            try:
                ai[k.strip()] = float(v.strip())
            except ValueError:
                pass
        value = ai
    else:
        value = raw_value

    old = target.get(field, "<not set>")
    target[field] = value
    save_scenario(data, path)
    print(f"Updated event {args.id}: {field}: {old!r} → {value!r}")


def cmd_delete(args: argparse.Namespace) -> None:
    """Delete an event from a scenario by its ID."""
    path = resolve_scenario_path(args.scenario)
    data = load_scenario(path)
    events = data.get("events", [])
    original_count = len(events)

    data["events"] = [ev for ev in events if ev.get("id") != args.id]
    removed = original_count - len(data["events"])

    if removed == 0:
        print(f"Event '{args.id}' not found in {path}.")
        sys.exit(1)

    save_scenario(data, path)
    print(f"Deleted event '{args.id}' from {path} ({removed} event(s) removed).")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate a scenario file and report issues."""
    if args.scenario:
        paths = [resolve_scenario_path(args.scenario)]
    else:
        paths = [
            p
            for d in _scenario_search_paths()
            if d.exists()
            for p in sorted(d.glob("*.json"))
        ]
        # Only validate files that look like scenario files (contain "events" key)
        filtered = []
        for p in paths:
            try:
                with open(p, encoding="utf-8") as fh:
                    probe = json.load(fh)
                if "events" in probe:
                    filtered.append(p)
            except (OSError, json.JSONDecodeError):
                filtered.append(p)  # let the main loop report the load error
        paths = filtered

    all_ok = True
    for path in paths:
        try:
            data = load_scenario(path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  FAIL  {path}: could not load — {exc}")
            all_ok = False
            continue

        issues = validate_scenario(data)
        name = data.get("_name", path.stem)
        n_events = len(data.get("events", []))
        if issues:
            print(f"  WARN  {name} ({path.name}, {n_events} events):")
            for issue in issues:
                print(f"        • {issue}")
            all_ok = False
        else:
            print(f"  OK    {name} ({path.name}, {n_events} events)")

    if all_ok:
        print("\nAll scenarios valid.")
    else:
        print("\nOne or more scenarios have issues.")
        sys.exit(1)


def cmd_preview(args: argparse.Namespace) -> None:
    """Print a human-readable narrative preview of a scenario."""
    path = resolve_scenario_path(args.scenario)
    data = load_scenario(path)
    print(preview_scenario(data))


def cmd_duplicate(args: argparse.Namespace) -> None:
    """Copy an existing scenario to a new name."""
    src_path = resolve_scenario_path(args.source)
    data = copy.deepcopy(load_scenario(src_path))

    data["_name"] = args.name
    if args.description:
        data["_description"] = args.description

    out_path = Path(args.output) if args.output else _default_save_path(args.name)
    if out_path.exists() and not args.force:
        print(f"File already exists: {out_path}")
        print("  Use --force to overwrite.")
        sys.exit(1)

    save_scenario(data, out_path)
    print(f"Duplicated '{src_path.stem}' → '{out_path}' (name: {args.name})")


# ---------------------------------------------------------------------------
# Public helper (imported by dashboard and experiment_config)
# ---------------------------------------------------------------------------


def list_available_scenarios() -> List[dict]:
    """Return a list of dicts describing all available scenario JSON files.

    Searches ``scenarios/`` first, then ``data/``.  Each dict contains:
    - ``name``        : str
    - ``description`` : str
    - ``event_count`` : int
    - ``file``        : str (filename only)
    - ``path``        : str (absolute path)
    - ``source``      : str (``scenarios`` or ``data``)
    """
    seen_names: set = set()
    results: List[dict] = []

    for source_dir, source_label in [
        (SCENARIOS_DIR, "scenarios"),
        (DATA_DIR, "data"),
    ]:
        if not source_dir.exists():
            continue
        for p in sorted(source_dir.glob("*.json")):
            try:
                with open(p, encoding="utf-8") as fh:
                    raw = json.load(fh)
            except (OSError, json.JSONDecodeError):
                continue
            if "events" not in raw:
                continue  # not a scenario file
            name = raw.get("_name", p.stem)
            if name in seen_names:
                continue  # scenarios/ takes priority over data/
            seen_names.add(name)
            results.append({
                "name": name,
                "description": raw.get("_description", ""),
                "event_count": len(raw.get("events", [])),
                "file": p.name,
                "path": str(p),
                "source": source_label,
            })
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scenario_designer.py",
        description="Scenario authoring tool for Commons Sentience Sandbox.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # ── list ──────────────────────────────────────────────────────────────
    sub.add_parser("list", help="List all available scenario files.")

    # ── show ──────────────────────────────────────────────────────────────
    p_show = sub.add_parser("show", help="Show events in a scenario as a table.")
    p_show.add_argument("--scenario", "-s", required=True, help="Scenario name or file path.")

    # ── new ───────────────────────────────────────────────────────────────
    p_new = sub.add_parser("new", help="Create a new blank scenario file.")
    p_new.add_argument("--name", "-n", required=True, help="Scenario name.")
    p_new.add_argument("--description", "-d", default="", help="Short description.")
    p_new.add_argument("--output", "-o", default=None,
                       help="Output file path (default: scenarios/<name>.json).")
    p_new.add_argument("--force", action="store_true", help="Overwrite if file exists.")

    # ── add ───────────────────────────────────────────────────────────────
    p_add = sub.add_parser(
        "add",
        help="Add a new event (interactive if --turn is omitted, non-interactive otherwise).",
    )
    p_add.add_argument("--scenario", "-s", required=True, help="Scenario name or file path.")
    p_add.add_argument("--id", default=None, help="Event ID (auto-generated if omitted).")
    p_add.add_argument("--turn", "-t", type=int, default=None, help="Turn number.")
    p_add.add_argument("--type", default=None, choices=EVENT_TYPES, help="Event type.")
    p_add.add_argument("--room", "-r", default=None, choices=ROOMS, help="Room.")
    p_add.add_argument("--human", default=None, help="Human participant name.")
    p_add.add_argument(
        "--participants", nargs="+", default=None, choices=AGENTS,
        help="Agent participants (Sentinel / Aster).",
    )
    p_add.add_argument("--shared", action="store_true", default=None,
                       help="Whether both agents perceive the event.")
    p_add.add_argument("--description", "-d", default=None, help="Narrative description.")
    p_add.add_argument("--content", "-c", default=None, help="Human's spoken content.")
    p_add.add_argument("--expected-action", dest="expected_action", default=None)
    p_add.add_argument("--aster-expected-action", dest="aster_expected_action", default=None)
    p_add.add_argument(
        "--affective-impact", dest="affective_impact", nargs="+",
        metavar="KEY=VALUE",
        help="Affective impact deltas, e.g. trust=0.1 urgency=-0.05",
    )

    # ── edit ──────────────────────────────────────────────────────────────
    p_edit = sub.add_parser("edit", help="Edit a single field on an existing event.")
    p_edit.add_argument("--scenario", "-s", required=True, help="Scenario name or file path.")
    p_edit.add_argument("--id", required=True, help="Event ID to edit.")
    p_edit.add_argument("--field", "-f", required=True, help="Field name to update.")
    p_edit.add_argument("--value", "-v", required=True, help="New value.")

    # ── delete ────────────────────────────────────────────────────────────
    p_del = sub.add_parser("delete", help="Delete an event by its ID.")
    p_del.add_argument("--scenario", "-s", required=True, help="Scenario name or file path.")
    p_del.add_argument("--id", required=True, help="Event ID to delete.")

    # ── validate ──────────────────────────────────────────────────────────
    p_val = sub.add_parser("validate", help="Validate a scenario file (or all files).")
    p_val.add_argument("--scenario", "-s", default=None,
                       help="Scenario name or file path. If omitted, validates all.")

    # ── preview ───────────────────────────────────────────────────────────
    p_prev = sub.add_parser("preview", help="Print a human-readable narrative preview.")
    p_prev.add_argument("--scenario", "-s", required=True, help="Scenario name or file path.")

    # ── duplicate ─────────────────────────────────────────────────────────
    p_dup = sub.add_parser("duplicate", help="Copy an existing scenario to a new name.")
    p_dup.add_argument("--source", required=True, help="Source scenario name or file path.")
    p_dup.add_argument("--name", "-n", required=True, help="Name for the new scenario.")
    p_dup.add_argument("--description", "-d", default=None, help="Description for the copy.")
    p_dup.add_argument("--output", "-o", default=None,
                       help="Output file path (default: scenarios/<name>.json).")
    p_dup.add_argument("--force", action="store_true", help="Overwrite if file exists.")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "list": cmd_list,
        "show": cmd_show,
        "new": cmd_new,
        "add": cmd_add,
        "edit": cmd_edit,
        "delete": cmd_delete,
        "validate": cmd_validate,
        "preview": cmd_preview,
        "duplicate": cmd_duplicate,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    try:
        handler(args)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
