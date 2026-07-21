# CODEBASE SNAPSHOT

## PROJECT STRUCTURE

```text
AI-GYM/
├── assets
│   ├── models
│   │   ├── pose_landmarker_full.task
│   │   └── pose_landmarker_lite.task
│   └── videos
│       ├── .gitkeep
│       ├── Chest.mp4
│       ├── Deadlift .png
│       ├── Deadlift.mp4
│       ├── Deadlift2.mp4
│       ├── Deadlift3.mp4
│       ├── hackw.mp4
│       ├── leg.mp4
│       └── leg2.mp4
├── output
│   └── sessions
│       ├── Hack_Squat_20260713_012947.json
│       └── Hack_Squat_20260713_013018.json
├── src
│   ├── analytics
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   ├── exporters.py
│   │   └── session_summary.py
│   ├── config
│   │   ├── __init__.py
│   │   └── app_settings.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── colors.py
│   │   └── pose_segments.py
│   ├── exercises
│   │   ├── leg
│   │   │   ├── __init__.py
│   │   │   ├── hack_squat.py
│   │   │   └── leg_press.py
│   │   ├── __init__.py
│   │   ├── biceps_curl.py
│   │   ├── cable_chest_fly.py
│   │   ├── deadlift.py
│   │   ├── exercise.py
│   │   ├── latpulldown.py
│   │   ├── pushup.py
│   │   ├── registry.py
│   │   ├── rules.py
│   │   ├── shoulder_press.py
│   │   ├── squat.py
│   │   └── validation.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── gym_engine.py
│   │   ├── pose_service.py
│   │   ├── rep_counter.py
│   │   └── rep_judge.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── geometry.py
│   │   └── render.py
│   ├── __init__.py
│   └── main.py
├── .env
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── codex
├── Makefile
├── README.md
└── requirements.txt
```

## SOURCE FILES

---

### FILE: [src/analytics/__init__.py](src/analytics/__init__.py)

```py
"""Session analytics: summarize and export a completed workout session.

These modules are independent of ``GymEngine`` and of any pose/counting logic —
they only consume the already-completed session data (``RepJudge.history``).
"""

from .analyzer import SessionAnalyzer
from .exporters import BaseSessionExporter, CsvSessionExporter, JsonSessionExporter
from .session_summary import SessionSummary

__all__ = [
    "SessionSummary",
    "SessionAnalyzer",
    "BaseSessionExporter",
    "JsonSessionExporter",
    "CsvSessionExporter",
]
```

---

### FILE: [src/analytics/analyzer.py](src/analytics/analyzer.py)

```py
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
```

---

### FILE: [src/analytics/exporters.py](src/analytics/exporters.py)

```py
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
```

---

### FILE: [src/analytics/session_summary.py](src/analytics/session_summary.py)

```py
"""Dataclass holding the computed statistics of one workout session.

Produced by :class:`~src.analytics.analyzer.SessionAnalyzer` and consumed by the
session exporters. All fields are plain, serializable data so a summary can be
trivially written to JSON/CSV or stored for later analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class SessionSummary:
    """Aggregated statistics for a single, completed workout session.

    Attributes:
        exercise:            Name of the exercise performed.
        date:                ISO-8601 timestamp of the session (or ``None``).
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

### FILE: [src/config/__init__.py](src/config/__init__.py)

```py
from .app_settings import (
    settings,
    PROJECT_ROOT,
    ASSETS_DIR,
    MODELS_DIR,
    VIDEOS_DIR,
    OUTPUT_DIR,
)

