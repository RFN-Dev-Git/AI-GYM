"""Architecture refactor verification — proves the refactor changed no behavior.

Covers:
  1. Enums are ``str``-compatible with the literals they replaced.
  2. Every registered exercise exposes typed ``ExerciseMetadata``/``Camera``.
  3. Rule immutability is intact and the ValidationRule hierarchy is right.
  4. ``validate_all`` dispatch still evaluates all three rule kinds correctly.
  5. RepJudge severity ranking/classification behaves identically (enum or
     plain-string severities, worst-severity de-duplication).
  6. RepCounter (simple + CustomCounterHelper paths) still advances stages.
  7. SessionAnalyzer severity weights accept enum- and str-keyed dicts alike.

Run from the repo root:  python tests/test_architecture.py
"""

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
    "mediapipe": _mp,
    "mediapipe.tasks": _mp_tasks,
    "mediapipe.tasks.python": _mp_python,
    "mediapipe.tasks.python.vision": _mp_python.vision,
})

import dataclasses

from src.exercises.exercise import Camera, ExerciseMetadata
from src.exercises.registry import registry
from src.exercises.rules import (
    AngleCounterRule, AngleROMValidationRule, AngleValidationRule,
    DistanceValidationRule, LandmarkPair, LandmarkTriplet,
    Severity, Stage, ValidationRule,
)
from src.exercises.validation import validate_all, violations
from src.services.rep_counter import RepCounter
from src.services.rep_judge import RepJudge


class LM:
    __slots__ = ("x", "y", "z", "visibility")

    def __init__(self, px, py, w=1000, h=1000):
        self.x, self.y = px / w, py / h
        self.z = 0.0
        self.visibility = 1.0


def landmarks(points: dict[int, tuple[float, float]]):
    lms = [LM(0, 0) for _ in range(33)]
    for idx, (px, py) in points.items():
        lms[idx] = LM(px, py)
    return lms


