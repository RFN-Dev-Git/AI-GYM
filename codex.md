# CODEBASE SNAPSHOT

## PROJECT STRUCTURE

```text
AI-GYM/
├── assets
│   ├── models
│   │   ├── pose_landmarker_full.task
│   │   └── pose_landmarker_lite.task
│   └── videos
│       ├── Chest.mp4
│       ├── Deadlift .png
│       ├── Deadlift.mp4
│       ├── Deadlift2.mp4
│       ├── Deadlift3.mp4
│       ├── hackw.mp4
│       ├── leg.mp4
│       └── leg2.mp4
├── backend
│   ├── src
│   │   ├── analytics
│   │   │   ├── __init__.py
│   │   │   ├── analyzer.py
│   │   │   ├── exporters.py
│   │   │   ├── session_report.py
│   │   │   └── session_summary.py
│   │   ├── config
│   │   │   ├── __init__.py
│   │   │   └── app_settings.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   │   ├── colors.py
│   │   │   └── pose_segments.py
│   │   ├── exercises
│   │   │   ├── leg
│   │   │   │   ├── __init__.py
│   │   │   │   ├── hack_squat.py
│   │   │   │   └── leg_press.py
│   │   │   ├── __init__.py
│   │   │   ├── biceps_curl.py
│   │   │   ├── cable_chest_fly.py
│   │   │   ├── deadlift.py
│   │   │   ├── exercise.py
│   │   │   ├── latpulldown.py
│   │   │   ├── pushup.py
│   │   │   ├── registry.py
│   │   │   ├── rules.py
│   │   │   ├── shoulder_press.py
│   │   │   ├── squat.py
│   │   │   └── validation.py
│   │   ├── server
│   │   │   ├── routes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── downloads.py
│   │   │   │   ├── exercises.py
│   │   │   │   ├── live.py
│   │   │   │   ├── sessions.py
│   │   │   │   ├── settings.py
│   │   │   │   └── uploads.py
│   │   │   ├── __init__.py
│   │   │   ├── app.py
│   │   │   ├── live_runner.py
│   │   │   └── store.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   ├── additional_casses.py
│   │   │   ├── gym_engine.py
│   │   │   ├── pose_service.py
│   │   │   ├── rep_counter.py
│   │   │   ├── rep_judge.py
│   │   │   └── video_source.py
│   │   ├── utils
│   │   │   ├── __init__.py
│   │   │   ├── camera_side.py
│   │   │   ├── geometry.py
│   │   │   └── render.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── tests
│   │   ├── test_architecture.py
│   │   ├── test_distance_handling.py
│   │   ├── test_hack_squat.py
│   │   ├── test_session_report.py
│   │   └── test_video_source.py
│   ├── .env
│   ├── .env.example
│   ├── ADDING_AN_EXERCISE.md
│   ├── ARCHITECTURE.md
│   └── requirements.txt
├── frontend
│   ├── src
│   │   ├── components
│   │   │   ├── layout
│   │   │   │   └── app-shell.tsx
│   │   │   ├── ui
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── progress.tsx
│   │   │   │   ├── skeleton.tsx
│   │   │   │   └── tooltip.tsx
│   │   │   └── shared.tsx
│   │   ├── features
│   │   │   ├── dashboard
│   │   │   │   └── page.tsx
│   │   │   ├── exercises
│   │   │   │   ├── exercise-card.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── history
│   │   │   │   └── page.tsx
│   │   │   ├── live
│   │   │   │   ├── page.tsx
│   │   │   │   └── use-live-session.ts
│   │   │   ├── report
│   │   │   │   └── page.tsx
│   │   │   ├── settings
│   │   │   │   └── page.tsx
│   │   │   └── not-found.tsx
│   │   ├── lib
│   │   │   ├── api
│   │   │   │   ├── client.ts
│   │   │   │   ├── exercises.ts
│   │   │   │   ├── live.ts
│   │   │   │   ├── sessions.ts
│   │   │   │   ├── settings.ts
│   │   │   │   ├── types.ts
│   │   │   │   └── uploads.ts
│   │   │   ├── format.ts
│   │   │   └── utils.ts
│   │   ├── providers
│   │   │   ├── theme.tsx
│   │   │   └── toast.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── .gitignore
│   ├── FRONTEND_ARCHITECTURE.md
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── output
│   ├── sessions
│   └── videos
│       └── Hack_Squat_20260722_010752.mp4
├── .gitignore
├── codex
├── Makefile
├── README.md
└── term
```

## SOURCE FILES

---

### FILE: [backend/src/analytics/__init__.py](backend/src/analytics/__init__.py)

```py
"""Session analytics: turn a finished workout into a complete JSON report.

Independent of ``GymEngine`` and of any pose/counting logic — everything here
only consumes the already-completed session data (``RepJudge.history``).

Responsibilities and data flow
------------------------------
::

    RepResult (RepJudge.history)
        │   one completed rep: classification + violations + complete
        │   per-rule evaluation record (pass and fail)
        ▼
    SessionAnalyzer
        │   aggregates the unchanged SessionSummary, resolves rule
        │   expectations against the exercise config, assembles per-rep
        │   records plus dashboard-facing aggregates (per-rule success
        │   rates, score extremes) — invents nothing
        ▼
    SessionReport
        │   one immutable value object: export identity (session) +
        │   exercise info + summary + rule definitions (stored once) +
        │   full repetition history (evaluations reference rules by name) +
        │   pre-aggregated stats
        ▼
    JsonSessionExporter
        └─► the single output artifact: a complete JSON session record

``SessionSummary`` remains available on its own via
:meth:`SessionAnalyzer.analyze` for callers that only need the aggregates.
"""

from .analyzer import SessionAnalyzer
from .exporters import JsonSessionExporter
from .session_report import (
    ExerciseInfo,
    RepetitionRecord,
    RuleDefinitionRecord,
    RuleEvaluationRecord,
    RuleStatsRecord,
    ScoreStatsRecord,
    SessionInfo,
    SessionReport,
    SessionStats,
)
from .session_summary import SessionSummary

__all__ = [
    "SessionAnalyzer",
    "SessionSummary",
    "SessionReport",
    "SessionInfo",
    "SessionStats",
    "ScoreStatsRecord",
    "ExerciseInfo",
    "RepetitionRecord",
    "RuleDefinitionRecord",
    "RuleEvaluationRecord",
    "RuleStatsRecord",
    "JsonSessionExporter",
]
```

---

### FILE: [backend/src/analytics/analyzer.py](backend/src/analytics/analyzer.py)

```py
"""Turn a completed session (``list[RepResult]``) into analytics.

``SessionAnalyzer`` is deliberately decoupled from ``GymEngine`` and performs
NO pose detection or repetition counting — it only reads the finished session
data and derives metrics. It has exactly two jobs, both implemented by small
private helpers so the public entry points stay thin:

* :meth:`SessionAnalyzer.analyze` — the aggregated :class:`SessionSummary`
  (unchanged legacy behaviour);
* :meth:`SessionAnalyzer.build_report` — the complete :class:`SessionReport`:
  the same summary plus static exercise info and the full per-rep,
  per-rule decision history.
"""

import uuid
from collections import Counter
from datetime import datetime, timezone
from statistics import pstdev
from typing import Dict, Mapping, Optional, Sequence, Tuple

from ..exercises.exercise import Exercise
from ..exercises.rules import (
    AngleROMValidationRule, AngleValidationRule, DistanceValidationRule,
    Severity, ValidationRule,
)
from ..exercises.validation import ValidationResult
from ..services.rep_judge import RepResult
from .session_report import (
    JUDGED_BY_COMPLETION, JUDGED_BY_COUNTER, JUDGED_BY_RULES,
    CounterRuleRecord, ExerciseInfo, RepetitionRecord, RuleDefinitionRecord,
    RuleEvaluationRecord, RuleStatsRecord, ScoreStatsRecord, SessionInfo,
    SessionReport, SessionStats,
)
from .session_summary import SessionSummary

# Heuristic weights used to derive a per-rep "validation score" when the
# underlying data does not carry an explicit score. Higher severity -> larger
# penalty. Override via the constructor for different scoring policies.
DEFAULT_SEVERITY_WEIGHTS: Dict[str, float] = {
    Severity.ERROR: 50.0, Severity.WARNING: 20.0, Severity.INFO: 10.0,
}

# Rule-kind labels used in RuleEvaluationRecord.type.
_KIND_ANGLE = "angle"
_KIND_ROM = "range_of_motion"
_KIND_DISTANCE = "distance"
_KIND_COUNTER = "counter"

# Value-unit labels used in RuleEvaluationRecord.value_unit.
_UNIT_DEGREES = "degrees"
_UNIT_RATIO = "ratio"


class SessionAnalyzer:
    """Derives session analytics from completed repetitions.

    Stateless apart from the scoring policy (``severity_weights``): every
    method takes the session data it needs and returns new objects — nothing
    is stored on the instance between calls.
    """

    def __init__(self, severity_weights: Optional[Mapping[str, float]] = None) -> None:
        # Copied to a plain dict: caller mappings are never aliased or mutated.
        self.severity_weights: Dict[str, float] = dict(
            severity_weights or DEFAULT_SEVERITY_WEIGHTS
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def analyze(
        self,
        results: Sequence[RepResult],
        *,
        exercise_name: Optional[str] = None,
        fps: float = 25.0,
        total_duration: Optional[float] = None,
        date: Optional[str] = None,
    ) -> SessionSummary:
        """Analyze ``results`` (a finished session) and return its summary.

        Args:
            results:        Completed repetitions (typically ``RepJudge.history``).
            exercise_name:  Label stored on the summary (defaults to ``""``).
            fps:            Frame rate used to convert frame spans into seconds.
            total_duration: Explicit total session duration (seconds). When given
                            it is used as-is; otherwise it is derived from the
                            first/last repetition frame span.
            date:           ISO-8601 session timestamp. Defaults to *now*.

        Returns:
            A populated :class:`SessionSummary`.
        """
        return self._summarize(
            results,
            exercise_name=exercise_name or "",
            fps=fps,
            total_duration=total_duration,
            date=date or datetime.now().isoformat(),
        )

    def build_report(
        self,
        results: Sequence[RepResult],
        *,
        exercise: Exercise,
        fps: float = 25.0,
        total_duration: Optional[float] = None,
        date: Optional[str] = None,
    ) -> SessionReport:
        """Build the complete :class:`SessionReport` for a finished session.

        The report embeds the same aggregated statistics :meth:`analyze`
        produces (derived by the same private helpers, so numbers can never
        drift apart), static exercise information, the session-level rule
        definitions (stored exactly once), and the complete per-rep /
        per-rule decision history referencing those definitions.

        Args:
            results:        Completed repetitions (typically ``RepJudge.history``).
            exercise:       The exercise configuration the session ran. Used for
                            the static info section and to enrich each rule
                            outcome with its expected range and rule kind.
            fps:            Frame rate used to convert frame spans into seconds.
            total_duration: Explicit total session duration (seconds).
            date:           ISO-8601 session timestamp. Defaults to *now*.
        """
        summary = self._summarize(
            results,
            exercise_name=exercise.name,
            fps=fps,
            total_duration=total_duration,
            date=date or datetime.now().isoformat(),
        )
        rules = self._rules_section(exercise, results)
        static_messages = {r.name: r.message for r in rules}
        # Same managed-path predicate RepCounter itself uses to engage its
        # quality-judging helper — kept in one expression so the report's
        # judged_by labels can never drift from real counting behaviour.
        managed = any(
            r.max_rom_angle is not None or r.min_rep_frames > 0
            for r in exercise.counter_rules
        )
        history = tuple(
            self._rep_record(rep, fps, static_messages, managed) for rep in results
        )
        return SessionReport(
            exercise=self._exercise_info(exercise),
            summary=summary,
            rules=rules,
            history=history,
            session=self._session_info(fps),
            stats=self._session_stats(rules, history),
        )

    # ------------------------------------------------------------------
    # Aggregation (the summary — numbers identical to the legacy behaviour)
    # ------------------------------------------------------------------
    def _summarize(
        self,
        results: Sequence[RepResult],
        *,
        exercise_name: str,
        fps: float,
        total_duration: Optional[float],
        date: str,
    ) -> SessionSummary:
        """Aggregate ``results`` into a :class:`SessionSummary` (unchanged math)."""
        total = len(results)
        good = sum(1 for r in results if r.good)

        return SessionSummary(
            exercise=exercise_name,
            date=date,
            total_reps=total,
            good_reps=good,
            bad_reps=total - good,
            accuracy=(good / total * 100.0) if total else 0.0,
            average_rep_time=self._mean_duration(results, fps),
            fastest_rep=self._extreme_duration(results, fps, min),
            slowest_rep=self._extreme_duration(results, fps, max),
            total_workout_duration=self._total_duration(results, fps, total_duration),
            common_errors=self._error_counts(results),
            most_common_error=self._most_common_error(results),
            score=(sum(self._rep_score(r) for r in results) / total) if total else None,
        )

    @staticmethod
    def _durations(results: Sequence[RepResult], fps: float) -> list[float]:
        """Per-repetition durations (seconds) from their frame spans."""
        return [
            (r.end_frame - r.start_frame + 1) / float(fps)
            for r in results
            if r.start_frame is not None and r.end_frame is not None
        ]

    def _mean_duration(self, results: Sequence[RepResult], fps: float) -> float:
        durations = self._durations(results, fps)
        return (sum(durations) / len(durations)) if durations else 0.0

    def _extreme_duration(self, results: Sequence[RepResult], fps: float, pick) -> float:
        durations = self._durations(results, fps)
        return pick(durations) if durations else 0.0

    @staticmethod
    def _total_duration(
        results: Sequence[RepResult], fps: float, explicit: Optional[float]
    ) -> float:
        """Total active workout duration: explicit value, else first->last span."""
        if explicit is not None:
            return float(explicit)
        if results and results[0].start_frame is not None and results[-1].end_frame is not None:
            return (results[-1].end_frame - results[0].start_frame + 1) / float(fps)
        return 0.0

    @staticmethod
    def _error_counts(results: Sequence[RepResult]) -> Dict[str, int]:
        """Frequency of each failed rule, sorted by occurrence (desc) then name.

        Derived from the complete evaluation record (``rep.evaluations``), so
        the statistics always agree with the exported repetition history —
        never from the sparse violation subset alone.
        """
        counts = Counter(
            e.rule_name for r in results for e in r.evaluations if not e.passed
        )
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

    @staticmethod
    def _most_common_error(results: Sequence[RepResult]) -> Optional[str]:
        counts = Counter(
            e.rule_name for r in results for e in r.evaluations if not e.passed
        )
        return counts.most_common(1)[0][0] if counts else None

    def _rep_score(self, rep: RepResult) -> float:
        """Per-repetition validation score in [0, 100].

        Uses an explicit ``score`` attribute if the rep carries one (so a future
        real score wins), otherwise falls back to a severity-weighted penalty
        over the rep's COMPLETE evaluation record. Deductions therefore mirror
        exactly the failures visible in the exported history — a rep with a
        failed ``error`` rule can no longer report a perfect 100, even when
        the counter classified the rep GOOD by design.
        """
        explicit = getattr(rep, "score", None)
        if explicit is not None:
            return float(explicit)
        penalty = sum(
            self.severity_weights.get(e.severity, 0.0)
            for e in rep.evaluations
            if not e.passed
        )
        return max(0.0, 100.0 - penalty)

    # ------------------------------------------------------------------
    # Report assembly (exercise info + rule definitions + decision history)
    # ------------------------------------------------------------------
    @staticmethod
    def _rules_section(
        exercise: Exercise, results: Sequence[RepResult]
    ) -> Tuple[RuleDefinitionRecord, ...]:
        """The session-level rule definitions, one entry per rule — stored once.

        Sources, in order:
          * every validation rule declared by the exercise (static:
            kind, severity, message, expected bounds, geometry);
          * counter-originated rules discovered in the produced results
            (e.g. tempo warnings) — entries whose name matches no validation
            rule; their severity/message are captured from the actual
            observed outcome, never invented.
        """
        definitions: Dict[str, RuleDefinitionRecord] = {}
        for rule in exercise.validation_rules:
            definitions[rule.name] = _rule_definition(rule)
        for rep in results:
            for outcome in rep.evaluations:
                if outcome.rule_name not in definitions:
                    definitions[outcome.rule_name] = RuleDefinitionRecord(
                        name=outcome.rule_name,
                        type=_KIND_COUNTER,
                        severity=outcome.severity,
                        message=outcome.message,
                    )
        return tuple(definitions.values())

    @staticmethod
    def _exercise_info(exercise: Exercise) -> ExerciseInfo:
        """Static exercise description section of the report."""
        counters = tuple(
            CounterRuleRecord(
                name=rule.name,
                joints=rule.joints,
                up_angle=rule.up_angle,
                down_angle=rule.down_angle,
                up_stage=rule.up_stage,
                down_stage=rule.down_stage,
                min_rom_angle=rule.min_rom_angle,
                max_rom_angle=rule.max_rom_angle,
                min_rep_frames=rule.min_rep_frames,
                sync_group=rule.sync_group,
            )
            for rule in exercise.counter_rules
        )
        return ExerciseInfo(
            name=exercise.name,
            description=exercise.metadata.description,
            muscle_groups=exercise.metadata.muscle_groups,
            camera=exercise.camera,
            counter_rules=counters,
        )

    def _session_info(self, fps: float) -> SessionInfo:
        """Export identity/provenance block: unique id + tz-aware timestamp.

        The scoring policy travels with the report so consumers can explain
        every exported score without hard-coding the analyzer's weights.
        """
        return SessionInfo(
            id=uuid.uuid4().hex,
            recorded_at=datetime.now(timezone.utc).isoformat(),
            fps=float(fps),
            severity_weights=tuple(self.severity_weights.items()),
        )

    @staticmethod
    def _session_stats(
        rules: Sequence[RuleDefinitionRecord],
        history: Sequence[RepetitionRecord],
    ) -> SessionStats:
        """Dashboard-facing aggregates, computed from the exported history.

        One row per *defined* rule — including rules that were never
        evaluated (kept with a ``None`` success rate rather than dropped, so
        a dashboard can see "configured but never triggered"). Aggregate
        counts therefore always reconcile with ``summary.common_errors`` and
        with the per-rep evaluation records by construction.
        """
        rows = []
        for rule in rules:
            evals = [e for rep in history for e in rep.evaluations if e.rule == rule.name]
            passed = sum(1 for e in evals if e.passed)
            values = [e.measured_value for e in evals if e.measured_value is not None]
            rows.append(
                RuleStatsRecord(
                    rule=rule.name,
                    evaluations=len(evals),
                    passed=passed,
                    failed=len(evals) - passed,
                    success_rate=(passed / len(evals) * 100.0) if evals else None,
                    avg_measured_value=(sum(values) / len(values)) if values else None,
                    min_measured_value=min(values) if values else None,
                    max_measured_value=max(values) if values else None,
                )
            )
        # Failure volume first, then name — the same ordering common_errors
        # uses, so "top mistakes" widgets read the first N rows directly.
        rows.sort(key=lambda row: (-row.failed, row.rule))
        scores = [rep.score for rep in history]
        return SessionStats(
            rules=tuple(rows),
            scores=ScoreStatsRecord(
                best=max(scores) if scores else None,
                worst=min(scores) if scores else None,
                std_dev=pstdev(scores) if scores else None,
            ),
        )

    def _rep_record(
        self,
        rep: RepResult,
        fps: float,
        static_messages: Mapping[str, str],
        managed: bool,
    ) -> RepetitionRecord:
        """One completed rep -> its full report record."""
        return RepetitionRecord(
            number=rep.number,
            good=rep.good,
            judged_by=self._judged_by(rep, managed),
            score=self._rep_score(rep),
            start_frame=rep.start_frame,
            end_frame=rep.end_frame,
            duration_seconds=self._rep_duration(rep, fps),
            evaluations=tuple(
                self._evaluation_record(outcome, static_messages)
                for outcome in rep.evaluations
            ),
        )

    @staticmethod
    def _judged_by(rep: RepResult, managed: bool) -> str:
        """Name the mechanism that decided ``rep.good`` (see JUDGED_BY_*).

        Explicit per-rep semantics so the exported data can never look
        contradictory: a GOOD rep with failed ERROR evaluations is explained
        by "completion" (a counter that does not judge quality), a BAD rep
        with no failed evaluation by "counter" (the ROM/tempo gate failed),
        anything else by "rules" (violations forced the verdict on a
        completion-only counter).
        """
        if managed:
            # Managed counters judge quality themselves (ROM/tempo/violations).
            return JUDGED_BY_COUNTER
        if not rep.good:
            # A completion-only counter only ever says GOOD; a BAD verdict can
            # therefore only originate from failing validation rules (e.g. a
            # distance rule poisoning the rep).
            return JUDGED_BY_RULES
        return JUDGED_BY_COMPLETION

    @staticmethod
    def _rep_duration(rep: RepResult, fps: float) -> Optional[float]:
        """Rep duration in seconds, or ``None`` when frame bounds are missing."""
        if rep.start_frame is None or rep.end_frame is None:
            return None
        return (rep.end_frame - rep.start_frame + 1) / float(fps)

    @staticmethod
    def _evaluation_record(
        outcome: ValidationResult, static_messages: Mapping[str, str]
    ) -> RuleEvaluationRecord:
        """One stored rule outcome -> its slim, reference-only report record.

        Keeps only the dynamic part (pass/fail + measured value). Static
        metadata lives in the session-level rule definition; the runtime
        message is kept ONLY when it differs from that static message
        (stage-dependent ROM cues), otherwise it is omitted to avoid
        repeating configuration data per rep.
        """
        override = outcome.message
        if override == static_messages.get(outcome.rule_name, ""):
            override = None
        return RuleEvaluationRecord(
            rule=outcome.rule_name,
            passed=outcome.passed,
            measured_value=outcome.angle,
            message=override,
        )


def _rule_definition(rule: ValidationRule) -> RuleDefinitionRecord:
    """Static definition of one validation rule for the report's rules section."""
    kind, min_expected, max_expected, unit = _rule_expectations(rule)
    geometry: Dict[str, Optional[tuple]] = {}
    if isinstance(rule, DistanceValidationRule):
        geometry = {"measurement": rule.measurement, "reference": rule.reference}
    elif isinstance(rule, (AngleValidationRule, AngleROMValidationRule)):
        geometry = {"joints": rule.joints}
    return RuleDefinitionRecord(
        name=rule.name,
        type=kind,
        severity=rule.severity,
        message=rule.message,
        expected_min=min_expected,
        expected_max=max_expected,
        value_unit=unit,
        **geometry,
    )


def _rule_expectations(
    rule: Optional[ValidationRule],
) -> tuple[str, Optional[float], Optional[float], Optional[str]]:
    """(kind, expected_min, expected_max, unit) for a rule, or counter defaults.

    Single place that knows how each rule kind's acceptable range is spelled
    on its configuration object.
    """
    if isinstance(rule, AngleROMValidationRule):
        return _KIND_ROM, rule.min_rom_angle, rule.max_rom_angle, _UNIT_DEGREES
    if isinstance(rule, DistanceValidationRule):
        return _KIND_DISTANCE, rule.min_ratio, rule.max_ratio, _UNIT_RATIO
    if isinstance(rule, AngleValidationRule):
        return _KIND_ANGLE, rule.min_angle, rule.max_angle, _UNIT_DEGREES
    return _KIND_COUNTER, None, None, None
```

