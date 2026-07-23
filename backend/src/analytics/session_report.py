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
        start_time:       Start time in seconds from session start (start_frame / fps)
        end_time:         End time in seconds from session start (end_frame / fps)
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
    start_time: Optional[float] = None
    end_time: Optional[float] = None
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
