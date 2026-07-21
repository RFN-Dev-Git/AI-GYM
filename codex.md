# CODEBASE SNAPSHOT

## PROJECT STRUCTURE

```text
AI-GYM/
├── assets
│   ├── models
│   │   ├── pose_landmarker_full.task
│   │   └── pose_landmarker_lite.task
│   └── videos
│       ├── Chest.mp4
│       ├── Deadlift .png
│       ├── Deadlift.mp4
│       ├── Deadlift2.mp4
│       ├── Deadlift3.mp4
│       ├── hackw.mp4
│       ├── leg.mp4
│       └── leg2.mp4
├── output
│   ├── sessions
│   │   ├── Hack_Squat_20260713_012947.json
│   │   ├── Hack_Squat_20260713_013018.json
│   │   ├── Hack_Squat_20260716_111811.json
│   │   ├── Hack_Squat_20260716_112114.json
│   │   ├── Hack_Squat_20260716_112451.json
│   │   └── Hack_Squat_20260719_173638.json
│   └── videos
│       └── result.mp4
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
│   │   ├── additional_casses.py
│   │   ├── gym_engine.py
│   │   ├── pose_service.py
│   │   ├── rep_counter.py
│   │   └── rep_judge.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── camera_side.py
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
├── requirements.txt
└── term
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

    # Arm direction: Hip -> Shoulder -> Elbow (Shoulder Press)
    # Checks if arm is extended upward (pressing) vs downward (resting).
    LEFT_ARM_DIRECTION  = (L_HIP, L_SHOULDER, L_ELBOW)
    RIGHT_ARM_DIRECTION = (R_HIP, R_SHOULDER, R_ELBOW)
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
    camera: str = "side"
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                up_angle=130,
                down_angle=90,
            ),
            AngleCounterRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                up_angle=130,
                down_angle=90,
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="knee_unlocked_left",
                joints=PoseSegments.LEFT_LEG,
                min_angle=60,
                max_angle=170,
                message="Don't lock your left knee",
                severity="warning",
            ),
            AngleValidationRule(
                name="knee_unlocked_right",
                joints=PoseSegments.RIGHT_LEG,
                min_angle=60,
                max_angle=170,
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
"""Leg Press exercise configuration (self-contained).

Counting logic:
  - DOWN phase: knee angle <= 110° (user is bending)
  - RETURNING: angle crosses back above 120°
  - Rep completes when angle >= 160° (fully extended)

ROM quality:
  - GOOD rep: must reach <= 80° at the bottom AND >= 160° at the top
  - BAD rep:  counted if the user reverses before reaching either extreme

Skeleton color:
  - Default (white) while at rest (UP stage, before rep starts)
  - RED while descending/returning but bottom not yet reached
  - GREEN once the bottom extreme (<= 80°) has been reached this rep
"""

from dataclasses import dataclass, field

from ...core.pose_segments import PoseSegments
from ..exercise import Exercise, DisplaySettings
from ..rules import AngleCounterRule, AngleROMValidationRule


@dataclass
class LegPressExercise(Exercise):
    name: str = "Leg Press"
    camera: str = "side"

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                up_angle=120,       # crosses this going back up → RETURNING phase
                down_angle=110,     # <= 110° = DOWN phase begins
                rom_min_angle=80,   # must reach <= 80° for a GOOD rep (deep enough)
                rom_max_angle=160,  # must reach >= 160° for a GOOD rep (full extension)
            ),
            AngleCounterRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                up_angle=120,
                down_angle=110,
                rom_min_angle=80,
                rom_max_angle=160,
            ),
        ]
    )

    validation_rules: list[AngleROMValidationRule] = field(
        default_factory=lambda: [
            AngleROMValidationRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                min_rom_angle=80,
                max_rom_angle=160,
                message="Full range: bend to 80° and extend to 160°",
                severity="warning",
            ),
            AngleROMValidationRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                min_rom_angle=80,
                max_rom_angle=160,
                message="Full range: bend to 80° and extend to 160°",
                severity="warning",
            ),
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

```

---

### FILE: [src/exercises/biceps_curl.py](src/exercises/biceps_curl.py)