---

### FILE: [backend/src/analytics/exporters.py](backend/src/analytics/exporters.py)

```py
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
```

---

### FILE: [backend/src/analytics/session_report.py](backend/src/analytics/session_report.py)

```py
"""The Session Report model — the complete, self-contained record of a workout.

A :class:`SessionReport` answers six questions about a finished session:

* :class:`SessionInfo`         — *which export is this, and when?*
  (export identity: unique id, tz-aware timestamp, fps, scoring policy)
* :class:`ExerciseInfo`        — *what was the athlete asked to do?*
  (static exercise configuration: identity, metadata, counter rules)
* :class:`~.session_summary.SessionSummary` — *how did the session go overall?*
  (the unchanged aggregated statistics)
* :class:`RuleDefinitionRecord` — *what form checks were in effect?*
  (each rule's static definition, stored EXACTLY ONCE per session)
* :class:`RepetitionRecord`    — *what exactly happened, rep by rep?*
  (every rule outcome: pass/fail + measured value, referencing the rule
  definitions above by name — never repeating them)
* :class:`SessionStats`        — *what should a dashboard plot?*
  (pre-aggregated per-rule success rates and score extremes, computed
  from the same history the report exports — so widgets render without
  re-walking every rep, and can never disagree with the history)

Why rules are stored once, at session level
--------------------------------------------
A rule's type, severity, message, and expected range never change during a
session, while its outcomes repeat for every rep. Embedding that static
metadata in every evaluation would duplicate it hundreds of times, making
reports bulky and comparisons noisy. So the report keeps a ``rules`` section
(the dictionary) and repetition history holds only the dynamic part (the
outcome), keyed by rule name (the reference). The report stays compact yet
fully self-describing: join ``history[].evaluations[].rule`` against
``rules[].name`` and everything about every evaluation is known.

Every record is a frozen dataclass holding plain, JSON-serializable data: a
report is assembled once by ``SessionAnalyzer`` and then read — by exporters,
tests, dashboards, or replay tools — never mutated. Only information the
system already produces is stored; nothing is invented at report time.
Summary statistics, per-rep scores, and error counts are all derived from
the same complete evaluation record that ``history`` exports, so the summary
can never contradict the history it describes.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple

from ..exercises.rules import Severity
from .session_summary import SessionSummary

# Runtime-semantics vocabulary for RepetitionRecord.judged_by. It answers the
# one question raw data cannot: "which mechanism decided good?" — so a rep is
# never ambiguous when ``good`` and the evaluations appear to disagree.
#
#   "completion":  the counter does NOT judge quality (simple counting path);
#                  ``good=True`` certifies only that a complete repetition was
#                  counted. Quality is expressed solely by ``score``, so a
#                  failed evaluation alongside good=True is expected here —
#                  the ERROR/WARNING rule coached but did not invalidate.
#   "rules":       good/bad was forced by failing validation rules (simple
#                  path + violations, e.g. a distance rule poisoning the rep).
#   "counter":     the counter itself judged quality (managed path: ROM
#                  extremes / tempo / accumulated violations). A good=False
#                  rep may legitimately carry NO failed evaluation here — the
#                  ROM target itself was missed (bounds live in
#                  exercise.counter_rules, so the reason stays self-contained).
JUDGED_BY_COMPLETION = "completion"
JUDGED_BY_RULES = "rules"
JUDGED_BY_COUNTER = "counter"


@dataclass(frozen=True)
class CounterRuleRecord:
    """Static description of one repetition counter used in the session.

    Captures the counting configuration a rep was judged against — the joint,
    the stage thresholds, and (where configured) the ROM and tempo limits.

    Attributes:
        name:           Counter rule id (e.g. "knee", "left_shoulder").
        joints:         Measured angle triplet (landmark indices).
        up_angle:       "Up"-end angle threshold (deg).
        down_angle:     "Down"-end angle threshold (deg).
        up_stage:       Display label for the up end.
        down_stage:     Display label for the down end.
        min_rom_angle:  Bottom extreme (deg) a GOOD rep must reach, if set.
        max_rom_angle:  Top extreme (deg) a GOOD rep must reach, if set.
        min_rep_frames: Minimum frames a rep may span (0 = no tempo limit).
        sync_group:     Synchronization group the counter belongs to, if any.
    """

    name: str
    joints: Tuple[int, int, int]
    up_angle: float
    down_angle: float
    up_stage: str
    down_stage: str
    min_rom_angle: Optional[float] = None
    max_rom_angle: Optional[float] = None
    min_rep_frames: int = 0
    sync_group: Optional[str] = None


@dataclass(frozen=True)
class ExerciseInfo:
    """Static exercise information: what the session was supposed to train.

    Attributes:
        name:          Exercise display name.
        description:   One-line description (from exercise metadata).
        muscle_groups: Primary muscle groups worked.
        camera:        Camera viewpoint the session was tracked from.
        counter_rules: The repetition counters that defined a rep.
    """

    name: str
    description: str
    muscle_groups: Tuple[str, ...]
    camera: str
    counter_rules: Tuple[CounterRuleRecord, ...] = ()


@dataclass(frozen=True)
class SessionInfo:
    """Export identity and provenance — the envelope a dashboard indexes by.

    When many exported files are merged into a dashboard's data store, each
    record must be uniquely identifiable and sortable in time; that is all
    this record is for. Everything here is generation-time metadata, not
    workout data.

    Attributes:
        id:               Unique export id (uuid4 hex). Lets a dashboard
                          deduplicate or upsert when the same file is
                          ingested twice.
        recorded_at:      The session's single canonical timestamp, ISO-8601
                          with UTC offset (e.g. ``2026-07-21T15:17:12+00:00``) —
                          when the session was recorded/reported. (This is the
                          ONLY timestamp in the report.)
        fps:              Frame rate the session was analyzed at. Needed to
                          re-time frame-indexed history (``start_frame`` /
                          ``end_frame``) into seconds outside this report.
        severity_weights: The scoring policy used to derive every ``score``
                          in the report — (severity, penalty) pairs. Exported
                          so consumers can explain a score ("failed error →
                          −50") without hard-coding the analyzer's weights.
        base_score:       The scale anchor scores start from (100).
    """

    id: str
    recorded_at: str
    fps: float
    severity_weights: Tuple[Tuple[str, float], ...] = ()
    base_score: float = 100.0


@dataclass(frozen=True)
class RuleDefinitionRecord:
    """A rule's static definition — everything about it that never changes.

    Stored once in the report's ``rules`` section and referenced by name from
    every evaluation in the repetition history.

    Attributes:
        name:         Rule id (the key evaluations reference).
        type:         Rule kind: "angle" | "range_of_motion" | "distance" |
                      "counter" (counter-originated entries, e.g. tempo).
        severity:     Severity assigned to failures of this rule.
        message:      The rule's static coaching cue. (Runtime overrides —
                      e.g. stage-dependent ROM cues — live on the evaluation.)
        expected_min: Lower bound of the expected range/ratio, if applicable.
        expected_max: Upper bound of the expected range/ratio, if applicable.
        value_unit:   What measured values/bounds express: "degrees" |
                      "ratio" | ``None``.
        joints:       Measured angle triplet (angle/ROM rules only).
        measurement:  Distance pair being checked (distance rules only).
        reference:    Normalizing distance pair (distance rules only).
    """

    name: str
    type: str
    severity: str = Severity.ERROR
    message: str = ""
    expected_min: Optional[float] = None
    expected_max: Optional[float] = None
    value_unit: Optional[str] = None
    joints: Optional[Tuple[int, ...]] = None
    measurement: Optional[Tuple[int, ...]] = None
    reference: Optional[Tuple[int, ...]] = None


@dataclass(frozen=True)
class RuleEvaluationRecord:
    """One rule's dynamic outcome during one repetition.

    Deliberately slim: static rule metadata (type, severity, expected range,
    static message) lives in the session-level rule definition — this record
    keeps only what happened at runtime.

    Attributes:
        rule:           Name of the rule evaluated (references
                        ``rules[].name`` in the report).
        passed:         Whether the rule was satisfied.
        measured_value: The measured angle (deg) or ratio, or ``None`` when
                        the value could not be determined.
        message:        Runtime message override — present ONLY when the
                        message produced at runtime differs from the rule's
                        static message (e.g. stage-dependent ROM cues).
                        ``None`` means "use the rule definition's message".
    """

    rule: str
    passed: bool
    measured_value: Optional[float] = None
    message: Optional[str] = None


@dataclass(frozen=True)
class RepetitionRecord:
    """Everything known about one completed repetition.

    Reading ``good`` together with ``evaluations`` — the semantics are
    explicit, not implied: ``judged_by`` names the mechanism that produced
    ``good`` (see the JUDGED_BY_* constants for the full vocabulary), so a
    rep NEVER looks contradictory on its own:

    * ``good=True`` with failed evaluations is valid exactly when
      ``judged_by="completion"`` (the counter only certifies the rep was
      completed; the failing ERROR/WARNING rule coached but did not
      invalidate, and its cost lives in the reduced ``score``).
    * ``good=False`` with NO failed evaluation is valid exactly when
      ``judged_by="counter"`` (the counter's own ROM/tempo gate failed the
      rep; the targets live in ``exercise.counter_rules``).
    * ``good=False`` with failed evaluations under ``judged_by="rules"`` or
      ``"counter"`` reads naturally (the failures explain the verdict).

    Attributes:
        number:           1-based rep index (matches the on-screen counter).
        good:             GOOD/BAD classification as decided at runtime.
        judged_by:        Which mechanism decided ``good`` — one of
                          "completion" | "rules" | "counter" (see module
                          constants for exact semantics).
        score:            Per-rep form-quality score in [0, 100], derived
                          from the complete evaluation record (severity-
                          weighted; 100 only when nothing failed).
        start_frame:      First frame of the rep window (the frame after the
                          previous rep completed), or ``None`` when no frame
                          was recorded for the rep.
        end_frame:        Frame the rep completed on, or ``None``.
        duration_seconds: ``(end_frame - start_frame + 1) / fps``, or
                          ``None`` when frame bounds are unavailable.
        evaluations:      Complete per-rule decision record (pass and fail),
                          referencing session-level rule definitions by name.
    """

    number: int
    good: bool
    judged_by: str
    score: float
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
    duration_seconds: Optional[float] = None
    evaluations: Tuple[RuleEvaluationRecord, ...] = ()

    @property
    def failed_rules(self) -> Tuple[str, ...]:
        """Names of the rules that failed during this rep (convenience)."""
        return tuple(e.rule for e in self.evaluations if not e.passed)


@dataclass(frozen=True)
class RuleStatsRecord:
    """Per-rule aggregate over the whole session — one dashboard widget row.

    Aggregated from the same evaluations ``history`` exports, so it can never
    contradict the repetition record; it exists so success-rate bars and
    "most common mistakes" widgets render without re-walking every rep.
    Rows are ordered by failure volume (descending), then rule name — the
    same ordering ``summary.common_errors`` uses — so a "top mistakes"
    widget reads the first N rows directly.

    Attributes:
        rule:               Rule name (references ``rules[].name``).
        evaluations:        How many times the rule was evaluated all session.
        passed:             Evaluations that passed.
        failed:             Evaluations that failed.
        success_rate:       ``passed / evaluations * 100`` (0-100), or
                            ``None`` when the rule was in the configuration
                            but never evaluated during the session.
        avg_measured_value: Mean of the measured values (deg or ratio),
                            or ``None`` when nothing was measurable.
        min_measured_value: Worst-case low of the measured values, or ``None``.
        max_measured_value: Worst-case high of the measured values, or ``None``.
    """

    rule: str
    evaluations: int = 0
    passed: int = 0
    failed: int = 0
    success_rate: Optional[float] = None
    avg_measured_value: Optional[float] = None
    min_measured_value: Optional[float] = None
    max_measured_value: Optional[float] = None


@dataclass(frozen=True)
class ScoreStatsRecord:
    """Distribution summary of the per-rep scores in ``history``.

    Attributes:
        best:    Highest per-rep score of the session, or ``None`` when no
                 rep was completed.
        worst:   Lowest per-rep score of the session, or ``None``.
        std_dev: Population standard deviation of the per-rep scores (0.0 for
                 a single rep) — the session's form-consistency measure.
                 ``None`` when no rep was completed.
    """

    best: Optional[float] = None
    worst: Optional[float] = None
    std_dev: Optional[float] = None


@dataclass(frozen=True)
class SessionStats:
    """Dashboard-facing aggregates over the full session.

    Everything here is *derived* — computed from ``history`` at report time
    and stored so widgets need no aggregation pass. Rep-level aggregates
    (good/bad counts, accuracy, durations) deliberately live ONLY in
    ``summary``; this block carries what the summary does not: per-rule
    success rates and the score distribution.

    Attributes:
        rules:  One :class:`RuleStatsRecord` per rule in the report's
                ``rules`` section, ordered by failure volume, then name.
        scores: Distribution summary of the per-rep scores.
    """

    rules: Tuple[RuleStatsRecord, ...] = ()
    scores: ScoreStatsRecord = field(default_factory=ScoreStatsRecord)


@dataclass(frozen=True)
class SessionReport:
    """The complete record of one workout session.

    Attributes:
        exercise:  Static exercise information (what was trained).
        summary:   Aggregated session statistics (exactly as produced today).
        rules:     Static rule definitions, stored once — referenced by name
                   from every evaluation in ``history``.
        history:   One :class:`RepetitionRecord` per completed rep, in order.
        session:   Export identity/provenance (id, timestamp, fps, scoring
                   policy). Optional only so hand-built reports in tests and
                   tooling can omit it; ``SessionAnalyzer`` always sets it.
        stats:     Dashboard-facing aggregates (per-rule success rates, score
                   distribution) derived from ``history`` at build time.
    """

    exercise: ExerciseInfo
    summary: SessionSummary
    rules: Tuple[RuleDefinitionRecord, ...] = ()
    history: Tuple[RepetitionRecord, ...] = field(default_factory=tuple)
    session: Optional[SessionInfo] = None
    stats: SessionStats = field(default_factory=SessionStats)
```

---

### FILE: [backend/src/analytics/session_summary.py](backend/src/analytics/session_summary.py)

```py
"""Dataclass holding the computed statistics of one workout session.

Produced by :class:`~src.analytics.analyzer.SessionAnalyzer`, either returned
on its own (:meth:`SessionAnalyzer.analyze`) or embedded as the ``summary``
section of a :class:`~src.analytics.session_report.SessionReport`. All fields
are plain, serializable data so a summary can be trivially written to JSON or
stored for later analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class SessionSummary:
    """Aggregated statistics for a single, completed workout session.

    Attributes:
        exercise:            Name of the exercise performed. Internal label
                             only — NOT exported in the session report (the
                             report's ``exercise`` section is the single home
                             of exercise identity).
        date:                ISO-8601 timestamp of the session (or ``None``).
                             Internal/legacy only — NOT exported in the
                             session report (``session.recorded_at`` is the
                             report's single canonical timestamp).
        total_reps:          Number of completed repetitions.
        good_reps:           Repetitions classified GOOD (no error violation).
        bad_reps:            Repetitions classified BAD.
        accuracy:            Percentage of GOOD repetitions (0-100).
        average_rep_time:    Mean duration of a repetition, in seconds.
        fastest_rep:         Shortest repetition duration, in seconds.
        slowest_rep:         Longest repetition duration, in seconds.
        total_workout_duration: Total active session time, in seconds.
        common_errors:       Rule name -> number of occurrences, descending.
        most_common_error:   Most frequent failed rule name (or ``None``).
        score:               Average validation score (0-100), or ``None`` when
                             not available.
    """

    exercise: str
    date: Optional[str] = None
    total_reps: int = 0
    good_reps: int = 0
    bad_reps: int = 0
    accuracy: float = 0.0
    average_rep_time: float = 0.0
    fastest_rep: float = 0.0
    slowest_rep: float = 0.0
    total_workout_duration: float = 0.0
    common_errors: Dict[str, int] = field(default_factory=dict)
    most_common_error: Optional[str] = None
    score: Optional[float] = None
```

---

### FILE: [backend/src/config/__init__.py](backend/src/config/__init__.py)

```py
from .app_settings import (
    settings,
    PROJECT_ROOT,
    REPO_ROOT,
    ASSETS_DIR,
    MODELS_DIR,
    VIDEOS_DIR,
    OUTPUT_DIR,
    SESSIONS_DIR,
    RENDERED_DIR,
    UPLOADS_DIR,
    resolve_path,
)

__all__ = [
    "settings",
    "PROJECT_ROOT",
    "REPO_ROOT",
    "ASSETS_DIR",
    "MODELS_DIR",
    "VIDEOS_DIR",
    "OUTPUT_DIR",
    "SESSIONS_DIR",
    "RENDERED_DIR",
    "UPLOADS_DIR",
    "resolve_path",
]
```

---

### FILE: [backend/src/config/app_settings.py](backend/src/config/app_settings.py)

```py
"""Application settings (pydantic-settings) with project-relative paths.

All filesystem paths are exposed as :class:`pathlib.Path` objects and resolved
against a fixed base, so the application behaves identically no matter which
directory it is launched from. The shared root/path constants live here so
paths are never scattered as ad-hoc strings across the codebase.

Path bases
----------
``PROJECT_ROOT`` (the ``backend/`` package root)
    code + configuration (``.env``) only.
``REPO_ROOT`` (the repository root, ``PROJECT_ROOT``'s parent)
    every *data* path. Inputs live in ``assets/`` (pose model, dev videos),
    generated artifacts in ``output/`` (``sessions/`` = exported reports,
    ``videos/`` = rendered sessions, ``uploads/`` = web-app uploads).

**Rule:** every relative path in ``.env`` resolves against ``REPO_ROOT``;
absolute paths pass through untouched.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Root path constants ────────────────────────────────────────────────────
# Derived from this file's location, so they are independent of the CWD.
#   src/config/app_settings.py -> parents[2] == backend package root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PROJECT_ROOT.parent

# Inputs (repo root): pose model + developer sample videos.
ASSETS_DIR = REPO_ROOT / "assets"
MODELS_DIR = ASSETS_DIR / "models"
VIDEOS_DIR = ASSETS_DIR / "videos"

# Generated artifacts (repo root): reports, rendered videos, web uploads.
OUTPUT_DIR = REPO_ROOT / "output"
SESSIONS_DIR = OUTPUT_DIR / "sessions"
RENDERED_DIR = OUTPUT_DIR / "videos"
UPLOADS_DIR = OUTPUT_DIR / "uploads"


def resolve_path(path, base: Path = REPO_ROOT) -> Path:
    """Resolve a (possibly relative) path against ``base`` (repo root)."""
    path = Path(path)
    return path if path.is_absolute() else base / path


class AppSettings(BaseSettings):
    # Paths are Path objects; relative strings are resolved against PROJECT_ROOT.
    MODEL_PATH: Path
    VIDEO_PATH: Optional[Path] = None

    DISPLAY_MAX_WIDTH: int = 1280

    USE_WEBCAM: bool = False
    WEBCAM_INDEX: int = 0

    SAVE_OUTPUT: bool = False
    OUTPUT_PATH: Path = RENDERED_DIR / "result.mp4"

    # Session analytics: frame rate used to turn per-repetition frame spans
    # into durations (seconds) in the generated SessionReport.
    ANALYTICS_FPS: float = 25.0

    # Session analytics export (opt-in). When EXPORT_SESSION is true the engine
    # persists a complete SessionReport (produced by the analytics module) as a
    # single JSON document after a run. EXPORT_FORMAT is kept only for .env
    # backward compatibility: JSON is now the sole export format (a complete
    # session history cannot be flattened to CSV without losing information),
    # and any other value is ignored with a console note.
    EXPORT_SESSION: bool = False
    EXPORT_FORMAT: str = "json"   # legacy; JSON is always used
    EXPORT_DIR: Path = SESSIONS_DIR

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _resolve_relative_paths(self) -> "AppSettings":
        """Resolve any relative .env path against ``REPO_ROOT``.

        An empty VIDEO_PATH (e.g. an empty env var) is normalised to ``None``.
        """
        self.MODEL_PATH = resolve_path(self.MODEL_PATH)
        if self.VIDEO_PATH is not None:
            # An empty env value coerces to Path(".") -> treat as unset.
            if str(self.VIDEO_PATH).strip() in ("", "."):
                self.VIDEO_PATH = None
            else:
                self.VIDEO_PATH = resolve_path(self.VIDEO_PATH)
        self.OUTPUT_PATH = resolve_path(self.OUTPUT_PATH)
        self.EXPORT_DIR = resolve_path(self.EXPORT_DIR)
        return self


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


settings = get_settings()
```

---

### FILE: [backend/src/core/__init__.py](backend/src/core/__init__.py)

```py
from .colors import Colors
from .pose_segments import PoseSegments

__all__ = ["Colors", "PoseSegments"]
```

---

### FILE: [backend/src/core/colors.py](backend/src/core/colors.py)

```py
from dataclasses import dataclass


@dataclass
class Colors:
    TEXT: tuple = (255, 255, 255)
    HIGHLIGHT: tuple = (0, 255, 0)
    LINE: tuple = (0, 255, 255)
    ERROR: tuple = (0, 0, 255)
```

---

### FILE: [backend/src/core/pose_segments.py](backend/src/core/pose_segments.py)

