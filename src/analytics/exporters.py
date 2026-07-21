"""Export a :class:`SessionSummary` to JSON or CSV.

Exporters depend only on :class:`SessionSummary` — they never touch
``GymEngine``, ``RepJudge``, or any pose/counting logic. ``export(summary,
path)`` normalizes the file extension, serializes the summary, writes the file,
and returns its path. The serialized shape matches the documented example
(``exercise``, ``date``, ``total_reps``, ``good_reps``, ``bad_reps``,
``accuracy``, ``average_rep_duration``, ``most_common_error``, ...).
"""

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from .session_summary import SessionSummary


class BaseSessionExporter(ABC):
    """Common export flow: normalize the path, serialize, then write."""

    extension: str = ""

    def export(self, summary: SessionSummary, path) -> Path:
        """Write ``summary`` to ``path`` (extension corrected) and return it."""
        path = Path(path)
        if path.suffix.lower() != f".{self.extension}":
            path = path.with_suffix(f".{self.extension}")
        self._write(path, self._serialize(summary))
        return path

    @abstractmethod
    def _serialize(self, summary: SessionSummary) -> Dict[str, Any]:
        """Return a JSON/CSV-friendly dict representation of ``summary``."""

    @abstractmethod
    def _write(self, path: Path, data: Dict[str, Any]) -> None:
        """Persist ``data`` to ``path``."""


class JsonSessionExporter(BaseSessionExporter):
    """Human-readable, indented JSON export."""

    extension = "json"

    def _serialize(self, summary: SessionSummary) -> Dict[str, Any]:
        return {
            "exercise": summary.exercise,
            "date": summary.date,
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

    def _write(self, path: Path, data: Dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class CsvSessionExporter(BaseSessionExporter):
    """Single-row CSV export (one column per metric)."""

    extension = "csv"

    def _serialize(self, summary: SessionSummary) -> Dict[str, Any]:
        return {
            "exercise": summary.exercise,
            "date": summary.date or "",
            "total_reps": summary.total_reps,
            "good_reps": summary.good_reps,
            "bad_reps": summary.bad_reps,
            "accuracy": round(summary.accuracy, 1),
            "average_rep_duration": round(summary.average_rep_time, 2),
            "fastest_rep": round(summary.fastest_rep, 2),
            "slowest_rep": round(summary.slowest_rep, 2),
            "total_workout_duration": round(summary.total_workout_duration, 2),
            "common_errors": "; ".join(f"{k}:{v}" for k, v in summary.common_errors.items()),
            "most_common_error": summary.most_common_error or "",
            "score": round(summary.score, 1) if summary.score is not None else "",
        }

    def _write(self, path: Path, data: Dict[str, Any]) -> None:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(data.keys()))
            writer.writeheader()
            writer.writerow(data)
