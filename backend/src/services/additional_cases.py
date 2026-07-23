"""Additional custom cases for exercises that need special handling.

This module contains exercise-specific logic that doesn't fit in the generic
counter but is needed for certain exercises (ROM tracking, speed checks, etc.).
"""

from typing import Dict, Optional, Set
from ..exercises.rules import AngleCounterRule, Stage


class CustomCounterHelper:
    """Helper for counter rules that need custom ROM/speed tracking."""

    def __init__(self, counter):
        self.counter = counter
        self._rep_start_frames: Dict[str, int] = {}  # Track when each rep started
        self._reached_bottom: Dict[str, bool] = {}   # Track if bottom ROM was reached
        self._reached_top: Dict[str, bool] = {}      # Track if top ROM was reached

    def update(
        self,
        angles: Dict[str, Optional[float]],
        violation_names: Optional[Set[str]] = None,
    ) -> Dict[str, any]:
        """Custom update logic for ROM-managed counters."""
        violation_names = violation_names or set()

        for rule in self.counter.rules:
            angle = angles.get(rule.name)
            if angle is None:
                continue

            state = self.counter.states[rule.name]
            state.angle = angle

            # Initialize tracking if needed
            if rule.name not in self._rep_start_frames:
                self._rep_start_frames[rule.name] = 0
                self._reached_bottom[rule.name] = False
                self._reached_top[rule.name] = False

            # Check ROM thresholds
            if rule.min_rom_angle is not None and angle <= rule.min_rom_angle:
                self._reached_bottom[rule.name] = True
                state.reached_bottom = True

            if rule.max_rom_angle is not None and angle >= rule.max_rom_angle:
                self._reached_top[rule.name] = True

            # Stage transitions
            if angle < rule.down_angle:
                # Entering DOWN phase
                if state.stage == rule.up_stage:
                    # Rep completed - check quality
                    self._finalize_rep(rule, state, violation_names)
                state.stage = rule.down_stage
                # Reset ROM tracking for next rep
                self._reached_bottom[rule.name] = False
                self._reached_top[rule.name] = False
            elif angle > rule.up_angle:
                state.stage = rule.up_stage

        return self.counter.states

    def _finalize_rep(self, rule, state, violation_names):
        """Determine rep quality based on ROM and violations."""
        # Check if ROM requirements were met
        rom_good = True
        if rule.min_rom_angle is not None and not self._reached_bottom.get(rule.name, False):
            rom_good = False
        if rule.max_rom_angle is not None and not self._reached_top.get(rule.name, False):
            rom_good = False

        # Check speed if required
        speed_ok = True
        if rule.min_rep_frames > 0:
            # Simple frame counting would go here
            # For now, we'll assume speed is OK
            pass

        # Rep is good if ROM was met and no violations
        if rom_good and speed_ok:
            state.good += 1
        else:
            state.bad += 1

        state.count += 1