```py
"""MediaPipe BlazePose landmark indices and common joint segments.

These are *anatomical* constants, not exercise logic. Exercises reference them
when building their AngleCounterRule / AngleValidationRule configurations, which keeps the
raw landmark numbers out of the exercise definitions and out of GymEngine.
"""

# --- Individual BlazePose landmarks (33-point model) ---
NOSE = 0
L_EYE_INNER = 1
L_EYE = 2
L_EYE_OUTER = 3
R_EYE_INNER = 4
R_EYE = 5
R_EYE_OUTER = 6
L_EAR = 7
R_EAR = 8
L_MOUTH = 9
R_MOUTH = 10
L_SHOULDER = 11
R_SHOULDER = 12
L_ELBOW = 13
R_ELBOW = 14
L_WRIST = 15
R_WRIST = 16
L_PINKY = 17
R_PINKY = 18
L_INDEX = 19
R_INDEX = 20
L_THUMB = 21
R_THUMB = 22
L_HIP = 23
R_HIP = 24
L_KNEE = 25
R_KNEE = 26
L_ANKLE = 27
R_ANKLE = 28
L_HEEL = 29
R_HEEL = 30
L_FOOT = 31
R_FOOT = 32


class PoseSegments:
    """Tuples of landmark indices describing a kinematic chain / angle."""

    LEFT_ARM = (L_SHOULDER, L_ELBOW, L_WRIST)
    RIGHT_ARM = (R_SHOULDER, R_ELBOW, R_WRIST)

    LEFT_LEG = (L_HIP, L_KNEE, L_ANKLE)
    RIGHT_LEG = (R_HIP, R_KNEE, R_ANKLE)

    # 4-point chains kept for convenience / future multi-angle features.
    LEFT_CHAIN = (L_SHOULDER, L_ELBOW, L_WRIST, L_HIP)
    RIGHT_CHAIN = (R_SHOULDER, R_ELBOW, R_WRIST, R_HIP)

    # Torso proxies: shoulder-hip-knee angle is a simple "is the back/trunk
    # reasonably straight?" check for many exercises.
    LEFT_TORSO = (L_SHOULDER, L_HIP, L_KNEE)
    RIGHT_TORSO = (R_SHOULDER, R_HIP, R_KNEE)

    # Hip / knee alignment proxies (placeholders for true symmetry checks).
    LEFT_HIP_ALIGN = (L_HIP, R_HIP, R_KNEE)
    RIGHT_HIP_ALIGN = (R_HIP, L_HIP, L_KNEE)

    # ----- Deadlift-specific segments -----
    # Neck / cervical-spine neutrality: Ear → Shoulder → Hip.
    # A neutral neck sits at ~160-180°; values below that flag forward-head.
    LEFT_NECK_ALIGN  = (L_EAR, L_SHOULDER, L_HIP)
    RIGHT_NECK_ALIGN = (R_EAR, R_SHOULDER, R_HIP)

    # Hip-hinge (abdomen / anterior-thigh angle): Shoulder → Hip → Knee.
    # Reuses LEFT_TORSO / RIGHT_TORSO; explicit aliases for readability.
    LEFT_HIP_HINGE  = (L_SHOULDER, L_HIP, L_KNEE)   # same as LEFT_TORSO
    RIGHT_HIP_HINGE = (R_SHOULDER, R_HIP, R_KNEE)   # same as RIGHT_TORSO

    # Elbow elevation: Hip -> Shoulder -> Elbow (Cable Chest Fly)
    # Flags when the elbow drops below the shoulder line.
    LEFT_ELBOW_ELEVATION  = (L_HIP, L_SHOULDER, L_ELBOW)
    RIGHT_ELBOW_ELEVATION = (R_HIP, R_SHOULDER, R_ELBOW)

    # Arm direction: Hip -> Shoulder -> Elbow (Shoulder Press)
    # Checks if arm is extended upward (pressing) vs downward (resting).
    LEFT_ARM_DIRECTION  = (L_HIP, L_SHOULDER, L_ELBOW)
    RIGHT_ARM_DIRECTION = (R_HIP, R_SHOULDER, R_ELBOW)
```

---

### FILE: [backend/src/exercises/leg/__init__.py](backend/src/exercises/leg/__init__.py)

```py
"""Leg exercises package configuration."""

from .hack_squat import HackSquatExercise
from .leg_press import LegPressExercise

__all__ = [
    "HackSquatExercise",
    "LegPressExercise",
]
```

---

### FILE: [backend/src/exercises/leg/hack_squat.py](backend/src/exercises/leg/hack_squat.py)

```py
"""Hack Squat exercise configuration (self-contained).

Counting logic (LEFT_LEG — Hip → Knee → Ankle angle, MANAGED ROM path):
  - DOWN phase begins when the angle drops to <= 90° (rep window starts).
  - RETURNING begins when the angle crosses back above 130°.
  - The rep COMPLETES when the angle reaches >= 150° and starts decreasing
    again (direction reversal at the top — the next descent has begun).
  - Bailing out early (angle falls back to <= 90° before reaching 150°)
    counts the rep BAD.

Rep quality:
  - GOOD rep: reached <= 85° at the bottom AND >= 150° at the top, with no
    validation violation during the rep window.
  - BAD rep: too shallow (never <= 85°), incomplete lockout (bailed before
    150°), or ``knee_unlocked`` failed anywhere inside the window.
  - ``min_rep_frames`` stays 0 — no tempo gate for now (set > 0 to judge
    speed as well).

Design notes
------------
* SINGLE LEFT-side rule set, by project convention: the exercise is filmed in
  profile (Camera.SIDE), so CameraSideDetector picks the visible side within
  the first ~30 frames and adapt_rules mirrors these LEFT rules onto the
  right automatically. Twin ``knee_left``/``knee_right`` rules would be
  redundant — adaptation keeps exactly one effective rule either way — and,
  worse, would make the exported rule names swap with the detected side.
  One LEFT rule keeps report names stable ("knee", "knee_unlocked") no matter
  which side is filmed, while the post-adaptation landmarks (and therefore
  every counted/measured angle) are identical to the old twin setup.
* Stage triggers (90/130) are the author's calibration for the machine's
  travel and did not change with the ROM upgrade. The ROM extremes are the
  judgment band around them: 85° demands going a little deeper than the
  DOWN trigger, 150° demands more extension than the 130° RETURNING trigger
  (lockout beyond 170° is separately flagged by ``knee_unlocked``). Tune the
  85/150 band against real footage if it proves too strict or too lenient.
* There is deliberately NO paired ``AngleROMValidationRule``: leg_press
  pairs one with its counter and, because RepJudge's record keeps a failed
  outcome sticky for the whole rep, its transient "go deeper" live cues end
  up exported as failed evaluations on *perfect* reps (score 80, and
  "most common error" on every rep). Here the counter's own ROM gate is the
  sole ROM judge — the same pattern biceps_curl uses. Consequence, mirrored
  by design: a rep judged BAD purely on ROM (e.g. only reached 88°) carries
  no failed validation evaluation, so its exported score stays 100 — rep
  classification comes from the counter, scores from validation rules.
* ``knee_unlocked`` spans 60°–170°: above 170° the knee is locked/
  hyperextended at the top; below 60° is beyond safe machine depth. The
  message is deliberately side-neutral — after mirroring it coaches whichever
  leg is visible.

Only the counter (knee) skeleton is drawn — the validation rule measures the
same joints, so drawing both would be visual noise
(``show_validation_skeleton=False``).
"""

from dataclasses import dataclass, field

from ...core.pose_segments import PoseSegments
from ..exercise import Camera, DisplaySettings, Exercise, ExerciseMetadata
from ..rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class HackSquatExercise(Exercise):
    name: str = "Hack Squat"
    camera: Camera = Camera.SIDE
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee",
                joints=PoseSegments.LEFT_LEG,   # Hip → Knee → Ankle
                up_angle=130,                   # crossing back above -> RETURNING phase
                down_angle=90,                  # <= 90° -> DOWN phase begins (rep window starts)
                min_rom_angle=85,               # GOOD rep must reach <= 85° at the bottom
                max_rom_angle=150,              # ... and >= 150° at full extension before reversing
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            # Lockout / over-depth guard on the same measured angle. On this
            # managed counter a failure inside the rep window also poisons
            # the rep (marks it BAD), not just the exported score.
            AngleValidationRule(
                name="knee_unlocked",
                joints=PoseSegments.LEFT_LEG,
                min_angle=60,
                max_angle=170,
                message="Don't lock your knee — stay between 60° and 170°",
                severity=Severity.WARNING,
            ),
        ]
    )
    display: DisplaySettings = field(
        # Validation joints == counter joints: one skeleton, not two.
        default_factory=lambda: DisplaySettings(show_validation_skeleton=False)
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Machine-guided squat emphasizing the quadriceps through the sled's fixed path.",
            muscle_groups=("quadriceps", "glutes", "hamstrings"),
        )
    )
```

---

### FILE: [backend/src/exercises/leg/leg_press.py](backend/src/exercises/leg/leg_press.py)

```py
"""Leg Press exercise configuration (self-contained).

Counting logic:
  - DOWN phase: knee angle <= 110° (user is bending)
  - RETURNING: angle crosses back above 120°
  - Rep completes when angle >= 160° (fully extended)

ROM quality:
  - GOOD rep: must reach <= 80° at the bottom AND >= 160° at the top
  - BAD rep:  counted if the user reverses before reaching either extreme

Skeleton color:
  - Default (white) while at rest (UP stage, before rep starts)
  - RED while descending/returning but bottom not yet reached
  - GREEN once the bottom extreme (<= 80°) has been reached this rep
"""

from dataclasses import dataclass, field

from ...core.pose_segments import PoseSegments
from ..exercise import Camera, Exercise, DisplaySettings, ExerciseMetadata
from ..rules import AngleCounterRule, AngleROMValidationRule, Severity


@dataclass
class LegPressExercise(Exercise):
    name: str = "Leg Press"
    camera: Camera = Camera.SIDE

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                up_angle=120,       # crosses this going back up → RETURNING phase
                down_angle=110,     # <= 110° = DOWN phase begins
                min_rom_angle=80,   # must reach <= 80° for a GOOD rep (deep enough)
                max_rom_angle=160,  # must reach >= 160° for a GOOD rep (full extension)
            ),
            AngleCounterRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                up_angle=120,
                down_angle=110,
                min_rom_angle=80,
                max_rom_angle=160,
            ),
        ]
    )

    validation_rules: list[AngleROMValidationRule] = field(
        default_factory=lambda: [
            AngleROMValidationRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                min_rom_angle=80,
                max_rom_angle=160,
                message="Full range: bend to 80° and extend to 160°",
                severity=Severity.WARNING,
            ),
            AngleROMValidationRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                min_rom_angle=80,
                max_rom_angle=160,
                message="Full range: bend to 80° and extend to 160°",
                severity=Severity.WARNING,
            ),
        ]
    )

    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Machine-based lower-body pushing exercise.",
            muscle_groups=("quadriceps", "glutes", "hamstrings"),
        )
    )
```

---

### FILE: [backend/src/exercises/__init__.py](backend/src/exercises/__init__.py)

```py

```

---

### FILE: [backend/src/exercises/biceps_curl.py](backend/src/exercises/biceps_curl.py)

```py
"""Biceps Curl exercise configuration (self-contained).

Counting logic (LEFT_ARM — Shoulder → Elbow → Wrist angle):
  - UP stage:   angle >= 150° (arm extended / hanging down)
  - DOWN stage: angle <= 90°  (arm curled up toward shoulder)
  - A rep counts when the user goes DOWN → UP (curled → extended)
  - GOOD rep: must reach <= 60° at the curl AND >= 150° at the extension

Validation rules:
  1. elbow_too_tight: angle must stay >= 30° — if lower than 30° the forearm
     is jammed too close, losing bicep tension (bad form).
  2. elbow_hyperextended: angle must stay <= 170° — if higher than 170° the
     elbow is hyperextended or locked out too straight (wrong position).
  3. elbow_drift: Hip → Shoulder → Elbow angle must stay <= 15°.
     If the elbow drifts forward, the front shoulder takes over and bicep tension drops.

Speed check:
  - min_rep_frames=18 (~0.7 s at 25 fps). Reps faster than this are marked BAD.

Only ARM joints are drawn on screen (show_validation_skeleton=False).
"""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments, L_HIP, L_SHOULDER, L_ELBOW
from .exercise import Camera, Exercise, DisplaySettings, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


# Hip → Shoulder → Elbow: detects elbow drift / forward swing
_LEFT_ELBOW_DRIFT = (L_HIP, L_SHOULDER, L_ELBOW)


@dataclass
class BicepsCurlExercise(Exercise):
    name: str = "Biceps Curl"
    camera: Camera = Camera.SIDE

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,   # Shoulder → Elbow → Wrist
                up_angle=139,                   # arm extended — UP stage (angle >= 150)
                down_angle=90,                  # arm curled — DOWN stage (angle <= 90)
                up_stage="down",                # map large angle (extension) to "down"
                down_stage="up",                # map small angle (curl peak) to "up"
                min_rom_angle=150,               # must reach <= 60° for a GOOD rep
                max_rom_angle=50,              # must reach >= 150° for a GOOD rep
                min_rep_frames=12,              # < 12 frames = too fast → BAD
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            # ── Form check 1: elbow angle must stay above 30° ──────────
            AngleValidationRule(
                name="elbow_too_tight",
                joints=PoseSegments.LEFT_ARM,
                min_angle=30,
                max_angle=180,
                message="Don't curl too tight — keep elbow above 30°",
                severity=Severity.WARNING,
            ),
            # ── Form check 2: elbow angle must stay below 170° ─────────
            AngleValidationRule(
                name="elbow_hyperextended",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=170,
                message="Don't lock or hyperextend your elbow (keep below 170°)",
                severity=Severity.WARNING,
            ),
            # ── Form check 3: elbow drift (Hip → Shoulder → Elbow) ─────
            # Upper arm stays vertical (parallel to torso) — angle <= 15°.
            AngleValidationRule(
                name="elbow_drift",
                joints=_LEFT_ELBOW_DRIFT,
                min_angle=0,
                max_angle=20,
                message="Keep elbow pinned to your side (drift < 20°)",
                severity=Severity.WARNING,
            ),
        ]
    )

    # Only draw the arm skeleton — the drift validation joints (Hip→Shoulder→Elbow)
    # would add a distracting second skeleton if allowed to render.
    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(show_validation_skeleton=False)
    )

    # Technique notes (kept as documentation — nothing consumes them at runtime):
    # keep the upper arm stationary and elbow pinned to your side (drift < 15°);
    # full extension at the bottom (~150°-170°) and full curl at the top (30°-60°);
    # controlled tempo — avoid ballistic / momentum-driven reps.
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Isolation dumbbell exercise for the biceps brachii.",
            muscle_groups=("biceps brachii", "brachialis", "brachioradialis"),
        )
    )
```

---

### FILE: [backend/src/exercises/cable_chest_fly.py](backend/src/exercises/cable_chest_fly.py)

```py
"""Cable Chest Fly exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class CableChestFlyExercise(Exercise):
    name: str = "Cable Chest Fly"

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="left",
                joints=PoseSegments.LEFT_ELBOW_ELEVATION,   # L_HIP -> L_SHOULDER -> L_ELBOW
                up_angle=110, down_angle=58,
                up_stage="open", down_stage="close",
            ),
            AngleCounterRule(
                name="right",
                joints=PoseSegments.RIGHT_ELBOW_ELEVATION,  # R_HIP -> R_SHOULDER -> R_ELBOW
                up_angle=110, down_angle=58,
                up_stage="open", down_stage="close",
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="chest_up",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=120, max_angle=180,
                message="Keep chest up — don't roll shoulders forward",
                severity=Severity.WARNING,
            ),
        ]
    )

    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Cable Chest Fly. Pectoral isolation via shoulder adduction.",
            muscle_groups=("pectorals", "anterior deltoid"),
        )
    )
```

---

### FILE: [backend/src/exercises/deadlift.py](backend/src/exercises/deadlift.py)

```py
"""Deadlift: Dissected — exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Camera, Exercise, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class DeadliftExercise(Exercise):
    name: str = "Deadlift: Dissected"
    camera: Camera = Camera.SIDE

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee",
                joints=PoseSegments.RIGHT_LEG,   # R_HIP -> R_KNEE -> R_ANKLE
                up_angle=165,
                down_angle=80,
                up_stage="lockout",
                down_stage="setup",
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            # Shoulder -> Hip -> Knee: detects back rounding under load
            AngleValidationRule(
                name="back_straight",
                joints=PoseSegments.RIGHT_HIP_HINGE,
                min_angle=40,
                max_angle=180,
                message="Keep your back straight — avoid rounding the lumbar spine",
                severity=Severity.ERROR,
            ),
            # Ear -> Shoulder -> Hip: detects forward head / neck drop
            AngleValidationRule(
                name="neck_neutral",
                joints=PoseSegments.RIGHT_NECK_ALIGN,
                min_angle=140,
                max_angle=180,
                message="Keep your neck neutral — chin should follow the spine",
                severity=Severity.ERROR,
            ),
        ]
    )

    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Deadlift: Dissected. Compound posterior-chain exercise.",
            muscle_groups=("hamstrings", "glutes", "erector spinae", "trapezius", "core"),
        )
    )
```

---

### FILE: [backend/src/exercises/exercise.py](backend/src/exercises/exercise.py)

```py
"""The Exercise configuration object — the single thing GymEngine needs."""

from dataclasses import dataclass, field
from enum import Enum

from .rules import AngleCounterRule, LandmarkPair


class Camera(str, Enum):
    """Camera viewpoint the exercise is filmed/tracked from.

    Finite, closed vocabulary (an exercise is either filmed from one fixed
    side or tracked from both/all sides), so it is an Enum rather than a
    free-form string. A ``str`` Enum, so ``Camera.SIDE == "side"`` is
    ``True`` and legacy comparisons keep working.

    SIDE selects the side-aware pipeline (``CameraSideDetector`` +
    ``adapt_rules`` mirror left/right rules onto the visible side); BOTH
    skips it.
    """

    BOTH = "both"
    SIDE = "side"


@dataclass(frozen=True)
class ExerciseMetadata:
    """Strongly typed, immutable exercise metadata.

    Replaces the previous free-form ``metadata: dict``. Only fields the
    project actually uses are modelled — keeping this small and explicit is
    intentional (structured data should not hide in generic dictionaries).
    Tuples (not lists) keep instances hashable as well as immutable.

    Attributes:
        description:    One-line human description of the exercise.
        muscle_groups:  Primary muscle groups worked, in rough priority order.
    """

    description: str = ""
    muscle_groups: tuple[str, ...] = ()


@dataclass(frozen=True)
class SegmentLine:
    """Declarative "draw a straight line between two landmarks" display rule.

    Pure presentation configuration: the engine renders every entry in
    ``DisplaySettings.segment_lines`` without knowing which exercise asked for
    it (today only Shoulder Press uses one — the wrist-to-wrist line at the
    top of the press).

    Attributes:
        endpoints:     The landmark pair to connect with a line.
        active_angles: Names of counter rules whose live angles must ALL be
                       >= ``min_angle`` for the line to appear (e.g. both arm
                       angles > 90 = "arms overhead"). Empty = always drawn.
        min_angle:     Angle threshold (deg) for ``active_angles``.
        error_rule:    Optional validation-rule name; while that rule is
                       failing the line is drawn in the ERROR colour instead
                       of HIGHLIGHT (e.g. the wrist-distance rule).
    """

    endpoints: LandmarkPair
    active_angles: tuple[str, ...] = ()
    min_angle: float = 90.0
    error_rule: str | None = None


@dataclass
class DisplaySettings:
    """Optional, per-exercise presentation knobs.

    Kept separate from counting/validation so visual tweaks never leak into
    exercise logic. All fields are optional with safe defaults.
    """

    show_angle_arc: bool = False
    show_skeleton: bool = True
    show_validation_skeleton: bool = True  # set False to hide validation-rule joints
    segment_lines: list[SegmentLine] = field(default_factory=list)  # landmark-to-landmark lines


@dataclass
class Exercise:
    """A fully self-contained description of one exercise.

    An Exercise is *pure configuration*: it carries the repetition-counting
    rules, the form-validation rules, optional display settings, and typed
    metadata. GymEngine consumes this object and never needs to know which
    exercise it is.

    Design notes
    -------------
    * Every field has a default so concrete exercises can be expressed either as
      dataclass subclasses that only override defaults (see ``pushup.py``,
      ``squat.py``, ...) or as plain ``Exercise(...)`` instances.
    * Lists (``counter_rules`` / ``validation_rules``) are the reason the design
      is open for extension: an exercise may use several angles / checks without
      any engine change.
    """

    name: str = ""
    counter_rules: list[AngleCounterRule] = field(default_factory=list)
    # Holds any ValidationRule subclass: AngleValidationRule,
    # AngleROMValidationRule, or DistanceValidationRule.
    validation_rules: list = field(default_factory=list)
    display: DisplaySettings = field(default_factory=DisplaySettings)
    metadata: ExerciseMetadata = field(default_factory=ExerciseMetadata)
    camera: str = Camera.BOTH
```

---

### FILE: [backend/src/exercises/latpulldown.py](backend/src/exercises/latpulldown.py)

```py
"""Lat Pulldown exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Camera, Exercise, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class LatPulldownExercise(Exercise):
    name: str = "Lat Pulldown"
    camera: Camera = Camera.SIDE

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=165,      # Arms almost fully extended
                down_angle=65,     # Bar pulled to upper chest
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=145,
                max_angle=180,
                message="Keep your back straight",
                severity=Severity.ERROR,
            ),
            AngleValidationRule(
                name="avoid_locking_elbows",
                joints=PoseSegments.LEFT_ARM,
                min_angle=15,
                max_angle=175,
                message="Don't lock your elbows",
                severity=Severity.WARNING,
            ),
            AngleValidationRule(
                name="full_pull",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=75,
                message="Pull the bar all the way down",
                severity=Severity.WARNING,
            ),
        ]
    )

    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Lat Pulldown machine exercise.",
            muscle_groups=(
                "latissimus dorsi",
                "teres major",
                "trapezius",
                "rhomboids",
                "biceps",
            ),
        )
    )
```

---

### FILE: [backend/src/exercises/pushup.py](backend/src/exercises/pushup.py)

```py
"""Push-Up exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Camera, Exercise, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class PushUpExercise(Exercise):
    name: str = "Push-Up"
    camera: Camera = Camera.SIDE
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=160,
                down_angle=90,
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=150,
                max_angle=180,
                message="Keep your back straight",
                severity=Severity.ERROR,
            ),
            AngleValidationRule(
                name="elbow_unlocked",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=170,
                message="Don't lock your elbows",
                severity=Severity.WARNING,
            ),
        ]
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Bodyweight chest, triceps and core exercise.",
            muscle_groups=("chest", "triceps", "shoulders", "core"),
        )
    )
```

---

### FILE: [backend/src/exercises/registry.py](backend/src/exercises/registry.py)

