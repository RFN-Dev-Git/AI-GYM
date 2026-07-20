"""Form-validation evaluation.

This module is the ONE place that knows *how* to turn an AngleValidationRule into a
pass/fail result. GymEngine never evaluates rules itself — it only calls
:func:`validate_all`. That indirection is what keeps the engine closed for
modification when new rule *kinds* are added later (see EXTENSION POINT below).
"""

from dataclasses import dataclass
from typing import Iterable, Sequence

from ..utils.geometry import calc_angle, get_points
from .rules import AngleValidationRule, AngleROMValidationRule

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
        else:
            results.append(evaluate_rule(rule, landmarks, width, height))
    return results


def violations(results: Sequence[ValidationResult]) -> list[ValidationResult]:
    """Filter a batch of results down to the ones that failed."""
    return [r for r in results if not r.passed]