__all__ = [
    "settings",
    "PROJECT_ROOT",
    "ASSETS_DIR",
    "MODELS_DIR",
    "VIDEOS_DIR",
    "OUTPUT_DIR",
]
```

---

### FILE: [src/config/app_settings.py](src/config/app_settings.py)

```py
"""Application settings (pydantic-settings) with project-root-relative paths.

All filesystem paths are exposed as :class:`pathlib.Path` objects and resolved
relative to the project root, so the application behaves identically no matter
which directory it is launched from. The shared root/path constants live here
so paths are never scattered as ad-hoc strings across the codebase.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Project-root path constants ────────────────────────────────────────────
# Derived from this file's location, so they are independent of the CWD.
#   src/config/app_settings.py -> parents[2] == project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
MODELS_DIR = ASSETS_DIR / "models"
VIDEOS_DIR = ASSETS_DIR / "videos"
OUTPUT_DIR = PROJECT_ROOT / "output"


def _abs_path(path) -> Path:
    """Resolve a (possibly relative) path against the project root."""
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


class AppSettings(BaseSettings):
    # Paths are Path objects; relative strings are resolved against PROJECT_ROOT.
    MODEL_PATH: Path
    VIDEO_PATH: Optional[Path] = None

    DISPLAY_MAX_WIDTH: int = 1280

    USE_WEBCAM: bool = False
    WEBCAM_INDEX: int = 0

    SAVE_OUTPUT: bool = False
    OUTPUT_PATH: Path = OUTPUT_DIR / "result.mp4"

    # Session analytics: frame rate used to turn per-repetition frame spans
    # into durations (seconds) in the generated SessionSummary.
    ANALYTICS_FPS: float = 25.0

    # Session analytics export (opt-in). When EXPORT_SESSION is true the engine
    # persists a SessionSummary (produced by the analytics module) after a run.
    EXPORT_SESSION: bool = False
    EXPORT_FORMAT: str = "json"   # "json" | "csv"
    EXPORT_DIR: Path = PROJECT_ROOT / "sessions"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _resolve_relative_paths(self) -> "AppSettings":
        """Resolve MODEL_PATH / VIDEO_PATH / OUTPUT_PATH against PROJECT_ROOT.

        An empty VIDEO_PATH (e.g. an empty env var) is normalised to ``None``.
        """
        self.MODEL_PATH = _abs_path(self.MODEL_PATH)
        if self.VIDEO_PATH is not None:
            # An empty env value coerces to Path(".") -> treat as unset.
            if str(self.VIDEO_PATH).strip() in ("", "."):
                self.VIDEO_PATH = None
            else:
                self.VIDEO_PATH = _abs_path(self.VIDEO_PATH)
        self.OUTPUT_PATH = _abs_path(self.OUTPUT_PATH)
        self.EXPORT_DIR = _abs_path(self.EXPORT_DIR)
        return self


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


settings = get_settings()
```

---

### FILE: [src/core/__init__.py](src/core/__init__.py)

```py
from .colors import Colors
from .pose_segments import PoseSegments

__all__ = ["Colors", "PoseSegments"]
```

---

### FILE: [src/core/colors.py](src/core/colors.py)

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

### FILE: [src/core/pose_segments.py](src/core/pose_segments.py)

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
```

---

### FILE: [src/exercises/leg/__init__.py](src/exercises/leg/__init__.py)

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

### FILE: [src/exercises/leg/hack_squat.py](src/exercises/leg/hack_squat.py)

```py
"""Hack Squat exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ...core.pose_segments import PoseSegments
from ..exercise import Exercise
from ..rules import AngleCounterRule, AngleValidationRule

