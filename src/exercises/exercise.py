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
