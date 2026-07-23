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
