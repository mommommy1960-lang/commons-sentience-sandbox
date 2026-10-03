"""A deterministic, non-actuating head-orientation and voice-intent simulation."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class VesselSim:
    angle_deg: int = 0
    stopped: bool = False
    permission: bool = False
    log: List[str] = field(default_factory=list)

    def command(self, utterance: str) -> str:
        words = utterance.strip().lower().split()
        if not words:
            return self._record("NO_INPUT")
        if "stop" in words or "freeze" in words:
            self.stopped = True
            self.permission = False
            self.angle_deg = 0
            return self._record("STOPPED")
        if words == ["grant", "motion"] and not self.stopped:
            self.permission = True
            return self._record("PERMISSION_GRANTED")
        if words == ["revoke", "motion"]:
            self.permission = False
            self.angle_deg = 0
            return self._record("PERMISSION_REVOKED")
        if words == ["reset"]:
            # Reset clears the latch but never grants motion authority.
            self.stopped = False
            self.permission = False
            self.angle_deg = 0
            return self._record("RESET_UNARMED")
        if self.stopped:
            return self._record("DENIED_STOPPED")
        if not self.permission:
            return self._record("DENIED_NO_PERMISSION")
        if words == ["look", "left"]:
            self.angle_deg = -30
            return self._record("LOOK_LEFT")
        if words == ["look", "right"]:
            self.angle_deg = 30
            return self._record("LOOK_RIGHT")
        if words == ["look", "center"]:
            self.angle_deg = 0
            return self._record("LOOK_CENTER")
        return self._record("UNKNOWN_COMMAND")

    def _record(self, event: str) -> str:
        self.log.append(event)
        return event


def demo() -> None:
    sim = VesselSim()
    for utterance in ("look left", "grant motion", "look left", "stop", "look right", "reset", "look right"):
        result = sim.command(utterance)
        print(f"{utterance:>12} -> {result:<21} angle={sim.angle_deg:+d}°")


if __name__ == "__main__":
    demo()
