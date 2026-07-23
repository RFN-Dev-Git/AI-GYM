"""The Exercise configuration object — the single thing GymEngine needs."""

from dataclasses import dataclass, field
from enum import Enum

from .rules import AngleCounterRule, LandmarkPair


class Camera(str, Enum):
    """Camera viewpoint the exercise is filmed/tracked from.

    Finite, closed vocabulary (an exercise is either filmed from one fixed
    side or tracked from both/all sides), so it is an Enum rather than a
    free-form string. A ``str`` Enum, so ``Camera.SIDE == "side"`` is
    ``True`` and legacy comparisons keep working.

    SIDE selects the side-aware pipeline (``CameraSideDetector`` +
    ``adapt_rules`` mirror left/right rules onto the visible side); BOTH
    skips it.
    """

    BOTH = "both"
    SIDE = "side"
    FRONT = "front"


@dataclass(frozen=True)
class ExerciseMetadata:
    """Strongly typed, immutable exercise metadata.

    Replaces the previous free-form ``metadata: dict``. Only fields the
    project actually uses are modelled — keeping this small and explicit is
    intentional (structured data should not hide in generic dictionaries).
    Tuples (not lists) keep instances hashable as well as immutable.

    Attributes:
        description:    One-line human description of the exercise.
        muscle_groups:  Primary muscle groups worked, in rough priority order.
    """

    description: str = ""
    muscle_groups: tuple[str, ...] = ()


@dataclass(frozen=True)
class SegmentLine:
    """Declarative "draw a straight line between two landmarks" display rule.

    Pure presentation configuration: the engine renders every entry in
    ``DisplaySettings.segment_lines`` without knowing which exercise asked for
    it (today only Shoulder Press uses one — the wrist-to-wrist line at the
    top of the press).

    Attributes:
        endpoints:     The landmark pair to connect with a line.
        active_angles: Names of counter rules whose live angles must ALL be
                       >= ``min_angle`` for the line to appear (e.g. both arm
                       angles > 90 = "arms overhead"). Empty = always drawn.
        min_angle:     Angle threshold (deg) for ``active_angles``.
        error_rule:    Optional validation-rule name; while that rule is
                       failing the line is drawn in the ERROR colour instead
                       of HIGHLIGHT (e.g. the wrist-distance rule).
    """

    endpoints: LandmarkPair
    active_angles: tuple[str, ...] = ()
    min_angle: float = 90.0
    error_rule: str | None = None


@dataclass
class DisplaySettings:
    """Optional, per-exercise presentation knobs.

    Kept separate from counting/validation so visual tweaks never leak into
    exercise logic. All fields are optional with safe defaults.
    """

    show_angle_arc: bool = False
    show_skeleton: bool = True
    show_validation_skeleton: bool = True  # set False to hide validation-rule joints
    segment_lines: list[SegmentLine] = field(default_factory=list)  # landmark-to-landmark lines


@dataclass
class Exercise:
    """A fully self-contained description of one exercise.

    An Exercise is *pure configuration*: it carries the repetition-counting
    rules, the form-validation rules, optional display settings, and typed
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
    # Holds any ValidationRule subclass: AngleValidationRule,
    # AngleROMValidationRule, or DistanceValidationRule.
    validation_rules: list = field(default_factory=list)
    display: DisplaySettings = field(default_factory=DisplaySettings)
    metadata: ExerciseMetadata = field(default_factory=ExerciseMetadata)
    camera: str = Camera.BOTH
