"""Exercise configuration package.

Everything in here is *data*, not behaviour. An exercise is described entirely
by an :class:`Exercise` instance built from :class:`CounterRule` and
:class:`ValidationRule` dataclasses. GymEngine consumes these objects and never
needs to know which exercise it is running.

Each exercise lives in its own module (``pushup.py``, ``squat.py``, ...); this
package re-exports them so callers can do ``from src.exercises import
PushUpExercise`` without knowing the internal file layout. Adding a new exercise
= adding one new self-contained module + one import line below. No engine code
changes.
"""

from .biceps_curl import BicepsCurlExercise
from .cable_chest_fly import CableChestFlyExercise
from .deadlift import DeadliftExercise
from .exercise import DisplaySettings, Exercise
from .latpulldown import LatPulldownExercise
from .leg import HackSquatExercise, LegPressExercise
from .pushup import PushUpExercise
from .rules import CounterRule, ValidationRule
from .shoulder_press import ShoulderPressExercise
from .squat import SquatExercise
from .validation import ValidationResult, validate_all, violations

__all__ = [
    "CounterRule",
    "ValidationRule",
    "Exercise",
    "DisplaySettings",
    "ValidationResult",
    "validate_all",
    "violations",
    "PushUpExercise",
    "SquatExercise",
    "LegPressExercise",
    "HackSquatExercise", 
    "ShoulderPressExercise",
    "BicepsCurlExercise",
    "LatPulldownExercise",
    "DeadliftExercise",
    "CableChestFlyExercise",
]