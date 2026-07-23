"""Persist a :class:`SessionReport` as a single JSON document.

JSON is the only export format, by design: the report's nested structure
(exercise info → summary → per-rep → per-rule evaluations) cannot be
flattened into rows without losing information, so the previous CSV export
was removed rather than degraded.

The exporter depends only on the report model — it never touches
``GymEngine``, ``RepJudge``, or any pose/counting logic. ``export(report,
path)`` normalizes the file extension, serializes the report, writes it, and
returns the final path.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict

from .session_report import SessionReport


class JsonSessionExporter:
    """Human-readable, indented JSON export of a complete session report.

    The serialized layout (root keys) is a durable, normalized session record
    suitable for dashboards, progress tracking, and replay tooling. It is
    deliberately unversioned (the format is still evolving) and carries each
    fact exactly once — identity and timestamp live in ``session``/``exercise``
    only, rule definitions live in ``rules`` only::

        {
            "session":  { ... },       # identity: id, recorded_at (the only
                                       #   timestamp), fps, scoring policy
            "exercise": { ... },       # what was trained + counter setup
            "summary":  { ... },       # aggregated stats (derived from history)
            "rules":    [ ... ],       # each rule's static definition, once
            "history":  [ ... ],       # one entry per completed rep (good +
                                       #   judged_by + score + evaluations)
            "stats":    { ... },       # dashboard aggregates (see below)
        }

    Dashboard cheat-sheet::

        session list / timeline    → session.id, session.recorded_at, exercise.name
        session score card         → summary.score, stats.scores (best/worst/std_dev)
        score-trend chart          → history[].number vs history[].score
        rep outcome table          → history[] joined on rules[] by name
        "why is this rep good/bad" → history[].judged_by + evaluations
        rule success-rate bars     → stats.rules (success_rate / failed)
        most common mistakes       → summary.common_errors or top-N of stats.rules
        "how is score computed?"   → session.scoring.severity_weights
    """

    extension = "json"

    def export(self, report: SessionReport, path) -> Path:
        """Write ``report`` to ``path`` (extension corrected) and return it."""
        path = Path(path)
        if path.suffix.lower() != f".{self.extension}":
            path = path.with_suffix(f".{self.extension}")
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write(path, self._serialize(report))
        return path

    # ------------------------------------------------------------------
    # Serialization (report model -> plain JSON-ready dicts)
    # ------------------------------------------------------------------
    def _serialize(self, report: SessionReport) -> Dict[str, Any]:
        data = {
            # Optional by model contract (tests/tools may build reports
            # without it); SessionAnalyzer-built reports always carry one.
            **({"session": self._session_dict(report.session)} if report.session else {}),
            "exercise": self._exercise_dict(report.exercise),
            "summary": self._summary_dict(report.summary),
            "rules": [self._rule_dict(rule) for rule in report.rules],
            "history": [self._rep_dict(rep) for rep in report.history],
            "stats": self._stats_dict(report.stats),
        }
        return data

    @staticmethod
    def _session_dict(session) -> Dict[str, Any]:
        """Export identity/provenance block (v4)."""
        return {
            "id": session.id,
            "recorded_at": session.recorded_at,
            "fps": session.fps,
            "scoring": {
                "base_score": session.base_score,
                "severity_weights": {
                    _value(sev): weight for sev, weight in session.severity_weights
                },
            },
        }

    @staticmethod
    def _stats_dict(stats) -> Dict[str, Any]:
        """Dashboard aggregates block (v4) — per-rule rows + score extremes."""
        return {
            "rules": [
                {
                    "rule": row.rule,
                    "evaluations": row.evaluations,
                    "passed": row.passed,
                    "failed": row.failed,
                    "success_rate": (
                        round(row.success_rate, 1)
                        if row.success_rate is not None else None
                    ),
                    "avg_measured_value": (
                        round(row.avg_measured_value, 2)
                        if row.avg_measured_value is not None else None
                    ),
                    "min_measured_value": (
                        round(row.min_measured_value, 2)
                        if row.min_measured_value is not None else None
                    ),
                    "max_measured_value": (
                        round(row.max_measured_value, 2)
                        if row.max_measured_value is not None else None
                    ),
                }
                for row in stats.rules
            ],
            "scores": {
                "best": (
                    round(stats.scores.best, 1)
                    if stats.scores.best is not None else None
                ),
                "worst": (
                    round(stats.scores.worst, 1)
                    if stats.scores.worst is not None else None
                ),
                "std_dev": (
                    round(stats.scores.std_dev, 2)
                    if stats.scores.std_dev is not None else None
                ),
            },
        }

    @staticmethod
    def _exercise_dict(info) -> Dict[str, Any]:
        return {
            "name": info.name,
            "description": info.description,
            "muscle_groups": list(info.muscle_groups),
            "camera": _value(info.camera),
            "counter_rules": [
                {
                    "name": c.name,
                    "joints": list(c.joints),
                    "up_angle": c.up_angle,
                    "down_angle": c.down_angle,
                    "up_stage": _value(c.up_stage),
                    "down_stage": _value(c.down_stage),
                    "min_rom_angle": c.min_rom_angle,
                    "max_rom_angle": c.max_rom_angle,
                    "min_rep_frames": c.min_rep_frames,
                    "sync_group": c.sync_group,
                }
                for c in info.counter_rules
            ],
        }

    @staticmethod
    def _summary_dict(summary) -> Dict[str, Any]:
        """The aggregated statistics — pure aggregates, every one of them
        derivable from ``history`` (identity and timestamp are NOT echoed
        here: they live once in ``exercise`` / ``session``)."""
        return {
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

    @staticmethod
    def _rule_dict(rule) -> Dict[str, Any]:
        data = {
            "name": rule.name,
            "type": rule.type,
            "severity": _value(rule.severity),
            "message": rule.message,
            "expected_min": rule.expected_min,
            "expected_max": rule.expected_max,
            "value_unit": rule.value_unit,
        }
        # Geometry is shape-specific: each rule kind carries only its own.
        for key in ("joints", "measurement", "reference"):
            if getattr(rule, key) is not None:
                data[key] = list(getattr(rule, key))
        return data

    @staticmethod
    def _rep_dict(rep) -> Dict[str, Any]:
        return {
            "number": rep.number,
            "good": rep.good,
            # The explicit runtime semantics: which mechanism decided "good"
            # ("completion" | "rules" | "counter") — so good=True alongside a
            # failed evaluation (or good=False with none) is self-explanatory.
            "judged_by": rep.judged_by,
            "score": round(rep.score, 1),
            "start_frame": rep.start_frame,
            "end_frame": rep.end_frame,
            "start_time": round(rep.start_time, 2) if getattr(rep, 'start_time', None) is not None else None,
            "end_time": round(rep.end_time, 2) if getattr(rep, 'end_time', None) is not None else None,
            "duration_seconds": (
                round(rep.duration_seconds, 2)
                if rep.duration_seconds is not None else None
            ),
            # Only the dynamic part — static metadata lives in the "rules"
            # section; "message" appears only when the runtime cue differs
            # from the rule's static message (live ROM hints), i.e. it is
            # never duplicated static configuration.
            "evaluations": [
                {
                    "rule": e.rule,
                    "passed": e.passed,
                    "measured_value": e.measured_value,
                    **({"message": e.message} if e.message is not None else {}),
                }
                for e in rep.evaluations
            ],
        }

    @staticmethod
    def _write(path: Path, data: Dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _value(field):
    """Plain value for a field that may be an Enum member (Severity/Stage/Camera)."""
    return field.value if isinstance(field, Enum) else field