```py
"""Exercise registry — the single source of truth for available exercises.

The registry decouples *which* exercises exist from the code that uses them
(the CLI, :class:`GymEngine`). ``GymEngine`` only ever receives an already
constructed :class:`~src.exercises.exercise.Exercise` instance; it never asks
the registry for one. To add a new exercise you create the ``Exercise`` object
and call :meth:`ExerciseRegistry.register` — no engine or CLI changes needed.
"""

from typing import Dict, List

from .biceps_curl import BicepsCurlExercise
from .cable_chest_fly import CableChestFlyExercise
from .deadlift import DeadliftExercise
from .exercise import Exercise
from .latpulldown import LatPulldownExercise
from .leg import HackSquatExercise, LegPressExercise
from .pushup import PushUpExercise
from .shoulder_press import ShoulderPressExercise
from .squat import SquatExercise


class UnknownExerciseError(Exception):
    """Raised when an exercise name is not present in the registry."""


class ExerciseRegistry:
    """Maps normalized exercise names to :class:`Exercise` instances."""

    def __init__(self) -> None:
        self._exercises: Dict[str, Exercise] = {}

    @staticmethod
    def _normalize(name: str) -> str:
        """Case/space-insensitive key (e.g. ``"Push-Up"`` -> ``"push-up"``)."""
        return name.strip().lower()

    def register(self, name: str, exercise: Exercise) -> None:
        """Register ``exercise`` under ``name`` (lookup is case-insensitive).

        Raises:
            TypeError: if ``exercise`` is not an :class:`Exercise` instance.
            ValueError: if ``name`` is already registered.
        """
        if not isinstance(exercise, Exercise):
            raise TypeError(
                f"exercise must be an Exercise instance, got {type(exercise).__name__}"
            )
        key = self._normalize(name)
        if key in self._exercises:
            raise ValueError(f"Exercise '{key}' is already registered")
        self._exercises[key] = exercise

    def get(self, name: str) -> Exercise:
        """Return the registered :class:`Exercise` for ``name``.

        Raises:
            UnknownExerciseError: if ``name`` is not registered.
        """
        key = self._normalize(name)
        if key not in self._exercises:
            raise UnknownExerciseError(f"Unknown exercise '{name}'")
        return self._exercises[key]

    def exists(self, name: str) -> bool:
        """Return ``True`` if ``name`` is registered."""
        return self._normalize(name) in self._exercises

    def list(self) -> List[str]:
        """Return all registered exercise names, sorted for stable display."""
        return sorted(self._exercises)

    def clear(self) -> None:
        """Remove every registration (convenience for tests)."""
        self._exercises.clear()


# Module-level singleton pre-populated with the built-in exercises. Importing
# this module is enough to make every shipped exercise available; GymEngine and
# the CLI simply ask the registry for what they need.
registry = ExerciseRegistry()
registry.register("deadlift", DeadliftExercise())
registry.register("cable_chest_fly", CableChestFlyExercise())
registry.register("squat", SquatExercise())
registry.register("pushup", PushUpExercise())
registry.register("biceps_curl", BicepsCurlExercise())
registry.register("lat_pulldown", LatPulldownExercise())
registry.register("leg_press", LegPressExercise())
registry.register("hack_squat", HackSquatExercise())
registry.register("shoulder_press", ShoulderPressExercise())
```

---

### FILE: [backend/src/exercises/rules.py](backend/src/exercises/rules.py)

```py
"""Rule dataclasses: the atomic, exercise-agnostic building blocks.

===============================================================================
DESIGN NOTES (read this before adding or changing a rule)
===============================================================================

A Rule is *pure configuration*: it describes **WHAT** should be true
("elbow angle must stay between 30° and 170°"), never **HOW** that is
checked or acted upon. Two consequences matter to every contributor:

*   Rules are immutable (``frozen=True``). They are shared, long-lived
    configuration — created once per exercise, reused for the whole session,
    and adapted by copy (``dataclasses.replace``) when the camera side is
    detected. Freezing guarantees a rule means the same thing on frame 1
    and frame 10,000.

*   Rules contain no evaluation logic (no ``validate()`` / ``evaluate()`` /
    ``count()`` methods). Behaviour-free configuration stays trivially
    testable, engine-agnostic, and open for extension: a new rule kind is a
    new frozen dataclass in this file plus one evaluator where rule kinds
    are interpreted — the rule classes themselves never change shape.

On grouping and naming
----------------------
Fields that only make sense together are grouped into named pairs/triplets
(:data:`LandmarkPair`, :data:`LandmarkTriplet`) instead of numbered
primitives (``point1``/``point2``/``reference1``/``reference2``). Range
bounds stay as separate ``min_*`` / ``max_*`` fields — the prefix names the
role, so a two-tuple would hide information, not add it. The ``min_`` /
``max_`` + concept naming is uniform across all rules:

    min_angle / max_angle  ·  min_rom_angle / max_rom_angle  ·  min_ratio / max_ratio

On the hierarchy
----------------
``ValidationRule`` is the shared base of the three validation kinds; it
exists because name/message/severity would otherwise be duplicated verbatim
across all three. There is deliberately NO ``CounterRule`` base class:
``AngleCounterRule`` is the only counting rule kind, and a one-member
hierarchy would be inheritance for its own sake. If a second counting kind
is ever added (e.g. tempo-based), factor out the common fields then.
"""

from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------------------------------------
# Landmark group aliases
#
# Anatomy beat primitive obsession: two or three landmark indices that only
# make sense *together* are modelled as one named group rather than numbered
# loose fields. These are documentation-bearing aliases, not new types —
# plain tuples of BlazePose landmark indices (see core/pose_segments.py).
# ---------------------------------------------------------------------------

#: Two BlazePose landmark indices between which a distance is measured.
LandmarkPair = tuple[int, int]

#: Three BlazePose landmark indices forming an angle: (first, vertex, second).
#: The measured angle is always the one *at the middle (vertex) index*.
LandmarkTriplet = tuple[int, int, int]


class Severity(str, Enum):
    """How severe a failed validation is.

    Drives feedback emphasis. A ``str`` Enum so members compare equal to the
    plain literals they replace (``Severity.ERROR == "error"`` is ``True``);
    string comparisons, dict keys, and JSON/CSV exports are unaffected.
    Extend freely (e.g. a new level) without touching consumers.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Stage(str, Enum):
    """The rep-progress vocabulary: where a repetition currently is.

    UP ↔ DOWN are the rest/end positions of a repetition; RETURNING is the
    transit from DOWN back towards UP. Distinct from per-rule *display*
    labels (e.g. "open"/"close"), which are exercise presentation and live
    on the counter rule itself.

    A ``str`` Enum, so ``Stage.UP == "up"`` is ``True`` and string
    comparisons keep working.
    """

    UP = "up"
    DOWN = "down"
    RETURNING = "returning"


@dataclass(frozen=True)
class AngleCounterRule:
    """One repetition, counted from the angle of a single joint.

    *What it represents:* the complete definition of "one rep" for one joint
    movement — when the measured angle crosses ``down_angle`` after having
    been above ``up_angle``, one repetition has happened.

    *What it measures:* the angle (in degrees) at the vertex landmark of
    ``joints``.

    *Why it exists:* everything needed to count a rep is four numbers and
    two labels, so a plain frozen description is the simplest honest
    model — no behaviour, no state, nothing to test beyond construction.

    *When a rep counts:* the angle leaves the ``up`` half and enters the
    ``down`` half of the range. With ``min_rom_angle`` / ``max_rom_angle``
    set, a rep additionally only counts as GOOD when both extremes were
    actually reached, and with ``min_rep_frames`` set, when it spanned at
    least that many frames.

    Attributes:
        name:          Stable id of this counter (e.g. "knee", "elbow").
        joints:        The triplet forming the measured angle (angle is
                       taken at the middle landmark).
        up_angle:      Angle (deg) marking the "up" end of the movement.
        down_angle:    Angle (deg) marking the "down" end of the movement.
        up_stage:      Display label for the up end (default "up"; exercises
                       may rename it, e.g. "open", "lockout").
        down_stage:    Display label for the down end (default "down").
        min_rom_angle: Optional bottom extreme (deg) a GOOD rep must reach.
        max_rom_angle: Optional top extreme (deg) a GOOD rep must reach.
        min_rep_frames: Minimum frames a rep may span (0 = no speed limit).
        sync_group:    Optional group name; rules sharing a group count only
                       when all of them reach their thresholds together.
    """

    name: str
    joints: LandmarkTriplet
    up_angle: float
    down_angle: float
    up_stage: str = Stage.UP
    down_stage: str = Stage.DOWN
    min_rom_angle: float | None = None
    max_rom_angle: float | None = None
    min_rep_frames: int = 0   # minimum frames a rep must span (0 = no check)
    sync_group: str | None = None  # optional synchronization group


@dataclass(frozen=True, kw_only=True)
class ValidationRule:
    """Base contract of every form-check rule: identity, feedback, emphasis.

    Every validation rule — regardless of what it measures — needs the same
    three things: a *name* to identify it, a *message* to coach the user
    when it fails, and a *severity* to say how much a failure matters. This
    base holds exactly those shared fields and nothing else.

    Defined with ``kw_only=True`` so subclasses can add their own required
    measurement fields after the defaulted ``severity``.

    Attributes:
        name:       Stable id of the check (e.g. "back_straight").
        message:    Coaching cue shown to the user while the rule fails.
        severity:   How much a failure matters (default ``Severity.ERROR``).
    """

    name: str
    message: str
    severity: str = Severity.ERROR


@dataclass(frozen=True, kw_only=True)
class AngleValidationRule(ValidationRule):
    """A per-frame form check: one joint angle inside an acceptable range.

    *What it represents:* "this joint should stay between X° and Y° while
    exercising" — e.g. keep the back straight, don't lock the elbows.

    *What it measures:* the angle (in degrees) at the vertex landmark of
    ``joints``, evaluated independently on each observation — the rule has
    no memory.

    *Why it exists:* most form cues are simple acceptable ranges on one
    angle; such a cue is fully described by a triplet and two bounds.

    *When it is satisfied:* whenever the measured angle lies inside
    [``min_angle``, ``max_angle``] (inclusive).

    Attributes:
        joints:     The triplet forming the measured angle (angle is taken
                    at the middle landmark).
        min_angle:  Lower bound of the acceptable range (deg, inclusive).
        max_angle:  Upper bound of the acceptable range (deg, inclusive).
    """

    joints: LandmarkTriplet
    min_angle: float
    max_angle: float


@dataclass(frozen=True, kw_only=True)
class AngleROMValidationRule(ValidationRule):
    """A Range-Of-Motion check: a rep must actually reach both extremes.

    *What it represents:* "go all the way down AND all the way up" — the
    check is on the *achievement of a range across a whole repetition*, not
    on the angle of any single frame (that is :class:`AngleValidationRule`).

    *What it measures:* the angle progression at the vertex of ``joints``
    over the course of a rep, against the bottom and top extremes.

    *Why it exists:* partial reps are the most common form fault and cannot
    be detected by any single-frame range check — every frame of a half-rep
    can look "in range".

    *When it is satisfied:* a rep reaches at least ``min_rom_angle`` at its
    bottom (angle small enough) AND at least ``max_rom_angle`` at its top
    (angle large enough). While the rep is short of the bottom extreme the
    rule reports "go deeper"; short of the top it reports "extend fully".

    Attributes:
        name:          Stable id matching the corresponding counter rule.
        joints:        The triplet forming the measured angle (angle is
                       taken at the middle landmark).
        min_rom_angle: Bottom threshold (deg) the rep must reach.
        max_rom_angle: Top threshold (deg) the rep must reach.
    """

    joints: LandmarkTriplet
    min_rom_angle: float
    max_rom_angle: float


@dataclass(frozen=True, kw_only=True)
class DistanceValidationRule(ValidationRule):
    """A spatial form check: one body distance relative to another.

    *What it represents:* "these two landmarks should stay between X× and
    Y× as far apart as those two" — e.g. wrists at least 1.2× shoulder
    width apart during an overhead press.

    *What it measures:* the distance between the ``measurement`` landmarks,
    expressed as a RATIO to the distance between the ``reference``
    landmarks. Because only a ratio is checked, the rule is independent of
    camera distance and body size — 1.2× shoulder width is 1.2× whether the
    person stands near or far.

    *Why it exists:* some form faults are about relative position, not
    angles (grip too narrow, knees caving inwards); a reference-normalized
    distance expresses them in the body's own units.

    *When it is satisfied:* whenever
    ``min_ratio <= dist(measurement) / dist(reference) <= max_ratio``.

    Attributes:
        measurement: The landmark pair whose distance is being checked.
        reference:   The landmark pair providing the normalizing distance
                     (e.g. the shoulders — a stable body-proportional unit).
        min_ratio:   Minimum acceptable ratio (inclusive).
        max_ratio:   Maximum acceptable ratio (inclusive).
    """

    measurement: LandmarkPair
    reference: LandmarkPair
    min_ratio: float
    max_ratio: float
```

---

### FILE: [backend/src/exercises/shoulder_press.py](backend/src/exercises/shoulder_press.py)

```py
"""Shoulder Press exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import L_SHOULDER, R_SHOULDER, L_WRIST, R_WRIST, PoseSegments
from .exercise import Camera, DisplaySettings, Exercise, ExerciseMetadata, SegmentLine
from .rules import (
    AngleCounterRule,
    AngleValidationRule,
    AngleROMValidationRule,
    DistanceValidationRule,
    Severity,
)


@dataclass
class ShoulderPressExercise(Exercise):
    name: str = "Shoulder Press"
    camera: Camera = Camera.BOTH
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            # Use elbow angles for stage detection (up/down)
            # Stage changes at 90°: >90 = up, <90 = down
            # Using LEFT_ARM (shoulder-elbow-wrist) so only arm points are shown in skeleton
            AngleCounterRule(
                name="left_shoulder",
                joints=PoseSegments.LEFT_ARM,
                up_angle=91,   # Trigger up stage when > 90
                down_angle=89,  # Trigger down stage when < 90
                sync_group="shoulder_press",
            ),
            AngleCounterRule(
                name="right_shoulder",
                joints=PoseSegments.RIGHT_ARM,
                up_angle=91,   # Trigger up stage when > 90
                down_angle=89,  # Trigger down stage when < 90
                sync_group="shoulder_press",
            ),
        ]
    )
    validation_rules: list = field(
        default_factory=lambda: [
            # ROM validation for shoulder angles
            AngleROMValidationRule(
                name="left_shoulder_rom",
                joints=PoseSegments.LEFT_ARM_DIRECTION,
                min_rom_angle=40,
                max_rom_angle=160,
                message="Shoulder: Reach 160° up, 40-80° down",
                severity=Severity.ERROR,
            ),
            AngleROMValidationRule(
                name="right_shoulder_rom",
                joints=PoseSegments.RIGHT_ARM_DIRECTION,
                min_rom_angle=40,
                max_rom_angle=160,
                message="Shoulder: Reach 160° up, 40-80° down",
                severity=Severity.ERROR,
            ),
            # ROM validation for elbow angles
            AngleROMValidationRule(
                name="left_elbow_rom",
                joints=PoseSegments.LEFT_ARM,
                min_rom_angle=60,
                max_rom_angle=170,
                message="Elbow: Reach 170° up, 60° down",
                severity=Severity.ERROR,
            ),
            AngleROMValidationRule(
                name="right_elbow_rom",
                joints=PoseSegments.RIGHT_ARM,
                min_rom_angle=60,
                max_rom_angle=170,
                message="Elbow: Reach 170° up, 60° down",
                severity=Severity.ERROR,
            ),
            # Distance validation: wrists should be at least shoulder-width apart
            # Name starts with counter rule name to auto-poison reps
            DistanceValidationRule(
                name="left_shoulder_wrist_distance",
                measurement=(L_WRIST, R_WRIST),      # wrist span being checked
                reference=(L_SHOULDER, R_SHOULDER),  # normalized to shoulder width
                min_ratio=1.2,  # Must be at least 1.2x shoulder width (stricter)
                max_ratio=3.0,
                message="Keep wrists wider than shoulders",
                severity=Severity.ERROR,
            ),
        ]
    )
    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(
            # Only arm (counter) skeletons — ROM-validation joints are the same
            # arms, so drawing them adds visual noise.
            show_validation_skeleton=False,
            segment_lines=[
                # Wrist-to-wrist line while both arms are overhead; turns red
                # when the wrist-distance rule is failing.
                SegmentLine(
                    endpoints=(L_WRIST, R_WRIST),
                    active_angles=("left_shoulder", "right_shoulder"),
                    min_angle=90,
                    error_rule="left_shoulder_wrist_distance",
                ),
            ],
        )
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Overhead pressing exercise for the shoulders.",
            muscle_groups=("shoulders", "triceps", "upper chest"),
        )
    )
```

---

### FILE: [backend/src/exercises/squat.py](backend/src/exercises/squat.py)

```py
"""Squat exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Camera, Exercise, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class SquatExercise(Exercise):
    name: str = "Squat"
    camera: Camera = Camera.SIDE
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee",
                joints=PoseSegments.LEFT_LEG,
                up_angle=160,
                down_angle=70,
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=60,
                max_angle=180,
                message="Keep your back straight",
                severity=Severity.ERROR,
            ),
            AngleValidationRule(
                name="knee_aligned",
                joints=PoseSegments.LEFT_LEG,
                min_angle=30,
                max_angle=180,
                message="Keep your knee aligned",
                severity=Severity.WARNING,
            ),
        ]
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Compound lower-body strength exercise.",
            muscle_groups=("quadriceps", "glutes", "hamstrings", "core"),
        )
    )
```

---

### FILE: [backend/src/exercises/validation.py](backend/src/exercises/validation.py)

```py
"""Form-validation evaluation.

This module is the ONE place that knows *how* to turn a ValidationRule into a
pass/fail result. GymEngine never evaluates rules itself — it only calls
:func:`validate_all`. That indirection is what keeps the engine closed for
modification when new rule *kinds* are added later (see the dispatch note on
:func:`validate_all` below).

Rules stay behaviour-free by design (see the rules module docstring); all
execution logic lives here and only here.
"""

from dataclasses import dataclass
from typing import Iterable, Sequence

from ..utils.geometry import calc_angle, get_points, calc_distance
from .rules import AngleValidationRule, AngleROMValidationRule, DistanceValidationRule, Severity, Stage


@dataclass
class ValidationResult:
    """Outcome of evaluating a single rule on one frame."""

    rule_name: str
    message: str
    severity: Severity
    passed: bool
    angle: float | None   # None when the angle could not be computed
    joints: tuple = ()  # the rule's landmark triple, carried for rendering


def evaluate_rule(
    rule: AngleValidationRule, landmarks, width: int, height: int
) -> ValidationResult:
    """Evaluate one angle-based AngleValidationRule against the detected pose."""
    pts = get_points(rule.joints, landmarks, width, height)
    angle = calc_angle(*pts) if len(pts) >= 3 else None
    # Preserve the prior behaviour for the pass/fail decision: when the angle
    # is undefined we fall back to 0° *only* for the range check. The reported
    # `angle` stays None so the UI can show "N/A" instead of a fake 0°.
    checked = 0.0 if angle is None else angle
    passed = rule.min_angle <= checked <= rule.max_angle
    return ValidationResult(
        rule.name, rule.message, rule.severity, passed, angle, joints=rule.joints
    )


def evaluate_rom_rule(
    rule: AngleROMValidationRule,
    landmarks,
    width: int,
    height: int,
    state,
) -> ValidationResult:
    """Evaluate a ROMValidationRule using the live RepState."""
    pts = get_points(rule.joints, landmarks, width, height)
    angle = calc_angle(*pts) if len(pts) >= 3 else None

    if angle is None:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=rule.joints)

    if state is None:
        return ValidationResult(rule.name, rule.message, rule.severity, True, angle, joints=rule.joints)

    if state.stage == Stage.DOWN and not getattr(state, "reached_bottom", False):
        msg = f"Go deeper — target <= {int(rule.min_rom_angle)} deg"
        return ValidationResult(rule.name, msg, rule.severity, False, angle, joints=rule.joints)

    if state.stage == Stage.RETURNING:
        msg = f"Extend fully — target >= {int(rule.max_rom_angle)} deg"
        return ValidationResult(rule.name, msg, rule.severity, False, angle, joints=rule.joints)

    return ValidationResult(rule.name, rule.message, rule.severity, True, angle, joints=rule.joints)


def evaluate_distance_rule(
    rule: DistanceValidationRule,
    landmarks,
    width: int,
    height: int,
) -> ValidationResult:
    """Evaluate a DistanceValidationRule based on distance ratios."""
    pts1 = get_points(rule.measurement, landmarks, width, height)
    pts2 = get_points(rule.reference, landmarks, width, height)

    if len(pts1) < 2 or len(pts2) < 2:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=())

    distance = calc_distance(pts1[0], pts1[1])
    reference_distance = calc_distance(pts2[0], pts2[1])

    if reference_distance == 0:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=())

    ratio = distance / reference_distance
    passed = rule.min_ratio <= ratio <= rule.max_ratio

    return ValidationResult(
        rule.name, rule.message, rule.severity, passed, ratio, joints=rule.measurement
    )


def validate_all(
    rules: Iterable,
    landmarks,
    width: int,
    height: int,
    states: dict | None = None,
) -> list[ValidationResult]:
    """Run every validation rule; dispatches on rule type.

    ``states`` is only needed for AngleROMValidationRule; it may be omitted for
    exercises that only use plain AngleValidationRules.

    Dispatch note: this is a deliberately small ``isinstance`` chain — one
    branch per concrete rule kind (ROM and distance first, the angle rule as
    the catch-all). With three kinds it is the simplest thing that works and
    reads top-to-bottom like a table of contents. A registry-based dispatcher
    was considered and rejected: it would add indirection (registration,
    lookup, ordering) without paying for itself until the number of rule
    kinds is much larger. To add a new kind: write one ``evaluate_*``
    function above and add one branch here.
    """
    results = []
    for rule in rules:
        if isinstance(rule, AngleROMValidationRule):
            state = (states or {}).get(rule.name)
            results.append(evaluate_rom_rule(rule, landmarks, width, height, state))
        elif isinstance(rule, DistanceValidationRule):
            results.append(evaluate_distance_rule(rule, landmarks, width, height))
        else:
            results.append(evaluate_rule(rule, landmarks, width, height))
    return results


def violations(results: Sequence[ValidationResult]) -> list[ValidationResult]:
    """Filter a batch of results down to the ones that failed."""
    return [r for r in results if not r.passed]
```

---

### FILE: [backend/src/server/routes/__init__.py](backend/src/server/routes/__init__.py)

```py
"""API route modules (all mounted under /api)."""
```

---

### FILE: [backend/src/server/routes/downloads.py](backend/src/server/routes/downloads.py)

```py
"""Downloads of generated artifacts (rendered session videos).

One deliberately narrow endpoint: files that already live inside the repo-root
``output/videos/`` directory, addressed by bare filename only.
"""

import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...config import RENDERED_DIR

router = APIRouter(prefix="/downloads", tags=["downloads"])

_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,180}\.mp4$")


@router.get("/rendered/{name}")
def download_rendered_video(name: str) -> FileResponse:
    """Serve a rendered/annotated session video produced by a live run."""
    if not _SAFE_NAME.match(name) or ".." in name:
        raise HTTPException(status_code=404, detail=f"Unknown video '{name}'")
    path = RENDERED_DIR / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Unknown video '{name}'")
    return FileResponse(path, media_type="video/mp4", filename=name)
```

---

### FILE: [backend/src/server/routes/exercises.py](backend/src/server/routes/exercises.py)

```py
"""Exercise catalogue endpoints — derived straight from the registry."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ...exercises.exercise import Exercise
from ...exercises.registry import registry

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _exercise_payload(key: str, ex: Exercise) -> Dict[str, Any]:
    """One exercise, using ONLY data that genuinely exists (no invented fields).

    ``image`` is a forward slot for real thumbnails/photos (null today);
    the frontend renders a placeholder for it.
    """
    return {
        "id": key,
        "name": ex.name,
        "description": ex.metadata.description,
        "muscle_groups": list(ex.metadata.muscle_groups),
        "camera": str(getattr(ex.camera, "value", ex.camera)),
        "counters": [c.name for c in ex.counter_rules],
        "rules": len(ex.validation_rules),
        "image": None,
    }


@router.get("")
def list_exercises() -> List[Dict[str, Any]]:
    return [_exercise_payload(key, registry.get(key)) for key in registry.list()]


@router.get("/{key}")
def get_exercise(key: str) -> Dict[str, Any]:
    if not registry.exists(key):
        raise HTTPException(status_code=404, detail=f"Unknown exercise '{key}'")
    return _exercise_payload(key, registry.get(key))
```

