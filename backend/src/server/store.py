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