@dataclass
class HackSquatExercise(Exercise):
    name: str = "Hack Squat"
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                up_angle=160,
                down_angle=90,
            ),
            AngleCounterRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                up_angle=160,
                down_angle=90,
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="knee_unlocked_left",
                joints=PoseSegments.LEFT_LEG,
                min_angle=65,
                max_angle=165,
                message="Don't lock your left knee",
                severity="warning",
            ),
            AngleValidationRule(
                name="knee_unlocked_right",
                joints=PoseSegments.RIGHT_LEG,
                min_angle=65,
                max_angle=165,
                message="Don't lock your right knee",
                severity="warning",
            )
        ]
    )
    metadata: dict = field(
        default_factory=lambda: {
            "description": "Machine-based lower-body squatting exercise emphasizing the quadriceps with dynamic hip movement.",
            "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        }
    )
```

---

### FILE: [src/exercises/leg/leg_press.py](src/exercises/leg/leg_press.py)

```py
"""Leg Press exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ...core.pose_segments import PoseSegments
from ..exercise import Exercise
from ..rules import AngleCounterRule, AngleValidationRule

@dataclass
class LegPressExercise(Exercise):
    name: str = "Leg Press"
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                up_angle=160,
                down_angle=90,
            ),
            AngleCounterRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                up_angle=160,
                down_angle=90,
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="knee_unlocked_left",
                joints=PoseSegments.LEFT_LEG,
                min_angle=0,
                max_angle=170,
                message="Don't lock your left knee",
                severity="warning",
            ),
            AngleValidationRule(
                name="knee_unlocked_right",
                joints=PoseSegments.RIGHT_LEG,
                min_angle=0,
                max_angle=170,
                message="Don't lock your right knee",
                severity="warning",
            )
        ]
    )
    metadata: dict = field(
        default_factory=lambda: {
            "description": "Machine-based lower-body pushing exercise.",
            "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        }
    )
```

---

### FILE: [src/exercises/__init__.py](src/exercises/__init__.py)

```py
"""Exercise configuration package.

Everything in here is *data*, not behaviour. An exercise is described entirely
by an :class:`Exercise` instance built from :class:`AngleCounterRule` and
:class:`AngleValidationRule` dataclasses. GymEngine consumes these objects and never
needs to know which exercise it is running.

Each exercise lives in its own module (``pushup.py``, ``squat.py``, ...); this
package re-exports them so callers can do ``from src.exercises import
PushUpExercise`` without knowing the internal file layout. Adding a new exercise
= adding one new self-contained module + one import line below. No engine code
changes.
"""

from .biceps_curl import BicepsCurlExercise
from .cable_chest_fly import CableChestFlyExercise
from .deadlift import DeadliftExercise
from .exercise import DisplaySettings, Exercise
from .latpulldown import LatPulldownExercise
from .leg import HackSquatExercise, LegPressExercise
from .pushup import PushUpExercise
from .registry import ExerciseRegistry, UnknownExerciseError, registry
from .rules import AngleCounterRule, AngleValidationRule
from .shoulder_press import ShoulderPressExercise
from .squat import SquatExercise
from .validation import ValidationResult, validate_all, violations

__all__ = [
    "AngleCounterRule",
    "AngleValidationRule",
    "Exercise",
    "DisplaySettings",
    "ValidationResult",
    "validate_all",
    "violations",
    "PushUpExercise",
    "SquatExercise",
    "LegPressExercise",
    "HackSquatExercise", 
    "ShoulderPressExercise",
    "BicepsCurlExercise",
    "LatPulldownExercise",
    "DeadliftExercise",
    "CableChestFlyExercise",
    # Registry
    "registry",
    "ExerciseRegistry",
    "UnknownExerciseError",
]
```

---

### FILE: [src/exercises/biceps_curl.py](src/exercises/biceps_curl.py)

```py
"""Biceps Curl exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import AngleCounterRule, AngleValidationRule


@dataclass
class BicepsCurlExercise(Exercise):
    name: str = "Biceps Curl"
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=160,
                down_angle=30,
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
                severity="error",
            ),
            AngleValidationRule(
                name="elbow_unlocked",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=170,
                message="Don't lock your elbows",
                severity="warning",
            ),
        ]
    )
    metadata: dict = field(
        default_factory=lambda: {
            "description": "Isolation exercise for the biceps.",
            "muscle_groups": ["biceps", "forearms"],
        }
    )
```

---

### FILE: [src/exercises/cable_chest_fly.py](src/exercises/cable_chest_fly.py)

```py
"""Cable Chest Fly exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import AngleCounterRule, AngleValidationRule


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
                severity="warning",
            ),
        ]
    )

    metadata: dict = field(
        default_factory=lambda: {
            "description": "Cable Chest Fly. Pectoral isolation via shoulder adduction.",
            "muscle_groups": ["pectorals", "anterior deltoid"],
        }
    )
```

---

### FILE: [src/exercises/deadlift.py](src/exercises/deadlift.py)

```py
"""Deadlift: Dissected — exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import AngleCounterRule, AngleValidationRule


