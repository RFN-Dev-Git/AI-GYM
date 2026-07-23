"""Form-validation evaluation.

This module is the ONE place that knows *how* to turn a ValidationRule into a
pass/fail result. GymEngine never evaluates rules itself — it only calls
:func:`validate_all`. That indirection is what keeps the engine closed for
modification when new rule *kinds* are added later (see the dispatch note on
:func:`validate_all` below).

Rules stay behaviour-free by design (see the rules module docstring); all
execution logic lives here and only here.
"""

from dataclasses import dataclass
from typing import Iterable, Sequence

from ..utils.geometry import calc_angle, get_points, calc_distance
from .rules import AngleValidationRule, AngleROMValidationRule, DistanceValidationRule, ShrugValidationRule, Severity, Stage


@dataclass
class ValidationResult:
    """Outcome of evaluating a single rule on one frame."""

    rule_name: str
    message: str
    severity: Severity
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

    if state.stage == Stage.DOWN and not getattr(state, "reached_bottom", False):
        msg = f"Go deeper — target <= {int(rule.min_rom_angle)} deg"
        return ValidationResult(rule.name, msg, rule.severity, False, angle, joints=rule.joints)

    if state.stage == Stage.RETURNING:
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
    pts1 = get_points(rule.measurement, landmarks, width, height)
    pts2 = get_points(rule.reference, landmarks, width, height)

    if len(pts1) < 2 or len(pts2) < 2:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=())

    distance = calc_distance(pts1[0], pts1[1])
    reference_distance = calc_distance(pts2[0], pts2[1])

    if reference_distance == 0:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=())

    ratio = distance / reference_distance
    passed = rule.min_ratio <= ratio <= rule.max_ratio

    return ValidationResult(
        rule.name, rule.message, rule.severity, passed, ratio, joints=rule.measurement
    )


def evaluate_shrug_rule(
    rule: ShrugValidationRule,
    landmarks,
    width: int,
    height: int,
) -> ValidationResult:
    """Evaluate a ShrugValidationRule based on shoulder height difference."""
    # Left shoulder (11), Right shoulder (12)
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]

    if left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=())

    # Get normalized Y coordinates (inverted because Y increases downward)
    left_y = left_shoulder.y
    right_y = right_shoulder.y

    # Calculate the absolute difference
    shoulder_delta = abs(left_y - right_y)

    # Normalize by torso height (hip to shoulder) for scale invariance
    left_hip = landmarks[23]
    right_hip = landmarks[24]
    hip_y = (left_hip.y + right_hip.y) / 2
    shoulder_y = (left_y + right_y) / 2
    torso_height = abs(shoulder_y - hip_y)

    if torso_height == 0:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=())

    normalized_delta = shoulder_delta / torso_height
    passed = normalized_delta <= rule.threshold

    return ValidationResult(
        rule.name, rule.message, rule.severity, passed, normalized_delta, joints=(11, 12)
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

    Dispatch note: this is a deliberately small ``isinstance`` chain — one
    branch per concrete rule kind (ROM and distance first, the angle rule as
    the catch-all). With three kinds it is the simplest thing that works and
    reads top-to-bottom like a table of contents. A registry-based dispatcher
    was considered and rejected: it would add indirection (registration,
    lookup, ordering) without paying for itself until the number of rule
    kinds is much larger. To add a new kind: write one ``evaluate_*``
    function above and add one branch here.
    """
    results = []
    for rule in rules:
        if isinstance(rule, AngleROMValidationRule):
            state = (states or {}).get(rule.name)
            results.append(evaluate_rom_rule(rule, landmarks, width, height, state))
        elif isinstance(rule, DistanceValidationRule):
            results.append(evaluate_distance_rule(rule, landmarks, width, height))
        elif isinstance(rule, ShrugValidationRule):
            results.append(evaluate_shrug_rule(rule, landmarks, width, height))
        else:
            results.append(evaluate_rule(rule, landmarks, width, height))
    return results


def violations(results: Sequence[ValidationResult]) -> list[ValidationResult]:
    """Filter a batch of results down to the ones that failed."""
    return [r for r in results if not r.passed]
