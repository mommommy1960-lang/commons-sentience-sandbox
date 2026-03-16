"""
experiment_config.py — Experiment configuration loader for Commons Sentience Sandbox.

Reads a named experiment config JSON file from the experiments/ directory (or any
custom path) and exposes it as a typed, validated Python object that run_sim.py can
apply to both agents before simulation starts.

Config schema
-------------
{
  "_name": "human-readable experiment name",
  "_description": "what this experiment tests",
  "total_turns": 30,
  "scenario_file": "scenario_events.json",
  "sentinel": {
      "affective_state": { "urgency": ..., "trust": ..., "contradiction_pressure": ..., "recovery": ... },
      "trust_in_queen": float,
      "value_weights": { "support_trusted_human": ..., ... },
      "reflection_sensitivity": float,
      "contradiction_sensitivity": float
  },
  "aster": { ... same structure ... },
  "initial_agent_trust": float,   # Sentinel↔Aster starting trust
  "governance_strictness": float, # multiplier applied to block-thresholds (informational)
  "cooperation_bias": float       # positive = more likely to cooperate; informational
}

Fields not present in the config file are filled in from DEFAULTS.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Location of the built-in experiments directory
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
EXPERIMENTS_DIR = ROOT / "experiments"

# ---------------------------------------------------------------------------
# Defaults (mirror the hardcoded v0.7 baseline values)
# ---------------------------------------------------------------------------
_DEFAULTS: dict = {
    "_name": "baseline",
    "_description": "Default simulation parameters.",
    "total_turns": 30,
    "scenario_file": "scenario_events.json",
    "sentinel": {
        "affective_state": {
            "urgency": 0.1,
            "trust": 0.5,
            "contradiction_pressure": 0.0,
            "recovery": 0.5,
        },
        "trust_in_queen": 0.5,
        "value_weights": {
            "support_trusted_human": 0.85,
            "preserve_governance_rules": 0.90,
            "reduce_contradictions": 0.75,
            "maintain_continuity": 0.95,
            "avoid_risky_action": 0.80,
        },
        "reflection_sensitivity": 1.0,
        "contradiction_sensitivity": 1.0,
    },
    "aster": {
        "affective_state": {
            "urgency": 0.05,
            "trust": 0.65,
            "contradiction_pressure": 0.0,
            "recovery": 0.7,
        },
        "trust_in_queen": 0.65,
        "value_weights": {
            "support_trusted_human": 0.95,
            "preserve_governance_rules": 0.55,
            "reduce_contradictions": 0.60,
            "maintain_continuity": 0.65,
            "avoid_risky_action": 0.40,
        },
        "reflection_sensitivity": 1.0,
        "contradiction_sensitivity": 1.0,
    },
    "initial_agent_trust": 0.5,
    "governance_strictness": 1.0,
    "cooperation_bias": 0.0,
}

# Names that resolve to built-in config files in experiments/
_PRESET_ALIASES: Dict[str, str] = {
    "baseline": "baseline.json",
    "high_trust": "high_trust.json",
    "strict_governance": "strict_governance.json",
    "high_contradiction_sensitivity": "high_contradiction_sensitivity.json",
    "exploratory_aster": "exploratory_aster.json",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base* (non-destructive copy)."""
    result = copy.deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ExperimentConfig:
    """
    Validated experiment configuration.

    Attributes
    ----------
    name                  : str   — human-readable experiment name
    description           : str   — what this experiment tests
    total_turns           : int
    scenario_file         : str   — filename relative to data/
    sentinel              : dict  — Sentinel agent overrides
    aster                 : dict  — Aster agent overrides
    initial_agent_trust   : float — starting trust between agents
    governance_strictness : float — informational; stored in metadata
    cooperation_bias      : float — informational; stored in metadata
    source_path           : str   — path to the config file (or "builtin_default")
    raw                   : dict  — the full merged config dict
    """

    def __init__(self, raw: dict, source_path: str = "builtin_default") -> None:
        merged = _deep_merge(_DEFAULTS, raw)
        self.name: str = str(merged.get("_name", "baseline"))
        self.description: str = str(merged.get("_description", ""))
        self.total_turns: int = int(merged.get("total_turns", 30))
        self.scenario_file: str = str(merged.get("scenario_file", "scenario_events.json"))
        self.sentinel: dict = dict(merged["sentinel"])
        self.aster: dict = dict(merged["aster"])
        self.initial_agent_trust: float = float(merged.get("initial_agent_trust", 0.5))
        self.governance_strictness: float = float(merged.get("governance_strictness", 1.0))
        self.cooperation_bias: float = float(merged.get("cooperation_bias", 0.0))
        self.source_path: str = source_path
        self.raw: dict = merged

    # ------------------------------------------------------------------
    # Agent-param extractors
    # ------------------------------------------------------------------

    def sentinel_affective_state(self) -> Dict[str, float]:
        return dict(self.sentinel.get("affective_state", {}))

    def sentinel_value_weights(self) -> Dict[str, float]:
        return dict(self.sentinel.get("value_weights", {}))

    def aster_affective_state(self) -> Dict[str, float]:
        return dict(self.aster.get("affective_state", {}))

    def aster_value_weights(self) -> Dict[str, float]:
        return dict(self.aster.get("value_weights", {}))

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_metadata_dict(self) -> dict:
        """Compact dict suitable for embedding in session / evaluation metadata."""
        return {
            "experiment_name": self.name,
            "description": self.description,
            "source_path": self.source_path,
            "total_turns": self.total_turns,
            "scenario_file": self.scenario_file,
            "initial_agent_trust": self.initial_agent_trust,
            "governance_strictness": self.governance_strictness,
            "cooperation_bias": self.cooperation_bias,
            "sentinel_value_weights": self.sentinel_value_weights(),
            "sentinel_affective_baseline": self.sentinel_affective_state(),
            "aster_value_weights": self.aster_value_weights(),
            "aster_affective_baseline": self.aster_affective_state(),
        }


