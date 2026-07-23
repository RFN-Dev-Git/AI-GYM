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