```py
"""Biceps Curl exercise configuration (self-contained).

Counting logic (LEFT_ARM — Shoulder → Elbow → Wrist angle):
  - UP stage:   angle >= 150° (arm extended / hanging down)
  - DOWN stage: angle <= 90°  (arm curled up toward shoulder)
  - A rep counts when the user goes DOWN → UP (curled → extended)
  - GOOD rep: must reach <= 60° at the curl AND >= 150° at the extension

Validation rules:
  1. elbow_too_tight: angle must stay >= 30° — if lower than 30° the forearm
     is jammed too close, losing bicep tension (bad form).
  2. elbow_hyperextended: angle must stay <= 170° — if higher than 170° the
     elbow is hyperextended or locked out too straight (wrong position).
  3. elbow_drift: Hip → Shoulder → Elbow angle must stay <= 15°.
     If the elbow drifts forward, the front shoulder takes over and bicep tension drops.

Speed check:
  - min_rep_frames=18 (~0.7 s at 25 fps). Reps faster than this are marked BAD.

Only ARM joints are drawn on screen (show_validation_skeleton=False).
"""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments, L_HIP, L_SHOULDER, L_ELBOW
from .exercise import Exercise, DisplaySettings
from .rules import AngleCounterRule, AngleValidationRule


# Hip → Shoulder → Elbow: detects elbow drift / forward swing
_LEFT_ELBOW_DRIFT = (L_HIP, L_SHOULDER, L_ELBOW)


@dataclass
class BicepsCurlExercise(Exercise):
    name: str = "Biceps Curl"
    camera: str = "side"

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,   # Shoulder → Elbow → Wrist
                up_angle=139,                   # arm extended — UP stage (angle >= 150)
                down_angle=90,                  # arm curled — DOWN stage (angle <= 90)
                up_stage="down",                # map large angle (extension) to "down"
                down_stage="up",                # map small angle (curl peak) to "up"
                rom_min_angle=150,               # must reach <= 60° for a GOOD rep
                rom_max_angle=50,              # must reach >= 150° for a GOOD rep
                min_rep_frames=12,              # < 12 frames = too fast → BAD
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            # ── Form check 1: elbow angle must stay above 30° ──────────
            AngleValidationRule(
                name="elbow_too_tight",
                joints=PoseSegments.LEFT_ARM,
                min_angle=30,
                max_angle=180,
                message="Don't curl too tight — keep elbow above 30°",
                severity="warning",
            ),
            # ── Form check 2: elbow angle must stay below 170° ─────────
            AngleValidationRule(
                name="elbow_hyperextended",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=170,
                message="Don't lock or hyperextend your elbow (keep below 170°)",
                severity="warning",
            ),
            # ── Form check 3: elbow drift (Hip → Shoulder → Elbow) ─────
            # Upper arm stays vertical (parallel to torso) — angle <= 15°.
            AngleValidationRule(
                name="elbow_drift",
                joints=_LEFT_ELBOW_DRIFT,
                min_angle=0,
                max_angle=20,
                message="Keep elbow pinned to your side (drift < 20°)",
                severity="warning",
            ),
        ]
    )

    # Only draw the arm skeleton — the drift validation joints (Hip→Shoulder→Elbow)
    # would add a distracting second skeleton if allowed to render.
    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(show_validation_skeleton=False)
    )

    metadata: dict = field(
        default_factory=lambda: {
            "description": "Isolation dumbbell exercise for the biceps brachii.",
            "muscle_groups": ["biceps brachii", "brachialis", "brachioradialis"],
            "technique_notes": (
                "Keep the upper arm stationary and elbow pinned to your side (drift < 15°). "
                "Full extension at the bottom (~150° - 170°) and full curl at the top (30° - 60°). "
                "Controlled tempo — avoid ballistic / momentum-driven reps."
            ),
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
    camera: str = "side"

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

    show_angle_arc: bool = False
    show_skeleton: bool = True
    show_validation_skeleton: bool = True  # set False to hide validation-rule joints


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
    camera: str = "both"
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
    camera: str = "side"

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
    camera: str = "side"
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
        sync_group:  Optional group name for synchronized multi-rule counting.
                     Rules with the same sync_group must reach thresholds together.

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
    rom_min_angle: float | None = None
    rom_max_angle: float | None = None
    min_rep_frames: int = 0   # minimum frames a rep must span (0 = no check)
    sync_group: str | None = None  # optional synchronization group


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


@dataclass(frozen=True)
class AngleROMValidationRule:
    """Describes a stateful Range of Motion (ROM) validation rule.

    Attributes:
        name:          Stable id matching the corresponding CounterRule name.
        joints:        Three pose-landmark indices forming the measured angle.
        min_rom_angle: Bottom angle threshold (deg) that must be reached.
        max_rom_angle: Top angle threshold (deg) that must be reached.
        message:       Human-readable coaching cue shown when the rule fails.
        severity:      "error" | "warning" | "info" — drives feedback emphasis.
    """

    name: str
    joints: tuple[int, int, int]
    min_rom_angle: float
    max_rom_angle: float
    message: str
    severity: Severity = "error"


@dataclass(frozen=True)
class DistanceValidationRule:
    """Describes a validation rule based on distance between two landmarks.

    Attributes:
        name:         Stable id.
        point1:       First landmark index.
        point2:       Second landmark index.
        min_ratio:    Minimum acceptable ratio (point1-point2 distance / reference distance).
        max_ratio:    Maximum acceptable ratio (point1-point2 distance / reference distance).
        reference1:   First reference landmark index for ratio calculation.
        reference2:   Second reference landmark index for ratio calculation.
        message:      Human-readable coaching cue shown when the rule fails.
        severity:     "error" | "warning" | "info" — drives feedback emphasis.
    """

    name: str
    point1: int
    point2: int
    min_ratio: float
    max_ratio: float
    reference1: int
    reference2: int
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
from .rules import (
    AngleCounterRule,
    AngleValidationRule,
    AngleROMValidationRule,
    DistanceValidationRule,
)


@dataclass
class ShoulderPressExercise(Exercise):
    name: str = "Shoulder Press"
    camera: str = "both"
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            # Use elbow angles for stage detection (up/down)
            # Stage changes at 90°: >90 = up, <90 = down
            # Using LEFT_ARM (shoulder-elbow-wrist) so only arm points are shown in skeleton
            AngleCounterRule(
                name="left_shoulder",
                joints=PoseSegments.LEFT_ARM,
                up_angle=91,   # Trigger up stage when > 90
                down_angle=89,  # Trigger down stage when < 90
                sync_group="shoulder_press",
            ),
            AngleCounterRule(
                name="right_shoulder",
                joints=PoseSegments.RIGHT_ARM,
                up_angle=91,   # Trigger up stage when > 90
                down_angle=89,  # Trigger down stage when < 90
                sync_group="shoulder_press",
            ),
        ]
    )
    validation_rules: list = field(
        default_factory=lambda: [
            # ROM validation for shoulder angles
            AngleROMValidationRule(
                name="left_shoulder_rom",
                joints=PoseSegments.LEFT_ARM_DIRECTION,
                min_rom_angle=40,
                max_rom_angle=160,
                message="Shoulder: Reach 160° up, 40-80° down",
                severity="error",
            ),
            AngleROMValidationRule(
                name="right_shoulder_rom",
                joints=PoseSegments.RIGHT_ARM_DIRECTION,
                min_rom_angle=40,
                max_rom_angle=160,
                message="Shoulder: Reach 160° up, 40-80° down",
                severity="error",
            ),
            # ROM validation for elbow angles
            AngleROMValidationRule(
                name="left_elbow_rom",
                joints=PoseSegments.LEFT_ARM,
                min_rom_angle=60,
                max_rom_angle=170,
                message="Elbow: Reach 170° up, 60° down",
                severity="error",
            ),
            AngleROMValidationRule(
                name="right_elbow_rom",
                joints=PoseSegments.RIGHT_ARM,
                min_rom_angle=60,
                max_rom_angle=170,
                message="Elbow: Reach 170° up, 60° down",
                severity="error",
            ),
            # Distance validation: wrists should be at least shoulder-width apart
            # Name starts with counter rule name to auto-poison reps
            DistanceValidationRule(
                name="left_shoulder_wrist_distance",
                point1=15,  # Left wrist
                point2=16,  # Right wrist
                min_ratio=1.2,  # Must be at least 1.2x shoulder width (stricter)
                max_ratio=3.0,
                reference1=11,  # Left shoulder
                reference2=12,  # Right shoulder
                message="Keep wrists wider than shoulders",
                severity="error",
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
    camera: str = "side"
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

from ..utils.geometry import calc_angle, get_points, calc_distance
from .rules import AngleValidationRule, AngleROMValidationRule, DistanceValidationRule

_STAGE_DOWN      = "down"
_STAGE_RETURNING = "returning"


@dataclass
class ValidationResult:
    """Outcome of evaluating a single rule on one frame."""

    rule_name: str
    message: str
    severity: str
    passed: bool
    angle: float | None   # None when the angle could not be computed
    joints: tuple = ()  # the rule's landmark triple, carried for rendering


def evaluate_rule(
    rule: AngleValidationRule, landmarks, width: int, height: int
) -> ValidationResult:
    """Evaluate one angle-based AngleValidationRule against the detected pose."""
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


def evaluate_rom_rule(
    rule: AngleROMValidationRule,
    landmarks,
    width: int,
    height: int,
    state,
) -> ValidationResult:
    """Evaluate a ROMValidationRule using the live RepState."""
    pts = get_points(rule.joints, landmarks, width, height)
    angle = calc_angle(*pts) if len(pts) >= 3 else None

    if angle is None:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=rule.joints)

    if state is None:
        return ValidationResult(rule.name, rule.message, rule.severity, True, angle, joints=rule.joints)

    if state.stage == _STAGE_DOWN and not getattr(state, "reached_bottom", False):
        msg = f"Go deeper — target <= {int(rule.min_rom_angle)} deg"
        return ValidationResult(rule.name, msg, rule.severity, False, angle, joints=rule.joints)

    if state.stage == _STAGE_RETURNING:
        msg = f"Extend fully — target >= {int(rule.max_rom_angle)} deg"
        return ValidationResult(rule.name, msg, rule.severity, False, angle, joints=rule.joints)

    return ValidationResult(rule.name, rule.message, rule.severity, True, angle, joints=rule.joints)


def evaluate_distance_rule(
    rule: DistanceValidationRule,
    landmarks,
    width: int,
    height: int,
) -> ValidationResult:
    """Evaluate a DistanceValidationRule based on distance ratios."""
    pts1 = get_points([rule.point1, rule.point2], landmarks, width, height)
    pts2 = get_points([rule.reference1, rule.reference2], landmarks, width, height)

    if len(pts1) < 2 or len(pts2) < 2:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=())

    distance = calc_distance(pts1[0], pts1[1])
    reference_distance = calc_distance(pts2[0], pts2[1])

    if reference_distance == 0:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=())

    ratio = distance / reference_distance
    passed = rule.min_ratio <= ratio <= rule.max_ratio

    return ValidationResult(
        rule.name, rule.message, rule.severity, passed, ratio, joints=(rule.point1, rule.point2)
    )


def validate_all(
    rules: Iterable,
    landmarks,
    width: int,
    height: int,
    states: dict | None = None,
) -> list[ValidationResult]:
    """Run every validation rule; dispatches on rule type.

    ``states`` is only needed for AngleROMValidationRule; it may be omitted for
    exercises that only use plain AngleValidationRules.
    """
    results = []
    for rule in rules:
        if isinstance(rule, AngleROMValidationRule):
            state = (states or {}).get(rule.name)
            results.append(evaluate_rom_rule(rule, landmarks, width, height, state))
        elif isinstance(rule, DistanceValidationRule):
            results.append(evaluate_distance_rule(rule, landmarks, width, height))
        else:
            results.append(evaluate_rule(rule, landmarks, width, height))
    return results


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

### FILE: [src/services/additional_casses.py](src/services/additional_casses.py)

```py
"""Additional cases and ROM logic helpers for RepCounter.

This module encapsulates all exercise-specific complexity (ROM, speed checks,
prefix-matched violations) to keep the core `rep_counter.py` clean and simple.
"""

