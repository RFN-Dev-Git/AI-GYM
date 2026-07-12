"""Session history writer — saves rep-by-rep results to history.json."""

import json
from datetime import datetime, timezone
from pathlib import Path

HISTORY_PATH = Path("history.json")


class HistoryWriter:
    def __init__(self, exercise_name: str, fps: float = 25.0):
        self._name = exercise_name
        self._fps = fps
        self._reps: list[dict] = []
        self._start = datetime.now(timezone.utc)

    def record(self, rep_num: int, result: str, frame_id: int, violations: list[str]):
        elapsed = frame_id / self._fps
        minutes, seconds = divmod(int(elapsed), 60)
        entry = {
            "rep": rep_num,
            "result": result,
            "time": f"{minutes:02d}:{seconds:02d}",
        }
        if violations:
            entry["violations"] = violations
        self._reps.append(entry)

    def save(self, good: int, bad: int):
        data = {
            "exercise": self._name,
            "date": self._start.strftime("%Y-%m-%dT%H:%M:%S"),
            "good": good,
            "bad": bad,
            "total": good + bad,
            "reps": self._reps,
        }
        HISTORY_PATH.write_text(json.dumps(data, indent=2))
