"""Repetition counter driven entirely by AngleCounterRule configuration."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from ..exercises.rules import AngleCounterRule


@dataclass
class RepState:
    """Live state for one counter rule across frames."""

    angle: float = 0.0
    count: int = 0
    stage: str = "up"

    # Fields for compatibility with custom cases
    good: int = 0
    bad: int = 0
    speed_warning: bool = False
    reached_bottom: bool = False


class RepCounter:
    """Counts repetitions from a list of AngleCounterRule configurations.

    One :class:`RepState` is kept per rule, so an exercise can count from
    several angles at once (e.g. left + right side for symmetry) with no change
    to this class or to GymEngine. The on-screen rep count comes from the first
    rule (``primary``); the others remain available in ``states``.
    """

    def __init__(self, rules: List[AngleCounterRule]):
        self.rules = rules
        self.states: Dict[str, RepState] = {r.name: RepState() for r in rules}

        # Delegate all counting, ROM, and violation logic to the helper
        from .additional_casses import CustomCounterHelper
        self._helper = CustomCounterHelper(self)

    @property
    def primary(self) -> RepState:
        """State backing the displayed rep count (first counter rule)."""
        return next(iter(self.states.values()))

    def update(
        self,
        angles: Dict[str, Optional[float]],
        violation_names: Optional[Set[str]] = None,
    ) -> Dict[str, RepState]:
        """Feed in the current angle for each rule; advance counts/stages."""
        return self._helper.update(angles, violation_names)