def main():
    # ── 1. Enums are str-compatible (legacy comparisons keep working) ───────
    assert Severity.ERROR == "error" and isinstance(Severity.ERROR, str)
    assert Severity.WARNING == "warning" and Severity.INFO == "info"
    assert Stage.UP == "up" and Stage.DOWN == "down" and Stage.RETURNING == "returning"
    assert Camera.BOTH == "both" and Camera.SIDE == "side"
    assert "error" in (Severity.ERROR, Severity.WARNING)          # membership both ways
    assert {Severity.ERROR: 1}.get("error") == 1                  # dict keys interchangeable

    # ── 2. Registry exercises: typed metadata & camera, configs unchanged ───
    expected = {
        "deadlift", "cable_chest_fly", "squat", "pushup", "biceps_curl",
        "lat_pulldown", "leg_press", "hack_squat", "shoulder_press",
    }
    assert set(registry.list()) == expected
    for name in registry.list():
        ex = registry.get(name)
        assert isinstance(ex.metadata, ExerciseMetadata), name
        assert isinstance(ex.metadata.description, str) and ex.metadata.description, name
        assert isinstance(ex.metadata.muscle_groups, tuple) and ex.metadata.muscle_groups, name
        assert dataclasses.is_dataclass(ex.metadata)
        try:
            dataclasses.replace(ex.metadata, description="x")  # frozen but replaceable-copy
        except Exception as e:
            raise AssertionError(f"{name}: metadata not a proper frozen dataclass: {e}")
        assert ex.camera in (Camera.BOTH, Camera.SIDE), name
        assert ex.counter_rules, name

    # spot-check a couple of values survived the refactor byte-for-byte
    assert registry.get("shoulder_press").metadata.muscle_groups == ("shoulders", "triceps", "upper chest")
    assert registry.get("hack_squat").camera == Camera.SIDE == "side"

    # ── 3. Rule hierarchy & immutability ────────────────────────────────────
    for cls in (AngleValidationRule, AngleROMValidationRule, DistanceValidationRule):
        assert issubclass(cls, ValidationRule) and dataclasses.is_dataclass(cls)
        assert cls.__dataclass_params__.frozen, cls
    # deliberate: AngleCounterRule has NO base class (single kind — no hierarchy)
    assert AngleCounterRule.__bases__ == (object,)

    r = AngleValidationRule(
        name="x", joints=(11, 13, 15), min_angle=0, max_angle=90, message="m",
    )
    assert r.severity == Severity.ERROR == "error"                # default preserved
    try:
        r.min_angle = 5
        raise AssertionError("rules must be immutable")
    except dataclasses.FrozenInstanceError:
        pass

    # ── 4. validate_all dispatch: all three kinds evaluate like before ──────
    lms = landmarks({
        11: (300, 300), 12: (700, 300),          # shoulders 400px apart
        13: (300, 480), 15: (300, 660),          # L elbow/wrist straight down (180°)
        14: (700, 480), 16: (750, 660),          # R wrist near shoulder-> narrow span
    })
    rules = [
        AngleValidationRule(name="ang", joints=(11, 13, 15), min_angle=150, max_angle=180,
                            message="a", severity=Severity.WARNING),
        DistanceValidationRule(name="dist", measurement=(15, 16), reference=(11, 12),
                               min_ratio=1.2, max_ratio=3.0, message="d", severity=Severity.ERROR),
        AngleROMValidationRule(name="rom", joints=(11, 13, 15), min_rom_angle=60, max_rom_angle=170,
                               message="r", severity=Severity.INFO),
    ]
    assert all(isinstance(rr.joints, tuple) for rr in rules if hasattr(rr, "joints"))
    assert by_name_dist_structure_ok(rules)  # see helper below
    results = validate_all(rules, lms, 1000, 1000, states={})
    by_name = {x.rule_name: x for x in results}
    assert by_name["ang"].passed                                  # ~180° in range
    assert not by_name["dist"].passed                             # span 452.5/400 = 1.13 < 1.2
    assert abs(by_name["dist"].angle - (452.548 / 400)) < 0.01
    assert by_name["rom"].passed                                  # no state -> passes
    assert by_name["dist"].severity == Severity.ERROR
    assert [v.rule_name for v in violations(results)] == ["dist"]

    # dispatch on the base type is unaffected by the new inheritance
    assert all(isinstance(x, ValidationRule) for x in rules)

    # ── 5. RepJudge: same classification & de-dup as before ─────────────────
    j = RepJudge()
    f_warn = dataclasses.replace(
        next(x for x in results if x.rule_name == "dist"), severity=Severity.WARNING)
    f_err = dataclasses.replace(f_warn, severity=Severity.ERROR)
    j.observe([f_warn], frame=1)                                  # warning first...
    j.observe([f_err], frame=2)                                   # ...then error: error must win
    rep = j.finalize_rep(1, frame=3)
    assert not rep.good and len(rep.violations) == 1
    assert rep.violations[0].severity == Severity.ERROR == "error"

    j2 = RepJudge()
    j2.observe([f_warn], frame=1)                                 # warning only -> still BAD (unchanged rule)
    assert not j2.finalize_rep(1, frame=2).good
    j3 = RepJudge()                                               # nothing observed -> GOOD
    assert j3.finalize_rep(1, frame=2).good

    # plain-string severities still classify identically (legacy interop)
    from src.exercises.validation import ValidationResult
    j4 = RepJudge()
    j4.observe([ValidationResult("n", "m", "error", False, None)], frame=1)
    assert not j4.finalize_rep(1, frame=2).good

    # ── 6. RepCounter: stage flow on both counting paths ────────────────────
    simple = RepCounter([AngleCounterRule(name="knee", joints=(23, 25, 27), up_angle=160, down_angle=70)])
    st = simple.update({"knee": 165})["knee"]
    assert st.stage == "up" and st.count == 0
    st = simple.update({"knee": 60})["knee"]
    assert st.count == 1 and st.stage == "down"                    # rep completed on entering down
    assert simple.update({"knee": 170})["knee"].stage == "up"

    rom = RepCounter([AngleCounterRule(name="k", joints=(23, 25, 27), up_angle=120, down_angle=110,
                                       min_rom_angle=80, max_rom_angle=160)])
    assert rom._helper is not None                                 # custom path engaged as before
    assert rom.update({"k": 100})["k"].stage == Stage.DOWN == "down"
    assert rom.update({"k": 130})["k"].stage == Stage.RETURNING == "returning"

    # default stage labels still the legacy strings
    assert AngleCounterRule(name="x", joints=(1, 2, 3), up_angle=1, down_angle=0).up_stage == "up"

    # ROM bounds use the unified min_/max_ prefix on the counter rule too
    cr = AngleCounterRule(name="x", joints=(1, 2, 3), up_angle=1, down_angle=0,
                          min_rom_angle=80, max_rom_angle=160)
    assert (cr.min_rom_angle, cr.max_rom_angle) == (80, 160)

    # ── 7. SessionAnalyzer: enum- and str-keyed severity weights both work ──
    from src.analytics.analyzer import DEFAULT_SEVERITY_WEIGHTS, SessionAnalyzer
    assert DEFAULT_SEVERITY_WEIGHTS[Severity.ERROR] == 50.0
    assert DEFAULT_SEVERITY_WEIGHTS["error"] == 50.0               # str lookup works too
    a = SessionAnalyzer({"error": 1.0, "warning": 0.5, "info": 0.0})
    assert a.severity_weights.get(Severity.ERROR) == 1.0           # enum lookup on user dict

    # ── 8. camera-side adaptation remaps measurement/reference pairs ────────
    from src.utils.camera_side import adapt_rules
    left_rules = [
        AngleValidationRule(name="back", joints=(11, 23, 25), min_angle=0, max_angle=180, message="x"),
        DistanceValidationRule(name="grip", measurement=(15, 11), reference=(11, 13),
                               min_ratio=0, max_ratio=5, message="y"),
    ]
    adapted = adapt_rules(left_rules, "right")
    assert adapted[0].joints == (12, 24, 26)
    assert adapted[1].measurement == (16, 12) and adapted[1].reference == (12, 14)
    # symmetric (both-side) distance rule passes through untouched
    both = [DistanceValidationRule(name="wrists", measurement=(15, 16), reference=(11, 12),
                                   min_ratio=1.2, max_ratio=3, message="z")]
    assert adapt_rules(both, "right")[0] is both[0]

    print("ALL ARCHITECTURE ASSERTIONS PASSED")


def by_name_dist_structure_ok(rules):
    """Landmark groups are named pairs/triplets, not numbered primitives."""
    dist = next(r for r in rules if isinstance(r, DistanceValidationRule))
    assert dist.measurement == (15, 16) and dist.reference == (11, 12)
    assert not hasattr(dist, "point1") and not hasattr(dist, "reference1")
    # aliases document the shapes
    assert LandmarkPair == tuple[int, int]
    assert LandmarkTriplet == tuple[int, int, int]
    return True


if __name__ == "__main__":
    main()
