import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Tuple

Vector2 = Tuple[float, float]

class ControllerInterface(ABC):
    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def update(self, setpoint: Vector2, measurement: Vector2, dt: float) -> Vector2:
        raise NotImplementedError()

@dataclass
class ProportionalController(ControllerInterface):
    kp: float = 1.0

    def reset(self) -> None:
        pass

    def update(self, setpoint: Vector2, measurement: Vector2, dt: float) -> Vector2:
        return ((setpoint[0] - measurement[0]) * self.kp, (setpoint[1] - measurement[1]) * self.kp)

@dataclass
class PIDController(ControllerInterface):
    kp: float = 1.0
    ki: float = 0.0
    kd: float = 0.0
    integral: Vector2 = field(default_factory=lambda: (0.0, 0.0))
    last_error: Vector2 = field(default_factory=lambda: (0.0, 0.0))

    def reset(self) -> None:
        self.integral = (0.0, 0.0)
        self.last_error = (0.0, 0.0)

    def update(self, setpoint: Vector2, measurement: Vector2, dt: float) -> Vector2:
        error = (setpoint[0] - measurement[0], setpoint[1] - measurement[1])
        self.integral = (self.integral[0] + error[0] * dt, self.integral[1] + error[1] * dt)
        derivative = ((error[0] - self.last_error[0]) / dt if dt else 0.0,
                      (error[1] - self.last_error[1]) / dt if dt else 0.0)
        self.last_error = error
        return (
            self.kp * error[0] + self.ki * self.integral[0] + self.kd * derivative[0],
            self.kp * error[1] + self.ki * self.integral[1] + self.kd * derivative[1],
        )

@dataclass
class FutureController(ControllerInterface):
    kp: float = 1.0
    horizon: float = 0.5

    def reset(self) -> None:
        pass

    def update(self, setpoint: Vector2, measurement: Vector2, dt: float) -> Vector2:
        lookahead = self.horizon / dt if dt else 1.0
        predicted = (measurement[0] + lookahead * (measurement[0] - setpoint[0]) * 0.1,
                     measurement[1] + lookahead * (measurement[1] - setpoint[1]) * 0.1)
        error = (setpoint[0] - predicted[0], setpoint[1] - predicted[1])
        return (error[0] * self.kp, error[1] * self.kp)

CONTROLLER_TYPES = {
    "proportional": ProportionalController,
    "pid": PIDController,
    "future": FutureController,
}
