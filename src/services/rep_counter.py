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

    # Fields for compatibility with custom ROM/speed/violation cases
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

        # Check if any rule requires stateful ROM checks or speed checks
        has_custom = any(
            r.rom_max_angle is not None or r.min_rep_frames > 0 for r in rules
        )
        if has_custom:
            from .additional_casses import CustomCounterHelper
            self._helper = CustomCounterHelper(self)
        else:
            self._helper = None

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
        if self._helper:
            return self._helper.update(angles, violation_names)

        # Original, simple generic counter code
        for rule in self.rules:
            angle = angles.get(rule.name)
            if angle is None:
                # Angle could not be computed this frame; skip this rule so a
                # degenerate pose is never treated as a real 0° angle.
                continue
            state = self.states[rule.name]
            state.angle = angle

            if angle < rule.down_angle:
                # Entering the "down" position from "up" completes a rep.
                if state.stage == rule.up_stage:
                    state.count += 1
                    state.good += 1  # default simple reps are always good
                state.stage = rule.down_stage
            elif angle > rule.up_angle:
                state.stage = rule.up_stage
            # Angles between thresholds hold the current stage.

        return self.states
