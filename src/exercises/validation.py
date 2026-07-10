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