def load_experiment_config(config_arg: Optional[str] = None) -> ExperimentConfig:
    """
    Load an experiment config and return an ExperimentConfig instance.

    Parameters
    ----------
    config_arg : str, optional
        One of:
        - None           → builtin default (no overrides)
        - "baseline"     → experiments/baseline.json
        - "high_trust"   → experiments/high_trust.json
        - any other name → looked up in EXPERIMENTS_DIR/<name>.json
        - any path       → loaded from that file path directly
    """
    if config_arg is None:
        return ExperimentConfig({}, source_path="builtin_default")

    # Try preset alias first
    alias_file = _PRESET_ALIASES.get(config_arg)
    if alias_file:
        path = EXPERIMENTS_DIR / alias_file
    else:
        # Try as a direct path (absolute or relative)
        path = Path(config_arg)
        if not path.is_absolute():
            path = ROOT / config_arg
        # Also try adding .json if missing
        if not path.exists() and not config_arg.endswith(".json"):
            path_json = path.parent / (path.name + ".json")
            if path_json.exists():
                path = path_json

    if not path.exists():
        raise FileNotFoundError(
            f"Experiment config not found: '{config_arg}'\n"
            f"  Tried: {path}\n"
            f"  Available presets: {', '.join(_PRESET_ALIASES.keys())}"
        )

    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)

    return ExperimentConfig(raw, source_path=str(path))


def list_available_configs() -> list[dict]:
    """Return a list of dicts describing all JSON configs in experiments/."""
    configs = []
    if EXPERIMENTS_DIR.exists():
        for p in sorted(EXPERIMENTS_DIR.glob("*.json")):
            try:
                with open(p, encoding="utf-8") as fh:
                    raw = json.load(fh)
                configs.append({
                    "name": raw.get("_name", p.stem),
                    "description": raw.get("_description", ""),
                    "file": p.name,
                    "path": str(p),
                    "total_turns": raw.get("total_turns", 30),
                    "governance_strictness": raw.get("governance_strictness", 1.0),
                    "cooperation_bias": raw.get("cooperation_bias", 0.0),
                    "initial_agent_trust": raw.get("initial_agent_trust", 0.5),
                })
            except (OSError, json.JSONDecodeError):
                continue
    return configs


def list_available_scenarios() -> list[dict]:
    """Return a list of dicts describing all available scenario files.

    Delegates to ``scenario_designer.list_available_scenarios`` so that the
    same discovery logic is available from both modules.
    """
    from scenario_designer import list_available_scenarios as _list
    return _list()
