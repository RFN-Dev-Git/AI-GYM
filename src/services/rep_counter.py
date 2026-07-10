"""Repetition counter driven entirely by CounterRule configuration."""

from dataclasses import dataclass
from typing import Dict, List

from ..exercises.rules import CounterRule


@dataclass
class RepState:
    """Live state for one counter rule across frames."""

    angle: float = 0.0
    count: int = 0
    stage: str = "up"


class RepCounter:
    """Counts repetitions from a list of CounterRule configurations.

    One :class:`RepState` is kept per rule, so an exercise can count from
    several angles at once (e.g. left + right side for symmetry) with no change
    to this class or to GymEngine. The on-screen rep count comes from the first
    rule (``primary``); the others remain available in ``states``.
    """

    def __init__(self, rules: List[CounterRule]):
        self.rules = rules
        self.states: Dict[str, RepState] = {r.name: RepState() for r in rules}

    @property
    def primary(self) -> RepState:
        """State backing the displayed rep count (first counter rule)."""
        return next(iter(self.states.values()))

    def update(self, angles: Dict[str, float]) -> Dict[str, RepState]:
        """Feed in the current angle for each rule; advance counts/stages."""
        for rule in self.rules:
            angle = angles.get(rule.name, 0.0)
            state = self.states[rule.name]
            state.angle = angle

            if angle < rule.down_angle:
                # Entering the "down" position from "up" completes a rep.
                if state.stage == rule.up_stage:
                    state.count += 1
                state.stage = rule.down_stage
            elif angle > rule.up_angle:
                state.stage = rule.up_stage
            # Angles between thresholds hold the current stage.

        return self.states