@dataclass
class DeadliftExercise(Exercise):
    name: str = "Deadlift: Dissected"

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
                severity="error",
            ),
            # Ear -> Shoulder -> Hip: detects forward head / neck drop
            AngleValidationRule(
                name="neck_neutral",
                joints=PoseSegments.RIGHT_NECK_ALIGN,
                min_angle=140,
                max_angle=180,
                message="Keep your neck neutral — chin should follow the spine",
                severity="error",
            ),
        ]
    )

    metadata: dict = field(
        default_factory=lambda: {
            "description": "Deadlift: Dissected. Compound posterior-chain exercise.",
            "muscle_groups": ["hamstrings", "glutes", "erector spinae", "trapezius", "core"],
        }
    )
```

---

### FILE: [src/exercises/exercise.py](src/exercises/exercise.py)

```py
"""The Exercise configuration object — the single thing GymEngine needs."""

from dataclasses import dataclass, field
from typing import Any

from .rules import AngleCounterRule, AngleValidationRule


@dataclass
class DisplaySettings:
    """Optional, per-exercise presentation knobs.

    Kept separate from counting/validation so visual tweaks never leak into
    exercise logic. All fields are optional with safe defaults.
    """

    show_angle_arc: bool = True
    show_skeleton: bool = True


@dataclass
class Exercise:
    """A fully self-contained description of one exercise.

    An Exercise is *pure configuration*: it carries the repetition-counting
    rules, the form-validation rules, optional display settings, and free-form
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
    validation_rules: list[AngleValidationRule] = field(default_factory=list)
    display: DisplaySettings = field(default_factory=DisplaySettings)
    metadata: dict[str, Any] = field(default_factory=dict)
```

---

### FILE: [src/exercises/latpulldown.py](src/exercises/latpulldown.py)

```py
"""Lat Pulldown exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import AngleCounterRule, AngleValidationRule


@dataclass
class LatPulldownExercise(Exercise):
    name: str = "Lat Pulldown"

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
                severity="error",
            ),
            AngleValidationRule(
                name="avoid_locking_elbows",
                joints=PoseSegments.LEFT_ARM,
                min_angle=15,
                max_angle=175,
                message="Don't lock your elbows",
                severity="warning",
            ),
            AngleValidationRule(
                name="full_pull",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=75,
                message="Pull the bar all the way down",
                severity="warning",
            ),
        ]
    )

    metadata: dict = field(
        default_factory=lambda: {
            "description": "Lat Pulldown machine exercise.",
            "muscle_groups": [
                "latissimus dorsi",
                "teres major",
                "trapezius",
                "rhomboids",
                "biceps",
            ],
        }
    )
```

---

### FILE: [src/exercises/pushup.py](src/exercises/pushup.py)

```py
"""Push-Up exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import AngleCounterRule, AngleValidationRule


@dataclass
class PushUpExercise(Exercise):
    name: str = "Push-Up"
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
                severity="error",
            ),
            AngleValidationRule(
                name="elbow_unlocked",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=170,
                message="Don't lock your elbows",
                severity="warning",
            ),
        ]
    )
    metadata: dict = field(
        default_factory=lambda: {
            "description": "Bodyweight chest, triceps and core exercise.",
            "muscle_groups": ["chest", "triceps", "shoulders", "core"],
        }
    )
```

---

### FILE: [src/exercises/registry.py](src/exercises/registry.py)

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

### FILE: [src/exercises/rules.py](src/exercises/rules.py)

```py
"""Rule dataclasses: the atomic, exercise-agnostic building blocks.

