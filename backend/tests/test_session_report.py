"""Verify the complete Session Report pipeline.

Covers:
  1. RepJudge record()/observe() — complete evaluations collected, existing
     violation/start_frame semantics byte-identical.
  2. SessionAnalyzer.analyze() — summary behaviour preserved.
  3. SessionAnalyzer.build_report() — exercise info; session-level rule
     definitions stored ONCE (static metadata + counter-originated rules
     discovered from produced data); per-rep records referencing rules by
     name with ONLY dynamic data (pass/fail, measured value, and a message
     solely when it is a runtime override); explicit judged_by semantics.
  4. JsonSessionExporter — round-trips; normalized layout (each fact once:
     no schema_version, no duplicate timestamp/exercise name); no static
     metadata repeated in history.
  5. End-to-end — engine history -> report -> JSON, with dynamic ROM
     messages preserved as overrides.
  6. Audit scenario — scores/error stats derived from the complete record.
  7. "session" + "stats" sections — id, recorded_at (the ONLY timestamp),
     fps, scoring policy; per-rule success rates + score extremes.
  8. Consistency invariants — summary always reconciles with history;
     judged_by explains every (good, evaluations) combination;
     session score == aggregation of exported per-rep scores.

Run from the repo root:  python tests/test_session_report.py
"""

import json
import sys
import tempfile
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

from src.analytics.analyzer import SessionAnalyzer
from src.analytics.exporters import JsonSessionExporter
from src.analytics.session_report import SessionReport
from src.exercises.registry import registry
from src.exercises.rules import Severity
from src.exercises.validation import ValidationResult
from src.services.rep_judge import RepJudge, RepResult


def outcome(rule, passed, severity=Severity.ERROR, value=90.0, message="msg"):
    return ValidationResult(rule, message, severity, passed, value)


# Static messages as configured in shoulder_press.py (for override checks)
DIST_MSG = "Keep wrists wider than shoulders"
ELBOW_MSG = "Elbow: Reach 170° up, 60° down"