from typing import Dict, Optional, Set
from ..exercises.rules import AngleCounterRule

# Stage constants
STAGE_UP        = "up"
STAGE_DOWN      = "down"
STAGE_RETURNING = "returning"


class CustomCounterHelper:
    """Helper class to handle stateful ROM, speed, and violation logic."""

    def __init__(self, counter_instance) -> None:
        self.counter = counter_instance
        # Per-rule violation flag: was there a violation during the current rep?
        self._pending_violations: Dict[str, bool] = {
            r.name: False for r in counter_instance.rules
        }
        # Per-rule frame counter: how many frames since DOWN phase began?
        self._rep_frame_counts: Dict[str, int] = {
            r.name: 0 for r in counter_instance.rules
        }
        # Remember the previous angle for each rule to detect direction changes
        self._prev_angles: Dict[str, float] = {
            r.name: 0.0 for r in counter_instance.rules
        }
        # Custom started flags to isolate rep window
        self._started: Dict[str, bool] = {
            r.name: False for r in counter_instance.rules
        }

    def _count_rep(self, rule: AngleCounterRule, state, *, good: bool, too_fast: bool = False) -> None:
        """Finalise one repetition and increment the corresponding counters."""
        state.count += 1
        if good:
            state.good += 1
        else:
            state.bad += 1
        self._started[rule.name] = False
        state.speed_warning = too_fast

    def _start_down(self, rule: AngleCounterRule, state, angle: float) -> None:
        """Enter DOWN phase: reset rep counters and start frame tracking."""
        state.stage = STAGE_DOWN
        self._started[rule.name] = True
        state.reached_bottom = False
        state.speed_warning = False
        self._pending_violations[rule.name] = False
        self._rep_frame_counts[rule.name] = 0
        rom_min = getattr(rule, "rom_min_angle", None)
        if rom_min is not None and angle <= rom_min:
            state.reached_bottom = True

    def update(
        self,
        angles: Dict[str, Optional[float]],
        violation_names: Optional[Set[str]] = None,
    ) -> Dict[str, any]:
        """Execute stateful ROM, speed check, and violation tracking."""
        vnames = violation_names or set()

        for rule in self.counter.rules:
            angle = angles.get(rule.name)
            if angle is None:
                continue

            state = self.counter.states[rule.name]
            prev_angle = self._prev_angles[rule.name]
            self._prev_angles[rule.name] = angle
            state.angle = angle

            has_rom = getattr(rule, "rom_max_angle", None) is not None

            # ── Violation accumulation during active rep window ───────────
            if self._started[rule.name]:
                active_viols = {
                    v for v in vnames
                    if v.startswith(rule.name) and not (has_rom and v == rule.name)
                }
                # Fallback general posture checks for primary counter rule
                if rule == self.counter.rules[0]:
                    other_viols = {
                        v for v in vnames
                        if not any(r.name != rule.name and v.startswith(r.name) for r in self.counter.rules)
                        and not (has_rom and v == rule.name)
                    }
                    active_viols.update(other_viols)

                if active_viols:
                    self._pending_violations[rule.name] = True

            # ── Rep frame counter for speed checks ────────────────────────
            if self._started[rule.name]:
                self._rep_frame_counts[rule.name] += 1

            # ── Standard exercises path (but with speed/violation checks) ─
            if not has_rom:
                if angle <= rule.down_angle:
                    if state.stage != STAGE_DOWN:
                        self._start_down(rule, state, angle)
                elif angle >= rule.up_angle:
                    if self._started[rule.name] and state.stage == STAGE_DOWN:
                        too_fast = (
                            rule.min_rep_frames > 0
                            and self._rep_frame_counts[rule.name] < rule.min_rep_frames
                        )
                        good = not self._pending_violations[rule.name] and not too_fast
                        self._count_rep(rule, state, good=good, too_fast=too_fast)
                    state.stage = STAGE_UP

            # ── Range of Motion (ROM) exercises path ──────────────────────
            else:
                rom_min = getattr(rule, "rom_min_angle", None)
                rom_max = rule.rom_max_angle

                # Track bottom depth
                if rom_min is not None and angle <= rom_min:
                    state.reached_bottom = True

                # DOWN phase begins (or RETURNING reversal)
                if angle <= rule.down_angle:
                    if state.stage == STAGE_RETURNING:
                        if self._started[rule.name]:
                            self._count_rep(rule, state, good=False)
                    if state.stage != STAGE_DOWN:
                        self._start_down(rule, state, angle)

                # Enter RETURNING stage when crossing up_angle
                elif angle >= rule.up_angle and state.stage == STAGE_DOWN and self._started[rule.name]:
                    state.stage = STAGE_RETURNING

                # Top extreme reached and user starts curling back up (reversal)
                elif state.stage == STAGE_RETURNING and angle >= rom_max:
                    if angle < prev_angle:
                        too_fast = (
                            rule.min_rep_frames > 0
                            and self._rep_frame_counts[rule.name] < rule.min_rep_frames
                        )
                        good = (
                            state.reached_bottom
                            and not self._pending_violations[rule.name]
                            and not too_fast
                        )
                        self._count_rep(rule, state, good=good, too_fast=too_fast)
                        state.stage = STAGE_UP

        return self.counter.states
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
from ..utils.render import draw_angle_arc, draw_angle_labels, draw_skeleton, draw_stats, fit_to_screen, draw_wrist_line
from ..utils.camera_side import CameraSideDetector
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
        self.side_detector = CameraSideDetector(30) if exercise.camera == "side" else None
        self.rules_adapted = False if exercise.camera == "side" else True
        # Track distance violations during current rep for shoulder press
        self._distance_violation_in_current_rep = False

    # ------------------------------------------------------------------
    # Analysis: pure logic, no I/O -> easy to unit test with fake landmarks.
    # ------------------------------------------------------------------
    def analyze(self, landmarks, width: int, height: int, frame: int) -> FrameResult:
        """Compute angles, update the counter, run validation, and judge reps."""
        if self.side_detector and not self.rules_adapted:
            side = self.side_detector.process_frame(landmarks)
            if side:
                from ..utils.camera_side import adapt_rules
                self.exercise.counter_rules = adapt_rules(self.exercise.counter_rules, side)
                self.exercise.validation_rules = adapt_rules(self.exercise.validation_rules, side)
                self.counter = RepCounter(self.exercise.counter_rules)
                self.rules_adapted = True
            if not self.rules_adapted:
                return FrameResult(angles={}, states=self.counter.states, results=[], views=[])

        angles = {}
        views = []  # unified per-rule angle views for the renderer

        for rule in self.exercise.counter_rules:
            pts = get_points(rule.joints, landmarks, width, height)
            angle = calc_angle(*pts) if len(pts) >= 3 else None
            angles[rule.name] = angle
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            # Counter angles are never "failed" -> drawn with the highlight colour.
            views.append(ComputedAngle(name=rule.name, vertex=vertex, angle=angle, is_error=False))

        results = validate_all(self.exercise.validation_rules, landmarks, width, height, states=self.counter.states)

        for res in results:
            pts = get_points(res.joints, landmarks, width, height)
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            views.append(
                ComputedAngle(name=res.rule_name, vertex=vertex, angle=res.angle, is_error=not res.passed)
            )

        # ── Rep quality tracking ───────────────────────────────────────
        # RepCounter owns counting AND quality (good/bad) decisions.
        # Pass violation_names (set of failing rule names) — not a single global
        # bool — so each counter rule only accumulates violations for its own joints.
        violation_names = {r.rule_name for r in violations(results)}
        prev_good  = self.counter.primary.good
        prev_count = self.counter.primary.count

        # Track distance violations for shoulder press
        if self.exercise.name == "Shoulder Press":
            if "left_shoulder_wrist_distance" in violation_names:
                self._distance_violation_in_current_rep = True
            # Reset flag when rep completes (checked below)
            if self.counter.primary.stage == "up" and prev_count == self.counter.primary.count:
                # We're in up stage but no new rep counted, so reset the flag
                self._distance_violation_in_current_rep = False

        self.counter.update(angles, violation_names)

        if self.counter.primary.count > prev_count:
            # Rep just completed - check if there was a distance violation
            if self.exercise.name == "Shoulder Press" and self._distance_violation_in_current_rep:
                # Force this rep to be bad
                self.judge.finalize_rep(
                    self.counter.primary.count,
                    frame,
                    force_good=False,
                )
                self._distance_violation_in_current_rep = False
            else:
                rep_was_good = self.counter.primary.good > prev_good
                if self.counter.primary.speed_warning:
                    # Inject a speed violation warning
                    from ..exercises.validation import ValidationResult
                    self.judge.observe([
                        ValidationResult(
                            rule_name=self.exercise.counter_rules[0].name + "_too_fast",
                            message="Too fast — control the movement",
                            severity="warning",
                            passed=False,
                            angle=None
                        )
                    ], frame)
                self.judge.finalize_rep(
                    self.counter.primary.count,
                    frame,
                    force_good=rep_was_good,
                )

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
            drawn_joints = set()
            for rule in self.exercise.counter_rules:
                pts = get_points(rule.joints, landmarks, width, height)
                if len(pts) >= 3:
                    custom_color = None
                    if bad:
                        custom_color = self.colors.ERROR
                    elif hasattr(rule, 'rom_min_angle') and rule.rom_min_angle is not None:
                        state = self.counter.states.get(rule.name)
                        if state is not None:
                            # Only show RED/GREEN feedback when actively in a rep
                            # (DOWN or RETURNING stage). At UP/rest, use default color.
                            if state.stage in (rule.up_stage,):
                                custom_color = None  # resting — default white
                            elif state.reached_bottom:
                                custom_color = self.colors.HIGHLIGHT   # GREEN — depth reached
                            else:
                                custom_color = self.colors.ERROR        # RED — need to go deeper
                    draw_skeleton(frame, pts, self.colors, is_bad=bad, custom_color=custom_color)
                    drawn_joints.add(tuple(sorted(rule.joints)))

            # Validation-rule skeletons (e.g. back angle for deadlift).
            # Can be suppressed per-exercise via DisplaySettings.show_validation_skeleton.
            # For shoulder press, only show arm joints (no validation skeletons)
            if show.show_validation_skeleton and self.exercise.name != "Shoulder Press":
                for rule in self.exercise.validation_rules:
                    # Only draw skeletons for rules with joints attribute (AngleValidationRule)
                    if hasattr(rule, 'joints'):
                        joints_key = tuple(sorted(rule.joints))
                        if joints_key not in drawn_joints:
                            pts = get_points(rule.joints, landmarks, width, height)
                            if len(pts) >= 3:
                                draw_skeleton(frame, pts, self.colors, is_bad=bad)
                                drawn_joints.add(joints_key)

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

        # Custom rendering for shoulder press: draw wrist line when both arms are up
        if self.exercise.name == "Shoulder Press":
            left_shoulder_angle = result.angles.get("left_shoulder")
            right_shoulder_angle = result.angles.get("right_shoulder")
            # Only show line when both shoulder angles > 90 (arms actually up)
            if left_shoulder_angle and right_shoulder_angle:
                if left_shoulder_angle > 90 and right_shoulder_angle > 90:
                    # Check if distance validation failed
                    distance_failed = any(
                        r.rule_name == "left_shoulder_wrist_distance" and not r.passed
                        for r in result.results
                    )
                    line_color = self.colors.ERROR if distance_failed else self.colors.HIGHLIGHT
                    from ..core.pose_segments import L_WRIST, R_WRIST
                    left_wrist_pt = get_points([L_WRIST], landmarks, width, height)
                    right_wrist_pt = get_points([R_WRIST], landmarks, width, height)
                    if left_wrist_pt and right_wrist_pt:
                        draw_wrist_line(frame, left_wrist_pt[0], right_wrist_pt[0], self.colors, line_color)

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
        display_stage = primary.stage
        if self.exercise.counter_rules:
            rule = self.exercise.counter_rules[0]
            if primary.stage == "up":
                display_stage = rule.up_stage
            elif primary.stage == "down":
                display_stage = rule.down_stage

        draw_stats(
            frame,
            exercise_name=self.exercise.name,
            reps=self.judge.total_reps,
            good_reps=self.judge.good_reps,
            bad_reps=self.judge.bad_reps,
            current_rep=current_rep,
            stage=display_stage,
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
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
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

        print(self.judge.history)
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
from typing import Dict, List, Optional, Set
from ..exercises.rules import AngleCounterRule


@dataclass
class RepState:
    """Live state for one counter rule across frames."""

    angle: float = 0.0
    count: int = 0
    stage: str = "up"

    # Fields for compatibility with custom ROM/speed/violation cases
    good: int = 0
    bad: int = 0
    speed_warning: bool = False
    reached_bottom: bool = False


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

        # Check if any rule requires stateful ROM checks or speed checks
        has_custom = any(
            r.rom_max_angle is not None or r.min_rep_frames > 0 for r in rules
        )
        if has_custom:
            from .additional_casses import CustomCounterHelper
            self._helper = CustomCounterHelper(self)
        else:
            self._helper = None

    @property
    def primary(self) -> RepState:
        """State backing the displayed rep count (first counter rule)."""
        return next(iter(self.states.values()))

    def update(
        self,
        angles: Dict[str, Optional[float]],
        violation_names: Optional[Set[str]] = None,
    ) -> Dict[str, RepState]:
        """Feed in the current angle for each rule; advance counts/stages."""
        if self._helper:
            return self._helper.update(angles, violation_names)

        # Original, simple generic counter code
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
                    state.good += 1  # default simple reps are always good
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
            bad = any(v.severity in ("error", "warning") for v in self._violations.values())
            good = not bad
        result = RepResult(
            number=rep_number,
            good=good,
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

### FILE: [src/utils/camera_side.py](src/utils/camera_side.py)

```py
import dataclasses

class CameraSideDetector:
    def __init__(self, target_frames: int = 30):
        self.target_frames = target_frames
        self.frame_count = 0
        self.left_vis_sum = 0.0
        self.right_vis_sum = 0.0
        self.detected_side = None

    def process_frame(self, landmarks) -> str | None:
        if self.detected_side is not None:
            return self.detected_side

        left_joints = [11, 13, 15, 23, 25, 27]
        right_joints = [12, 14, 16, 24, 26, 28]

        l_vis = sum(landmarks[i].visibility for i in left_joints) / len(left_joints)
        r_vis = sum(landmarks[i].visibility for i in right_joints) / len(right_joints)

        self.left_vis_sum += l_vis
        self.right_vis_sum += r_vis
        self.frame_count += 1

        if self.frame_count >= self.target_frames:
            if self.left_vis_sum > self.right_vis_sum:
                self.detected_side = "left"
            else:
                self.detected_side = "right"
            return self.detected_side

        return None


def normalize_name(name: str) -> str:
    for suffix in ["_left", "_right", "_l", "_r"]:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def get_joints_side(joints) -> str:
    left_count = sum(1 for j in joints if j >= 7 and j <= 32 and j % 2 != 0)
    right_count = sum(1 for j in joints if j >= 7 and j <= 32 and j % 2 == 0)
    if left_count > right_count:
        return "left"
    elif right_count > left_count:
        return "right"
    return "both"


def adapt_rules(rules, target_side: str):
    adapted = []
    target_side_normalized_names = set()
    for rule in rules:
        side = get_joints_side(rule.joints)
        if side == target_side:
            target_side_normalized_names.add(normalize_name(rule.name))

    for rule in rules:
        side = get_joints_side(rule.joints)
        if side == target_side or side == "both":
            adapted.append(rule)
        elif side != "both":
            norm_name = normalize_name(rule.name)
            if norm_name not in target_side_normalized_names:
                new_joints = []
                for j in rule.joints:
                    if j >= 7 and j <= 32:
                        is_odd = (j % 2 != 0)
                        if target_side == "left" and not is_odd:
                            new_joints.append(j - 1)
                        elif target_side == "right" and is_odd:
                            new_joints.append(j + 1)
                        else:
                            new_joints.append(j)
                    else:
                        new_joints.append(j)
                new_rule = dataclasses.replace(rule, joints=tuple(new_joints))
                adapted.append(new_rule)
    return adapted
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


def get_points(indices, landmarks, w, h, threshold: float = 0.5):
    pts = []
    for i in indices:
        lm = landmarks[i]
        if hasattr(lm, "visibility") and lm.visibility < threshold:
            continue
        pts.append((int(lm.x * w), int(lm.y * h)))
    return pts


def calc_distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])
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


def draw_skeleton(frame, pts, colors, is_bad=False, custom_color=None):
    if len(pts) < 3:
        return

    # Dodger-blue BGR = (235, 145, 30) -> RGB(30,145,235) bright blue
    SKEL_COLOR = (255, 255, 255)
    if custom_color is not None:
        line_color = custom_color
        point_color = custom_color
    else:
        line_color = colors.ERROR if is_bad else SKEL_COLOR
        point_color = colors.ERROR if is_bad else SKEL_COLOR

    LINE_W = 5    # thin line — exactly like the reference image
    RADIUS = 12   # circle radius slightly bigger than line width
    BORDER_W = 8    # circle border — same weight as the lines

    def _edge_point(src, dst, r):
        """Point on the edge of the circle at *src* facing *dst*.
        Lines are drawn FROM here so they never cross into the circle."""
        dx, dy = dst[0] - src[0], dst[1] - src[1]
        dist = math.hypot(dx, dy)
        if dist < 1:
            return src
        return (int(src[0] + dx / dist * r),
                int(src[1] + dy / dist * r))

    p0, p1, p2 = pts[0], pts[1], pts[2]

    # ① Lines drawn FIRST — sit behind the circles
    cv2.line(frame,
             _edge_point(p0, p1, RADIUS), _edge_point(p1, p0, RADIUS),
             line_color, LINE_W, cv2.LINE_AA)
    cv2.line(frame,
             _edge_point(p1, p2, RADIUS), _edge_point(p2, p1, RADIUS),
             line_color, LINE_W, cv2.LINE_AA)

    # ② Hollow circles drawn LAST — always on top, clean edges, never filled
    for p in pts:
        cv2.circle(frame, p, RADIUS, point_color, BORDER_W, cv2.LINE_AA)



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

    The arc radius is set LARGER than the skeleton circle (RADIUS=22) so the
    arc appears clearly OUTSIDE the joint circle — never overlapping it.
    Only the arc is drawn here; the numeric label is rendered by draw_angle_labels.
    """
    # Arc must be bigger than the skeleton circle radius (22px) to sit outside it
    ARC_RADIUS = 42   # clearly outside the 22px skeleton circle

    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    angle1 = math.degrees(math.atan2(ba[1], ba[0]))
    angle2 = math.degrees(math.atan2(bc[1], bc[0]))

    start_angle = int(angle1)
    end_angle   = int(angle2)

    # Always draw the smallest arc (the actual angle, not the reflex)
    if end_angle < start_angle:
        end_angle += 360
    if end_angle - start_angle > 180:
        start_angle, end_angle = end_angle, start_angle + 360

    color = colors.ERROR if is_bad else colors.HIGHLIGHT

    cv2.ellipse(frame, b, (ARC_RADIUS, ARC_RADIUS),
                0, start_angle, end_angle, color, 2, cv2.LINE_AA)


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
        # Don't show N/A label when angle couldn't be computed
        if v.angle is None:
            continue
        color = colors.ERROR if v.is_error else colors.HIGHLIGHT
        text = f"{int(round(v.angle))} deg"

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


def draw_wrist_line(frame, left_wrist, right_wrist, colors, custom_color=None):
    """Draw a line between left and right wrists (for shoulder press peak position)."""
    line_color = custom_color if custom_color is not None else colors.HIGHLIGHT
    cv2.line(frame, left_wrist, right_wrist, line_color, 3, cv2.LINE_AA)
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
from .exercises.registry import registry
from .services.gym_engine import GymEngine

DEFAULT_EXERCISE = "cable_chest_fly"


def main():
    args = sys.argv[1:]

    exercise_key = args[0].lower() if len(args) >= 1 else None

    # Parse CLI flags: 'c' for webcam, 's' for saving output
    lower_args = [arg.lower() for arg in args[1:]]
    save_flag = "s" in lower_args
    settings.SAVE_OUTPUT = save_flag

    use_webcam_flag = "c" in lower_args
    if use_webcam_flag:
        settings.USE_WEBCAM = True
        video_path = None
    else:
        remaining_args = [arg for arg in args[1:] if arg.lower() not in ("s", "c")]
        video_path = remaining_args[0] if remaining_args else None

    # The CLI simply asks the registry for an exercise — it knows nothing about
    # which exercises exist. GymEngine stays completely unaware of the registry.
    if exercise_key and not registry.exists(exercise_key):
        print(f"Unknown exercise '{exercise_key}'.")
        print(f"Available: {', '.join(registry.list())}")
        sys.exit(1)

    exercise = (
        registry.get(exercise_key) if exercise_key else registry.get(DEFAULT_EXERCISE)
    )

    if video_path:
        import os
        if not os.path.exists(video_path):
            alt_path = os.path.join("videos", video_path)
            if os.path.exists(alt_path):
                video_path = alt_path

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

- Files exported: 36
- Lines exported: 2853
