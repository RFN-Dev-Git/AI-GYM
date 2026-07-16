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
