# CODEBASE SNAPSHOT

## PROJECT STRUCTURE

```text
AI-GYM/
├── src
│   ├── assets
│   │   ├── models
│   │   │   ├── pose_landmarker_full.task
│   │   │   ├── pose_landmarker_heavy.task
│   │   │   └── pose_landmarker_lite.task
│   │   └── videos
│   │       ├── 12727710_1080_1920_60fps.mp4
│   │       ├── 13692089_720_1280_24fps.mp4
│   │       ├── 13902118_720_1280_30fps.mp4
│   │       ├── 13944287_720_1280_30fps.mp4
│   │       ├── 13944406_720_1280_30fps.mp4
│   │       ├── 15885581_360_640_25fps.mp4
│   │       ├── 15885583_720_1280_25fps.mp4
│   │       ├── 4686178-hd_1080_1920_30fps.mp4
│   │       ├── back.mp4
│   │       ├── Legpress.demo.video.mp4
│   │       ├── move.mp4
│   │       ├── Pushups.demo.video.mp4
│   │       ├── Squats.demo.video.mp4
│   │       └── vv.mp4
│   ├── config
│   │   ├── __init__.py
│   │   └── app_settings.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── colors.py
│   │   └── pose_segments.py
│   ├── exercises
│   │   ├── __init__.py
│   │   ├── biceps_curl.py
│   │   ├── exercise.py
│   │   ├── latpulldown.py
│   │   ├── leg_press.py
│   │   ├── pushup.py
│   │   ├── rules.py
│   │   ├── shoulder_press.py
│   │   ├── squat.py
│   │   └── validation.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── gym_engine.py
│   │   ├── pose_service.py
│   │   └── rep_counter.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── geometry.py
│   │   └── render.py
│   ├── __init__.py
│   └── main.py
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── Makefile
├── README.md
└── requirements.txt
```

## SOURCE FILES

---

### FILE: [src/config/__init__.py](src/config/__init__.py)

```py
from .app_settings import settings

__all__ = ["settings"]
```

---

### FILE: [src/config/app_settings.py](src/config/app_settings.py)

```py
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    MODEL_PATH: str
    VIDEO_PATH: str | None = None

    DISPLAY_MAX_WIDTH: int = 1280

    USE_WEBCAM: bool = False
    WEBCAM_INDEX: int = 0

    SAVE_OUTPUT: bool = False
    OUTPUT_PATH: str = "./output/result.mp4"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


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
when building their CounterRule / ValidationRule configurations, which keeps the
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
```

---

### FILE: [src/exercises/__init__.py](src/exercises/__init__.py)

```py
"""Exercise configuration package.

Everything in here is *data*, not behaviour. An exercise is described entirely
by an :class:`Exercise` instance built from :class:`CounterRule` and
:class:`ValidationRule` dataclasses. GymEngine consumes these objects and never
needs to know which exercise it is running.

Each exercise lives in its own module (``pushup.py``, ``squat.py``, ...); this
package re-exports them so callers can do ``from src.exercises import
PushUpExercise`` without knowing the internal file layout. Adding a new exercise
= adding one new self-contained module + one import line below. No engine code
changes.
"""

from .biceps_curl import BicepsCurlExercise
from .exercise import DisplaySettings, Exercise
from .latpulldown import LatPulldownExercise
from .leg_press import LegPressExercise
from .pushup import PushUpExercise
from .rules import CounterRule, ValidationRule
from .shoulder_press import ShoulderPressExercise
from .squat import SquatExercise
from .validation import ValidationResult, validate_all, violations

__all__ = [
    "CounterRule",
    "ValidationRule",
    "Exercise",
    "DisplaySettings",
    "ValidationResult",
    "validate_all",
    "violations",
    "PushUpExercise",
    "SquatExercise",
    "LegPressExercise",
    "ShoulderPressExercise",
    "BicepsCurlExercise",
    "LatPulldownExercise",
]
```

---

### FILE: [src/exercises/biceps_curl.py](src/exercises/biceps_curl.py)

```py
"""Biceps Curl exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import CounterRule, ValidationRule


@dataclass
class BicepsCurlExercise(Exercise):
    name: str = "Biceps Curl"
    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=160,
                down_angle=30,
            ),
        ]
    )
    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            ValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=150,
                max_angle=180,
                message="Keep your back straight",
                severity="error",
            ),
            ValidationRule(
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

### FILE: [src/exercises/exercise.py](src/exercises/exercise.py)

```py
"""The Exercise configuration object — the single thing GymEngine needs."""