def main():
    # ── 1. RepJudge: record() is additive; observe() keeps legacy semantics ─
    j = RepJudge()
    j.record([outcome("back", True, value=170.0), outcome("elbow", True, value=160.0)], frame=0)
    j.record([outcome("back", True, value=165.0)], frame=1)          # latest pass wins
    assert j._start_frame == 0 and not j._violations   # record() tracks the window from frame 0

    j.observe([outcome("back", False, Severity.WARNING, 140.0)], frame=10)
    j.observe([outcome("back", False, Severity.ERROR, 130.0, "worse")], frame=11)
    j.record([outcome("elbow", True, value=155.0)])

    rep = j.finalize_rep(1, frame=12)
    assert rep.start_frame == 0 and rep.end_frame == 12   # window started at first recorded frame
    assert [v.rule_name for v in rep.violations] == ["back"]
    assert rep.violations[0].severity == Severity.ERROR and rep.violations[0].message == "worse"
    assert not rep.good
    by_rule = {e.rule_name: e for e in rep.evaluations}
    assert set(by_rule) == {"back", "elbow"}
    assert by_rule["back"].passed is False and by_rule["back"].severity == Severity.ERROR
    assert by_rule["elbow"].passed is True and by_rule["elbow"].angle == 155.0

    j2 = RepJudge()
    j2.record([outcome("x", False)], frame=0)
    j2.record([outcome("x", True)], frame=1)                # pass never overwrites a fail
    rep2 = j2.finalize_rep(1, frame=1, force_good=False)
    assert rep2.evaluations[0].passed is False

    # observe() with no prior record() still starts the window at the observed frame
    j3 = RepJudge()
    j3.observe([outcome("y", False)], frame=42)
    assert j3.finalize_rep(1, frame=43).start_frame == 42

    # ── 2. analyze(): legacy summary behaviour preserved ────────────────────
    reps = [
        RepResult(1, True, violations=[], start_frame=0, end_frame=49),
        RepResult(2, False, violations=[outcome("depth", False)], start_frame=50, end_frame=129,
                  evaluations=[outcome("depth", False)]),
        RepResult(3, True, violations=[], start_frame=130, end_frame=199),
    ]
    summary = SessionAnalyzer().analyze(reps, exercise_name="Squat", fps=25.0)
    assert summary.total_reps == 3 and summary.good_reps == 2 and summary.bad_reps == 1
    assert abs(summary.accuracy - 66.6667) < 0.01
    assert abs(summary.average_rep_time - (2.0 + 3.2 + 2.8) / 3) < 1e-9
    assert summary.fastest_rep == 2.0 and summary.slowest_rep == 3.2
    assert summary.common_errors == {"depth": 1} and summary.most_common_error == "depth"
    # score: 100, 50 (one error), 100 -> session 83.33
    assert abs(summary.score - (100 + 50 + 100) / 3) < 0.01

    # ── 3. build_report(): structure, definitions-once, slim evaluations ────
    exercise = registry.get("shoulder_press")
    reps_b = [
        RepResult(
            1, True, violations=[], start_frame=0, end_frame=49,
            evaluations=[
                outcome("left_shoulder_wrist_distance", True, value=2.10, message=DIST_MSG),
                outcome("left_elbow_rom", True, value=171.0, message=ELBOW_MSG),
            ],
        ),
        RepResult(
            2, False,
            violations=[
                outcome("left_shoulder_wrist_distance", False, value=1.02, message=DIST_MSG),
                outcome("left_elbow_rom", False, value=66.0,
                        message="Go deeper — target <= 60 deg"),     # dynamic ROM cue
                outcome("left_shoulder_too_fast", False, Severity.WARNING, None,
                        "Too fast — control the movement"),
            ],
            start_frame=50, end_frame=124,
            evaluations=[
                outcome("left_shoulder_wrist_distance", False, value=1.02, message=DIST_MSG),
                outcome("left_elbow_rom", False, value=66.0,
                        message="Go deeper — target <= 60 deg"),     # dynamic override
                outcome("left_shoulder_rom", True, value=165.0,
                        message="Shoulder: Reach 160° up, 40-80° down"),
                outcome("left_shoulder_too_fast", False, Severity.WARNING, None,
                        "Too fast — control the movement"),
            ],
        ),
    ]
    report = SessionAnalyzer().build_report(
        reps_b, exercise=exercise, fps=25.0, date="2026-07-21T10:00:00",
    )
    assert isinstance(report, SessionReport)

    # exercise info
    assert report.exercise.name == "Shoulder Press"
    assert report.exercise.muscle_groups == ("shoulders", "triceps", "upper chest")
    assert report.exercise.camera == "both"
    assert [c.name for c in report.exercise.counter_rules] == ["left_shoulder", "right_shoulder"]
    assert report.exercise.counter_rules[0].sync_group == "shoulder_press"

    # summary embedded == analyze() summary
    legacy_summary = SessionAnalyzer().analyze(
        reps_b, exercise_name=exercise.name, fps=25.0, date="2026-07-21T10:00:00",
    )
    assert report.summary == legacy_summary

    # ── rules section: every definition stored EXACTLY ONCE ─────────────────
    defs = {r.name: r for r in report.rules}
    assert len(defs) == len(report.rules)                       # no duplicates
    # all validation rules from the exercise are defined...
    for vr in exercise.validation_rules:
        assert vr.name in defs
    # ...plus the counter-originated rule discovered in the produced data
    d_dist = defs["left_shoulder_wrist_distance"]
    assert d_dist.type == "distance" and d_dist.value_unit == "ratio"
    assert (d_dist.expected_min, d_dist.expected_max) == (1.2, 3.0)
    assert d_dist.measurement == (15, 16) and d_dist.reference == (11, 12)
    assert d_dist.joints is None and d_dist.severity == Severity.ERROR
    d_rom = defs["left_elbow_rom"]
    assert d_rom.type == "range_of_motion" and d_rom.value_unit == "degrees"
    assert (d_rom.expected_min, d_rom.expected_max) == (60, 170)
    assert d_rom.joints == (11, 13, 15)
    d_fast = defs["left_shoulder_too_fast"]
    assert d_fast.type == "counter" and d_fast.severity == Severity.WARNING
    assert d_fast.message == "Too fast — control the movement"
    assert d_fast.expected_min is None and d_fast.joints is None

    # ── history: references + dynamic data only ─────────────────────────────
    assert len(report.history) == 2
    r1, r2 = report.history
    assert r1.good and r1.score == 100.0 and r1.failed_rules == ()
    assert r1.duration_seconds == 2.0
    e1 = {e.rule: e for e in r1.evaluations}
    assert e1["left_shoulder_wrist_distance"] == type(e1["left_shoulder_wrist_distance"])(
        rule="left_shoulder_wrist_distance", passed=True, measured_value=2.10, message=None,
    )

    assert r2.good is False and r2.duration_seconds == 3.0
    assert set(r2.failed_rules) == {
        "left_shoulder_wrist_distance", "left_elbow_rom", "left_shoulder_too_fast",
    }
    e2 = {e.rule: e for e in r2.evaluations}
    # static message identical to the definition -> omitted (no duplication)
    assert e2["left_shoulder_wrist_distance"].message is None
    assert e2["left_shoulder_rom"].message is None
    assert e2["left_shoulder_too_fast"].message is None
    # dynamic runtime cue -> kept as override
    assert e2["left_elbow_rom"].message == "Go deeper — target <= 60 deg"
    # nothing static leaks into the slim record
    assert not hasattr(e2["left_elbow_rom"], "severity")
    assert not hasattr(e2["left_elbow_rom"], "expected_min")
    assert not hasattr(e2["left_elbow_rom"], "type")
    # per-rep score from the complete evaluation record: 100 - 50 - 50 - 20 -> 0
    assert r2.score == 0.0

    # summary error statistics match the exported history
    assert report.summary.common_errors == {
        "left_elbow_rom": 1, "left_shoulder_too_fast": 1, "left_shoulder_wrist_distance": 1,
    }
    assert report.summary.most_common_error == "left_shoulder_wrist_distance"
    assert abs(report.summary.score - (100.0 + 0.0) / 2) < 0.01

    # ── 4. Exporter: JSON round-trip + legacy summary layout ────────────────
    with tempfile.TemporaryDirectory() as tmp:
        out = JsonSessionExporter().export(report, Path(tmp) / "session")
        assert out.suffix == ".json" and out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))

    # FIX 1: no schema_version; the layout is deliberately unversioned
    assert "schema_version" not in data
    assert set(data) == {"session", "exercise", "summary", "rules", "history", "stats"}

    # FIX 2 + 3: identity/timestamp live exactly once — in exercise/session,
    # NOT duplicated inside summary (summary carries pure aggregates only)
    assert "exercise" not in data["summary"] and "date" not in data["summary"]
    assert data["exercise"]["name"] == "Shoulder Press"

    legacy_json = {
        "total_reps": summary.total_reps,
        "good_reps": summary.good_reps,
        "bad_reps": summary.bad_reps,
        "accuracy": round(summary.accuracy, 1),
        "average_rep_duration": round(summary.average_rep_time, 2),
        "fastest_rep": round(summary.fastest_rep, 2),
        "slowest_rep": round(summary.slowest_rep, 2),
        "total_workout_duration": round(summary.total_workout_duration, 2),
        "common_errors": dict(summary.common_errors),
        "most_common_error": summary.most_common_error,
        "score": round(summary.score, 1) if summary.score is not None else None,
    }
    legacy_report = JsonSessionExporter()._serialize(
        SessionAnalyzer().build_report(
            reps, exercise=registry.get("squat"), fps=25.0, date=summary.date,
        )
    )
    assert legacy_report["summary"] == legacy_json
    assert set(data["summary"]) == set(legacy_json)

    # enums serialized to plain values
    assert data["exercise"]["camera"] == "both"
    json_defs = {d["name"]: d for d in data["rules"]}
    assert json_defs["left_shoulder_wrist_distance"]["severity"] == "error"
    assert json_defs["left_shoulder_wrist_distance"]["measurement"] == [15, 16]
    assert json_defs["left_shoulder_too_fast"]["severity"] == "warning"

    # history holds no repeated static metadata
    for ev in data["history"][1]["evaluations"]:
        assert set(ev) <= {"rule", "passed", "measured_value", "message"}
    ev2 = {e["rule"]: e for e in data["history"][1]["evaluations"]}
    assert ev2["left_shoulder_wrist_distance"] == {
        "rule": "left_shoulder_wrist_distance", "passed": False, "measured_value": 1.02,
    }
    assert ev2["left_elbow_rom"]["message"] == "Go deeper — target <= 60 deg"

    # every evaluation references a defined rule (self-describing join works)
    defined = set(json_defs)
    for rep_d in data["history"]:
        for ev in rep_d["evaluations"]:
            assert ev["rule"] in defined
    # every defined rule is used at least once (no dead definitions)
    used = {ev["rule"] for rep_d in data["history"] for ev in rep_d["evaluations"]}
    assert set(json_defs) == used | set(json_defs)  # superset by construction
    assert used <= defined

    # ── 5. End-to-end: engine history -> report -> JSON ─────────────────────
    from tests.test_distance_handling import pose, UP_WIDE, UP_NARROW, DOWN, W, H
    from src.services.gym_engine import GymEngine

    engine = GymEngine(registry.get("shoulder_press"))
    seq = ([UP_WIDE] * 3 + [DOWN] * 3 + [UP_NARROW] * 3 + [DOWN] * 3 + [UP_WIDE] * 3 + [DOWN] * 3)
    for i, b in enumerate(seq):
        engine.analyze(pose(b), W, H, i)

    live = SessionAnalyzer().build_report(
        engine.judge.history, exercise=engine.exercise, fps=25.0, total_duration=1.0,
    )
    assert len(live.history) == 3 and not live.history[1].good
    # frame windows now span whole reps (no nulls, no single-frame durations)
    windows = [(r.start_frame, r.end_frame, r.duration_seconds) for r in live.history]
    assert windows == [(0, 3, 0.16), (4, 9, 0.24), (10, 15, 0.24)]
    assert live.summary.fastest_rep == 0.16 and live.summary.slowest_rep == 0.24
    assert abs(live.summary.average_rep_time - (0.16 + 0.24 + 0.24) / 3) < 1e-9
    assert live.summary.common_errors == {"left_shoulder_wrist_distance": 1}
    assert live.summary.most_common_error == "left_shoulder_wrist_distance"
    live_defs = {r.name for r in live.rules}
    rep2_rules = {e.rule: e for e in live.history[1].evaluations}
    assert "left_shoulder_wrist_distance" in live_defs
    assert rep2_rules["left_shoulder_wrist_distance"].passed is False
    assert "left_elbow_rom" in rep2_rules and "left_shoulder_rom" in rep2_rules
    # ROM rules passed with static messages -> no override stored
    assert rep2_rules["left_elbow_rom"].message is None
    assert len(live.history[0].evaluations) >= 5
    assert all(e.rule in live_defs for e in live.history[1].evaluations)
    json.dumps(JsonSessionExporter()._serialize(live), ensure_ascii=False)

    # ── 6. Audit scenario: GOOD-by-counter reps with failing ERROR rules ────
    import math as _m

    class _LM:
        __slots__ = ("x", "y", "z", "visibility")
        def __init__(s2, x, y): s2.x, s2.y, s2.z, s2.visibility = x, y, 0.0, 1.0

    def squat_pose(knee_deg, torso_deg):
        a = _m.radians(180 - knee_deg); kp = (0.50, 0.75); hip = (0.50, 0.55)
        ank = (kp[0] + 0.25 * _m.sin(a), kp[1] + 0.25 * _m.cos(a))
        t = _m.radians(180 - torso_deg); sh = (hip[0] + 0.20 * _m.sin(t), hip[1] - 0.20 * _m.cos(t))
        lms = [_LM(0.5, 0.1) for _ in range(33)]
        lms[24] = _LM(*hip); lms[26] = _LM(*kp); lms[28] = _LM(*ank)
        lms[12] = _LM(*sh); lms[11] = _LM(sh[0] - 0.02, sh[1])
        lms[23] = _LM(hip[0] - 0.02, hip[1]); lms[25] = _LM(*kp); lms[27] = _LM(ank[0] - 0.02, ank[1])
        return lms

    sq = GymEngine(registry.get("squat"))
    sq_seq = [170] * 40 + [60] * 6 + [170] * 6 + [60] * 6 + [170] * 6 + [60] * 6 + [170] * 6
    for i, k in enumerate(sq_seq):
        torso = 40 if i < 52 else 175          # bad form for 2 reps, then textbook form
        sq.analyze(squat_pose(k, torso), 1000, 1000, i)

    sq_report = SessionAnalyzer().build_report(
        sq.judge.history, exercise=sq.exercise, fps=25.0, total_duration=3.0,
    )
    assert len(sq_report.history) == 3
    # INTENDED: the simple-path counter still classifies all reps GOOD (unchanged runtime)
    assert all(r.good for r in sq_report.history)
    # FIXED: the record no longer claims perfection — scores reflect the evidence
    assert [r.score for r in sq_report.history] == [50.0, 50.0, 100.0]
    assert sq_report.history[0].failed_rules == ("back_straight",)
    assert sq_report.history[2].failed_rules == ()
    # FIXED: summary error statistics agree with history
    assert sq_report.summary.common_errors == {"back_straight": 2}
    assert sq_report.summary.most_common_error == "back_straight"
    assert abs(sq_report.summary.score - (50 + 50 + 100) / 3) < 0.01
    # FIXED: every rep has a real frame window and duration (no null exports)
    # (first ~30 frames are consumed by side-camera adaptation -> 12-frame windows)
    for r in sq_report.history:
        assert r.start_frame is not None and r.end_frame is not None
        assert r.duration_seconds is not None and r.duration_seconds > 0.4
    assert abs(sq_report.summary.average_rep_time - 0.48) < 0.01
    # INVARIANT: score < 100 iff the rep has failed evaluations
    for r in sq_report.history:
        assert (r.score < 100.0) == bool(r.failed_rules)
    # INTENDED & DOCUMENTED: good may be True alongside failed rules (see RepetitionRecord docs)
    json.dumps(JsonSessionExporter()._serialize(sq_report), ensure_ascii=False)

    # ── 7. "session" + "stats" sections ──────────────────────────────────────
    from datetime import datetime as _dt
    from statistics import pstdev as _pstdev

    # --- session block (in-memory report from section 3) -------------------
    ses = report.session
    assert ses is not None and len(ses.id) == 32 and int(ses.id, 16) >= 0   # uuid4 hex
    assert _dt.fromisoformat(ses.recorded_at).tzinfo is not None            # tz-aware
    assert ses.fps == 25.0 and ses.base_score == 100.0
    assert dict(ses.severity_weights) == {
        Severity.ERROR: 50.0, Severity.WARNING: 20.0, Severity.INFO: 10.0,
    }

    # --- stats.rules: hand-checked against the known section-3 data --------
    rows = {row.rule: row for row in report.stats.rules}
    # one row per defined rule, including never-evaluated ones
    assert {row.rule for row in report.stats.rules} == {d.name for d in report.rules}
    d = rows["left_shoulder_wrist_distance"]
    assert (d.evaluations, d.passed, d.failed) == (2, 1, 1)
    assert d.success_rate == 50.0
    assert abs(d.avg_measured_value - (2.10 + 1.02) / 2) < 1e-9
    assert d.min_measured_value == 1.02 and d.max_measured_value == 2.10
    e = rows["left_elbow_rom"]
    assert (e.evaluations, e.passed, e.failed, e.success_rate) == (2, 1, 1, 50.0)
    f = rows["left_shoulder_too_fast"]
    assert (f.evaluations, f.failed, f.success_rate) == (1, 1, 0.0)
    assert f.avg_measured_value is None and f.min_measured_value is None  # no measured value
    z = rows["right_elbow_rom"]          # configured but never evaluated
    assert (z.evaluations, z.passed, z.failed) == (0, 0, 0)
    assert z.success_rate is None and z.avg_measured_value is None
    # ordering: failure volume desc, then name (top-mistakes widgets read top-N)
    ordering = [(row.rule, row.failed) for row in report.stats.rules]
    assert ordering == [
        ("left_elbow_rom", 1), ("left_shoulder_too_fast", 1),
        ("left_shoulder_wrist_distance", 1),
        ("left_shoulder_rom", 0), ("right_elbow_rom", 0), ("right_shoulder_rom", 0),
    ]

    # --- stats.scores -------------------------------------------------------
    assert report.stats.scores.best == 100.0 and report.stats.scores.worst == 0.0
    assert abs(report.stats.scores.std_dev - _pstdev([100.0, 0.0])) < 1e-9

    # --- reconciliation: stats can never disagree with summary/history -----
    assert sum(row.failed for row in report.stats.rules) == sum(
        report.summary.common_errors.values()
    )
    assert {
        row.rule: row.failed for row in report.stats.rules if row.failed
    } == report.summary.common_errors

    # --- serialized form ----------------------------------------------------
    s_ses = data["session"]
    assert set(s_ses) == {"id", "recorded_at", "fps", "scoring"}
    assert s_ses["fps"] == 25.0
    assert s_ses["scoring"]["base_score"] == 100.0
    assert s_ses["scoring"]["severity_weights"] == {
        "error": 50.0, "warning": 20.0, "info": 10.0,
    }
    s_rows = {row["rule"]: row for row in data["stats"]["rules"]}
    assert s_rows["left_shoulder_wrist_distance"]["success_rate"] == 50.0
    assert s_rows["left_shoulder_wrist_distance"]["avg_measured_value"] == 1.56
    assert s_rows["right_elbow_rom"]["success_rate"] is None    # honest null, not fake 0/100
    assert data["stats"]["scores"] == {"best": 100.0, "worst": 0.0, "std_dev": 50.0}

    # --- audit scenario (squat): stats reconcile with history --------------
    sq_rows = {row.rule: row for row in sq_report.stats.rules}
    assert sq_rows["back_straight"].failed == 2                    # == common_errors
    assert sq_report.stats.rules[0].rule == "back_straight"        # top mistake first
    assert abs(sq_report.stats.scores.std_dev - _pstdev([50.0, 50.0, 100.0])) < 1e-9
    for r_name, row in sq_rows.items():
        agg = [ev for rep in sq_report.history for ev in rep.evaluations if ev.rule == r_name]
        assert row.evaluations == len(agg)
        assert row.passed == sum(1 for ev in agg if ev.passed)

    # ── 8. Consistency invariants: judged_by + summary↔history reconciliation ─
    from collections import Counter as _Counter
    from src.analytics.session_report import (
        JUDGED_BY_COMPLETION as _C, JUDGED_BY_COUNTER as _Q, JUDGED_BY_RULES as _R,
    )

    # FIX 4: the runtime semantics are explicit per rep, for each counter path
    assert report.history[0].judged_by == _C          # simple counter, GOOD by completion
    assert report.history[1].judged_by == _R          # distance violation forced BAD on the simple path
    hack = SessionAnalyzer().build_report(
        reps, exercise=registry.get("hack_squat"), fps=25.0,
    )
    assert {r.judged_by for r in hack.history} == {_Q}  # managed counter judges quality itself
    assert all(r.judged_by == _C for r in sq_report.history)   # squat = simple path by design

    # no rep may ever look contradictory: the only (good, evaluations) combos
    # that raw data couldn't explain are now labelled with their mechanism
    for rep_ in (*report.history, *sq_report.history, *live.history, *hack.history):
        assert rep_.judged_by in (_C, _R, _Q)
        if rep_.good and rep_.failed_rules:
            # GOOD with evidence of failure: only meaningful if the counter
            # never claimed to judge quality...
            assert rep_.judged_by in (_C, _Q)
            # ...and the failures are always priced into the score
            assert rep_.score < 100.0
        if not rep_.good:
            assert rep_.judged_by in (_R, _Q)         # never "completion"
        if rep_.score < 100.0:
            assert rep_.failed_rules                  # score always has evidence

    # FIX 5 + 6: exported summary is ALWAYS re-derivable from exported history
    def reconcile(d):
        hist = d["history"]
        ok = [r for r in hist if r["good"]]
        summ = d["summary"]
        assert summ["total_reps"] == len(hist)
        assert summ["good_reps"] == len(ok) and summ["bad_reps"] == len(hist) - len(ok)
        assert summ["accuracy"] == round(len(ok) / len(hist) * 100, 1) if hist else True
        scores = [r["score"] for r in hist]
        assert summ["score"] == round(sum(scores) / len(scores), 1)
        errs = _Counter(e["rule"] for r in hist for e in r["evaluations"] if not e["passed"])
        assert summ["common_errors"] == dict(
            sorted(errs.items(), key=lambda kv: (-kv[1], kv[0]))
        )
        assert summ["most_common_error"] == (errs.most_common(1)[0][0] if errs else None)
        durations = [
            round((r["end_frame"] - r["start_frame"] + 1) / d["session"]["fps"], 2)
            for r in hist
        ]
        assert summ["average_rep_duration"] == round(sum(durations) / len(durations), 2)
        assert [round(r["duration_seconds"], 2) for r in hist] == durations
        # rep keys complete and no impossible nulls
        for r in hist:
            assert set(r) == {
                "number", "good", "judged_by", "score",
                "start_frame", "end_frame", "duration_seconds", "evaluations",
            }
            assert r["start_frame"] is not None and r["end_frame"] is not None

    reconcile(data)

    print("ALL SESSION-REPORT ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
