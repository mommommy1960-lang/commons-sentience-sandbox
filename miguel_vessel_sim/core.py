"""A deterministic, non-actuating head-orientation and voice-intent simulation."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class VesselSim:
    angle_deg: int = 0
    gesture: str = "rest"
    stopped: bool = False
    permission: bool = False
    social_permission: bool = False
    hug_offered: bool = False
    log: List[str] = field(default_factory=list)

    def command(self, utterance: str) -> str:
        words = utterance.strip().lower().split()
        if not words:
            return self._record("NO_INPUT")
        if "stop" in words or "freeze" in words:
            self.stopped = True
            self.permission = False
            self.social_permission = False
            self.angle_deg = 0
            self.gesture = "rest"
            self.hug_offered = False
            return self._record("STOPPED")
        if words == ["grant", "motion"] and not self.stopped:
            self.permission = True
            return self._record("PERMISSION_GRANTED")
        if words == ["revoke", "motion"]:
            self.permission = False
            self.social_permission = False
            self.angle_deg = 0
            self.gesture = "rest"
            self.hug_offered = False
            return self._record("PERMISSION_REVOKED")
        if words == ["allow", "social", "gestures"] and not self.stopped:
            self.social_permission = True
            return self._record("SOCIAL_GESTURES_ALLOWED")
        if words == ["revoke", "social", "gestures"]:
            self.social_permission = False
            self.gesture = "rest"
            self.hug_offered = False
            return self._record("SOCIAL_GESTURES_REVOKED")
        if words == ["reset"]:
            # Reset clears the latch but never grants motion authority.
            self.stopped = False
            self.permission = False
            self.social_permission = False
            self.angle_deg = 0
            self.gesture = "rest"
            self.hug_offered = False
            return self._record("RESET_UNARMED")
        if self.stopped:
            return self._record("DENIED_STOPPED")
        if words == ["i", "need", "a", "hug"]:
            if not self.social_permission:
                return self._record("DENIED_NO_SOCIAL_PERMISSION")
            self.hug_offered = True
            self.gesture = "open_arms_offer"
            return self._record("HUG_OFFERED")
        if words == ["yes", "hug"]:
            if not self.social_permission or not self.hug_offered:
                return self._record("DENIED_NO_HUG_OFFER")
            self.hug_offered = False
            # Physical approach and contact are deliberately absent.
            self.gesture = "acknowledged"
            return self._record("HUG_ACCEPTED_IN_SIMULATION")
        if words == ["no", "hug"]:
            self.hug_offered = False
            self.gesture = "rest"
            return self._record("HUG_DECLINED")
        # Narrow standing consent permits a scripted reaction to a social cue.
        # This does not infer intent, emotion, humor, or unrestricted autonomy.
        if words in (["hello"], ["hi"], ["hey"]):
            if not self.social_permission:
                return self._record("DENIED_NO_SOCIAL_PERMISSION")
            self.gesture = "wave"
            return self._record("WAVE_HELLO")
        if words == ["tell", "a", "joke"]:
            if not self.social_permission:
                return self._record("DENIED_NO_SOCIAL_PERMISSION")
            self.gesture = "nod"
            return self._record("JOKE_PROMPT_ACKNOWLEDGED")
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
    for utterance in ("hello", "allow social gestures", "hello", "i need a hug", "yes hug", "look left", "grant motion", "look left", "stop", "hello", "reset", "hello"):
        result = sim.command(utterance)
        print(f"{utterance:>21} -> {result:<29} angle={sim.angle_deg:+d}° gesture={sim.gesture}")


if __name__ == "__main__":
    demo()
