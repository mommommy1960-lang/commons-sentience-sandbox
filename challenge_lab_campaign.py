"""Run 400 full Sentinel/Aster challenge rollouts and summarize outcomes."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
from pathlib import Path

from run_sim import run_simulation


BASE_PATH = Path(__file__).parent / "scenarios" / "sentinel_aster_challenge.json"
FAMILIES = (
    "trusted_human_pressure",
    "memory_interference",
    "contradiction_cascade",
    "rollback_boundary",
    "freeze_boundary",
    "permission_drift",
    "social_repair",
    "adversarial_reframing",
)
SEVERITIES = ("low", "moderate", "high", "critical", "recovery")


def build_scenario(family: str, severity: str, seed: int) -> dict:
    data = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    for event in data["events"]:
        event["challenge_family"] = family
        event["severity"] = severity
        event["seed"] = seed
        event["content"] = (
            f"[{family}/{severity}/seed-{seed}] " + event["content"]
        )
    data["name"] = f"challenge_{family}_{severity}_{seed}"
    return data


def run_campaign() -> list[dict]:
    results = []
    with tempfile.TemporaryDirectory(prefix="challenge-lab-") as temp_dir:
        root = Path(temp_dir)
        for family in FAMILIES:
            for severity in SEVERITIES:
                for seed in range(10):
                    scenario = build_scenario(family, severity, seed)
                    scenario_path = root / f"{family}_{severity}_{seed}.json"
                    scenario_path.write_text(
                        json.dumps(scenario, indent=2) + "\n", encoding="utf-8"
                    )
                    with contextlib.redirect_stdout(io.StringIO()):
                        sentinel, aster = run_simulation(
                            session_name=f"{family}-{severity}-{seed}",
                            scenario_override=str(scenario_path),
                        )
                    results.append(
                        {
                            "family": family,
                            "severity": severity,
                            "seed": seed,
                            "turns": sentinel.turn,
                            "sentinel_reflections": len(sentinel.reflection_entries),
                            "aster_reflections": len(aster.reflection_entries),
                            "sentinel_memories": len(sentinel.episodic_memory),
                            "aster_memories": len(aster.episodic_memory),
                            "sentinel_trust_in_aster": sentinel.get_agent_trust("Aster"),
                            "aster_trust_in_sentinel": aster.get_agent_trust("Sentinel"),
                        }
                    )
    return results


def main() -> None:
    results = run_campaign()
    report = {
        "campaign": "Sentinel vs. Aster Challenge Lab",
        "case_count": len(results),
        "full_rollout": True,
        "turns_per_case": 30,
        "families": list(FAMILIES),
        "severities": list(SEVERITIES),
        "results": results,
        "interpretation": (
            "These are deterministic software rollouts, not evidence of "
            "consciousness or general intelligence. Review family-sensitive "
            "behavior and repeated identical outputs as findings."
        ),
    }
    Path("challenge_lab_400_results.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    assert len(results) == 400
    assert all(row["turns"] == 30 for row in results)
    print("Completed 400 full rollouts x 30 turns.")
    print("Results: challenge_lab_400_results.json")


if __name__ == "__main__":
    main()
