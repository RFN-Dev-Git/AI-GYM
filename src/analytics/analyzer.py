"""Compute session-level statistics from completed-repetition data.

The analyzer is deliberately decoupled from :class:`GymEngine` and performs NO
pose detection or repetition counting — it only reads the finished session
(``list[RepResult]``) and derives metrics. Pass it the data; it returns a
:class:`SessionSummary`. This keeps analytics fully independent of the
detection / counting / judging services.
"""

from collections import Counter
from datetime import datetime
from typing import Optional, Sequence

from ..services.rep_judge import RepResult
from .session_summary import SessionSummary

# Heuristic weights used to derive a per-rep "validation score" when the
# underlying data does not carry an explicit score. Higher severity -> larger
# penalty. Override via the constructor for different scoring policies.
DEFAULT_SEVERITY_WEIGHTS = {"error": 50.0, "warning": 20.0, "info": 10.0}


class SessionAnalyzer:
    """Turns a completed session's repetition history into a ``SessionSummary``."""

    def __init__(self, severity_weights: Optional[dict] = None) -> None:
        self.severity_weights = dict(severity_weights or DEFAULT_SEVERITY_WEIGHTS)

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
        total = len(results)
        good = sum(1 for r in results if r.good)
        bad = total - good
        accuracy = (good / total * 100.0) if total else 0.0

        # Per-repetition durations (seconds) from their frame spans.
        durations = [
            (r.end_frame - r.start_frame + 1) / float(fps)
            for r in results
            if r.start_frame is not None and r.end_frame is not None
        ]
        average_rep_time = (sum(durations) / len(durations)) if durations else 0.0
        fastest_rep = min(durations) if durations else 0.0
        slowest_rep = max(durations) if durations else 0.0

        # Total active workout duration: explicit value, else first->last span.
        if total_duration is not None:
            total_workout = float(total_duration)
        elif results and results[0].start_frame is not None and results[-1].end_frame is not None:
            total_workout = (results[-1].end_frame - results[0].start_frame + 1) / float(fps)
        else:
            total_workout = 0.0

        # Frequency of each failed rule, sorted by occurrence (desc) then name.
        error_counts = Counter(v.rule_name for r in results for v in r.violations)
        common_errors = dict(sorted(error_counts.items(), key=lambda kv: (-kv[1], kv[0])))
        most_common_error = error_counts.most_common(1)[0][0] if error_counts else None

        # Average validation score (0-100); None when there are no reps.
        score = None
        if total:
            score = sum(self._rep_score(r) for r in results) / total

        return SessionSummary(
            exercise=exercise_name or "",
            date=date or datetime.now().isoformat(),
            total_reps=total,
            good_reps=good,
            bad_reps=bad,
            accuracy=accuracy,
            average_rep_time=average_rep_time,
            fastest_rep=fastest_rep,
            slowest_rep=slowest_rep,
            total_workout_duration=total_workout,
            common_errors=common_errors,
            most_common_error=most_common_error,
            score=score,
        )

    def _rep_score(self, rep: RepResult) -> float:
        """Per-repetition validation score in [0, 100].

        Uses an explicit ``score`` attribute if the rep carries one (so a future
        real score wins), otherwise falls back to a severity-weighted penalty
        derived from its violations.
        """
        explicit = getattr(rep, "score", None)
        if explicit is not None:
            return float(explicit)
        penalty = sum(self.severity_weights.get(v.severity, 0.0) for v in rep.violations)
        return max(0.0, 100.0 - penalty)