A rule is pure configuration. It knows nothing about *which* exercise uses it
and contains no logic. GymEngine reads these fields and acts on them.
"""

from dataclasses import dataclass
from typing import Literal

# How severe a failed validation is. Used by the renderer for colouring /
# weighting feedback. Extend freely (e.g. "info") without touching the engine.
Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class AngleCounterRule:
    """Describes how ONE repetition is counted from a single joint angle.

    Why a dataclass (not a function/class hierarchy): a rep count is fully
    described by four numbers and two labels. There is no behaviour to model,
    so a frozen dataclass is the simplest honest representation.

    Attributes:
        name:        Stable id, also used as the on-screen label.
        joints:      Three pose-landmark indices forming the measured angle.
        up_angle:    Angle (deg) that marks the "up" / top of a rep.
        down_angle:  Angle (deg) that marks the "down" / bottom of a rep.
        up_stage:    Label applied while at/above ``up_angle`` (default "up").
        down_stage:  Label applied while at/below ``down_angle`` (default "down").

    ``up_stage`` / ``down_stage`` exist so the stage vocabulary is configurable
    ("up"/"down" today, but a future exercise could use different labels or a
    reversed count direction) without changing GymEngine or RepCounter.
    """

    name: str
    joints: tuple[int, int, int]
    up_angle: float
    down_angle: float
    up_stage: str = "up"
    down_stage: str = "down"


@dataclass(frozen=True)
class AngleValidationRule:
    """Describes ONE independent form-check based on a joint angle.

    Each rule is completely self-contained: it knows which angle to measure and
    the acceptable ``[min_angle, max_angle]`` window. If the measured angle
    falls outside that window, ``message`` is surfaced to the user.

    Attributes:
        name:       Stable id.
        joints:     Three pose-landmark indices forming the measured angle.
        min_angle:  Lower bound of the acceptable range (deg).
        max_angle:  Upper bound of the acceptable range (deg).
        message:    Human-readable coaching cue shown when the rule fails.
        severity:   "error" | "warning" | "info" — drives feedback emphasis.
    """

    name: str
    joints: tuple[int, int, int]
    min_angle: float
    max_angle: float
    message: str
    severity: Severity = "error"
```

---

### FILE: [src/exercises/shoulder_press.py](src/exercises/shoulder_press.py)

```py
"""Shoulder Press exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import AngleCounterRule, AngleValidationRule


@dataclass
class ShoulderPressExercise(Exercise):
    name: str = "Shoulder Press"
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=160,
                down_angle=60,
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
                severity="error",
            ),
            AngleValidationRule(
                name="elbow_unlocked",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=170,
                message="Don't lock your elbows",
                severity="warning",
            ),
        ]
    )
    metadata: dict = field(
        default_factory=lambda: {
            "description": "Overhead pressing exercise for the shoulders.",
            "muscle_groups": ["shoulders", "triceps", "upper chest"],
        }
    )
```

---

### FILE: [src/exercises/squat.py](src/exercises/squat.py)

```py
"""Squat exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import AngleCounterRule, AngleValidationRule


@dataclass
class SquatExercise(Exercise):
    name: str = "Squat"
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
                severity="error",
            ),
            AngleValidationRule(
                name="knee_aligned",
                joints=PoseSegments.LEFT_LEG,
                min_angle=30,
                max_angle=180,
                message="Keep your knee aligned",
                severity="warning",
            ),
        ]
    )
    metadata: dict = field(
        default_factory=lambda: {
            "description": "Compound lower-body strength exercise.",
            "muscle_groups": ["quadriceps", "glutes", "hamstrings", "core"],
        }
    )
```

---

### FILE: [src/exercises/validation.py](src/exercises/validation.py)

```py
"""Form-validation evaluation.

