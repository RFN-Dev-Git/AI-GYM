"""Additional cases and ROM logic helpers for RepCounter.

This module encapsulates all exercise-specific complexity (ROM, speed checks,
prefix-matched violations) to keep the core `rep_counter.py` clean and simple.
"""

from typing import Dict, Optional, Set
from ..exercises.rules import AngleCounterRule

# Stage constants
STAGE_UP        = "up"
STAGE_DOWN      = "down"
STAGE_RETURNING = "returning"


# Keep track of baseline torso heights statefully across runs
_baseline_torso_heights = {}


def is_violation_related(viol_name: str, rule_name: str, all_rules: list) -> bool:
    """Determine if a validation violation name is related to a counter rule."""
    # 1. Exact or prefix match (e.g. "elbow_drift" for "elbow")
    if viol_name.startswith(rule_name):
        return True
    
    # 2. Side-specific routing (e.g. "knee_unlocked_left" for "knee_left")
    if "left" in rule_name and "left" in viol_name:
        return True
    if "right" in rule_name and "right" in viol_name:
        return True
        
    # 3. General posture checks (e.g. "back_straight") affect the primary rule
    if "left" not in viol_name and "right" not in viol_name:
        if rule_name == all_rules[0].name:
            return True
            
    return False


def evaluate_custom_rule(rule, landmarks, width: int, height: int, states) -> any:
    """Evaluate custom non-angle rules like shrug detection and wrist height."""
    from ..exercises.validation import ValidationResult
    
    if rule.__class__.__name__ == "ShrugValidationRule":
        # Requires Shoulders (11, 12) and Hips (23, 24)
        if len(landmarks) < 25:
            return ValidationResult(rule.name, rule.message, rule.severity, True, 0.0)
            
        primary_state = next(iter(states.values())) if states else None
        angle = primary_state.angle if primary_state else 0.0
        
        # Calculate shoulder width for normalization
        dx = landmarks[11].x - landmarks[12].x
        dy = landmarks[11].y - landmarks[12].y
        shoulder_width = (dx*dx + dy*dy) ** 0.5
        if shoulder_width == 0:
            shoulder_width = 1.0
            
        hip_mid_y = (landmarks[23].y + landmarks[24].y) / 2
        sh_mid_y = (landmarks[11].y + landmarks[12].y) / 2
        current_height = (hip_mid_y - sh_mid_y) / shoulder_width
        
        # Record baseline when at rest (angle < 25)
        session_key = id(states)
        if angle < 25.0 or session_key not in _baseline_torso_heights:
            _baseline_torso_heights[session_key] = current_height
            
        baseline = _baseline_torso_heights.get(session_key, current_height)
        delta = current_height - baseline
        
        # If shoulders shrug up, torso height increases (since sh_mid_y decreases).
        # We only validate when arms are raised (angle > 30)
        passed = True
        if angle > 30.0:
            passed = delta <= rule.threshold
            
        return ValidationResult(
            rule.name,
            rule.message,
            rule.severity,
            passed,
            float(delta),
            joints=(11, 12, 23)
        )
        
    elif rule.__class__.__name__ == "WristLevelValidationRule":
        # Requires Wrists (15, 16) and Shoulders (11, 12)
        if len(landmarks) < 17:
            return ValidationResult(rule.name, rule.message, rule.severity, True, 0.0)
            
        primary_state = next(iter(states.values())) if states else None
        angle = primary_state.angle if primary_state else 0.0
        
        passed = True
        # Only validate when arms are raised (angle > 30)
        if angle > 30.0:
            left_bad = landmarks[15].y < landmarks[11].y
            right_bad = landmarks[16].y < landmarks[12].y
            if left_bad or right_bad:
                passed = False
                
        return ValidationResult(
            rule.name,
            rule.message,
            rule.severity,
            passed,
            0.0,
            joints=(15, 16, 11, 12)
        )

    elif rule.__class__.__name__ == "DistanceValidationRule":
        if len(landmarks) <= max(rule.point1, rule.point2, rule.reference1, rule.reference2):
            return ValidationResult(rule.name, rule.message, rule.severity, True, 0.0)

        def _dist(a, b):
            dx = landmarks[a].x - landmarks[b].x
            dy = landmarks[a].y - landmarks[b].y
            return (dx*dx + dy*dy) ** 0.5

        measured = _dist(rule.point1, rule.point2)
        reference = _dist(rule.reference1, rule.reference2)
        ratio = measured / reference if reference > 0 else 0.0
        passed = rule.min_ratio <= ratio <= rule.max_ratio

        return ValidationResult(
            rule.name,
            rule.message,
            rule.severity,
            passed,
            float(ratio),
            joints=getattr(rule, "joints", ())
        )
        
    return ValidationResult(rule.name, rule.message, rule.severity, True, 0.0)


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
        # Peak angle per rule for complete_on_return exercises
        self._peak_angles: Dict[str, float] = {
            r.name: 0.0 for r in counter_instance.rules
        }

        # For complete_on_return exercises, initial rest stage is "down"
        for r in counter_instance.rules:
            if getattr(r, "complete_on_return", False):
                counter_instance.states[r.name].stage = STAGE_DOWN

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
        rom_min = getattr(rule, "rom_min_angle", None)
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

            # complete_on_return exercises store ROM bounds internally — don't use the ROM path
            has_rom = (
                getattr(rule, "rom_max_angle", None) is not None
                and not getattr(rule, "complete_on_return", False)
            )

            # ── Violation accumulation during active rep window ───────────
            if self._started[rule.name]:
                # Filter out the ROM rule's own coaching warning
                active_viols = {
                    v for v in vnames
                    if is_violation_related(v, rule.name, self.counter.rules)
                    and not (has_rom and v == rule.name)
                }
                if active_viols:
                    self._pending_violations[rule.name] = True

            # ── Rep frame counter for speed checks ────────────────────────
            if self._started[rule.name]:
                self._rep_frame_counts[rule.name] += 1

            # ── Standard exercises path (but with speed/violation checks) ─
            if not has_rom:
                # ── complete_on_return exercises (e.g. Lateral Raise): rest→raised→rest = 1 rep ──
                if getattr(rule, "complete_on_return", False):
                    raised_threshold = rule.up_angle   # e.g. 30°
                    rest_threshold   = rule.down_angle  # e.g. 30°
                    rom_min = getattr(rule, "rom_min_angle", None)
                    rom_max = getattr(rule, "rom_max_angle", None)

                    # Enter RAISED state (UP stage) when angle exceeds raised_threshold
                    if angle >= raised_threshold and state.stage == STAGE_DOWN:
                        state.stage = STAGE_UP   # Arms raised = UP stage
                        self._started[rule.name] = True
                        self._pending_violations[rule.name] = False
                        self._rep_frame_counts[rule.name] = 0
                        self._peak_angles[rule.name] = angle

                    # Track peak while in raised state (UP)
                    if state.stage == STAGE_UP and angle > self._peak_angles[rule.name]:
                        self._peak_angles[rule.name] = angle

                    # Return to rest position (DOWN stage) → rep completes
                    if state.stage == STAGE_UP and angle < rest_threshold:
                        if self._started[rule.name]:
                            too_fast = (
                                rule.min_rep_frames > 0
                                and self._rep_frame_counts[rule.name] < rule.min_rep_frames
                            )
                            # Good: peak in valid range AND no violations AND not too fast
                            peak = self._peak_angles[rule.name]
                            peak_ok = True
                            if rom_min is not None and peak < rom_min:
                                peak_ok = False
                            if rom_max is not None and peak > rom_max:
                                peak_ok = False
                            good = peak_ok and not self._pending_violations[rule.name] and not too_fast
                            self._count_rep(rule, state, good=good, too_fast=too_fast)
                        self._peak_angles[rule.name] = 0.0
                        state.stage = STAGE_DOWN

                # ── Standard counter: rep completes on transition LOW→HIGH ──
                else:
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
                rom_min = getattr(rule, "rom_min_angle", None)
                rom_max = rule.rom_max_angle

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