---

### FILE: [backend/src/server/routes/live.py](backend/src/server/routes/live.py)

```py
"""Live coaching stream — one WebSocket per workout.

Protocol
--------
Client connects to
``/ws/live?exercise=<key>&source=webcam|video[&video=<ref>]``.

``video`` reference forms (only with ``source=video``):

* ``upload:<id>`` — a video previously uploaded via ``POST /api/uploads``
  (the **web app flow**; ids resolve strictly inside ``output/uploads/``);
* an explicit path — developer escape hatch / CLI parity (local, single-user);
* omitted — falls back to ``VIDEO_PATH`` from ``.env``.

Server → client::

    binary frame  — one JPEG per processed frame (~capture rate)
    {"type": "state", ...}  — metrics/feedback, ~15 Hz while active
    {"type": "end",  ...}   — workout finished; carries session_id of export
                              and rendered_video when rendering is enabled
    {"type": "error", ...}  — fatal problem (unknown exercise, no camera, ...)

Client → server::

    {"action": "stop"}      — finish now (rep history so far is exported)

Only ONE live session may run at a time (a webcam is a single-user device);
a second connection is rejected with an error event and closed.
"""

import asyncio
import queue
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...exercises.registry import registry
from ..live_runner import LiveSession
from .uploads import stored_path

router = APIRouter(tags=["live"])

# Single-slot gate. An asyncio.Lock would work too, but the boolean+guard
# lives entirely inside the handler's task — simple and race-free there.
_active_session: Optional[LiveSession] = None


@router.websocket("/ws/live")
async def live_session(websocket: WebSocket, exercise: str, source: str = "webcam", video: Optional[str] = None):
    global _active_session
    await websocket.accept()

    if exercise not in registry.list():
        await websocket.send_json({"type": "error", "message": f"Unknown exercise '{exercise}'"})
        return await websocket.close()
    if source not in ("webcam", "video"):
        await websocket.send_json({"type": "error", "message": "source must be 'webcam' or 'video'"})
        return await websocket.close()

    # Resolve upload references to real paths inside output/uploads/.
    if video is not None and video.startswith("upload:"):
        upload_id = video[len("upload:"):]
        resolved = stored_path(upload_id)
        if resolved is None:
            await websocket.send_json({"type": "error", "message": f"Unknown upload '{upload_id}'"})
            return await websocket.close()
        video = str(resolved)

    if _active_session is not None and _active_session.is_alive():
        await websocket.send_json({"type": "error", "message": "Another live session is already running"})
        return await websocket.close()

    events: "queue.Queue" = queue.Queue(maxsize=120)
    session = LiveSession(exercise, source, events, video_path=video)
    _active_session = session
    session.start()

    async def forward_events() -> None:
        """Pump runner events to the socket without blocking the loop."""
        loop = asyncio.get_running_loop()
        while True:
            event = await loop.run_in_executor(None, events.get)
            if isinstance(event, (bytes, bytearray)):
                await websocket.send_bytes(bytes(event))
            else:
                await websocket.send_json(event)
                if event.get("type") in ("end", "error"):
                    return

    async def listen_commands() -> None:
        try:
            while True:
                message = await websocket.receive_json()
                if message.get("action") == "stop":
                    session.stop()
        except WebSocketDisconnect:
            session.stop()

    forward = asyncio.create_task(forward_events())
    listen = asyncio.create_task(listen_commands())
    try:
        await asyncio.wait({forward, listen}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        session.stop()
        forward.cancel()
        listen.cancel()
        if _active_session is session:
            _active_session = None
        try:
            await websocket.close()
        except RuntimeError:
            pass  # already closed by the peer
```

---

### FILE: [backend/src/server/routes/sessions.py](backend/src/server/routes/sessions.py)

```py
"""Workout history endpoints — the exported JSON reports, served as-is."""

from dataclasses import asdict
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ..store import SessionStore

router = APIRouter(prefix="/sessions", tags=["sessions"])
_store = SessionStore()


@router.get("")
def list_sessions() -> List[Dict[str, Any]]:
    """Session list items, newest first."""
    return [asdict(item) for item in _store.list()]


@router.get("/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    """The complete session report document (verbatim export)."""
    report = _store.get(session_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Unknown session '{session_id}'")
    return report


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str) -> None:
    if not _store.delete(session_id):
        raise HTTPException(status_code=404, detail=f"Unknown session '{session_id}'")
```

---

### FILE: [backend/src/server/routes/settings.py](backend/src/server/routes/settings.py)

```py
"""Editable application settings (safe subset) — runtime + .env persistence.

Only operational knobs are exposed; exercise rules, thresholds and any
counting/validation configuration are deliberately NOT editable through the
API (configs remain code, versioned with the backend).
"""

import re
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config import PROJECT_ROOT, REPO_ROOT, resolve_path, settings

router = APIRouter(prefix="/settings", tags=["settings"])
_ENV_PATH = PROJECT_ROOT / ".env"


def _display_path(path: Path) -> str:
    """Serialize a path .env-style: repo-root-relative (``assets/…``,
    ``output/…``) when possible, otherwise absolute. This mirrors the
    AppSettings validator, which resolves every relative path against the
    repository root."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()

#: key -> (kind). Paths are stored .env-style (relative to the backend root).
_EDITABLE: Dict[str, str] = {
    "USE_WEBCAM": "bool",
    "WEBCAM_INDEX": "int",
    "VIDEO_PATH": "path",
    "MODEL_PATH": "path",
    "SAVE_OUTPUT": "bool",
    "OUTPUT_PATH": "path",
    "ANALYTICS_FPS": "float",
    "DISPLAY_MAX_WIDTH": "int",
    "EXPORT_SESSION": "bool",
}


class SettingsPatch(BaseModel):
    """Partial settings update (only editable keys, already typed)."""

    model_config = {"extra": "forbid"}

    USE_WEBCAM: bool | None = None
    WEBCAM_INDEX: int | None = None
    VIDEO_PATH: str | None = None
    MODEL_PATH: str | None = None
    SAVE_OUTPUT: bool | None = None
    OUTPUT_PATH: str | None = None
    ANALYTICS_FPS: float | None = None
    DISPLAY_MAX_WIDTH: int | None = None
    EXPORT_SESSION: bool | None = None


def _serialize_value(key: str, value: Any) -> str:
    kind = _EDITABLE[key]
    if kind == "bool":
        return "true" if value else "false"
    if kind == "path":
        return _display_path(Path(value))
    return str(value)


def _current() -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for key, kind in _EDITABLE.items():
        value = getattr(settings, key)
        if isinstance(value, Path):
            value = _display_path(value)
        data[key] = value
    return data


def _persist_env(updates: Dict[str, Any]) -> None:
    """Rewrite/update KEY=VALUE lines in .env, preserving everything else."""
    rendered = {key: _serialize_value(key, value) for key, value in updates.items()}
    lines = _ENV_PATH.read_text(encoding="utf-8").splitlines() if _ENV_PATH.exists() else []
    seen = set()
    pattern = re.compile(r"^\s*([A-Z0-9_]+)\s*=")
    out = []
    for line in lines:
        match = pattern.match(line)
        if match and match.group(1) in rendered:
            key = match.group(1)
            out.append(f"{key}={rendered[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, value in rendered.items():
        if key not in seen:
            out.append(f"{key}={value}")
    _ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


@router.get("")
def get_settings() -> Dict[str, Any]:
    return _current()


@router.put("")
def update_settings(patch: SettingsPatch) -> Dict[str, Any]:
    updates = patch.model_dump(exclude_none=True)
    if not updates:
        return _current()
    if "ANALYTICS_FPS" in updates and updates["ANALYTICS_FPS"] <= 0:
        raise HTTPException(status_code=422, detail="ANALYTICS_FPS must be positive")
    # Apply to the live settings object first (Path coercion kept intact).
    # Relative paths are resolved against the repo root here because
    # assignment does not re-run the AppSettings validator — the engine must
    # always see absolute paths regardless of the server's CWD.
    for key, value in updates.items():
        current = getattr(settings, key)
        if isinstance(current, Path):
            value = resolve_path(value)
        setattr(settings, key, value)
    # ...then persist for future runs.
    try:
        _persist_env(updates)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write .env: {exc}")
    return _current()
```

---

### FILE: [backend/src/server/routes/uploads.py](backend/src/server/routes/uploads.py)

```py
"""Video uploads — the web app's way to pick a workout video.

Browser uploads land in the repo-root ``output/uploads/`` directory under a
name the server controls::

    <uuid12>__<sanitized-original-name>.<ext>

The returned ``id`` IS that stored filename. The WebSocket live endpoint
references an upload as ``video=upload:<id>`` — clients never hand the server
an arbitrary filesystem path (``_SAFE_STORED_NAME`` + the uploads-dir lookup
make traversal attempts resolve to "unknown upload").

Uploads are cleaned up manually via DELETE (no TTL/GC yet — local single-user
deployment).
"""

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from ...config import UPLOADS_DIR

router = APIRouter(prefix="/uploads", tags=["uploads"])

_ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
_MAX_UPLOAD_BYTES = 1024 * 1024 * 1024  # 1 GiB
_CHUNK = 1024 * 1024

#: What an upload id (the stored filename) is allowed to look like.
_SAFE_STORED_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,180}$")


def _sanitize_original(name: str) -> str:
    """Keep the original name recognizable but filesystem- and URL-safe."""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).stem).strip("._-")
    return stem[:60] or "video"


def stored_path(upload_id: str) -> Optional[Path]:
    """Resolve an upload id to an existing file inside the uploads dir.

    Returns ``None`` for anything malformed or absent — never a path outside
    the uploads directory.
    """
    if not _SAFE_STORED_NAME.match(upload_id) or ".." in upload_id:
        return None
    path = UPLOADS_DIR / upload_id
    return path if path.is_file() else None


def _describe(path: Path) -> Dict[str, Any]:
    name = path.name
    original = name.split("__", 1)[1] if "__" in name else name
    return {
        "id": name,
        "name": original,
        "size": path.stat().st_size,
        "uploaded_at": datetime.fromtimestamp(
            path.stat().st_mtime, tz=timezone.utc
        ).isoformat(),
    }


@router.get("")
def list_uploads() -> List[Dict[str, Any]]:
    """Previously uploaded videos, newest first."""
    if not UPLOADS_DIR.is_dir():
        return []
    files = (p for p in UPLOADS_DIR.iterdir() if p.is_file() and _SAFE_STORED_NAME.match(p.name))
    return [_describe(p) for p in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)]


@router.post("", status_code=201)
async def upload_video(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Store one uploaded video; returns the id used to start a live session."""
    original = file.filename or "video"
    ext = Path(original).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext or 'none'}' — allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
        )

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid.uuid4().hex[:12]}__{_sanitize_original(original)}{ext}"
    dest = UPLOADS_DIR / stored

    size = 0
    try:
        with dest.open("wb") as fh:
            while chunk := await file.read(_CHUNK):
                size += len(chunk)
                if size > _MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="File too large (max 1 GiB)")
                fh.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise

    if size == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Empty file")

    return {"id": stored, "name": _describe(dest)["name"], "size": size}


@router.delete("/{upload_id}", status_code=204)
def delete_upload(upload_id: str) -> None:
    path = stored_path(upload_id)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Unknown upload '{upload_id}'")
    path.unlink()
```

---

### FILE: [backend/src/server/__init__.py](backend/src/server/__init__.py)

```py
"""HTTP + WebSocket API for AI-GYM — a thin presentation layer over the engine.

The Python backend (engine, counter, validation, analytics) remains the single
source of truth. This package ONLY exposes what already exists:

* ``routes/exercises.py``  — exercise catalogue (straight from the registry)
* ``routes/sessions.py``   — workout history (the exported JSON reports)
* ``routes/settings.py``   — editable subset of the application settings
* ``routes/live.py``       — real-time coaching stream (WebSocket)

Neither the engine, the counting rules, nor the validation logic are modified;
routes compose public behaviour and re-serialize existing artifacts.
"""
```

---

### FILE: [backend/src/server/app.py](backend/src/server/app.py)

```py
"""FastAPI application factory — the single entry point for the AI-GYM API.

Routers are mounted under ``/api`` (versioned paths can be introduced later
without moving handlers). CORS is open to local dev origins (Vite on :5173
and :4173); tighten for real deployments via a reverse proxy.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import downloads, exercises, live, sessions, settings as settings_routes, uploads


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI-GYM API",
        description="Pose-estimation gym trainer — session analytics and live coaching.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(exercises.router, prefix="/api")
    app.include_router(sessions.router, prefix="/api")
    app.include_router(settings_routes.router, prefix="/api")
    app.include_router(uploads.router, prefix="/api")
    app.include_router(downloads.router, prefix="/api")
    app.include_router(live.router)
    return app


app = create_app()
```

---

### FILE: [backend/src/server/live_runner.py](backend/src/server/live_runner.py)

```py
"""Live coaching session runner — streams an engine session over a queue.

A single background thread drives the *existing* pipeline exactly the way
``GymEngine.run`` does (PoseService -> GymEngine.analyze -> overlay render),
but instead of ``cv2.imshow`` it publishes events for the WebSocket layer:

* ``bytes``  — one JPEG per processed frame (binary WS message)
* ``dict``   — JSON state updates: ``{"type": "state" | "end" | "error"}``

Nothing here reimplements counting, validation, or rendering — the engine's
own methods produce everything; this class only pumps and packages.
"""

import queue
import threading
import time
from typing import Any, Dict, List, Optional

import cv2

from ..config import RENDERED_DIR, settings
from ..exercises.exercise import Camera
from ..exercises.rules import Severity
from ..exercises.validation import violations
from ..services.gym_engine import GymEngine
from ..services.video_source import VideoSourceError, open_capture
from ..services.pose_service import PoseService
from ..utils.render import fit_to_screen

# Live state is throttled: frames stream at capture rate, metrics at ~15 Hz.
_STATE_EVERY_N_FRAMES = 2
_STREAM_MAX_WIDTH = 960
_JPEG_QUALITY = 70

_DEFAULT_WEIGHTS = {"error": 50.0, "warning": 20.0, "info": 10.0}


class LiveSession(threading.Thread):
    """One live workout: capture + analyze + render + publish until stopped.

    Args:
        exercise:  Registry key of the exercise to run.
        source:    ``"webcam"`` (index from settings) or ``"video"``
                   (``video_path`` / settings.VIDEO_PATH).
        events:    Thread-safe queue the WS handler drains (bytes | dict).
        video_path: Explicit video override (only used when source="video").
    """

    def __init__(self, exercise: str, source: str, events: "queue.Queue", video_path: Optional[str] = None) -> None:
        super().__init__(daemon=True)
        self.exercise_key = exercise
        self.source = source
        self.video_path = video_path
        self.events = events
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------
    def _publish(self, event) -> None:
        """Drop-oldest publish: a slow consumer never stalls the workout."""
        try:
            self.events.put_nowait(event)
        except queue.Full:
            try:
                self.events.get_nowait()
            except queue.Empty:
                pass
            try:
                self.events.put_nowait(event)
            except queue.Full:
                pass

    @staticmethod
    def _live_score(results, weights) -> Optional[float]:
        """Instant form score from the CURRENT frame's failing rules."""
        penalty = sum(weights.get(r.severity, weights.get(str(r.severity), 0.0))
                      for r in results if not r.passed)
        return max(0.0, 100.0 - penalty)

    def _state(self, engine: GymEngine, results, elapsed: float, fps: float) -> Dict[str, Any]:
        primary = engine.counter.primary
        last = engine.judge.last_rep
        rule = engine.exercise.counter_rules[0] if engine.exercise.counter_rules else None
        stage_map = {
            "up": getattr(rule, "up_stage", "up"),
            "down": getattr(rule, "down_stage", "down"),
        }
        failing = violations(results)
        return {
            "type": "state",
            "exercise": engine.exercise.name,
            "elapsed": round(elapsed, 1),
            "fps": round(fps, 1),
            "reps": engine.counter.primary.count,
            "good": engine.judge.good_reps,
            "bad": engine.judge.bad_reps,
            "stage": stage_map.get(primary.stage, primary.stage),
            "angle": round(primary.angle, 1),
            "last_rep": ("good" if last.good else "bad") if last else None,
            "live_score": self._live_score(results, _DEFAULT_WEIGHTS),
            "side": (engine.side_detector.detected_side if engine.side_detector else "both"),
            "adapting": not engine.rules_adapted,
            "feedback": [r.message for r in failing][:3],
            "rules": [
                {
                    "name": r.rule_name,
                    "passed": r.passed,
                    "severity": str(getattr(r.severity, "value", r.severity)),
                    "message": r.message,
                    "value": round(r.angle, 1) if r.angle is not None else None,
                }
                for r in results
            ],
        }

    # ------------------------------------------------------------------
    # Main loop (mirrors GymEngine.run's composition, output = queue)
    # ------------------------------------------------------------------
    def run(self) -> None:
        from ..exercises.registry import registry

        try:
            engine = GymEngine(registry.get(self.exercise_key))
        except Exception as exc:  # unknown exercise
            self._publish({"type": "error", "message": f"Unknown exercise: {exc}"})
            return

        try:
            cap = open_capture(
                video_path=self.video_path
                or (str(settings.VIDEO_PATH) if settings.VIDEO_PATH else None),
                use_webcam=self.source == "webcam",
                webcam_index=settings.WEBCAM_INDEX,
            )
        except VideoSourceError as exc:
            self._publish({"type": "error", "message": str(exc)})
            return

        # Optional rendered-video output (mirrors GymEngine.run: mp4v, 25 fps):
        # annotated frames are written per-session under output/videos/ so the
        # web app can offer the user a download after the workout. Best-effort:
        # a writer failure never kills the workout or the report export.
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in engine.exercise.name)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        writer = None
        rendered_name: Optional[str] = None
        rendered_error: Optional[str] = None
        if settings.SAVE_OUTPUT:
            try:
                RENDERED_DIR.mkdir(parents=True, exist_ok=True)
                rendered_name = f"{safe_name}_{stamp}.mp4"
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(RENDERED_DIR / rendered_name), fourcc, 25.0, (width, height))
                if not writer.isOpened():
                    writer.release()
                    writer, rendered_name = None, None
                    rendered_error = "OpenCV could not create the output video"
            except Exception as exc:
                writer, rendered_name = None, None
                rendered_error = str(exc)

        try:
            pose_service = PoseService(settings.MODEL_PATH)
        except Exception as exc:
            cap.release()
            if writer is not None:
                writer.release()
                (RENDERED_DIR / rendered_name).unlink(missing_ok=True)
            self._publish({"type": "error", "message": f"Pose model unavailable: {exc}"})
            return

        fps = 25.0
        results: List = []
        frame_id, frames_tick = 0, 0
        start = time.perf_counter()
        last_fps_check = start
        live_fps = 0.0

        while not self._stop.is_set():
            ok, frame = cap.read()
            if not ok:
                break
            h, w = frame.shape[:2]
            timestamp = int((frame_id / fps) * 1000)
            detected = pose_service.detect(frame, timestamp)
            frame_result = None
            if detected and detected.pose_landmarks:
                lm = detected.pose_landmarks[0]
                frame_result = engine.analyze(lm, w, h, frame_id)
                results = frame_result.results
                engine._render(frame, frame_result, lm, w, h)

            if writer is not None:
                writer.write(frame)
            stream = fit_to_screen(frame, max_width=_STREAM_MAX_WIDTH)
            ok_jpg, jpg = cv2.imencode(
                ".jpg", stream, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY]
            )
            if ok_jpg:
                self._publish(jpg.tobytes())
            if frame_result is not None and frame_id % _STATE_EVERY_N_FRAMES == 0:
                elapsed = time.perf_counter() - start
                self._publish(self._state(engine, results, elapsed, live_fps))
            frame_id += 1
            frames_tick += 1
            now = time.perf_counter()
            if now - last_fps_check >= 1.0:
                live_fps = frames_tick / (now - last_fps_check)
                frames_tick, last_fps_check = 0, now

        cap.release()
        if writer is not None:
            writer.release()

        # ── Finalize & export (always: the app depends on the report) ──
        elapsed = time.perf_counter() - start
        ended: Dict[str, Any] = {"type": "end", "reps": engine.judge.total_reps}
        if rendered_name is not None:
            ended["rendered_video"] = rendered_name
        if rendered_error is not None:
            ended["rendered_error"] = rendered_error
        try:
            from ..analytics.analyzer import SessionAnalyzer
            from ..analytics.exporters import JsonSessionExporter

            report = SessionAnalyzer().build_report(
                engine.judge.history,
                exercise=engine.exercise,
                fps=settings.ANALYTICS_FPS,
                total_duration=elapsed,
            )
            settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            target = settings.EXPORT_DIR / f"{safe_name}_{stamp}"
            out = JsonSessionExporter().export(report, target)
            ended["session_id"] = report.session.id if report.session else out.stem
        except Exception as exc:
            ended["export_error"] = str(exc)
        self._publish(ended)
```

---

### FILE: [backend/src/server/store.py](backend/src/server/store.py)

```py
"""Session report storage — file-backed today, swappable for a database later.

All session persistence goes through :class:`SessionStore`. It deliberately
exposes a tiny, storage-agnostic vocabulary (``list`` / ``get`` / ``delete``)
so a future database backend can replace the JSON-file implementation without
touching any route. The exported report document itself is passed through
verbatim — it IS the API response model (backend remains source of truth).
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import settings


@dataclass(frozen=True)
class SessionListItem:
    """Compact session summary for list/history views.

    Derived from the stored report — never from separately recorded state —
    so the list can never disagree with the report it links to.

    Attributes:
        id:           Session id (``report.session.id``), or the filename
                      stem for legacy files predating the session block.
        file:         Report filename within the export directory.
        exercise:     Exercise display name.
        recorded_at:  Canonical session timestamp (may be ``None`` for very
                      old exports).
        total_reps:   Repetitions completed.
        good_reps:    Repetitions classified GOOD.
        accuracy:     GOOD-rep percentage (0-100).
        score:        Session score (mean of per-rep scores).
        duration:     Total active workout duration (seconds).
        most_common_error: The session's top failed rule, if any.
    """

    id: str
    file: str
    exercise: str
    recorded_at: Optional[str]
    total_reps: int
    good_reps: int
    accuracy: float
    score: Optional[float]
    duration: float
    most_common_error: Optional[str]


class SessionStore:
    """Lists, loads and deletes exported session reports (JSON files)."""

    def __init__(self, directory: Path | None = None) -> None:
        self._dir = Path(directory) if directory else Path(settings.EXPORT_DIR)

    # -- reading --------------------------------------------------------
    def _load_file(self, path: Path) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None  # unreadable/corrupt file: skip rather than 500
        return data if isinstance(data, dict) else None

    def _files(self) -> List[Path]:
        if not self._dir.exists():
            return []
        return sorted(self._dir.glob("*.json"))

    @staticmethod
    def _to_item(path: Path, data: Dict[str, Any]) -> SessionListItem:
        session = data.get("session") or {}
        summary = data.get("summary") or {}
        exercise = data.get("exercise") or {}
        return SessionListItem(
            id=session.get("id") or path.stem,
            file=path.name,
            exercise=exercise.get("name") or summary.get("exercise") or "Unknown",
            recorded_at=session.get("recorded_at") or summary.get("date"),
            total_reps=summary.get("total_reps", 0),
            good_reps=summary.get("good_reps", 0),
            accuracy=summary.get("accuracy", 0.0),
            score=summary.get("score"),
            duration=summary.get("total_workout_duration", 0.0),
            most_common_error=summary.get("most_common_error"),
        )

    def list(self) -> List[SessionListItem]:
        """All known sessions, newest first by recorded timestamp."""
        items = [
            self._to_item(path, data)
            for path in self._files()
            if (data := self._load_file(path)) is not None
        ]
        items.sort(key=lambda item: item.recorded_at or "", reverse=True)
        return items

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Full report document for one session (by id or filename stem)."""
        for path in self._files():
            if path.stem == session_id:
                return self._load_file(path)
            data = self._load_file(path)
            if data and (data.get("session") or {}).get("id") == session_id:
                return data
        return None

    # -- writing --------------------------------------------------------
    def delete(self, session_id: str) -> bool:
        """Remove one session's report file. ``True`` when something was deleted."""
        for path in self._files():
            data = self._load_file(path)
            if path.stem == session_id or (
                data and (data.get("session") or {}).get("id") == session_id
            ):
                path.unlink(missing_ok=True)
                return True
        return False
```