This module is the ONE place that knows *how* to turn an AngleValidationRule into a
pass/fail result. GymEngine never evaluates rules itself — it only calls
:func:`validate_all`. That indirection is what keeps the engine closed for
modification when new rule *kinds* are added later (see EXTENSION POINT below).
"""

from dataclasses import dataclass
from typing import Iterable, Sequence

from ..utils.geometry import calc_angle, get_points
from .rules import AngleValidationRule


@dataclass
class ValidationResult:
    """Outcome of evaluating a single AngleValidationRule on one frame."""

    rule_name: str
    message: str
    severity: str
    passed: bool
    angle: float | None   # None when the angle could not be computed
    joints: tuple = ()  # the rule's landmark triple, carried for rendering


def evaluate_rule(
    rule: AngleValidationRule, landmarks, width: int, height: int
) -> ValidationResult:
    """Evaluate one angle-based AngleValidationRule against the detected pose.

    EXTENSION POINT
    ----------------
    Today every AngleValidationRule is angle-based, so we just measure the angle at
    ``rule.joints``. To support the future rule kinds from the brief
    (distance-based, alignment, symmetry, richer feedback) you only need to:

        1. add a new rule dataclass in ``rules.py``
           (e.g. ``DistanceValidationRule``), and
        2. branch on its type here (``isinstance`` or a ``kind`` field).

    GymEngine calls ``validate_all`` and reads ``ValidationResult`` objects, so
    **it does not change** when a new rule kind appears.
    """
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


def validate_all(
    rules: Iterable[AngleValidationRule], landmarks, width: int, height: int
) -> list[ValidationResult]:
    """Run every validation rule; order matches the input list."""
    return [evaluate_rule(rule, landmarks, width, height) for rule in rules]


def violations(results: Sequence[ValidationResult]) -> list[ValidationResult]:
    """Filter a batch of results down to the ones that failed."""
    return [r for r in results if not r.passed]
```

---

### FILE: [src/services/__init__.py](src/services/__init__.py)

```py
from .gym_engine import GymEngine
from .pose_service import PoseService
from .rep_counter import RepCounter, RepState
from .rep_judge import RepJudge, RepResult

__all__ = ["GymEngine", "PoseService", "RepCounter", "RepState", "RepJudge", "RepResult"]
```

---

### FILE: [src/services/gym_engine.py](src/services/gym_engine.py)

```py
"""Generic, exercise-agnostic training engine."""

import datetime
import time

import cv2

from ..analytics.analyzer import SessionAnalyzer
from ..analytics.session_summary import SessionSummary
from ..config import settings
from ..core import Colors
from ..exercises.exercise import Exercise
from ..exercises.validation import ValidationResult, validate_all, violations
from ..utils.geometry import ComputedAngle, calc_angle, get_points
from ..utils.render import draw_angle_arc, draw_angle_labels, draw_skeleton, draw_stats, fit_to_screen
from .pose_service import PoseService
from .rep_counter import RepCounter
from .rep_judge import RepJudge


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

    # ------------------------------------------------------------------
    # Analysis: pure logic, no I/O -> easy to unit test with fake landmarks.
    # ------------------------------------------------------------------
    def analyze(self, landmarks, width: int, height: int, frame: int) -> FrameResult:
        """Compute angles, update the counter, run validation, and judge reps."""
        angles = {}
        views = []  # unified per-rule angle views for the renderer

        for rule in self.exercise.counter_rules:
            pts = get_points(rule.joints, landmarks, width, height)
            angle = calc_angle(*pts) if len(pts) >= 3 else None
            angles[rule.name] = angle
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            # Counter angles are never "failed" -> drawn with the highlight colour.
            views.append(ComputedAngle(name=rule.name, vertex=vertex, angle=angle, is_error=False))

        results = validate_all(self.exercise.validation_rules, landmarks, width, height)

        for res in results:
            pts = get_points(res.joints, landmarks, width, height)
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            views.append(
                ComputedAngle(name=res.rule_name, vertex=vertex, angle=res.angle, is_error=not res.passed)
            )

        # ── Rep quality tracking (orchestration only) ──────────────────
        # GymEngine feeds validation results to the judge every frame and tells
        # the judge when a rep completed. Completion is detected here by reading
        # RepCounter's rep count -- RepCounter remains the sole authority on
        # counting and is never told about validation. All GOOD/BAD logic lives
        # in RepJudge, so nothing in this class decides rep quality.
        self.judge.observe(results, frame)

        prev_count = self.counter.primary.count
        self.counter.update(angles)  # RepCounter detects completion
        if self.counter.primary.count > prev_count:
            self.judge.finalize_rep(self.counter.primary.count, frame)

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
            for rule in self.exercise.counter_rules + self.exercise.validation_rules:
                pts = get_points(rule.joints, landmarks, width, height)
                if len(pts) >= 3:
                    draw_skeleton(frame, pts, self.colors, is_bad=bad)

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
        draw_stats(
            frame,
            exercise_name=self.exercise.name,
            reps=self.judge.total_reps,
            good_reps=self.judge.good_reps,
            bad_reps=self.judge.bad_reps,
            current_rep=current_rep,
            stage=primary.stage,
            angle=primary.angle,
            feedback=feedback,
            colors=self.colors,
        )

    # ------------------------------------------------------------------
    # Session analytics + export (orchestration only — no logic here).
    # ------------------------------------------------------------------
    def _export_session(self, summary: "SessionSummary") -> None:
        """Persist ``summary`` using the configured exporter (opt-in)."""
        from ..analytics.exporters import CsvSessionExporter, JsonSessionExporter

        settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.exercise.name)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target = settings.EXPORT_DIR / f"{safe_name}_{stamp}"
        exporter = (
            JsonSessionExporter() if settings.EXPORT_FORMAT.lower() == "json"
            else CsvSessionExporter()
        )
        out_path = exporter.export(summary, target)
        print(f"Session summary exported to {out_path}")

    # ------------------------------------------------------------------
    # Orchestration: video source + detection + render loop.
    # ------------------------------------------------------------------
    def run(self, video_path: str | None = None):
        if settings.USE_WEBCAM:
            cap = cv2.VideoCapture(settings.WEBCAM_INDEX)
        else:
            src = video_path or settings.VIDEO_PATH
            cap = cv2.VideoCapture(str(src) if src is not None else None)

        if not cap.isOpened():
            raise RuntimeError("Cannot open video source")

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
        # (RepJudge.history) to the analytics module and, if enabled, asks an
        # exporter to persist the resulting SessionSummary. No analytics logic
        # lives in the engine.
        if settings.EXPORT_SESSION:
            summary = SessionAnalyzer().analyze(
                self.judge.history,
                exercise_name=self.exercise.name,
                fps=settings.ANALYTICS_FPS,
                total_duration=elapsed,
            )
            self._export_session(summary)

        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
```

---

### FILE: [src/services/pose_service.py](src/services/pose_service.py)

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

### FILE: [src/services/rep_counter.py](src/services/rep_counter.py)

```py
"""Repetition counter driven entirely by AngleCounterRule configuration."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..exercises.rules import AngleCounterRule


