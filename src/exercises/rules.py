"""Rule dataclasses: the atomic, exercise-agnostic building blocks.

A rule is pure configuration. It knows nothing about *which* exercise uses it
and contains no logic. GymEngine reads these fields and acts on them.
"""

from dataclasses import dataclass
from typing import Literal

# How severe a failed validation is. Used by the renderer for colouring /
# weighting feedback. Extend freely (e.g. "info") without touching the engine.
Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class AngleCounterRule:
    """Describes how ONE repetition is counted from a single joint angle.

    Why a dataclass (not a function/class hierarchy): a rep count is fully
    described by four numbers and two labels. There is no behaviour to model,
    so a frozen dataclass is the simplest honest representation.

    Attributes:
        name:        Stable id, also used as the on-screen label.
        joints:      Three pose-landmark indices forming the measured angle.
        up_angle:    Angle (deg) that marks the "up" / top of a rep.
        down_angle:  Angle (deg) that marks the "down" / bottom of a rep.
        up_stage:    Label applied while at/above ``up_angle`` (default "up").
        down_stage:  Label applied while at/below ``down_angle`` (default "down").

    ``up_stage`` / ``down_stage`` exist so the stage vocabulary is configurable
    ("up"/"down" today, but a future exercise could use different labels or a
    reversed count direction) without changing GymEngine or RepCounter.
    """

    name: str
    joints: tuple[int, int, int]
    up_angle: float
    down_angle: float
    up_stage: str = "up"
    down_stage: str = "down"


@dataclass(frozen=True)
class AngleValidationRule:
    """Describes ONE independent form-check based on a joint angle.

    Each rule is completely self-contained: it knows which angle to measure and
    the acceptable ``[min_angle, max_angle]`` window. If the measured angle
    falls outside that window, ``message`` is surfaced to the user.

    Attributes:
        name:       Stable id.
        joints:     Three pose-landmark indices forming the measured angle.
        min_angle:  Lower bound of the acceptable range (deg).
        max_angle:  Upper bound of the acceptable range (deg).
        message:    Human-readable coaching cue shown when the rule fails.
        severity:   "error" | "warning" | "info" — drives feedback emphasis.
    """

    name: str
    joints: tuple[int, int, int]
    min_angle: float
    max_angle: float
    message: str
    severity: Severity = "error"