---

### FILE: [backend/src/services/__init__.py](backend/src/services/__init__.py)

```py
from .gym_engine import GymEngine
from .pose_service import PoseService
from .rep_counter import RepCounter, RepState
from .rep_judge import RepJudge, RepResult
from .video_source import VideoSourceError, open_capture, resolve_video_path

__all__ = [
    "GymEngine",
    "PoseService",
    "RepCounter",
    "RepState",
    "RepJudge",
    "RepResult",
    "VideoSourceError",
    "open_capture",
    "resolve_video_path",
]
```

---

### FILE: [backend/src/services/additional_casses.py](backend/src/services/additional_casses.py)

```py
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
```

---

### FILE: [backend/src/services/gym_engine.py](backend/src/services/gym_engine.py)

```py
"""Generic, exercise-agnostic training engine."""

import datetime
import time

import cv2

from ..config import settings
from ..core import Colors
from ..exercises.exercise import Camera, Exercise
from ..exercises.validation import ValidationResult, validate_all, violations
from ..exercises.rules import DistanceValidationRule, Severity, Stage
from ..utils.geometry import ComputedAngle, calc_angle, get_points
from ..utils.render import draw_angle_arc, draw_angle_labels, draw_skeleton, draw_stats, fit_to_screen, draw_segment_line
from ..utils.camera_side import CameraSideDetector
from .pose_service import PoseService
from .rep_counter import RepCounter
from .rep_judge import RepJudge
from .video_source import open_capture


class FrameResult:
    """Everything computed for a single frame, handed to the renderer."""

    def __init__(self, angles, states, results, views=None):
        self.angles = angles
        self.states = states
        self.results: list[ValidationResult] = results
        # One ComputedAngle per rule (counter + validation) for the renderer.
        self.views: list[ComputedAngle] = views or []


class GymEngine:
    """Runs any exercise described by an :class:`Exercise` configuration.

    GymEngine knows NOTHING about Push-Ups, Squats, or any specific movement.
    Its single responsibility is the loop: detect pose -> compute the angles the
    exercise asked for -> update the counter -> run the validation rules ->
    forward everything to the renderer. Behaviour comes entirely from the
    ``Exercise`` object passed in.

    This is the Open/Closed Principle in practice: to support a new exercise you
    add a new ``Exercise`` definition; you never modify this class.
    """

    def __init__(self, exercise: Exercise, colors: Colors | None = None, display_width: int = 1280):
        self.exercise = exercise
        self.counter = RepCounter(exercise.counter_rules)
        self.judge = RepJudge()
        self.colors = colors or Colors()
        # Optional maximum display width (e.g. DISPLAY_MAX_WIDTH). The frame is
        # first auto-fit to the detected screen; this only caps it further.
        self.display_width = display_width
        self.side_detector = CameraSideDetector(30) if exercise.camera == Camera.SIDE else None
        self.rules_adapted = False if exercise.camera == Camera.SIDE else True
        # ── Distance-based form rules (exercise-agnostic) ──────────────
        # Every DistanceValidationRule declared by the exercise participates:
        # a violation of any of them poisons the repetition it occurs in.
        # Exercises without distance rules get an empty set here and are
        # completely unaffected by this machinery.
        self._distance_rule_names = {
            r.name for r in exercise.validation_rules
            if isinstance(r, DistanceValidationRule)
        }
        # Set when any distance rule fails; consumed when the rep completes.
        self._distance_violation_in_current_rep = False
        # Failing results kept per rule name so the rep report can explain
        # *why* (the rule may pass again by the frame the rep completes on).
        self._distance_violation_results = {}

    # ------------------------------------------------------------------
    # Analysis: pure logic, no I/O -> easy to unit test with fake landmarks.
    # ------------------------------------------------------------------
    def analyze(self, landmarks, width: int, height: int, frame: int) -> FrameResult:
        """Compute angles, update the counter, run validation, and judge reps."""
        if self.side_detector and not self.rules_adapted:
            side = self.side_detector.process_frame(landmarks)
            if side:
                from ..utils.camera_side import adapt_rules
                self.exercise.counter_rules = adapt_rules(self.exercise.counter_rules, side)
                self.exercise.validation_rules = adapt_rules(self.exercise.validation_rules, side)
                self.counter = RepCounter(self.exercise.counter_rules)
                self.rules_adapted = True
            if not self.rules_adapted:
                return FrameResult(angles={}, states=self.counter.states, results=[], views=[])

        angles = {}
        views = []  # unified per-rule angle views for the renderer

        for rule in self.exercise.counter_rules:
            pts = get_points(rule.joints, landmarks, width, height)
            angle = calc_angle(*pts) if len(pts) >= 3 else None
            angles[rule.name] = angle
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            # Counter angles are never "failed" -> drawn with the highlight colour.
            views.append(ComputedAngle(name=rule.name, vertex=vertex, angle=angle, is_error=False))

        results = validate_all(self.exercise.validation_rules, landmarks, width, height, states=self.counter.states)

        for res in results:
            pts = get_points(res.joints, landmarks, width, height)
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            views.append(
                ComputedAngle(name=res.rule_name, vertex=vertex, angle=res.angle, is_error=not res.passed)
            )

        # ── Rep quality tracking ───────────────────────────────────────
        # RepCounter owns counting AND quality (good/bad) decisions.
        # Pass violation_names (set of failing rule names) — not a single global
        # bool — so each counter rule only accumulates violations for its own joints.
        violation_names = {r.rule_name for r in violations(results)}
        prev_good  = self.counter.primary.good
        prev_count = self.counter.primary.count

        # Preserve every rule outcome of this frame in the rep's complete
        # evaluation record. Pure data collection for reporting — it does not
        # affect classification or any other decision.
        self.judge.record(results, frame)

        # ── Distance-violation tracking (works for ANY exercise) ────────
        # Accumulate: a distance failure at any point during the current rep
        # marks the whole rep. The flag is only consumed (and cleared) when a
        # rep completes below — never reset per-frame, so a violation at the
        # top of a press still poisons the rep that is counted on the way down.
        if self._distance_rule_names & violation_names:
            self._distance_violation_in_current_rep = True
            for r in results:
                if not r.passed and r.rule_name in self._distance_rule_names:
                    self._distance_violation_results[r.rule_name] = r

        self.counter.update(angles, violation_names)

        if self.counter.primary.count > prev_count:
            # Rep just completed - check if there was a distance violation
            if self._distance_violation_in_current_rep:
                # Hand the stored failing result(s) to the judge so the
                # session report explains *why* this rep is bad, then force
                # the rep to be bad.
                self.judge.observe(
                    list(self._distance_violation_results.values()), frame,
                )
                self.judge.finalize_rep(
                    self.counter.primary.count,
                    frame,
                    force_good=False,
                )
                self._distance_violation_in_current_rep = False
                self._distance_violation_results.clear()
            else:
                rep_was_good = self.counter.primary.good > prev_good
                if self.counter.primary.speed_warning:
                    # Inject a speed violation warning
                    from ..exercises.validation import ValidationResult
                    self.judge.observe([
                        ValidationResult(
                            rule_name=self.exercise.counter_rules[0].name + "_too_fast",
                            message="Too fast — control the movement",
                            severity=Severity.WARNING,
                            passed=False,
                            angle=None
                        )
                    ], frame)
                self.judge.finalize_rep(
                    self.counter.primary.count,
                    frame,
                    force_good=rep_was_good,
                )

        return FrameResult(
            angles=angles, states=self.counter.states, results=results, views=views
        )

    # ------------------------------------------------------------------
    # Rendering: draws whatever the Exercise configuration describes.
    # ------------------------------------------------------------------
    def _render(self, frame, result: FrameResult, landmarks, width: int, height: int):
        bad = bool(violations(result.results))
        show = self.exercise.display

        # Skeleton for every joint set the exercise cares about.
        if show.show_skeleton:
            drawn_joints = set()
            for rule in self.exercise.counter_rules:
                pts = get_points(rule.joints, landmarks, width, height)
                if len(pts) >= 3:
                    custom_color = None
                    if bad:
                        custom_color = self.colors.ERROR
                    elif hasattr(rule, 'min_rom_angle') and rule.min_rom_angle is not None:
                        state = self.counter.states.get(rule.name)
                        if state is not None:
                            # Only show RED/GREEN feedback when actively in a rep
                            # (DOWN or RETURNING stage). At UP/rest, use default color.
                            if state.stage in (rule.up_stage,):
                                custom_color = None  # resting — default white
                            elif state.reached_bottom:
                                custom_color = self.colors.HIGHLIGHT   # GREEN — depth reached
                            else:
                                custom_color = self.colors.ERROR        # RED — need to go deeper
                    draw_skeleton(frame, pts, self.colors, is_bad=bad, custom_color=custom_color)
                    drawn_joints.add(tuple(sorted(rule.joints)))

            # Validation-rule skeletons (e.g. back angle for deadlift).
            # Can be suppressed per-exercise via DisplaySettings.show_validation_skeleton.
            if show.show_validation_skeleton:
                for rule in self.exercise.validation_rules:
                    # Only draw skeletons for rules with joints attribute (AngleValidationRule)
                    if hasattr(rule, 'joints'):
                        joints_key = tuple(sorted(rule.joints))
                        if joints_key not in drawn_joints:
                            pts = get_points(rule.joints, landmarks, width, height)
                            if len(pts) >= 3:
                                draw_skeleton(frame, pts, self.colors, is_bad=bad)
                                drawn_joints.add(joints_key)

        # Live angle arcs for each counter rule (visual only; the numeric
        # value is drawn by draw_angle_labels for EVERY computed angle).
        if show.show_angle_arc:
            for rule in self.exercise.counter_rules:
                pts = get_points(rule.joints, landmarks, width, height)
                if len(pts) >= 3:
                    draw_angle_arc(frame, pts[0], pts[1], pts[2], self.colors, is_bad=bad)

        # Floating angle label for EVERY computed angle (counter + validation),
        # positioned at the rule's vertex joint. Fully automatic & rule-agnostic.
        draw_angle_labels(frame, result.views, self.colors, width, height)

        # Declarative landmark-to-landmark segment lines (e.g. the wrist line
        # at the top of a shoulder press). Driven entirely by
        # DisplaySettings.segment_lines — the engine knows nothing about
        # which exercise configured them.
        for seg in show.segment_lines:
            active = all(
                (result.angles.get(name) or 0.0) >= seg.min_angle
                for name in seg.active_angles
            )
            if not active:
                continue
            failed = seg.error_rule is not None and any(
                r.rule_name == seg.error_rule and not r.passed
                for r in result.results
            )
            line_color = self.colors.ERROR if failed else self.colors.HIGHLIGHT
            pts = get_points(seg.endpoints, landmarks, width, height)
            if len(pts) == 2:
                draw_segment_line(frame, pts[0], pts[1], self.colors, line_color)

        # Stats / coaching panel: a fixed bottom-left overlay (not anchored to
        # any body landmark). Layout lives in utils/render.py. Rep-quality
        # figures come from RepJudge (history is the single source of truth).
        primary = self.counter.primary
        issues = violations(result.results)
        feedback = [r.message for r in issues]
        last = self.judge.last_rep
        current_rep = (
            "GOOD" if (last is not None and last.good)
            else "BAD" if last is not None
            else "—"
        )
        display_stage = primary.stage
        if self.exercise.counter_rules:
            rule = self.exercise.counter_rules[0]
            if primary.stage == Stage.UP:
                display_stage = rule.up_stage
            elif primary.stage == Stage.DOWN:
                display_stage = rule.down_stage

        draw_stats(
            frame,
            exercise_name=self.exercise.name,
            reps=self.judge.total_reps,
            good_reps=self.judge.good_reps,
            bad_reps=self.judge.bad_reps,
            current_rep=current_rep,
            stage=display_stage,
            angle=primary.angle,
            feedback=feedback,
            colors=self.colors,
        )

    # ------------------------------------------------------------------
    # Session analytics + export (orchestration only — no logic here).
    # ------------------------------------------------------------------
    def _export_session(self, report: "SessionReport") -> None:
        """Persist the complete session ``report`` as JSON (opt-in)."""
        from ..analytics.exporters import JsonSessionExporter

        if settings.EXPORT_FORMAT.lower() != "json":
            # CSV export was removed: a complete session history is nested
            # data and cannot be flattened without losing information. The
            # report is always written as JSON.
            print(
                f"EXPORT_FORMAT '{settings.EXPORT_FORMAT}' is no longer supported"
                " for session reports — writing JSON instead."
            )

        settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.exercise.name)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target = settings.EXPORT_DIR / f"{safe_name}_{stamp}"
        out_path = JsonSessionExporter().export(report, target)
        print(f"Session report exported to {out_path}")

    # ------------------------------------------------------------------
    # Orchestration: video source + detection + render loop.
    # ------------------------------------------------------------------
    def run(self, video_path: str | None = None):
        # Source acquisition + failure diagnostics live in video_source, so the
        # CLI, the engine and the live server all produce identical, actionable
        # errors (which path was tried, what assets/videos actually contains).
        cap = open_capture(
            video_path=video_path or settings.VIDEO_PATH,
            use_webcam=settings.USE_WEBCAM,
            webcam_index=settings.WEBCAM_INDEX,
        )

        fps = 25  # fixed for deterministic timestamps

        writer = None
        if settings.SAVE_OUTPUT:
            settings.OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(settings.OUTPUT_PATH), fourcc, fps, (width, height))

        pose_service = PoseService(settings.MODEL_PATH)
        start_time = time.perf_counter()
        frame_id = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            timestamp = int((frame_id / fps) * 1000)

            result = pose_service.detect(frame, timestamp)

            if result and result.pose_landmarks:
                lm = result.pose_landmarks[0]
                frame_result = self.analyze(lm, w, h, frame_id)
                self._render(frame, frame_result, lm, w, h)

            if writer:
                writer.write(frame)

            # Display-only resize: pose math + saved output use the original frame.
            frame = fit_to_screen(frame, max_width=self.display_width)
            cv2.imshow("AI Gym Trainer", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            frame_id += 1

        # ── Session report (built entirely from RepJudge.history) ─────
        # GymEngine only supplies engine-level context (exercise, source,
        # frames, time); all rep-quality figures are derived by RepJudge so no
        # state is duplicated here.
        elapsed = time.perf_counter() - start_time
        frames_processed = frame_id
        if settings.USE_WEBCAM:
            input_source = f"Webcam (index {settings.WEBCAM_INDEX})"
        else:
            src = video_path or settings.VIDEO_PATH
            input_source = str(src) if src is not None else "none"

        print(self.judge.session_report(
            exercise_name=self.exercise.name,
            input_source=input_source,
            total_frames=frames_processed,
            elapsed_seconds=elapsed,
        ))

        # ── Session analytics + optional export ──────────────────────
        # GymEngine only *orchestrates*: it hands the finished session
        # (RepJudge.history + the exercise it ran) to the analytics module
        # and, if enabled, asks an exporter to persist the resulting
        # SessionReport. No analytics logic lives in the engine.
        if settings.EXPORT_SESSION:
            # Imported lazily (like the exporters) so analytics stays an
            # optional, one-way dependency of the engine and import cycles
            # with the services package are avoided.
            from ..analytics.analyzer import SessionAnalyzer

            report = SessionAnalyzer().build_report(
                self.judge.history,
                exercise=self.exercise,
                fps=settings.ANALYTICS_FPS,
                total_duration=elapsed,
            )
            self._export_session(report)

        print(self.judge.history)
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
```

---

### FILE: [backend/src/services/pose_service.py](backend/src/services/pose_service.py)

```py
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path


class PoseService:
    def __init__(self, model_path: str | Path):
        # mediapipe expects a string asset path; accept Path for convenience.
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
        )

        self.model = vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame, timestamp_ms: int):
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame,
        )

        return self.model.detect_for_video(mp_image, timestamp_ms)
```

---

### FILE: [backend/src/services/rep_counter.py](backend/src/services/rep_counter.py)

```py
"""Repetition counter driven entirely by AngleCounterRule configuration."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from ..exercises.rules import AngleCounterRule, Stage


@dataclass
class RepState:
    """Live state for one counter rule across frames.

    ``stage`` holds the internal counting protocol values (:class:`Stage`)
    for ROM/speed-managed rules, or the exercise's configured display labels
    (``up_stage`` / ``down_stage``) for simple rules — hence plain ``str``.
    """

    angle: float = 0.0
    count: int = 0
    stage: str = Stage.UP

    # Fields for compatibility with custom ROM/speed/violation cases
    good: int = 0
    bad: int = 0
    speed_warning: bool = False
    reached_bottom: bool = False


class RepCounter:
    """Counts repetitions from a list of AngleCounterRule configurations.

    One :class:`RepState` is kept per rule, so an exercise can count from
    several angles at once (e.g. left + right side for symmetry) with no change
    to this class or to GymEngine. The on-screen rep count comes from the first
    rule (``primary``); the others remain available in ``states``.
    """

    def __init__(self, rules: List[AngleCounterRule]):
        self.rules = rules
        self.states: Dict[str, RepState] = {r.name: RepState() for r in rules}

        # Check if any rule requires stateful ROM checks or speed checks
        has_custom = any(
            r.max_rom_angle is not None or r.min_rep_frames > 0 for r in rules
        )
        if has_custom:
            from .additional_casses import CustomCounterHelper
            self._helper = CustomCounterHelper(self)
        else:
            self._helper = None

    @property
    def primary(self) -> RepState:
        """State backing the displayed rep count (first counter rule)."""
        return next(iter(self.states.values()))

    def update(
        self,
        angles: Dict[str, Optional[float]],
        violation_names: Optional[Set[str]] = None,
    ) -> Dict[str, RepState]:
        """Feed in the current angle for each rule; advance counts/stages."""
        if self._helper:
            return self._helper.update(angles, violation_names)

        # Original, simple generic counter code
        for rule in self.rules:
            angle = angles.get(rule.name)
            if angle is None:
                # Angle could not be computed this frame; skip this rule so a
                # degenerate pose is never treated as a real 0° angle.
                continue
            state = self.states[rule.name]
            state.angle = angle

            if angle < rule.down_angle:
                # Entering the "down" position from "up" completes a rep.
                if state.stage == rule.up_stage:
                    state.count += 1
                    state.good += 1  # default simple reps are always good
                state.stage = rule.down_stage
            elif angle > rule.up_angle:
                state.stage = rule.up_stage
            # Angles between thresholds hold the current stage.

        return self.states
```

---

### FILE: [backend/src/services/rep_judge.py](backend/src/services/rep_judge.py)

