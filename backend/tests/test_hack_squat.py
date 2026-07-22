"""Hack Squat configuration verification.

Covers:
  1. Registry/config invariants: single LEFT-side rule set, SIDE camera,
     calibrated stage triggers (130/90) preserved, managed ROM extremes
     (85/150) set, bounds (60-170) preserved, validation skeleton hidden.
  2. Side-adaptation equivalence: the previous twin left_/right_ configuration
     and the new single-LEFT configuration adapt to the SAME effective
     landmarks on BOTH camera sides — while the new one additionally keeps the
     exported rule names stable ("knee", "knee_unlocked") across sides.
  3. Managed counter protocol: GOOD rep on full depth+extension+reversal;
     BAD rep when depth (85°) is missed or the lifter bails before the top.
  4. Engine end-to-end on synthetic side-view poses (left AND right visible):
     reps count identically either way; recorded evaluation names stay
     {"knee_unlocked"}; a locked-out (>170°) rep poisons the rep to BAD and
     scores 80 (100 − 20 warning); a ROM-shallow rep is BAD by the counter
     with NO failed evaluation (score 100 — counter-originated quality).

Run from the repo root:  python tests/test_hack_squat.py
"""

import math
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root

import os
os.environ.setdefault("MODEL_PATH", "assets/models/pose_landmarker_lite.task")

# ── Stub mediapipe (only PoseService needs it; these tests never call it) ──
_mp = types.ModuleType("mediapipe")
_mp_tasks = types.ModuleType("mediapipe.tasks")
_mp_python = types.ModuleType("mediapipe.tasks.python")
_mp_python.vision = types.ModuleType("mediapipe.tasks.python.vision")
_mp.tasks = _mp_tasks
_mp_tasks.python = _mp_python
sys.modules.update({
    "mediapipe": _mp, "mediapipe.tasks": _mp_tasks,
    "mediapipe.tasks.python": _mp_python,
    "mediapipe.tasks.python.vision": _mp_python.vision,
})

from src.core.pose_segments import PoseSegments
from src.exercises.registry import registry
from src.exercises.exercise import Camera
from src.exercises.rules import AngleCounterRule, AngleValidationRule, Severity
from src.services.rep_counter import RepCounter
from src.utils.camera_side import adapt_rules

W = H = 1000  # synthetic frame size (px)


class _LM:
    __slots__ = ("x", "y", "z", "visibility")

    def __init__(self, x, y, visibility):
        self.x, self.y, self.z, self.visibility = x, y, 0.0, visibility


def hack_pose(knee_deg: float, visible: str):
    """Side-view hack-squat pose with a controllable knee angle.

    ``visible`` ("left" | "right") side gets full visibility (1.0), the hidden
    side 0.3 (below get_points' 0.5 threshold, like a real side view). Both
    legs carry real, mirrored geometry so a right-side detection can mirror
    the LEFT rules and still measure a correct angle.
    """
    hip_y, knee_y = 0.55, 0.75
    a = math.radians(180 - knee_deg)
    lms = [_LM(0.5, 0.1, 0.3) for _ in range(33)]

    def leg(hip_i, knee_i, ankle_i, x, vis):
        knee = (x, knee_y)
        ankle = (knee[0] + 0.25 * math.sin(a), knee[1] + 0.25 * math.cos(a))
        lms[hip_i] = _LM(x, hip_y, vis)
        lms[knee_i] = _LM(*knee, vis)
        lms[ankle_i] = _LM(*ankle, vis)

    l_vis, r_vis = (1.0, 0.3) if visible == "left" else (0.3, 1.0)
    leg(23, 25, 27, 0.45, l_vis)                     # LEFT_LEG
    leg(24, 26, 28, 0.55, r_vis)                     # RIGHT_LEG (mirrored geometry)
    # upper-body fillers so the side detector sees both arms/shoulders
    for i, vis, x in ((11, l_vis, 0.41), (13, l_vis, 0.40), (15, l_vis, 0.40),
                      (12, r_vis, 0.59), (14, r_vis, 0.60), (16, r_vis, 0.60)):
        lms[i] = _LM(x, 0.35, vis)
    return lms


