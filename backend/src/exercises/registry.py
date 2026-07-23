"""Exercise registry — the single source of truth for available exercises.

The registry decouples *which* exercises exist from the code that uses them
(the CLI, :class:`GymEngine`). ``GymEngine`` only ever receives an already
constructed :class:`~src.exercises.exercise.Exercise` instance; it never asks
the registry for one. To add a new exercise you create the ``Exercise`` object
and call :meth:`ExerciseRegistry.register` — no engine or CLI changes needed.
"""

from typing import Dict, List

from .biceps_curl import BicepsCurlExercise
from .cable_chest_fly import CableChestFlyExercise
from .cable_straight_arm_pulldown import CableStraightArmPulldownExercise
from .deadlift import DeadliftExercise
from .exercise import Exercise
from .latpulldown import LatPulldownExercise
from .lateral_raise import LateralRaiseExercise
from .leg import HackSquatExercise, LegPressExercise
from .pushup import PushUpExercise
from .shoulder_press import ShoulderPressExercise
from .squat import SquatExercise


class UnknownExerciseError(Exception):
    """Raised when an exercise name is not present in the registry."""


class ExerciseRegistry:
    """Maps normalized exercise names to :class:`Exercise` instances."""

    def __init__(self) -> None:
        self._exercises: Dict[str, Exercise] = {}

    @staticmethod
    def _normalize(name: str) -> str:
        """Case/space-insensitive key (e.g. ``"Push-Up"`` -> ``"push-up"``)."""
        return name.strip().lower()

    def register(self, name: str, exercise: Exercise) -> None:
        """Register ``exercise`` under ``name`` (lookup is case-insensitive).

        Raises:
            TypeError: if ``exercise`` is not an :class:`Exercise` instance.
            ValueError: if ``name`` is already registered.
        """
        if not isinstance(exercise, Exercise):
            raise TypeError(
                f"exercise must be an Exercise instance, got {type(exercise).__name__}"
            )
        key = self._normalize(name)
        if key in self._exercises:
            raise ValueError(f"Exercise '{key}' is already registered")
        self._exercises[key] = exercise

    def get(self, name: str) -> Exercise:
        """Return the registered :class:`Exercise` for ``name``.

        Raises:
            UnknownExerciseError: if ``name`` is not registered.
        """
        key = self._normalize(name)
        if key not in self._exercises:
            raise UnknownExerciseError(f"Unknown exercise '{name}'")
        return self._exercises[key]

    def exists(self, name: str) -> bool:
        """Return ``True`` if ``name`` is registered."""
        return self._normalize(name) in self._exercises

    def list(self) -> List[str]:
        """Return all registered exercise names, sorted for stable display."""
        return sorted(self._exercises)

    def clear(self) -> None:
        """Remove every registration (convenience for tests)."""
        self._exercises.clear()


# Module-level singleton pre-populated with the built-in exercises. Importing
# this module is enough to make every shipped exercise available; GymEngine and
# the CLI simply ask the registry for what they need.
# Merged: original 9 exercises + 2 new from friend (cable_straight_arm_pulldown, lateral_raise) + 3D support
registry = ExerciseRegistry()
registry.register("deadlift", DeadliftExercise())
registry.register("cable_chest_fly", CableChestFlyExercise())
registry.register("cable_arm", CableStraightArmPulldownExercise())  # friend's new - straight arm pulldown
registry.register("cable_straight_arm_pulldown", CableStraightArmPulldownExercise())  # alias
registry.register("squat", SquatExercise())
registry.register("pushup", PushUpExercise())
registry.register("biceps_curl", BicepsCurlExercise())
registry.register("lat_pulldown", LatPulldownExercise())
registry.register("lateral_raise", LateralRaiseExercise())  # friend's new - lateral raise with shrug detection
registry.register("leg_press", LegPressExercise())
registry.register("hack_squat", HackSquatExercise())
registry.register("shoulder_press", ShoulderPressExercise())
