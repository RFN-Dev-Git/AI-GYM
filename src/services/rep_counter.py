"""Repetition counter driven entirely by CounterRule configuration."""

from dataclasses import dataclass
from typing import Dict, List

from ..exercises.rules import CounterRule


@dataclass
class RepState:
    """Live state for one counter rule across frames."""

    angle: float = 0.0
    good: int = 0
    bad: int = 0
    stage: str = "up"
    started: bool = False  # True after the first down_stage visit

    @property
    def count(self) -> int:
        return self.good + self.bad


class RepCounter:
    """Counts repetitions from CounterRule configurations.

    A repetition is completed when the movement goes:

        UP -> DOWN -> UP

    Validation errors are accumulated only during the current repetition.
    """

    def __init__(self, rules: List[CounterRule]):
        self.rules = rules
        self.states: Dict[str, RepState] = {
            r.name: RepState() for r in rules
        }
        self._pending_violations: Dict[str, bool] = {
            r.name: False for r in rules
        }

    @property
    def primary(self) -> RepState:
        return next(iter(self.states.values()))

    def update(
        self,
        angles: Dict[str, float],
        has_violation: bool = False,
    ) -> Dict[str, RepState]:

        for rule in self.rules:

            state = self.states[rule.name]
            angle = angles.get(rule.name, 0.0)
            state.angle = angle

            # --------------------------------------------------
            # Accumulate violations for the CURRENT repetition.
            # --------------------------------------------------
            if has_violation:
                self._pending_violations[rule.name] = True

            # --------------------------------------------------
            # Reached DOWN position -> Start a NEW repetition.
            # --------------------------------------------------
            if angle <= rule.down_angle:

                if state.stage != rule.down_stage:
                    state.stage = rule.down_stage
                    state.started = True

                    # Reset violations for this new repetition.
                    self._pending_violations[rule.name] = False

            # --------------------------------------------------
            # Returned to UP -> Rep completed.
            # --------------------------------------------------
            elif angle >= rule.up_angle:

                if state.started and state.stage == rule.down_stage:

                    if self._pending_violations[rule.name]:
                        state.bad += 1
                    else:
                        state.good += 1

                state.stage = rule.up_stage

        return self.states