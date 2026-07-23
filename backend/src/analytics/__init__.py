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