```py
"""Repetition quality judging — independent of counting and validation.

RepJudge turns a stream of per-frame :class:`ValidationResult` objects into a
stream of per-repetition :class:`RepResult` objects. It is deliberately
ignorant of *how* repetitions are counted (that is :class:`RepCounter`'s job)
and of *how* angles become pass/fail decisions (that is the validation
module's job). Its single responsibility is: collect the validation failures
that occur during one repetition, then, once the repetition finishes, classify
it and emit a result.

GymEngine is the only component that wires RepJudge to RepCounter. It does so
purely through public methods -- ``observe`` every frame and ``finalize_rep``
when RepCounter reports a completed repetition -- so the two services stay
fully decoupled and can evolve independently (e.g. a future ``RepCounter`` that
counts by tempo or symmetry would not require any change here).
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..exercises.rules import Severity
from ..exercises.validation import ValidationResult

# Severity ordering used purely for de-duplication: when the same rule fails on
# several frames we keep the *worst* observed severity, so an ``error`` is never
# masked by an earlier ``warning``. Higher rank == more severe.
_SEVERITY_RANK: Dict[str, int] = {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}


@dataclass
class RepResult:
    """Quality outcome of one completed repetition.

    A ``RepResult`` is the durable record stored in :attr:`RepJudge.history` and
    is the single source of truth for all rep-quality statistics. The raw
    :class:`ValidationResult` objects are stored (not just human-readable
    messages) so future analytics -- form score, time-under-tension, most-common
    errors, session reports -- can be derived from history without changing this
    class or anything upstream.

    Attributes:
        number:       1-based index of the repetition (matches the on-screen
                      rep counter).
        good:         ``True`` iff the repetition had no ``error``-severity
                      violation.
        violations:   The distinct validation rules that FAILED during the rep,
                      de-duplicated by rule name (worst severity kept), in
                      first-failure order. Unchanged legacy semantics.
        evaluations:  The COMPLETE decision record: every rule outcome
                      observed during the rep -- passing AND failing --
                      de-duplicated by rule name (a rule that ever failed
                      stays failed, at its worst observed severity; a rule
                      that never failed keeps its latest passing
                      measurement). Insertion-ordered by first observation.
        start_frame:  First frame of the rep window (the first frame observed
                      after the previous rep completed, or of the session for
                      the first rep), or ``None`` when no frame was recorded.
        end_frame:    Frame index on which the rep completed, or ``None``.
    """

    number: int
    good: bool
    violations: List[ValidationResult]
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
    # Appended last with a default so existing positional construction is
    # unaffected. Empty when no outcomes were recorded for the rep.
    evaluations: List[ValidationResult] = field(default_factory=list)


class RepJudge:
    """Classifies completed repetitions as GOOD / BAD from validation history.

    Responsibilities (and nothing else):
      * observe validation results every frame,
      * remember which rules failed during the current repetition,
      * finalize the repetition once RepCounter reports completion,
      * produce a :class:`RepResult`, store it, and reset for the next rep.

    It exposes read-only statistics (``total_reps``, ``good_reps``,
    ``bad_reps``, ``last_rep``) that are *always derived from* :attr:`history`.
    No separate counters are kept, so the statistics can never drift out of sync
    with the stored results.
    """

    def __init__(self) -> None:
        self.history: List[RepResult] = []
        self._reset_current()

    # -- per-frame observation ------------------------------------------
    def observe(self, results: List[ValidationResult], frame: int = 0) -> None:
        """Collect the validation failures for the frame being processed.

        Call this once per frame (its order relative to ``RepCounter.update``
        does not matter to RepJudge). Failed results are de-duplicated by rule
        name, so a rule that fails across many consecutive frames is recorded
        exactly once in the resulting rep. When the same rule fails with
        differing severities we keep the worst one (see :data:`_SEVERITY_RANK`)
        so an ``error`` is never hidden behind an earlier ``warning``.

        The results are additionally merged into the rep's complete
        evaluation record (see :meth:`record`).
        """
        for r in results:
            if r.passed:
                continue
            existing = self._violations.get(r.rule_name)
            if existing is None or _SEVERITY_RANK.get(r.severity, 0) > _SEVERITY_RANK.get(existing.severity, 0):
                self._violations[r.rule_name] = r

        self.record(results, frame)

    def record(self, results: List[ValidationResult], frame: int = 0) -> None:
        """Merge frame outcomes into the rep's complete evaluation record.

        This is a pure data-collection path: it touches neither the
        violations used for classification nor the GOOD/BAD decision itself.
        Its only purposes are to preserve the outcome of *every* rule
        evaluated during the rep (passing and failing) and to track the rep
        window (``start_frame`` = its first observed frame), so downstream
        reporting can reconstruct the complete decision process.

        De-duplication, per rule name: a rule that ever failed remains
        failed at its worst observed severity; a rule that never failed
        keeps its latest passing measurement.
        """
        if self._start_frame is None:
            # First frame observed since the previous rep was finalized:
            # the start of this rep's window.
            self._start_frame = frame

        for r in results:
            existing = self._evaluations.get(r.rule_name)
            if existing is None:
                self._evaluations[r.rule_name] = r
            elif not r.passed:
                # A failure always supersedes a pass record; among failures
                # keep the worst observed severity.
                if existing.passed or _SEVERITY_RANK.get(r.severity, 0) > _SEVERITY_RANK.get(existing.severity, 0):
                    self._evaluations[r.rule_name] = r
            elif existing.passed:
                # Latest passing measurement wins.
                self._evaluations[r.rule_name] = r

    # -- completion ------------------------------------------------------
    def finalize_rep(self, rep_number: int, frame: int = 0, force_good: bool | None = None) -> RepResult:
        """Finalize the current repetition and begin tracking the next one.

        Builds a :class:`RepResult`, appends it to :attr:`history`, resets the
        temporary per-rep state, and returns the result.

        If ``force_good`` is provided (not None), it overrides the internal
        violation tracking. This is used when RepCounter has already decided
        quality (tracking violations only from DOWN phase start onward).
        """
        if force_good is not None:
            good = force_good
        else:
            bad = any(v.severity in (Severity.ERROR, Severity.WARNING) for v in self._violations.values())
            good = not bad
        result = RepResult(
            number=rep_number,
            good=good,
            violations=list(self._violations.values()),
            start_frame=self._start_frame,
            end_frame=frame,
            evaluations=list(self._evaluations.values()),
        )
        self.history.append(result)
        self._reset_current()
        return result

    # -- derived, read-only statistics ----------------------------------
    @property
    def total_reps(self) -> int:
        """Total completed repetitions (length of history)."""
        return len(self.history)

    @property
    def good_reps(self) -> int:
        """Count of repetitions classified GOOD."""
        return sum(1 for r in self.history if r.good)

    @property
    def bad_reps(self) -> int:
        """Count of repetitions classified BAD."""
        return sum(1 for r in self.history if not r.good)

    @property
    def last_rep(self) -> Optional[RepResult]:
        """The most recently completed :class:`RepResult`, or ``None``."""
        return self.history[-1] if self.history else None

    # -- reporting -------------------------------------------------------
    def summary(self) -> str:
        """Compact one-line rep-quality summary (legacy format)."""
        return (
            f"Total reps: {self.total_reps}, "
            f"Good: {self.good_reps}, "
            f"Bad: {self.bad_reps}"
        )

    def session_report(
        self,
        *,
        exercise_name: Optional[str] = None,
        input_source: Optional[str] = None,
        total_frames: Optional[int] = None,
        elapsed_seconds: Optional[float] = None,
    ) -> str:
        """Build a complete, human-readable session report from ``history``.

        Engine-level context (exercise name, input source, frame count, elapsed
        time) is supplied by GymEngine; everything else is derived from the
        stored :class:`RepResult` history, so no state is duplicated here. The
        same method can later feed a CLI, GUI, log file, or JSON export.
        """
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("SESSION REPORT")
        lines.append("=" * 60)

        # Session Summary
        lines.append("")
        lines.append("Session Summary")
        lines.append("-" * 15)
        if exercise_name is not None:
            lines.append(f"  Exercise            : {exercise_name}")
        if input_source is not None:
            lines.append(f"  Input source        : {input_source}")
        if total_frames is not None:
            lines.append(f"  Total frames        : {total_frames}")
        if elapsed_seconds is not None:
            lines.append(f"  Processing time     : {elapsed_seconds:.2f} s")
            fps = (total_frames / elapsed_seconds) if elapsed_seconds > 0 and total_frames else 0.0
            lines.append(f"  Average FPS         : {fps:.1f}")
        lines.append(f"  Total repetitions   : {self.total_reps}")
        lines.append(f"  Good repetitions    : {self.good_reps}")
        lines.append(f"  Bad repetitions     : {self.bad_reps}")
        rate = (self.good_reps / self.total_reps * 100) if self.total_reps else 0.0
        lines.append(f"  Success rate        : {rate:.1f}%")

        # Repetition Details
        lines.append("")
        lines.append("Repetition Details")
        lines.append("-" * 18)
        if not self.history:
            lines.append("  (no repetitions completed)")
        for rep in self.history:
            status = "GOOD" if rep.good else "BAD"
            n = len(rep.violations)
            suffix = f"   ({n} violation{'s' if n != 1 else ''})" if not rep.good else ""
            lines.append(f"Rep #{rep.number:<3} {status}{suffix}")

        # Violation Details (BAD reps only)
        bad_reps = [r for r in self.history if not r.good]
        if bad_reps:
            lines.append("")
            lines.append("Violation Details")
            lines.append("-" * 17)
            for rep in bad_reps:
                lines.append("")
                lines.append(f"Rep #{rep.number}")
                lines.append("")
                for v in rep.violations:
                    lines.append(f"  - {v.rule_name}")
                    lines.append(f"    Severity : {v.severity.upper()}")
                    lines.append(f"    Message  : {v.message}")
                    lines.append("")

        # Overall Error Statistics
        lines.append("")
        lines.append("Most Common Violations")
        lines.append("-" * 23)
        counts = Counter(v.rule_name for r in self.history for v in r.violations)
        if not counts:
            lines.append("  (none)")
        else:
            label_width = 23
            for name, count in counts.most_common():
                dots = "." * max(1, label_width - len(name))
                lines.append(f"  {name} {dots} {count}")

        # Legacy one-line summary (kept for compatibility)
        lines.append("")
        lines.append(self.summary())

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.session_report()

    # -- internal --------------------------------------------------------
    def _reset_current(self) -> None:
        self._violations: Dict[str, ValidationResult] = {}
        self._start_frame: Optional[int] = None
        self._evaluations: Dict[str, ValidationResult] = {}
```

---

### FILE: [backend/src/services/video_source.py](backend/src/services/video_source.py)

```py
"""Video-source resolution & diagnostics for engine runs.

This module is the single source of truth for *how* a run locates its input.
It is shared by the desktop CLI (``src.main``), the engine orchestrator
(:class:`~src.services.gym_engine.GymEngine`) and the WebSocket live runner
(``src.server.live_runner``) so that all three report **identical, actionable
errors** instead of a bare ``Cannot open video source`` traceback.

Path resolution order for a user-supplied video argument
--------------------------------------------------------
1. **as given** — an absolute path, or a path relative to the current working
   directory (preserves the historic "path relative to where you launched the
   CLI" behaviour);
2. **inside the project videos directory** — ``assets/videos/<arg>`` (covers
   ``videos/x.mp4``-style arguments);
3. **by file name** — ``assets/videos/<name>`` (covers bare names such as
   ``hackw.mp4`` and stale ``assets/videos/x.mp4``-style arguments).

The first existing candidate wins. If none exists, callers raise
:class:`VideoSourceError` (or print :func:`diagnose_video_error` directly) with
every tried path plus a live overview of what *is* inside ``assets/videos/``.

The module performs **no OpenCV import at module level** (only inside
:func:`open_capture`), so the pure-path helpers stay importable in environments
without OpenCV — e.g. the unit-test sandbox.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Union

from ..config.app_settings import VIDEOS_DIR

PathLike = Union[str, Path]

# Candidate source of the BlazePose landmarker model, surfaced to the user
# when MODEL_PATH points at a file that does not exist.
MODEL_ZOO_URL = (
    "https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models"
)


class VideoSourceError(RuntimeError):
    """Raised when no usable video source (file or webcam) can be opened.

    Subclasses :class:`RuntimeError` for backward compatibility: callers that
    caught the engine's historical ``RuntimeError("Cannot open video source")``
    keep working. The string form of the exception is a complete, human
    actionable diagnosis (paths tried, directory contents, how to fix).
    """


# ---------------------------------------------------------------------------
# Path resolution (pure — no OpenCV required)
# ---------------------------------------------------------------------------
def _resolution_candidates(arg: PathLike, videos_dir: Path) -> List[Path]:
    """Return the ordered, de-duplicated candidate paths for ``arg``."""
    p = Path(arg)
    candidates: List[Path] = []

    def add(path: Path) -> None:
        if path not in candidates:
            candidates.append(path)

    if p.is_absolute():
        add(p)
    else:
        add(Path.cwd() / p)          # 1. as given, relative to the launch CWD
        add(videos_dir / p)          # 2. inside the project videos directory
        if p.name != str(p):         # 3. by bare file name
            add(videos_dir / p.name)
    return candidates


def resolve_video_path(arg: PathLike, videos_dir: Path = VIDEOS_DIR) -> Optional[Path]:
    """Resolve a user-supplied video argument to an existing file.

    Returns the first existing candidate per the documented resolution order,
    or ``None`` when no candidate exists on disk.
    """
    for candidate in _resolution_candidates(arg, videos_dir):
        if candidate.is_file():
            return candidate
    return None


def _videos_dir_overview(videos_dir: Path, limit: int = 10) -> str:
    """Human-readable summary of the project videos directory's contents."""
    if not videos_dir.is_dir():
        return (
            f"The project videos directory does not exist: {videos_dir}\n"
            f"Create it (mkdir -p {videos_dir}) and drop your clips there."
        )
    names = sorted(p.name for p in videos_dir.iterdir() if p.is_file())
    if not names:
        return f"The project videos directory ({videos_dir}) exists but is empty."
    shown = "\n".join(f"  {n}" for n in names[:limit])
    extra = f"\n  … and {len(names) - limit} more" if len(names) > limit else ""
    return f"The project videos directory ({videos_dir}) currently contains:\n{shown}{extra}"


def diagnose_video_error(arg: Optional[PathLike], videos_dir: Path = VIDEOS_DIR) -> str:
    """Build the full actionable message for an unresolvable/missing source."""
    if arg is None or str(arg).strip() == "":
        return (
            "No video source configured.\n\n"
            "Provide one of:\n"
            f"  • a video file:  python -m src.main <exercise> <file>\n"
            f"                   (bare names are looked up in {videos_dir})\n"
            "  • VIDEO_PATH:    set it in backend/.env\n"
            "  • the webcam:    USE_WEBCAM=true in backend/.env,\n"
            "                   or the 'c' flag: python -m src.main <exercise> c"
        )

    tried = "\n".join(f"  - {c}" for c in _resolution_candidates(arg, videos_dir))
    return (
        f"Video file not found: {arg}\n\n"
        f"Tried:\n{tried}\n\n"
        f"{_videos_dir_overview(videos_dir)}\n\n"
        "Fix it by either:\n"
        f"  • placing the file at {videos_dir / Path(arg).name}\n"
        "  • passing a path that exists:  python -m src.main <exercise> <path-to-video>\n"
        "  • setting VIDEO_PATH in backend/.env\n"
        "  • using the webcam instead:    python -m src.main <exercise> c"
    )


def diagnose_model_error(model_path: PathLike) -> str:
    """Build the actionable message for a missing pose-model file."""
    return (
        f"Pose model file not found: {model_path}\n\n"
        "Download a BlazePose pose-landmarker .task model and place it at that "
        f"path — see the MediaPipe model zoo:\n  {MODEL_ZOO_URL}\n"
        "then point MODEL_PATH at it (backend/.env)."
    )


def _diagnose_undecodable(path: Path) -> str:
    """Message for a file that exists but OpenCV fails to open."""
    size = path.stat().st_size
    human = f"{size / 1e6:.1f} MB" if size >= 1e6 else f"{size / 1e3:.1f} KB"
    return (
        f"Video file exists but OpenCV could not decode it: {path} ({human})\n\n"
        "The file is corrupted or uses a codec this OpenCV build cannot read "
        "(e.g. HEVC/AV1 in some builds). Re-encode to H.264:\n"
        f"  ffmpeg -i {path.name} -c:v libx264 -pix_fmt yuv420p fixed_{path.name}"
    )


def _diagnose_webcam(index: int) -> str:
    """Message for an unopenable webcam."""
    return (
        f"Cannot open webcam at index {index}.\n\n"
        "Check that a camera is connected, is not held by another application, "
        "and that the OS grants camera permission. Adjust WEBCAM_INDEX in "
        "backend/.env, or use a video file instead (USE_WEBCAM=false + "
        "VIDEO_PATH / CLI argument)."
    )


# ---------------------------------------------------------------------------
# Source acquisition (OpenCV imported lazily)
# ---------------------------------------------------------------------------
def open_capture(
    *,
    video_path: Optional[PathLike] = None,
    use_webcam: bool = False,
    webcam_index: int = 0,
    frame_size: Optional[Tuple[int, int]] = (1280, 720),
    videos_dir: Path = VIDEOS_DIR,
):
    """Open an already-*opened* ``cv2.VideoCapture`` for a run.

    ``video_path`` arguments are resolved via :func:`resolve_video_path`, so
    bare file names are looked up in the project videos directory. On any
    failure a :class:`VideoSourceError` carrying the full diagnosis is raised
    instead of returning a silently-closed capture.

    ``cv2`` is imported lazily so the pure-path helpers above remain usable
    without OpenCV installed.
    """
    import cv2

    if use_webcam:
        cap = cv2.VideoCapture(webcam_index)
        if frame_size is not None:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_size[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_size[1])
        if not cap.isOpened():
            cap.release()
            raise VideoSourceError(_diagnose_webcam(webcam_index))
        return cap

    if video_path is None or str(video_path).strip() == "":
        raise VideoSourceError(diagnose_video_error(None, videos_dir))

    resolved = resolve_video_path(video_path, videos_dir)
    if resolved is None:
        raise VideoSourceError(diagnose_video_error(video_path, videos_dir))

    cap = cv2.VideoCapture(str(resolved))
    if not cap.isOpened():
        cap.release()
        raise VideoSourceError(_diagnose_undecodable(resolved))
    return cap
```

---

### FILE: [backend/src/utils/__init__.py](backend/src/utils/__init__.py)

```py
from .geometry import calc_angle, get_points
from .render import draw_angle_arc
```

---

### FILE: [backend/src/utils/camera_side.py](backend/src/utils/camera_side.py)

```py
import dataclasses

class CameraSideDetector:
    def __init__(self, target_frames: int = 30):
        self.target_frames = target_frames
        self.frame_count = 0
        self.left_vis_sum = 0.0
        self.right_vis_sum = 0.0
        self.detected_side = None

    def process_frame(self, landmarks) -> str | None:
        if self.detected_side is not None:
            return self.detected_side

        left_joints = [11, 13, 15, 23, 25, 27]
        right_joints = [12, 14, 16, 24, 26, 28]

        l_vis = sum(landmarks[i].visibility for i in left_joints) / len(left_joints)
        r_vis = sum(landmarks[i].visibility for i in right_joints) / len(right_joints)

        self.left_vis_sum += l_vis
        self.right_vis_sum += r_vis
        self.frame_count += 1

        if self.frame_count >= self.target_frames:
            if self.left_vis_sum > self.right_vis_sum:
                self.detected_side = "left"
            else:
                self.detected_side = "right"
            return self.detected_side

        return None


def normalize_name(name: str) -> str:
    for suffix in ["_left", "_right", "_l", "_r"]:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def get_joints_side(joints) -> str:
    left_count = sum(1 for j in joints if j >= 7 and j <= 32 and j % 2 != 0)
    right_count = sum(1 for j in joints if j >= 7 and j <= 32 and j % 2 == 0)
    if left_count > right_count:
        return "left"
    elif right_count > left_count:
        return "right"
    return "both"


# Landmark-group fields a rule may carry: an angle triplet (angle-style
# rules) or measurement/reference pairs (DistanceValidationRule).
_LANDMARK_FIELDS = ("joints", "measurement", "reference")


def _rule_landmarks(rule) -> tuple[int, ...]:
    """All BlazePose landmark indices referenced by a rule, whatever its shape."""
    indices: list[int] = []
    for field in _LANDMARK_FIELDS:
        value = getattr(rule, field, None)
        if value is None:
            continue
        indices.extend(value if isinstance(value, (tuple, list)) else (value,))
    return tuple(indices)


def _flip_index(j: int, target_side: str) -> int:
    """Mirror a single landmark index onto ``target_side`` (L/R swap)."""
    if 7 <= j <= 32:
        is_odd = (j % 2 != 0)
        if target_side == "left" and not is_odd:
            return j - 1
        if target_side == "right" and is_odd:
            return j + 1
    return j


def adapt_rules(rules, target_side: str):
    adapted = []
    target_side_normalized_names = set()
    for rule in rules:
        side = get_joints_side(_rule_landmarks(rule))
        if side == target_side:
            target_side_normalized_names.add(normalize_name(rule.name))

    for rule in rules:
        side = get_joints_side(_rule_landmarks(rule))
        if side == target_side or side == "both":
            adapted.append(rule)
        elif side != "both":
            norm_name = normalize_name(rule.name)
            if norm_name not in target_side_normalized_names:
                remapped = {}
                for field in _LANDMARK_FIELDS:
                    value = getattr(rule, field, None)
                    if value is None:
                        continue
                    if isinstance(value, (tuple, list)):
                        remapped[field] = tuple(_flip_index(j, target_side) for j in value)
                    else:
                        remapped[field] = _flip_index(value, target_side)
                new_rule = dataclasses.replace(rule, **remapped)
                adapted.append(new_rule)
    return adapted
```

---

### FILE: [backend/src/utils/geometry.py](backend/src/utils/geometry.py)

```py
import math
from dataclasses import dataclass


@dataclass
class ComputedAngle:
    """One computed angle, ready for the renderer to draw.

    This is the single contract between the analysis layer and the rendering
    layer: ``GymEngine`` produces one ``ComputedAngle`` per ``AngleCounterRule`` and
    per ``AngleValidationRule``, and the renderer iterates over them without knowing
    which exercise or rule produced them. Adding a rule (or a whole new
    exercise) therefore needs zero renderer changes.
    """

    name: str
    vertex: tuple          # pixel (x, y) of the middle/vertex joint
    angle: float | None   # None when the angle could not be computed
    is_error: bool         # True -> draw with the error colour


def calc_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag1 = math.hypot(*ba)
    mag2 = math.hypot(*bc)

    if mag1 == 0 or mag2 == 0:
        # Degenerate geometry (overlapping joints) -> angle is undefined.
        return None

    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_theta))


def get_points(indices, landmarks, w, h, threshold: float = 0.5):
    pts = []
    for i in indices:
        lm = landmarks[i]
        if hasattr(lm, "visibility") and lm.visibility < threshold:
            continue
        pts.append((int(lm.x * w), int(lm.y * h)))
    return pts


def calc_distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])
```

---

### FILE: [backend/src/utils/render.py](backend/src/utils/render.py)

