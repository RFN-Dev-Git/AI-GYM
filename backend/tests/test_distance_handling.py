"""Logic test for the generalized distance-violation handling in GymEngine.

Drives engine.analyze() with synthetic shoulder-press landmarks and asserts:
  1. Reps with proper wrist spacing are counted GOOD.
  2. A rep whose wrists come too close AT THE TOP of the press is BAD, and
     the session history records *why* (violations list is not empty).
  3. Exercises without DistanceValidationRules are completely unaffected.

Run from the repo root:  python tests/test_distance_handling.py
"""

import sys
import types
from pathlib import Path
from math import cos, sin, radians

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root

import os
os.environ.setdefault("MODEL_PATH", "assets/models/pose_landmarker_lite.task")

# ── Stub mediapipe (only PoseService needs it; analyze() never touches it) ──
_mp = types.ModuleType("mediapipe")
_mp_tasks = types.ModuleType("mediapipe.tasks")
_mp_python = types.ModuleType("mediapipe.tasks.python")
_mp_python.vision = types.ModuleType("mediapipe.tasks.python.vision")
_mp.tasks = _mp_tasks
_mp_tasks.python = _mp_python
sys.modules.update({
    "mediapipe": _mp,
    "mediapipe.tasks": _mp_tasks,
    "mediapipe.tasks.python": _mp_python,
    "mediapipe.tasks.python.vision": _mp_python.vision,
})

from src.exercises.registry import registry
from src.services.gym_engine import GymEngine

W = H = 1000  # synthetic frame size (px)


class LM:
    __slots__ = ("x", "y", "z", "visibility")

    def __init__(self, px, py):
        self.x, self.y = px / W, py / H
        self.z = 0.0
        self.visibility = 1.0


# Landmark indices
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16
L_HIP, R_HIP = 23, 24


def pose(beta_deg: float):
    """Build a 33-landmark pose for a shoulder press.

    beta: arm bend — 0° = arm straight overhead (elbow angle 180°),
          120° = weight at chest (elbow angle ~60°).
    Shoulders are 400px apart; wrists flare out symmetrically with beta, so:
      beta=20  -> wrists 523px apart -> ratio 1.31 (PASS >= 1.2)
      beta=2   -> wrists 413px apart -> ratio 1.03 (FAIL, too narrow)
      beta=120 -> wrists 711px apart -> ratio 1.78 (PASS <= 3.0)
    """
    beta = radians(beta_deg)
    pts = [LM(0, 0) for _ in range(33)]

    pts[L_SHOULDER] = LM(300, 300)
    pts[R_SHOULDER] = LM(700, 300)
    pts[L_ELBOW] = LM(300, 480)
    pts[R_ELBOW] = LM(700, 480)
    # Wrist sits *below* the elbow (arm hanging), so the elbow angle is
    # 180° - beta as intended: beta=20 -> ~160° (up), beta=120 -> ~60° (down).
    pts[L_WRIST] = LM(300 - 180 * sin(beta), 480 + 180 * cos(beta))
    pts[R_WRIST] = LM(700 + 180 * sin(beta), 480 + 180 * cos(beta))
    pts[L_HIP] = LM(300, 650)
    pts[R_HIP] = LM(700, 650)
    return pts


UP_WIDE = 20        # arms overhead, wrists properly wide   -> no violation
UP_NARROW = 2       # arms overhead, wrists too close       -> distance violation
DOWN = 120          # weight at chest


def run_sequence(engine, sequence):
    for frame_idx, beta in enumerate(sequence):
        engine.analyze(pose(beta), W, H, frame_idx)


def main():
    exercise = registry.get("shoulder_press")
    engine = GymEngine(exercise)

    assert engine._distance_rule_names == {"left_shoulder_wrist_distance"}, \
        f"distance rules not discovered: {engine._distance_rule_names}"

    sequence = (
        [UP_WIDE] * 3 + [DOWN] * 3      # rep 1: good
        + [UP_NARROW] * 3 + [DOWN] * 3  # rep 2: wrists narrow at top -> bad
        + [UP_WIDE] * 3 + [DOWN] * 3    # rep 3: good
    )
    run_sequence(engine, sequence)

    history = engine.judge.history
    total, good, bad = (
        engine.judge.total_reps, engine.judge.good_reps, engine.judge.bad_reps,
    )
    print(f"reps: total={total} good={good} bad={bad}")
    for rep in history:
        status = "GOOD" if rep.good else "BAD"
        names = [v.rule_name for v in rep.violations]
        print(f"  rep #{rep.number}: {status}  violations={names}")

    assert total == 3, f"expected 3 reps, got {total}"
    assert good == 2, f"expected 2 good reps, got {good}"
    assert bad == 1, f"expected 1 bad rep, got {bad}"

    rep2 = history[1]
    assert not rep2.good, "rep #2 (narrow wrists at top) should be BAD"
    assert any(v.rule_name == "left_shoulder_wrist_distance" for v in rep2.violations), \
        "rep #2 should carry the distance violation explaining why it is bad"

    # ── Regression: exercises without distance rules are untouched ────────
    for name in ("squat", "pushup", "deadlift", "lat_pulldown", "cable_chest_fly"):
        e = GymEngine(registry.get(name))
        assert e._distance_rule_names == set(), f"{name}: unexpected distance rules"
        assert e._distance_violation_in_current_rep is False

    print("\nALL ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
