"""Reusable control-system primitives for domain physics engines.

Provides:
- HysteresisController: On/off control with deadband
- MinOnOffTimer: Minimum on/off time constraint
- PIController: Proportional-Integral controller with anti-windup
- LeadLagController: Lead-lag rotation for multi-unit staging
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HysteresisController:
    """On/off hysteresis controller with deadband around setpoint.

    Turns ON when measurement > setpoint + deadband_high,
    turns OFF when measurement < setpoint - deadband_low.
    """

    setpoint: float
    deadband_high: float = 0.5
    deadband_low: float = 0.5
    state: bool = False

    def update(self, measurement: float) -> bool:
        """Return desired on/off based on measurement vs setpoint."""
        if self.state:
            # Currently on -> turn off if below low threshold
            if measurement < self.setpoint - self.deadband_low:
                self.state = False
        else:
            # Currently off -> turn on if above high threshold
            if measurement > self.setpoint + self.deadband_high:
                self.state = True
        return self.state


@dataclass
class MinOnOffTimer:
    """Enforces minimum on-time and minimum off-time constraints.

    Prevents rapid cycling by holding state for at least
    min_on_minutes (when on) or min_off_minutes (when off).
    """

    min_on_minutes: float = 10.0
    min_off_minutes: float = 10.0
    state: bool = False
    _elapsed: float = field(default=0.0, repr=False)

    def update_time(self, dt_minutes: float) -> None:
        """Advance the internal timer by *dt_minutes*."""
        self._elapsed += dt_minutes

    def change_state(self, desired: bool) -> bool:
        """Request a state change; returns the actual state after constraint."""
        if desired == self.state:
            return self.state

        required = self.min_on_minutes if self.state else self.min_off_minutes
        if self._elapsed >= required:
            self.state = desired
            self._elapsed = 0.0
        return self.state


class PIController:
    """Discrete PI controller with integrator clamping (anti-windup).

    Parameters
    ----------
    setpoint : float
        Target value.
    kp : float
        Proportional gain.
    ki : float
        Integral gain.
    output_min, output_max : float | None
        Optional bounds for the controller output.
    integrator_min, integrator_max : float
        Bounds for the integrator state (anti-windup).
    """

    def __init__(
        self,
        setpoint: float,
        kp: float = 1.0,
        ki: float = 0.1,
        output_min: float | None = None,
        output_max: float | None = None,
        integrator_min: float = -200.0,
        integrator_max: float = 200.0,
    ):
        self.setpoint = setpoint
        self.kp = kp
        self.ki = ki
        self.output_min = output_min
        self.output_max = output_max
        self.integrator_min = integrator_min
        self.integrator_max = integrator_max
        self._integral: float = 0.0

    def update(self, measurement: float, dt_minutes: float) -> float:
        """Compute controller output, clamped to output bounds if set."""
        error = measurement - self.setpoint
        self._integral += error * dt_minutes
        # Anti-windup clamp
        self._integral = max(self.integrator_min, min(self.integrator_max, self._integral))
        output = self.kp * error + self.ki * self._integral
        if self.output_min is not None:
            output = max(self.output_min, output)
        if self.output_max is not None:
            output = min(self.output_max, output)
        return output

    def reset(self) -> None:
        self._integral = 0.0


class LeadLagController:
    """Lead-lag rotation controller for multi-unit staging.

    Selects which units to run based on accumulated runtime,
    rotating the lead unit periodically.
    """

    def __init__(self, n_units: int = 2, rotation_hours: float = 48.0):
        self.n_units = n_units
        self.rotation_hours = rotation_hours
        self._runtimes: list[float] = [0.0] * n_units
        self._lead_index: int = 0
        self._hours_since_rotation: float = 0.0

    @property
    def lead_index(self) -> int:
        return self._lead_index

    def select_units(self, n_needed: int) -> list[bool]:
        """Return a list of booleans indicating which units to activate.

        The lead unit is activated first; additional units are chosen
        by ascending runtime (least-run first).
        """
        n_needed = max(0, min(n_needed, self.n_units))
        selected = [False] * self.n_units
        if n_needed == 0:
            return selected

        # Lead always first
        selected[self._lead_index] = True
        remaining = n_needed - 1

        if remaining > 0:
            # Sort other indices by runtime (ascending)
            others = sorted(
                (i for i in range(self.n_units) if i != self._lead_index),
                key=lambda i: self._runtimes[i],
            )
            for idx in others[:remaining]:
                selected[idx] = True

        return selected

    def update(self, running: list[bool], dt_hours: float) -> None:
        """Update runtimes and check rotation."""
        for i, is_running in enumerate(running):
            if is_running:
                self._runtimes[i] += dt_hours

        self._hours_since_rotation += dt_hours
        if self._hours_since_rotation >= self.rotation_hours:
            self._rotate()
            self._hours_since_rotation = 0.0

    def _rotate(self) -> None:
        """Rotate lead to the unit with least runtime."""
        self._lead_index = int(min(range(self.n_units), key=lambda i: self._runtimes[i]))