```py
import functools
import math

import cv2

from .geometry import ComputedAngle


# ── Stats overlay layout ────────────────────────────────────────────────────
# Centralized here (the rendering module) so these values are never scattered
# as magic numbers across the project.
STATS_MARGIN = 20          # distance from left & bottom frame edges (px)
STATS_PADDING = 10         # inner padding inside the box (px)
STATS_LINE_HEIGHT = 25     # vertical space reserved per text line (px)
STATS_FONT = cv2.FONT_HERSHEY_SIMPLEX
STATS_FONT_SCALE = 0.6
STATS_THICKNESS = 2
STATS_BG_ALPHA = 0.5       # opacity of the semi-transparent background


def draw_skeleton(frame, pts, colors, is_bad=False, custom_color=None):
    if len(pts) < 3:
        return

    # Dodger-blue BGR = (235, 145, 30) -> RGB(30,145,235) bright blue
    SKEL_COLOR = (255, 255, 255)
    if custom_color is not None:
        line_color = custom_color
        point_color = custom_color
    else:
        line_color = colors.ERROR if is_bad else SKEL_COLOR
        point_color = colors.ERROR if is_bad else SKEL_COLOR

    LINE_W = 5    # thin line — exactly like the reference image
    RADIUS = 12   # circle radius slightly bigger than line width
    BORDER_W = 8    # circle border — same weight as the lines

    def _edge_point(src, dst, r):
        """Point on the edge of the circle at *src* facing *dst*.
        Lines are drawn FROM here so they never cross into the circle."""
        dx, dy = dst[0] - src[0], dst[1] - src[1]
        dist = math.hypot(dx, dy)
        if dist < 1:
            return src
        return (int(src[0] + dx / dist * r),
                int(src[1] + dy / dist * r))

    p0, p1, p2 = pts[0], pts[1], pts[2]

    # ① Lines drawn FIRST — sit behind the circles
    cv2.line(frame,
             _edge_point(p0, p1, RADIUS), _edge_point(p1, p0, RADIUS),
             line_color, LINE_W, cv2.LINE_AA)
    cv2.line(frame,
             _edge_point(p1, p2, RADIUS), _edge_point(p2, p1, RADIUS),
             line_color, LINE_W, cv2.LINE_AA)

    # ② Hollow circles drawn LAST — always on top, clean edges, never filled
    for p in pts:
        cv2.circle(frame, p, RADIUS, point_color, BORDER_W, cv2.LINE_AA)



def draw_stats(
    frame,
    *,
    exercise_name: str,
    reps: int,
    good_reps: int,
    bad_reps: int,
    current_rep: str,
    stage: str,
    angle: float | None,
    feedback: list[str] | None = None,
    colors,
):
    """Draw the stats / coaching overlay in the bottom-left corner.

    The box is positioned with a small margin from the left and bottom edges
    and is clamped so it always stays fully inside the frame, regardless of
    resolution. It is intentionally NOT anchored to any body landmark — its
    position is fixed on screen.

    Core lines: exercise name, Total/Good/Bad reps, Current Rep quality, Stage,
    and Current Angle. Exercise-specific feedback (validation cues) is appended
    below.

    ``reps`` is the total completed-repetition count; ``good_reps`` /
    ``bad_reps`` split it by quality; ``current_rep`` shows the quality of the
    last *completed* repetition ("GOOD" / "BAD" / "—" before any rep finishes).
    All three counts are supplied by the caller (typically ``RepJudge``) so they
    stay consistent with the stored history.
    """
    h, w = frame.shape[:2]
    feedback = feedback or []

    lines = [
        exercise_name,
        f"Total Reps : {reps}",
        f"Good Reps  : {good_reps}",
        f"Bad Reps   : {bad_reps}",
        f"Current Rep: {current_rep}",
        f"Stage      : {stage}",
        f"Angle      : {int(angle)} deg" if angle is not None else "Angle: N/A",
    ]
    # Exercise-specific feedback below the core information.
    for msg in feedback:
        lines.append(f"- {msg}")

    def line_color(text: str):
        if text.startswith("- "):
            return colors.ERROR
        if text.startswith("Current Rep:"):
            return colors.ERROR if "BAD" in text else colors.HIGHLIGHT
        return colors.TEXT

    # Measure the box from the actual text.
    sizes = [
        cv2.getTextSize(t, STATS_FONT, STATS_FONT_SCALE, STATS_THICKNESS)[0]
        for t in lines
    ]
    box_width = max(s[0] for s in sizes) + STATS_PADDING * 2
    box_height = len(lines) * STATS_LINE_HEIGHT + STATS_PADDING * 2

    # Bottom-left, then clamp so the whole box stays on screen.
    box_x = STATS_MARGIN
    box_y = h - STATS_MARGIN - box_height
    box_x = max(STATS_MARGIN, min(box_x, w - STATS_MARGIN - box_width))
    box_y = max(STATS_MARGIN, min(box_y, h - STATS_MARGIN - box_height))

    # Semi-transparent background (readable on both dark and bright frames).
    overlay = frame.copy()
    cv2.rectangle(overlay, (box_x, box_y), (box_x + box_width, box_y + box_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, STATS_BG_ALPHA, frame, 1 - STATS_BG_ALPHA, 0, frame)

    for i, text in enumerate(lines):
        cv2.putText(
            frame, text,
            (box_x + STATS_PADDING, box_y + STATS_PADDING + (i + 1) * STATS_LINE_HEIGHT - 5),
            STATS_FONT, STATS_FONT_SCALE, line_color(text), STATS_THICKNESS, cv2.LINE_AA,
        )


# ── Screen-fit display ──────────────────────────────────────────────────────
# Centralized, cross-platform helpers so frame fitting is computed in exactly
# one place (never scattered around the project). No magic numbers: the margin
# and fallback values are exposed as constants below.
SCREEN_MARGIN_RATIO = 0.05   # fraction of the screen kept as margin on each side
SCREEN_MARGIN_PX = 50        # minimum margin in pixels (wins on tiny screens)
DEFAULT_SCREEN_WIDTH = 1280  # fallback if the screen size can't be detected
DEFAULT_SCREEN_HEIGHT = 720


@functools.lru_cache(maxsize=1)
def get_screen_size():
    """Return the primary screen ``(width, height)`` in pixels.

    Cached with :func:`functools.lru_cache` so detection runs **only once**.
    Uses Tkinter (part of the Python stdlib, available on Windows / Linux /
    macOS). Falls back to :data:`DEFAULT_SCREEN_WIDTH` x
    :data:`DEFAULT_SCREEN_HEIGHT` when no display/GUI is reachable.
    """
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()          # avoid flashing a window
        root.update_idletasks()  # ensure geometry is computed
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.destroy()
        if w > 0 and h > 0:
            return (w, h)
    except Exception:
        pass
    return (DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)


def fit_to_screen(frame, max_width=None,
                  margin_ratio=SCREEN_MARGIN_RATIO, margin_px=SCREEN_MARGIN_PX):
    """Resize ``frame`` to fit the screen while preserving aspect ratio.

    Behaviour:
    * Only **downscales** — small videos are never upscaled (scale capped at 1).
    * Respects a margin so the window never touches the screen edges.
    * ``max_width`` (optional) adds an extra maximum-width cap on top of the
      screen fit (e.g. the ``DISPLAY_MAX_WIDTH`` setting).
    * The returned frame is for **display only**; pose math and video recording
      continue to use the original-resolution frame.

    Returns the original ``frame`` unchanged when no downscaling is needed.
    """
    screen_w, screen_h = get_screen_size()
    margin_x = max(int(screen_w * margin_ratio), margin_px)
    margin_y = max(int(screen_h * margin_ratio), margin_px)
    avail_w = max(1, screen_w - 2 * margin_x)
    avail_h = max(1, screen_h - 2 * margin_y)

    h, w = frame.shape[:2]
    caps = [avail_w / w, avail_h / h, 1.0]   # 1.0 => never upscale
    if max_width is not None:
        caps.append(max_width / w)
    scale = min(caps)

    if scale >= 1.0:
        return frame
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def draw_angle_arc(frame, a, b, c, colors, is_bad=False, radius=20):
    """Draw the visual angle arc at point B between BA and BC.

    The arc radius is set LARGER than the skeleton circle (RADIUS=22) so the
    arc appears clearly OUTSIDE the joint circle — never overlapping it.
    Only the arc is drawn here; the numeric label is rendered by draw_angle_labels.
    """
    # Arc must be bigger than the skeleton circle radius (22px) to sit outside it
    ARC_RADIUS = 42   # clearly outside the 22px skeleton circle

    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    angle1 = math.degrees(math.atan2(ba[1], ba[0]))
    angle2 = math.degrees(math.atan2(bc[1], bc[0]))

    start_angle = int(angle1)
    end_angle   = int(angle2)

    # Always draw the smallest arc (the actual angle, not the reflex)
    if end_angle < start_angle:
        end_angle += 360
    if end_angle - start_angle > 180:
        start_angle, end_angle = end_angle, start_angle + 360

    color = colors.ERROR if is_bad else colors.HIGHLIGHT

    cv2.ellipse(frame, b, (ARC_RADIUS, ARC_RADIUS),
                0, start_angle, end_angle, color, 2, cv2.LINE_AA)


# ── Floating angle-label layout ──────────────────────────────────────────────
# Centralized so these values are not scattered as magic numbers across files.
ANGLE_FONT = cv2.FONT_HERSHEY_SIMPLEX
ANGLE_BASE_SCALE = 0.9      # font scale at a 1280px-wide frame (see _scale)
ANGLE_PADDING = 6           # inner padding of the label box (px)
ANGLE_OFFSET = 14           # push the label away from the joint (px)
ANGLE_BG_ALPHA = 0.65       # opacity of the semi-transparent backing
ANGLE_MIN_SCALE = 0.7
ANGLE_MAX_SCALE = 2.0


def _angle_scale(width: int) -> float:
    """Keep on-screen label size constant regardless of source resolution.

    The frame is later resized to ``display_width`` (1280) before display, so
    scaling the font by the *source* width makes the final on-screen size
    resolution-independent.
    """
    return max(ANGLE_MIN_SCALE, min(ANGLE_MAX_SCALE, width / 1280.0))


def draw_angle_labels(frame, views: list[ComputedAngle], colors, width: int, height: int):
    """Draw a small floating angle box for EVERY computed angle.

    ``views`` already contains one entry per AngleCounterRule and per
    AngleValidationRule (built by GymEngine.analyze), so this function is completely
    exercise/rule-agnostic: add a rule or a whole new exercise and the labels
    appear automatically with no change here.

    Colour: highlight for normal angles and counter rules; error for failed
    validation. Each label sits at the rule's vertex joint (so it tracks the
    person) with a small offset so it doesn't cover the joint.
    """
    scale = _angle_scale(width)
    font_scale = ANGLE_BASE_SCALE * scale
    thickness = max(1, round(2 * scale))
    padding = round(ANGLE_PADDING * scale)
    offset = round(ANGLE_OFFSET * scale)
    border = max(1, round(2 * scale))

    for v in views:
        # Don't show N/A label when angle couldn't be computed
        if v.angle is None:
            continue
        color = colors.ERROR if v.is_error else colors.HIGHLIGHT
        text = f"{int(round(v.angle))} deg"

        (tw, th), _ = cv2.getTextSize(text, ANGLE_FONT, font_scale, thickness)
        box_w = tw + padding * 2
        box_h = th + padding * 2

        # Anchor up-and-right of the vertex so the box clears the joint.
        bx = v.vertex[0] + offset
        by = v.vertex[1] - offset - box_h
        # Keep the whole label on screen.
        bx = max(0, min(bx, width - box_w))
        by = max(0, min(by, height - box_h))

        # Dark, semi-transparent backing -> readable on light or dark frames.
        overlay = frame.copy()
        cv2.rectangle(overlay, (bx, by), (bx + box_w, by + box_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, ANGLE_BG_ALPHA, frame, 1 - ANGLE_BG_ALPHA, 0, frame)

        # State colour on the border + text (project palette).
        cv2.rectangle(frame, (bx, by), (bx + box_w, by + box_h), color, border)
        cv2.putText(
            frame, text, (bx + padding, by + padding + th),
            ANGLE_FONT, font_scale, color, thickness, cv2.LINE_AA,
        )


def draw_segment_line(frame, pt1, pt2, colors, custom_color=None):
    """Draw a straight line between two pixel points.

    Generic rendering primitive backing DisplaySettings.segment_lines
    (e.g. the wrist-to-wrist line at the top of a shoulder press).
    """
    line_color = custom_color if custom_color is not None else colors.HIGHLIGHT
    cv2.line(frame, pt1, pt2, line_color, 3, cv2.LINE_AA)


# Back-compat alias (older name; the helper is generic, not wrist-specific).
def draw_wrist_line(frame, left_wrist, right_wrist, colors, custom_color=None):
    draw_segment_line(frame, left_wrist, right_wrist, colors, custom_color)
```

---

### FILE: [backend/src/__init__.py](backend/src/__init__.py)

```py

```

---

### FILE: [backend/src/main.py](backend/src/main.py)

```py
"""AI Gym Trainer — entry point.

Usage
-----
  python -m src.main                               # uses .env defaults
  python -m src.main deadlift                      # deadlift, video from .env
  python -m src.main deadlift Deadlift3.mp4        # bare name: assets/videos/
  python -m src.main cable_chest_fly /path/Chest.mp4   # explicit path
  python -m src.main hack_squat leg.mp4            # hack squat + video
  python -m src.main hack_squat c                  # webcam ('s' saves output)

Video arguments are resolved in order: as given (relative to the launch
directory), inside ``assets/videos/``, then by bare file name inside
``assets/videos/``. A missing video or pose model aborts with an actionable
message (paths tried, directory contents, how to fix) — no traceback.

Available exercises
-------------------
  deadlift  cable_chest_fly  squat  pushup
  biceps_curl  lat_pulldown  leg_press  shoulder_press  hack_squat
"""

import sys
from pathlib import Path

from .config import settings
from .core.colors import Colors
from .exercises.registry import registry
from .services.gym_engine import GymEngine
from .services.video_source import (
    VideoSourceError,
    diagnose_model_error,
    diagnose_video_error,
    resolve_video_path,
)

DEFAULT_EXERCISE = "cable_chest_fly"


def main():
    args = sys.argv[1:]

    exercise_key = args[0].lower() if len(args) >= 1 else None

    # Parse CLI flags: 'c' for webcam, 's' for saving output
    lower_args = [arg.lower() for arg in args[1:]]
    save_flag = "s" in lower_args
    settings.SAVE_OUTPUT = save_flag

    use_webcam_flag = "c" in lower_args
    if use_webcam_flag:
        settings.USE_WEBCAM = True
        video_path = None
    else:
        remaining_args = [arg for arg in args[1:] if arg.lower() not in ("s", "c")]
        video_path = remaining_args[0] if remaining_args else None

    # The CLI simply asks the registry for an exercise — it knows nothing about
    # which exercises exist. GymEngine stays completely unaware of the registry.
    if exercise_key and not registry.exists(exercise_key):
        print(f"Unknown exercise '{exercise_key}'.")
        print(f"Available: {', '.join(registry.list())}")
        sys.exit(1)

    exercise = (
        registry.get(exercise_key) if exercise_key else registry.get(DEFAULT_EXERCISE)
    )

    # ── Preflight: fail fast with an actionable message, not a traceback ────
    # (Resolution shared with the engine and the live server: video_source.)
    if not settings.USE_WEBCAM:
        source_arg = video_path or settings.VIDEO_PATH
        resolved = resolve_video_path(source_arg) if source_arg else None
        if resolved is None:
            print(diagnose_video_error(source_arg))
            sys.exit(2)
        video_path = str(resolved)

    if not Path(settings.MODEL_PATH).is_file():
        print(diagnose_model_error(settings.MODEL_PATH))
        sys.exit(2)

    try:
        GymEngine(
            exercise,
            colors=Colors(),
            display_width=settings.DISPLAY_MAX_WIDTH,
        ).run(video_path=video_path)
    except VideoSourceError as exc:
        # File existed at preflight but could not be opened (e.g. undecodable
        # codec) — same clean, actionable output, no traceback.
        print(exc)
        sys.exit(2)


if __name__ == "__main__":
    main()
```

---

### FILE: [backend/tests/test_architecture.py](backend/tests/test_architecture.py)

```py
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
```

---

### FILE: [backend/tests/test_distance_handling.py](backend/tests/test_distance_handling.py)

```py
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
```

---

### FILE: [backend/tests/test_hack_squat.py](backend/tests/test_hack_squat.py)

```py
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
```

---

### FILE: [backend/tests/test_session_report.py](backend/tests/test_session_report.py)

```py
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
```

---

### FILE: [backend/tests/test_video_source.py](backend/tests/test_video_source.py)

```py
"""Video-source resolution & diagnostics verification.

Covers ``src/services/video_source.py`` — the shared source-acquisition layer
used by the CLI (``src.main``), ``GymEngine.run`` and the WebSocket live
runner:

  1. Resolution order: as-given (cwd) → videos_dir/<arg> → videos_dir/<name>.
  2. Missing inputs yield ``None`` from resolve_video_path, not exceptions.
  3. ``VideoSourceError`` is a ``RuntimeError`` (backward-compatible catching).
  4. Diagnosis messages name every tried path, describe the real contents of
     the videos directory, and suggest actionable fixes (file/.env/webcam).
  5. ``open_capture`` raises actionable errors for: no source, missing file,
     undecodable file, unopenable webcam — and returns an *opened* capture,
     applying the frame size, on success.

Run from backend/:  python tests/test_video_source.py
"""

import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/

os.environ.setdefault("MODEL_PATH", "assets/models/pose_landmarker_lite.task")

# ── Stub mediapipe (importing src.services pulls in gym_engine → pose_service)
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

import shutil
import tempfile

from src.services.video_source import (
    VideoSourceError,
    diagnose_model_error,
    diagnose_video_error,
    open_capture,
    resolve_video_path,
)

try:
    import cv2
except ImportError:  # pragma: no cover - OpenCV optional for part of the suite
    cv2 = None


class FakeCap:
    """Minimal cv2.VideoCapture stand-in for the webcam tests."""
    instances = []

    def __init__(self, opened):
        self._opened = opened
        self.released = False
        self.sets = []
        FakeCap.instances.append(self)

    def set(self, prop, value):
        self.sets.append((prop, value))

    def isOpened(self):
        return self._opened

    def release(self):
        self.released = True


def _fake_cv2(cap: FakeCap) -> types.ModuleType:
    mod = types.ModuleType("cv2")
    mod.VideoCapture = lambda *_a, **_k: cap
    mod.CAP_PROP_FRAME_WIDTH = 3
    mod.CAP_PROP_FRAME_HEIGHT = 4
    return mod


def expect_raises(exc_type, fn, needle=None):
    try:
        fn()
    except exc_type as exc:
        if needle is not None:
            assert needle.lower() in str(exc).lower(), f"missing {needle!r} in:\n{exc}"
        return exc
    raise AssertionError(f"expected {exc_type.__name__}")


# --------------------------------------------------------------------------
# 1. Resolution order
# --------------------------------------------------------------------------
def test_resolution_order(tmp: Path):
    cwd_dir = tmp / "cwd"
    videos = tmp / "videos"
    cwd_file = cwd_dir / "clip.mp4"
    vid_file = videos / "clip.mp4"
    cwd_dir.mkdir(parents=True)
    videos.mkdir()
    cwd_file.write_bytes(b"cwd")
    vid_file.write_bytes(b"videos")

    old_cwd = os.getcwd()
    os.chdir(cwd_dir)
    try:
        # absolute path: returned verbatim
        assert resolve_video_path(str(vid_file), videos) == vid_file
        # as-given (cwd) beats the videos directory
        assert resolve_video_path("clip.mp4", videos) == cwd_file
        # videos_dir/<arg> step: argument with a directory part
        nested = videos / "sessions"
        nested.mkdir()
        (nested / "s.mp4").write_bytes(b"x")
        assert resolve_video_path("sessions/s.mp4", videos) == nested / "s.mp4"
    finally:
        os.chdir(old_cwd)

    # name fallback: stale 'assets/videos/x.mp4'-style argument
    stale_arg = "assets/videos/clip.mp4"
    # (videos/assets/videos/clip.mp4 must NOT exist for the name step to win)
    assert resolve_video_path(stale_arg, videos) == vid_file

    # nothing exists → None (and an absolute miss does not scan videos_dir)
    assert resolve_video_path("nope.mp4", videos) is None
    assert resolve_video_path(str(tmp / "abs" / "nope.mp4"), videos) is None
    print("1. resolution order: OK")


# --------------------------------------------------------------------------
# 2. Error type compatibility
# --------------------------------------------------------------------------
def test_error_type():
    assert issubclass(VideoSourceError, RuntimeError)
    print("2. VideoSourceError is a RuntimeError: OK")


# --------------------------------------------------------------------------
# 3. Diagnosis messages
# --------------------------------------------------------------------------
def test_diagnoses(tmp: Path):
    videos = tmp / "videos"

    # no source configured
    msg = diagnose_video_error(None, videos)
    assert "No video source configured" in msg
    for needle in ("VIDEO_PATH", "USE_WEBCAM", "src.main <exercise> c"):
        assert needle in msg, needle

    # missing file → tried paths + directory overview + fixes
    videos.mkdir(parents=True)
    (videos / "demo.mp4").write_bytes(b"x")
    arg = tmp / "missing.mp4"
    msg = diagnose_video_error(str(arg), videos)
    assert f"Video file not found: {arg}" in msg
    assert f"  - {arg}" in msg                      # tried path listed
    assert "demo.mp4" in msg                         # real contents shown
    assert str(videos / arg.name) in msg             # 'place the file at' fix
    for needle in ("VIDEO_PATH", "backend/.env", "webcam"):
        assert needle in msg, needle

    # missing directory overview
    gone = tmp / "gone"
    msg = diagnose_video_error("x.mp4", gone)
    assert f"does not exist: {gone}" in msg
    assert "mkdir" in msg

    # relative argument also lists the videos_dir/<name> candidate
    vids2 = tmp / "vids2"
    msg = diagnose_video_error("assets/videos/x.mp4", vids2)
    assert str(vids2 / "x.mp4") in msg

    # model error
    msg = diagnose_model_error(tmp / "models" / "pose.task")
    assert f"Pose model file not found: {tmp / 'models' / 'pose.task'}" in msg
    assert "MODEL_PATH" in msg and "http" in msg
    print("3. diagnosis messages: OK")


# --------------------------------------------------------------------------
# 4. open_capture failure modes (+ successful acquisition when OpenCV exists)
# --------------------------------------------------------------------------
def test_open_capture(tmp: Path):
    videos = tmp / "videos"
    videos.mkdir(parents=True)

    # no source at all
    expect_raises(VideoSourceError, lambda: open_capture(), "No video source")
    expect_raises(
        VideoSourceError,
        lambda: open_capture(video_path=""),
        "No video source",
    )
    # missing file
    expect_raises(
        VideoSourceError,
        lambda: open_capture(video_path="ghost.mp4", videos_dir=videos),
        "not found",
    )

    if cv2 is None:
        print("4. open_capture failures: OK  (cv2 absent — success paths skipped)")
        test_webcam(FakeCap(False))
        return

    # undecodable file: exists, but OpenCV can't open it
    junk = videos / "broken.mp4"
    junk.write_bytes(os.urandom(4096))
    expect_raises(
        VideoSourceError,
        lambda: open_capture(video_path=str(junk)),
        "could not decode",
    )

    # successful acquisition: bare name resolved via videos_dir, capture opened
    clip = _write_clip(videos / "clip.mp4")
    if clip is None:
        print("4. open_capture failures: OK  (mp4v writer unavailable — e2e skipped)")
    else:
        cap = open_capture(video_path="clip.mp4", videos_dir=videos)
        assert cap.isOpened()
        ok, frame = cap.read()
        assert ok and frame is not None and frame.shape[2] == 3
        cap.release()
        print("4. open_capture: failures + real-clip acquisition: OK")

    test_webcam(FakeCap(False))


def _write_clip(path: Path):
    """Write a tiny readable mp4v clip; None when the codec is unavailable."""
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"mp4v"), 25.0, (64, 48)
    )
    if not writer.isOpened():
        writer.release()
        return None
    import numpy as np

    frame = np.zeros((48, 64, 3), dtype="uint8")
    for _ in range(3):
        writer.write(frame)
    writer.release()
    return path


# --------------------------------------------------------------------------
# 5. Webcam diagnostics via a stubbed cv2 (no hardware required)
# --------------------------------------------------------------------------
def test_webcam(cap: FakeCap):
    real = sys.modules.get("cv2")
    sys.modules["cv2"] = _fake_cv2(cap)
    try:
        expect_raises(
            VideoSourceError,
            lambda: open_capture(use_webcam=True, webcam_index=3),
            "webcam at index 3",
        )
        # frame size applied before the open check, capture released after
        assert len(cap.sets) == 2
        assert cap.released is True
    finally:
        if real is not None:
            sys.modules["cv2"] = real
        else:
            del sys.modules["cv2"]
    print("5. webcam diagnostics (stubbed cv2): OK")


def main():
    tmp_root = Path(tempfile.mkdtemp(prefix="ai_gym_video_src_"))
    try:
        test_resolution_order(tmp_root / "t1")
        test_error_type()
        test_diagnoses(tmp_root / "t3")
        test_open_capture(tmp_root / "t4")
        # success-path webcam: stubbed cv2 reports an opened camera
        cap = FakeCap(True)
        real = sys.modules.get("cv2")
        sys.modules["cv2"] = _fake_cv2(cap)
        try:
            opened = open_capture(use_webcam=True, webcam_index=0, frame_size=None)
            assert opened is cap and cap.sets == []  # frame_size=None → no set()
        finally:
            if real is not None:
                sys.modules["cv2"] = real
            else:
                del sys.modules["cv2"]
        print("6. webcam success path (stubbed cv2): OK")
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    print("\nAll video_source tests passed ✔")


if __name__ == "__main__":
    main()
```

---

## EXPORT SUMMARY

- Files exported: 54
- Lines exported: 6742
