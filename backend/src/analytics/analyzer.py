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
