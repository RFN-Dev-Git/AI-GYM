"""Repetition counter driven entirely by AngleCounterRule configuration.

Stage machine per rule (using internal stage constants):
  STAGE_UP:        resting / extended position (e.g. arms straight down)
  STAGE_DOWN:      contracted / flexed position (e.g. biceps curled up)
  STAGE_RETURNING: returning from contraction to extension

State machine transitions:
  Standard rule (no rom_max_angle):
    STAGE_UP  --(angle <= down_angle)--> STAGE_DOWN
    STAGE_DOWN--(angle >= up_angle)  --> STAGE_UP   [rep counted, quality decided]

  ROM rule (rom_max_angle set):
    STAGE_UP  --(angle <= down_angle)        --> STAGE_DOWN
    STAGE_DOWN--(angle >= up_angle)          --> STAGE_RETURNING
    STAGE_RETURNING--(angle >= rom_max_angle)--> STAGE_UP   [rep counted GOOD if both extremes reached]
    STAGE_RETURNING--(angle <= down_angle)   --> STAGE_DOWN  [rep counted BAD, new rep starts]
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from ..exercises.rules import AngleCounterRule

# Internal Stage constants
STAGE_UP        = "up"
STAGE_DOWN      = "down"
STAGE_RETURNING = "returning"


@dataclass
class RepState:
    """Live state for one counter rule across frames."""

    angle: float = 0.0
    good: int = 0
    bad: int = 0
    stage: str = STAGE_UP
    started: bool = False           # True after the first DOWN phase visit
    reached_bottom: bool = False    # ROM: True once angle <= rom_min_angle this rep
    speed_warning: bool = False     # True if the last completed rep was too fast

    @property
    def count(self) -> int:
        """Total reps completed (good + bad)."""
        return self.good + self.bad


class RepCounter:
    """Counts repetitions from AngleCounterRule configurations."""

    def __init__(self, rules: List[AngleCounterRule]):
        self.rules = rules
        self.states: Dict[str, RepState] = {
            r.name: RepState() for r in rules
        }
        # Per-rule violation flag: was there a violation during the current rep?
        self._pending_violations: Dict[str, bool] = {
            r.name: False for r in rules
        }
        # Per-rule frame counter: how many frames since DOWN phase began?
        self._rep_frame_counts: Dict[str, int] = {
            r.name: 0 for r in rules
        }

    @property
    def primary(self) -> RepState:
        """State backing the displayed rep count (first counter rule)."""
        return next(iter(self.states.values()))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _count_rep(self, rule: AngleCounterRule, state: RepState, *, good: bool, too_fast: bool = False) -> None:
        """Finalise one repetition exactly once."""
        if good:
            state.good += 1
        else:
            state.bad += 1
        state.started = False
        state.speed_warning = too_fast

    def _start_down(self, rule: AngleCounterRule, state: RepState, angle: float) -> None:
        """Enter DOWN phase: reset ALL per-rep tracking."""
        state.stage = STAGE_DOWN
        state.started = True
        state.reached_bottom = False
        state.speed_warning = False
        self._pending_violations[rule.name] = False
        self._rep_frame_counts[rule.name] = 0
        rom_min = getattr(rule, "rom_min_angle", None)
        if rom_min is not None and angle <= rom_min:
            state.reached_bottom = True

    # ------------------------------------------------------------------
    # Public update — called once per frame by GymEngine
    # ------------------------------------------------------------------

    def update(
        self,
        angles: Dict[str, Optional[float]],
        violation_names: Optional[Set[str]] = None,
    ) -> Dict[str, RepState]:
        """Feed in the current angle for each rule; advance counts/stages."""
        vnames = violation_names or set()

        for rule in self.rules:
            angle = angles.get(rule.name)
            if angle is None:
                continue

            state = self.states[rule.name]
            prev_angle = state.angle
            state.angle = angle

            has_rom = getattr(rule, "rom_max_angle", None) is not None

            # ── Per-rule violation accumulation (only after rep started) ─
            if state.started:
                # Filter out the ROM rule's own coaching warning (which has the exact same name as the rule)
                # because it is just temporary guidance during the phase. Other form violations (like
                # elbow_drift, elbow_too_tight, elbow_hyperextended) must poison the rep.
                active_viols = {
                    v for v in vnames
                    if v.startswith(rule.name) and not (has_rom and v == rule.name)
                }
                # If this is the primary rule, any other general/unmatched violations also apply.
                if rule == self.rules[0]:
                    other_viols = {
                        v for v in vnames
                        if not any(r.name != rule.name and v.startswith(r.name) for r in self.rules)
                        and not (has_rom and v == rule.name)
                    }
                    active_viols.update(other_viols)

                if active_viols:
                    self._pending_violations[rule.name] = True

            # ── Frame counter (for speed check) ──────────────────────────
            if state.started:
                self._rep_frame_counts[rule.name] += 1

            # ----------------------------------------------------------
            # STANDARD path (no ROM thresholds)
            # ----------------------------------------------------------
            if not has_rom:

                # DOWN phase begins
                if angle <= rule.down_angle:
                    if state.stage != STAGE_DOWN:
                        self._start_down(rule, state, angle)

                # UP phase — rep completes
                elif angle >= rule.up_angle:
                    if state.started and state.stage == STAGE_DOWN:
                        too_fast = (
                            rule.min_rep_frames > 0
                            and self._rep_frame_counts[rule.name] < rule.min_rep_frames
                        )
                        good = not self._pending_violations[rule.name] and not too_fast
                        self._count_rep(rule, state, good=good, too_fast=too_fast)
                    state.stage = STAGE_UP

            # ----------------------------------------------------------
            # ROM path (rom_max_angle is set)
            # ----------------------------------------------------------
            else:
                rom_min = getattr(rule, "rom_min_angle", None)
                rom_max = rule.rom_max_angle

                # ── Track bottom extreme ──────────────────────────────
                if rom_min is not None and angle <= rom_min:
                    if not state.reached_bottom:
                        state.reached_bottom = True

                # ── DOWN phase begins (or RETURNING reversal — count BAD) ──
                if angle <= rule.down_angle:
                    if state.stage == STAGE_RETURNING:
                        # Reversed before reaching the top — count as BAD.
                        if state.started:
                            self._count_rep(rule, state, good=False)
                    if state.stage != STAGE_DOWN:
                        self._start_down(rule, state, angle)

                # ── Crossed up_angle on the way back up → RETURNING ───
                elif angle >= rule.up_angle and state.stage == STAGE_DOWN and state.started:
                    state.stage = STAGE_RETURNING

                # ── Top extreme reached and starts decreasing → rep completes ───────────────
                elif state.stage == STAGE_RETURNING and angle >= rom_max:
                    # Wait until the user actually finishes extending and starts curling back up
                    # (angle decreases) to capture peak hyperextension at the very bottom.
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

        return self.states