@dataclass
class RepState:
    """Live state for one counter rule across frames."""

    angle: float = 0.0
    count: int = 0
    stage: str = "up"


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

    @property
    def primary(self) -> RepState:
        """State backing the displayed rep count (first counter rule)."""
        return next(iter(self.states.values()))

    def update(self, angles: Dict[str, Optional[float]]) -> Dict[str, RepState]:
        """Feed in the current angle for each rule; advance counts/stages."""
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
                state.stage = rule.down_stage
            elif angle > rule.up_angle:
                state.stage = rule.up_stage
            # Angles between thresholds hold the current stage.

        return self.states
```

---

### FILE: [src/services/rep_judge.py](src/services/rep_judge.py)

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
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..exercises.validation import ValidationResult

# Severity ordering used purely for de-duplication: when the same rule fails on
# several frames we keep the *worst* observed severity, so an ``error`` is never
# masked by an earlier ``warning``. Higher rank == more severe.
_SEVERITY_RANK: Dict[str, int] = {"info": 0, "warning": 1, "error": 2}


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
        violations:   The distinct validation rules that failed during the rep,
                      de-duplicated by rule name (one entry per failed rule).
        start_frame:  First frame index observed for this rep, or ``None``.
        end_frame:    Frame index on which the rep completed, or ``None``.
    """

    number: int
    good: bool
    violations: List[ValidationResult]
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None


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
        """
        if self._start_frame is None:
            self._start_frame = frame

        for r in results:
            if r.passed:
                continue
            existing = self._violations.get(r.rule_name)
            if existing is None or _SEVERITY_RANK.get(r.severity, 0) > _SEVERITY_RANK.get(existing.severity, 0):
                self._violations[r.rule_name] = r

    # -- completion ------------------------------------------------------
    def finalize_rep(self, rep_number: int, frame: int = 0) -> RepResult:
        """Finalize the current repetition and begin tracking the next one.

        Builds a :class:`RepResult`, appends it to :attr:`history`, resets the
        temporary per-rep state, and returns the result.

        A repetition is BAD iff at least one stored violation has
        ``severity == "error"``; warnings alone leave it GOOD.
        """
        bad = any(v.severity == "error" for v in self._violations.values())
        result = RepResult(
            number=rep_number,
            good=not bad,
            violations=list(self._violations.values()),
            start_frame=self._start_frame,
            end_frame=frame,
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
```