def run_session(visible: str, reps):
    """One synthetic session: 30 detection frames, then managed-path reps.

    reps: list of (deep, top) knee-angle pairs. Each rep is played as: bottom
    hold at ``deep`` (DOWN phase), rise through RETURNING, a top overshoot at
    ``top + 5``, then the reversal at ``top`` — the managed counter completes
    the rep exactly on the first decreasing frame >= max_rom_angle. Top
    values keep ~2° of margin against get_points' pixel-quantization, which
    can shave ~0.2° off the synthetic angles (152 plays as ~151.9, so a
    nominal 150 would land *below* the 150° gate and never count).
    """
    from src.services.gym_engine import GymEngine

    engine = GymEngine(registry.get("hack_squat"))
    frame = 0
    for _ in range(35):                                    # settle + detect side
        engine.analyze(hack_pose(150, visible), W, H, frame)
        frame += 1
    for deep, top in reps:
        for angle in [deep] * 5 + [140] * 3 + [top + 5] * 2 + [top] * 2:
            engine.analyze(hack_pose(angle, visible), W, H, frame)
            frame += 1
    return engine


def main():
    # ── 1. Registry/config invariants ───────────────────────────────────────
    ex = registry.get("hack_squat")
    assert ex.camera == Camera.SIDE == "side"
    assert [r.name for r in ex.counter_rules] == ["knee"]
    counter = ex.counter_rules[0]
    assert counter.joints == PoseSegments.LEFT_LEG == (23, 25, 27)
    assert (counter.up_angle, counter.down_angle) == (130, 90)   # untouched calibration
    # managed ROM path: extremes set, tempo gate off
    assert (counter.min_rom_angle, counter.max_rom_angle) == (85, 150)
    assert counter.min_rep_frames == 0
    assert RepCounter([counter])._helper is not None             # CustomCounterHelper engages
    assert [r.name for r in ex.validation_rules] == ["knee_unlocked"]
    guard = ex.validation_rules[0]
    assert (guard.min_angle, guard.max_angle) == (60, 170)
    assert guard.severity == Severity.WARNING == "warning"
    assert ex.display.show_validation_skeleton is False
    assert ex.metadata.muscle_groups == ("quadriceps", "glutes", "hamstrings")

    # ── 2. Side-adaptation equivalence: twins (old) vs single LEFT (new) ────
    legacy_counters = [
        AngleCounterRule(name="knee_left", joints=PoseSegments.LEFT_LEG, up_angle=130, down_angle=90),
        AngleCounterRule(name="knee_right", joints=PoseSegments.RIGHT_LEG, up_angle=130, down_angle=90),
    ]
    legacy_validations = [
        AngleValidationRule(name="knee_unlocked_left", joints=PoseSegments.LEFT_LEG,
                            min_angle=60, max_angle=170, message="Don't lock your left knee"),
        AngleValidationRule(name="knee_unlocked_right", joints=PoseSegments.RIGHT_LEG,
                            min_angle=60, max_angle=170, message="Don't lock your right knee"),
    ]
    for side in ("left", "right"):
        old_c = adapt_rules(legacy_counters, side)
        new_c = adapt_rules([counter], side)
        old_v = adapt_rules(legacy_validations, side)
        new_v = adapt_rules([guard], side)
        # SAME effective measurement: one rule, identical landmarks
        assert len(old_c) == len(new_c) == 1
        assert tuple(old_c[0].joints) == tuple(new_c[0].joints), side
        assert len(old_v) == len(new_v) == 1
        assert tuple(old_v[0].joints) == tuple(new_v[0].joints), side
        # the old names flipped with the side; the new ones never move
        assert new_c[0].name == "knee" and new_v[0].name == "knee_unlocked"
        # the measured side is the detected side either way
        expected_leg = PoseSegments.LEFT_LEG if side == "left" else PoseSegments.RIGHT_LEG
        assert tuple(new_c[0].joints) == expected_leg and tuple(new_v[0].joints) == expected_leg
    # …and the old setup did NOT have that stability — this was the real defect
    assert {r.name for r in adapt_rules(legacy_counters, "left")} == {"knee_left"}
    assert {r.name for r in adapt_rules(legacy_counters, "right")} == {"knee_right"}

    # ── 3. Managed counter protocol: ROM gate + bailout + violations ────────
    # GOOD rep: depth <= 85, extension >= 150, top reversal, no violations
    good_counter = RepCounter([counter])
    for angle in [160, 160, 80, 80, 140, 140, 152, 152, 150]:
        good_counter.update({"knee": angle})
    assert (good_counter.primary.count, good_counter.primary.good, good_counter.primary.bad) == (1, 1, 0)

    # BAD rep — too shallow (never <= 85): bails back down before the top
    # ...wait: shallow here means the ROM gate fails even when the top is reached
    shallow_counter = RepCounter([counter])
    for angle in [160, 160, 88, 88, 140, 140, 152, 152, 150]:
        shallow_counter.update({"knee": angle})
    assert (shallow_counter.primary.count, shallow_counter.primary.bad) == (1, 1)

    # BAD rep — bailout: RETURNING then drops back below 90 before reaching 150
    bail_counter = RepCounter([counter])
    for angle in [160, 160, 80, 80, 140, 88, 88]:
        bail_counter.update({"knee": angle})
    assert (bail_counter.primary.count, bail_counter.primary.bad) == (1, 1)

    # BAD rep — knee_unlocked failed anywhere inside the rep window poisons it
    poison_counter = RepCounter([counter])
    frames = [160, 160, 80, 80, 140, 175, 152, 152, 150]
    for angle in frames:
        poison = {"knee_unlocked"} if angle > 170 else set()
        poison_counter.update({"knee": angle}, poison)
    assert (poison_counter.primary.count, poison_counter.primary.bad) == (1, 1)

    # ── 4. Engine end-to-end, both camera sides ─────────────────────────────
    for visible in ("left", "right"):
        engine = run_session(visible, reps=[(80, 152), (80, 152)])
        history = engine.judge.history
        assert len(history) == 2, (visible, len(history))
        assert all(rep.good for rep in history)
        # stable names in the record, whichever side was filmed
        assert {e.rule_name for rep in history for e in rep.evaluations} == {"knee_unlocked"}

        # locked-out top (177/172 measures > 170): the violation poisons the rep
        engine2 = run_session(visible, reps=[(80, 152), (80, 172)])
        rep2 = engine2.judge.history[1]
        assert rep2.good is False                                  # managed path judges
        guard_eval = {e.rule_name: e for e in rep2.evaluations}["knee_unlocked"]
        assert guard_eval.passed is False and guard_eval.angle > 170.0

    # report integration: lockout rep BAD + scored 80 (100 − 20 warning)
    from src.analytics.analyzer import SessionAnalyzer

    engine3 = run_session("left", reps=[(80, 152), (80, 172)])
    report = SessionAnalyzer().build_report(
        engine3.judge.history, exercise=engine3.exercise, fps=25.0,
    )
    assert [r.good for r in report.history] == [True, False]
    assert [r.score for r in report.history] == [100.0, 80.0]
    assert report.history[1].failed_rules == ("knee_unlocked",)
    # managed counter: every rep is explicitly "counter"-judged —
    # a good=False with/without failed evaluations is self-explained
    assert {r.judged_by for r in report.history} == {"counter"}
    assert report.summary.common_errors == {"knee_unlocked": 1}
    stat = {row.rule: row for row in report.stats.rules}["knee_unlocked"]
    assert (stat.evaluations, stat.failed) == (2, 1) and stat.success_rate == 50.0

    # ROM-shallow rep (depth 88 > 85): BAD by the counter, but NO failed
    # validation evaluation -> score 100. Counter-originated quality, by design
    # (same semantics as biceps_curl; see the hack_squat module docstring).
    engine4 = run_session("left", reps=[(80, 152), (88, 152)])
    report4 = SessionAnalyzer().build_report(
        engine4.judge.history, exercise=engine4.exercise, fps=25.0,
    )
    assert [r.good for r in report4.history] == [True, False]
    assert report4.history[1].failed_rules == () and report4.history[1].score == 100.0
    assert report4.summary.common_errors == {}

    print("ALL HACK-SQUAT ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