from dataclasses import dataclass, field
from typing import Any

from .rules import CounterRule, ValidationRule


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
    counter_rules: list[CounterRule] = field(default_factory=list)
    validation_rules: list[ValidationRule] = field(default_factory=list)
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
from .rules import CounterRule, ValidationRule


@dataclass
class LatPulldownExercise(Exercise):
    name: str = "Lat Pulldown"

    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=165,      # Arms almost fully extended
                down_angle=65,     # Bar pulled to upper chest
            ),
        ]
    )

    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            ValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=145,
                max_angle=180,
                message="Keep your back straight",
                severity="error",
            ),
            ValidationRule(
                name="avoid_locking_elbows",
                joints=PoseSegments.LEFT_ARM,
                min_angle=15,
                max_angle=175,
                message="Don't lock your elbows",
                severity="warning",
            ),
            ValidationRule(
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

### FILE: [src/exercises/leg_press.py](src/exercises/leg_press.py)

```py
"""Leg Press exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import CounterRule, ValidationRule


@dataclass
class LegPressExercise(Exercise):
    name: str = "Leg Press"
    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="knee",
                joints=PoseSegments.LEFT_LEG,
                up_angle=160,
                down_angle=90,
            ),
        ]
    )
    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            ValidationRule(
                name="knee_unlocked",
                joints=PoseSegments.LEFT_LEG,
                min_angle=0,
                max_angle=170,
                message="Don't lock your knees",
                severity="warning",
            ),
            ValidationRule(
                name="hip_aligned",
                joints=PoseSegments.LEFT_HIP_ALIGN,
                min_angle=0,
                max_angle=180,
                message="Maintain hip alignment",
                severity="error",
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

### FILE: [src/exercises/pushup.py](src/exercises/pushup.py)

```py
"""Push-Up exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import CounterRule, ValidationRule


@dataclass
class PushUpExercise(Exercise):
    name: str = "Push-Up"
    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=160,
                down_angle=90,
            ),
        ]
    )
    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            ValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=150,
                max_angle=180,
                message="Keep your back straight",
                severity="error",
            ),
            ValidationRule(
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
class CounterRule:
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
class ValidationRule:
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
from .rules import CounterRule, ValidationRule


@dataclass
class ShoulderPressExercise(Exercise):
    name: str = "Shoulder Press"
    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=160,
                down_angle=60,
            ),
        ]
    )
    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            ValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=150,
                max_angle=180,
                message="Keep your back straight",
                severity="error",
            ),
            ValidationRule(
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
from .rules import CounterRule, ValidationRule


@dataclass
class SquatExercise(Exercise):
    name: str = "Squat"
    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="knee",
                joints=PoseSegments.LEFT_LEG,
                up_angle=160,
                down_angle=70,
            ),
        ]
    )
    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            ValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=60,
                max_angle=180,
                message="Keep your back straight",
                severity="error",
            ),
            ValidationRule(
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

This module is the ONE place that knows *how* to turn a ValidationRule into a
pass/fail result. GymEngine never evaluates rules itself — it only calls
:func:`validate_all`. That indirection is what keeps the engine closed for
modification when new rule *kinds* are added later (see EXTENSION POINT below).
"""

from dataclasses import dataclass
from typing import Iterable, Sequence

from ..utils.geometry import calc_angle, get_points
from .rules import ValidationRule


@dataclass
class ValidationResult:
    """Outcome of evaluating a single ValidationRule on one frame."""

    rule_name: str
    message: str
    severity: str
    passed: bool
    angle: float
    joints: tuple = ()  # the rule's landmark triple, carried for rendering


def evaluate_rule(
    rule: ValidationRule, landmarks, width: int, height: int
) -> ValidationResult:
    """Evaluate one angle-based ValidationRule against the detected pose.

    EXTENSION POINT
    ----------------
    Today every ValidationRule is angle-based, so we just measure the angle at
    ``rule.joints``. To support the future rule kinds from the brief
    (distance-based, alignment, symmetry, richer feedback) you only need to:

        1. add a new rule dataclass in ``rules.py``
           (e.g. ``DistanceValidationRule``), and
        2. branch on its type here (``isinstance`` or a ``kind`` field).

    GymEngine calls ``validate_all`` and reads ``ValidationResult`` objects, so
    **it does not change** when a new rule kind appears.
    """
    pts = get_points(rule.joints, landmarks, width, height)
    angle = calc_angle(*pts) if len(pts) >= 3 else 0.0
    passed = rule.min_angle <= angle <= rule.max_angle
    return ValidationResult(
        rule.name, rule.message, rule.severity, passed, angle, joints=rule.joints
    )


def validate_all(
    rules: Iterable[ValidationRule], landmarks, width: int, height: int
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

__all__ = ["GymEngine", "PoseService", "RepCounter", "RepState"]
```

---

### FILE: [src/services/gym_engine.py](src/services/gym_engine.py)

```py
"""Generic, exercise-agnostic training engine."""

import os

import cv2

from ..config import settings
from ..core import Colors
from ..exercises.exercise import Exercise
from ..exercises.validation import ValidationResult, validate_all, violations
from ..utils.geometry import ComputedAngle, calc_angle, get_points
from ..utils.render import draw_angle_arc, draw_angle_labels, draw_skeleton, draw_stats, fit_to_screen
from .pose_service import PoseService
from .rep_counter import RepCounter


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
        self.colors = colors or Colors()
        # Optional maximum display width (e.g. DISPLAY_MAX_WIDTH). The frame is
        # first auto-fit to the detected screen; this only caps it further.
        self.display_width = display_width

    # ------------------------------------------------------------------
    # Analysis: pure logic, no I/O -> easy to unit test with fake landmarks.
    # ------------------------------------------------------------------
    def analyze(self, landmarks, width: int, height: int) -> FrameResult:
        """Compute angles, update the counter, and run validation rules."""
        angles = {}
        views = []  # unified per-rule angle views for the renderer

        for rule in self.exercise.counter_rules:
            pts = get_points(rule.joints, landmarks, width, height)
            angle = calc_angle(*pts) if len(pts) >= 3 else 0.0
            angles[rule.name] = angle
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            # Counter angles are never "failed" -> drawn with the highlight colour.
            views.append(ComputedAngle(name=rule.name, vertex=vertex, angle=angle, is_error=False))

        self.counter.update(angles)
        results = validate_all(self.exercise.validation_rules, landmarks, width, height)

        for res in results:
            pts = get_points(res.joints, landmarks, width, height)
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            views.append(
                ComputedAngle(name=res.rule_name, vertex=vertex, angle=res.angle, is_error=not res.passed)
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
        # any body landmark). Layout lives in utils/render.py.
        primary = self.counter.primary
        issues = violations(result.results)
        feedback = [r.message for r in issues]
        draw_stats(
            frame,
            exercise_name=self.exercise.name,
            reps=primary.count,
            stage=primary.stage,
            state="GOOD" if not issues else "BAD",
            angle=primary.angle,
            feedback=feedback,
            colors=self.colors,
        )

    # ------------------------------------------------------------------
    # Orchestration: video source + detection + render loop.
    # ------------------------------------------------------------------
    def run(self):
        if settings.USE_WEBCAM:
            cap = cv2.VideoCapture(settings.WEBCAM_INDEX)
        else:
            cap = cv2.VideoCapture(settings.VIDEO_PATH)

        if not cap.isOpened():
            raise RuntimeError("Cannot open video source")

        fps = 25  # fixed for deterministic timestamps

        writer = None
        if settings.SAVE_OUTPUT:
            os.makedirs(os.path.dirname(settings.OUTPUT_PATH), exist_ok=True)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(settings.OUTPUT_PATH, fourcc, fps, (width, height))

        pose_service = PoseService(settings.MODEL_PATH)
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
                frame_result = self.analyze(lm, w, h)
                self._render(frame, frame_result, lm, w, h)

            if writer:
                writer.write(frame)

            # Display-only resize: pose math + saved output use the original frame.
            frame = fit_to_screen(frame, max_width=self.display_width)
            cv2.imshow("AI Gym Trainer", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            frame_id += 1

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


class PoseService:
    def __init__(self, model_path: str):
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
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
"""Repetition counter driven entirely by CounterRule configuration."""

from dataclasses import dataclass
from typing import Dict, List

from ..exercises.rules import CounterRule


@dataclass
class RepState:
    """Live state for one counter rule across frames."""

    angle: float = 0.0
    count: int = 0
    stage: str = "up"


class RepCounter:
    """Counts repetitions from a list of CounterRule configurations.

    One :class:`RepState` is kept per rule, so an exercise can count from
    several angles at once (e.g. left + right side for symmetry) with no change
    to this class or to GymEngine. The on-screen rep count comes from the first
    rule (``primary``); the others remain available in ``states``.
    """

    def __init__(self, rules: List[CounterRule]):
        self.rules = rules
        self.states: Dict[str, RepState] = {r.name: RepState() for r in rules}

    @property
    def primary(self) -> RepState:
        """State backing the displayed rep count (first counter rule)."""
        return next(iter(self.states.values()))

    def update(self, angles: Dict[str, float]) -> Dict[str, RepState]:
        """Feed in the current angle for each rule; advance counts/stages."""
        for rule in self.rules:
            angle = angles.get(rule.name, 0.0)
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
    layer: ``GymEngine`` produces one ``ComputedAngle`` per ``CounterRule`` and
    per ``ValidationRule``, and the renderer iterates over them without knowing
    which exercise or rule produced them. Adding a rule (or a whole new
    exercise) therefore needs zero renderer changes.
    """

    name: str
    vertex: tuple          # pixel (x, y) of the middle/vertex joint
    angle: float
    is_error: bool         # True -> draw with the error colour


def calc_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag1 = math.hypot(*ba)
    mag2 = math.hypot(*bc)

    if mag1 == 0 or mag2 == 0:
        return 0.0

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
    stage: str,
    state: str,
    angle: float,
    feedback: list[str] | None = None,
    colors,
):
    """Draw the stats / coaching overlay in the bottom-left corner.

    The box is positioned with a small margin from the left and bottom edges
    and is clamped so it always stays fully inside the frame, regardless of
    resolution. It is intentionally NOT anchored to any body landmark — its
    position is fixed on screen.

    Core lines: exercise name, Reps, Stage, State, Current Angle.
    Exercise-specific feedback (validation cues) is appended below.
    """
    h, w = frame.shape[:2]
    feedback = feedback or []

    lines = [
        exercise_name,
        f"Reps: {reps}",
        f"Stage: {stage}",
        f"State: {state}",
        f"Angle: {int(angle)}°",
    ]
    # Exercise-specific feedback below the core information.
    for msg in feedback:
        lines.append(f"- {msg}")

    def line_color(text: str):
        if text.startswith("- "):
            return colors.ERROR
        if text.startswith("State: GOOD"):
            return colors.HIGHLIGHT
        if text.startswith("State: BAD"):
            return colors.ERROR
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
ANGLE_BASE_SCALE = 0.6      # font scale at a 1280px-wide frame (see _scale)
ANGLE_PADDING = 5           # inner padding of the label box (px)
ANGLE_OFFSET = 12           # push the label away from the joint (px)
ANGLE_BG_ALPHA = 0.55       # opacity of the semi-transparent backing
ANGLE_MIN_SCALE = 0.5
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

    ``views`` already contains one entry per CounterRule and per
    ValidationRule (built by GymEngine.analyze), so this function is completely
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
        text = f"{int(round(v.angle))}°"

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
from .config import settings
from .core import Colors
from .exercises import LatPulldownExercise, PushUpExercise
from .services.gym_engine import GymEngine


def main():
    # The engine is now fully generic: it runs whatever Exercise configuration
    # is handed to it. Swap PushUpExercise() for SquatExercise(), etc. — no
    # engine changes required.
    engine = GymEngine(
        LatPulldownExercise(),
        colors=Colors(),
        display_width=settings.DISPLAY_MAX_WIDTH,
    )

    engine.run()


if __name__ == "__main__":
    main()
```

---

### FILE: [requirements.txt](requirements.txt)

```txt
mediapipe==0.10.32
opencv_contrib_python==4.5.5.64
opencv_python==4.11.0.86
opencv_python_headless==4.11.0.86
pydantic_settings==2.14.2
```

---

## EXPORT SUMMARY

- Files exported: 25
- Lines exported: 1211