---

### FILE: [src/utils/__init__.py](src/utils/__init__.py)

```py
from .geometry import calc_angle, get_points
from .render import draw_angle_arc
```

---

### FILE: [src/utils/geometry.py](src/utils/geometry.py)

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


def get_points(indices, landmarks, w, h):
    return [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in indices]
```

---

### FILE: [src/utils/render.py](src/utils/render.py)

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


def draw_skeleton(frame, pts, colors, is_bad=False):
    if len(pts) < 3:
        return

    line_color = colors.ERROR if is_bad else colors.LINE
    point_color = colors.ERROR if is_bad else colors.HIGHLIGHT

    cv2.line(frame, pts[0], pts[1], line_color, 3)
    cv2.line(frame, pts[1], pts[2], line_color, 3)

    for p in pts:
        cv2.circle(frame, p, 6, point_color, -1)


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

    Only the arc is drawn here; the numeric angle value is rendered by
    ``draw_angle_labels`` for every computed angle (counter + validation).
    """

    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    angle1 = math.degrees(math.atan2(ba[1], ba[0]))
    angle2 = math.degrees(math.atan2(bc[1], bc[0]))

    start_angle = int(angle1)
    end_angle = int(angle2)

    # fix direction (always draw smallest arc)
    if end_angle < start_angle:
        end_angle += 360

    if end_angle - start_angle > 180:
        start_angle, end_angle = end_angle, start_angle + 360

    color = colors.ERROR if is_bad else colors.HIGHLIGHT

    cv2.ellipse(frame, b, (radius, radius), 0, start_angle, end_angle, color, 5)


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
        color = colors.ERROR if v.is_error else colors.HIGHLIGHT
        text = "N/A" if v.angle is None else f"{int(round(v.angle))} deg"

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
```

---

### FILE: [src/__init__.py](src/__init__.py)

```py

```

---

### FILE: [src/main.py](src/main.py)

```py
"""AI Gym Trainer — entry point.

Usage
-----
  python -m src.main                               # uses .env defaults
  python -m src.main deadlift                      # deadlift, video from .env
  python -m src.main deadlift Deadlift3.mp4        # deadlift + video override
  python -m src.main cable_chest_fly Chest.mp4     # cable fly + video
  python -m src.main hack_squat leg.mp4            # hack squat + video

Available exercises
-------------------
  deadlift  cable_chest_fly  squat  pushup
  biceps_curl  lat_pulldown  leg_press  shoulder_press  hack_squat
"""

import sys

from .config import settings
from .core.colors import Colors
from .exercises import registry
from .services.gym_engine import GymEngine

DEFAULT_EXERCISE = "cable_chest_fly"


def main():
    args = sys.argv[1:]

    exercise_key = args[0].lower() if len(args) >= 1 else None
    video_path   = args[1]         if len(args) >= 2 else None

    # The CLI simply asks the registry for an exercise — it knows nothing about
    # which exercises exist. GymEngine stays completely unaware of the registry.
    if exercise_key and not registry.exists(exercise_key):
        print(f"Unknown exercise '{exercise_key}'.")
        print(f"Available: {', '.join(registry.list())}")
        sys.exit(1)

    exercise = (
        registry.get(exercise_key) if exercise_key else registry.get(DEFAULT_EXERCISE)
    )

    GymEngine(
        exercise,
        colors=Colors(),
        display_width=settings.DISPLAY_MAX_WIDTH,
    ).run(video_path=video_path)


if __name__ == "__main__":
    main()
```

---

## EXPORT SUMMARY

- Files exported: 34
- Lines exported: 2198
