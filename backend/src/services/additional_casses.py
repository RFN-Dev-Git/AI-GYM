"""Additional cases and ROM logic helpers for RepCounter.

This module encapsulates all exercise-specific complexity (ROM, speed checks,
prefix-matched violations) to keep the core `rep_counter.py` clean and simple.
"""

from typing import Dict, Optional, Set
from ..exercises.rules import AngleCounterRule, Stage

# The counting pipeline's stage vocabulary lives in ``rules.Stage`` — one
# shared definition used by the counter, the ROM evaluator, and the engine.
STAGE_UP        = Stage.UP
STAGE_DOWN      = Stage.DOWN
STAGE_RETURNING = Stage.RETURNING


class CustomCounterHelper:
    """Helper class to handle stateful ROM, speed, and violation logic."""

    def __init__(self, counter_instance) -> None:
        self.counter = counter_instance
        # Per-rule violation flag: was there a violation during the current rep?
        self._pending_violations: Dict[str, bool] = {
            r.name: False for r in counter_instance.rules
        }
        # Per-rule frame counter: how many frames since DOWN phase began?
        self._rep_frame_counts: Dict[str, int] = {
            r.name: 0 for r in counter_instance.rules
        }
        # Remember the previous angle for each rule to detect direction changes
        self._prev_angles: Dict[str, float] = {
            r.name: 0.0 for r in counter_instance.rules
        }
        # Custom started flags to isolate rep window
        self._started: Dict[str, bool] = {
            r.name: False for r in counter_instance.rules
        }

    def _count_rep(self, rule: AngleCounterRule, state, *, good: bool, too_fast: bool = False) -> None:
        """Finalise one repetition and increment the corresponding counters."""
        state.count += 1
        if good:
            state.good += 1
        else:
            state.bad += 1
        self._started[rule.name] = False
        state.speed_warning = too_fast

    def _start_down(self, rule: AngleCounterRule, state, angle: float) -> None:
        """Enter DOWN phase: reset rep counters and start frame tracking."""
        state.stage = STAGE_DOWN
        self._started[rule.name] = True
        state.reached_bottom = False
        state.speed_warning = False
        self._pending_violations[rule.name] = False
        self._rep_frame_counts[rule.name] = 0
        rom_min = getattr(rule, "min_rom_angle", None)
        if rom_min is not None and angle <= rom_min:
            state.reached_bottom = True

    def update(
        self,
        angles: Dict[str, Optional[float]],
        violation_names: Optional[Set[str]] = None,
    ) -> Dict[str, any]:
        """Execute stateful ROM, speed check, and violation tracking."""
        vnames = violation_names or set()

        for rule in self.counter.rules:
            angle = angles.get(rule.name)
            if angle is None:
                continue

            state = self.counter.states[rule.name]
            prev_angle = self._prev_angles[rule.name]
            self._prev_angles[rule.name] = angle
            state.angle = angle

            has_rom = getattr(rule, "max_rom_angle", None) is not None

            # ── Violation accumulation during active rep window ───────────
            if self._started[rule.name]:
                active_viols = {
                    v for v in vnames
                    if v.startswith(rule.name) and not (has_rom and v == rule.name)
                }
                # Fallback general posture checks for primary counter rule
                if rule == self.counter.rules[0]:
                    other_viols = {
                        v for v in vnames
                        if not any(r.name != rule.name and v.startswith(r.name) for r in self.counter.rules)
                        and not (has_rom and v == rule.name)
                    }
                    active_viols.update(other_viols)

                if active_viols:
                    self._pending_violations[rule.name] = True

            # ── Rep frame counter for speed checks ────────────────────────
            if self._started[rule.name]:
                self._rep_frame_counts[rule.name] += 1

            # ── Standard exercises path (but with speed/violation checks) ─
            if not has_rom:
                if angle <= rule.down_angle:
                    if state.stage != STAGE_DOWN:
                        self._start_down(rule, state, angle)
                elif angle >= rule.up_angle:
                    if self._started[rule.name] and state.stage == STAGE_DOWN:
                        too_fast = (
                            rule.min_rep_frames > 0
                            and self._rep_frame_counts[rule.name] < rule.min_rep_frames
                        )
                        good = not self._pending_violations[rule.name] and not too_fast
                        self._count_rep(rule, state, good=good, too_fast=too_fast)
                    state.stage = STAGE_UP

            # ── Range of Motion (ROM) exercises path ──────────────────────
            else:
                rom_min = getattr(rule, "min_rom_angle", None)
                rom_max = rule.max_rom_angle

                # Track bottom depth
                if rom_min is not None and angle <= rom_min:
                    state.reached_bottom = True

                # DOWN phase begins (or RETURNING reversal)
                if angle <= rule.down_angle:
                    if state.stage == STAGE_RETURNING:
                        if self._started[rule.name]:
                            self._count_rep(rule, state, good=False)
                    if state.stage != STAGE_DOWN:
                        self._start_down(rule, state, angle)

                # Enter RETURNING stage when crossing up_angle
                elif angle >= rule.up_angle and state.stage == STAGE_DOWN and self._started[rule.name]:
                    state.stage = STAGE_RETURNING

                # Top extreme reached and user starts curling back up (reversal)
                elif state.stage == STAGE_RETURNING and angle >= rom_max:
                    if angle < prev_angle:
                        too_fast = (
                            rule.min_rep_frames > 0
                            and self._rep_frame_counts[rule.name] < rule.min_rep_frames
                        )
                        good = (
                            state.reached_bottom
                            and not self._pending_violations[rule.name]
                            and not too_fast
                        )
                        self._count_rep(rule, state, good=good, too_fast=too_fast)
                        state.stage = STAGE_UP

        return self.counter.states
