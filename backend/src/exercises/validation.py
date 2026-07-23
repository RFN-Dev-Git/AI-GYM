"""Form-validation evaluation - now FULL 3D with Shrug support.

This module evaluates rules using 3D world landmarks for true body angles.
2D fallback kept for cases where world landmarks unavailable.

All angles now calculated in 3D world space (meters) -> camera independent.
Rendering still uses 2D pixel positions.

Merged: 
- Our 3D logic (calc_angle_3d, world_landmarks support)
- Friend's ShrugValidationRule (lateral raise shoulder shrug detection)
"""

from dataclasses import dataclass
from typing import Iterable, Sequence

from ..utils.geometry import (
    calc_angle, calc_angle_3d, 
    get_points, get_points_3d, 
    calc_distance, calc_distance_3d, calc_distance_ratio_3d
)
from .rules import (
    AngleValidationRule, AngleROMValidationRule, DistanceValidationRule, 
    ShrugValidationRule, Severity, Stage
)


@dataclass
class ValidationResult:
    """Outcome of evaluating a single rule on one frame."""
    rule_name: str
    message: str
    severity: Severity
    passed: bool
    angle: float | None   # Now 3D angle or ratio or delta
    joints: tuple = ()  # the rule's landmark triple, carried for rendering
    is_3d: bool = True  # Whether this was computed in 3D


def evaluate_rule(
    rule: AngleValidationRule, 
    image_landmarks, 
    world_landmarks,
    width: int, 
    height: int,
    use_3d: bool = True
) -> ValidationResult:
    """Evaluate angle rule - 3D preferred, 2D fallback."""
    
    angle = None
    
    # Try 3D first if world landmarks available and use_3d enabled
    if use_3d and world_landmarks is not None and len(world_landmarks) > max(rule.joints):
        pts_3d = get_points_3d(rule.joints, world_landmarks)
        if len(pts_3d) >= 3:
            angle = calc_angle_3d(*pts_3d)
    
    # 2D fallback
    if image_landmarks is not None:
        pts_2d = get_points(rule.joints, image_landmarks, width, height)
        if angle is None and len(pts_2d) >= 3:
            angle = calc_angle(*pts_2d)
    
    checked = 0.0 if angle is None else angle
    passed = rule.min_angle <= checked <= rule.max_angle
    
    return ValidationResult(
        rule.name, rule.message, rule.severity, passed, angle, 
        joints=rule.joints, is_3d=use_3d
    )


def evaluate_rom_rule(
    rule: AngleROMValidationRule,
    image_landmarks,
    world_landmarks,
    width: int,
    height: int,
    state,
    use_3d: bool = True
) -> ValidationResult:
    """Evaluate ROM rule using 3D angles."""
    
    angle = None
    
    if use_3d and world_landmarks is not None:
        pts_3d = get_points_3d(rule.joints, world_landmarks)
        if len(pts_3d) >= 3:
            angle = calc_angle_3d(*pts_3d)
    
    if angle is None and image_landmarks is not None:
        pts = get_points(rule.joints, image_landmarks, width, height)
        if len(pts) >= 3:
            angle = calc_angle(*pts)

    if angle is None:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=rule.joints, is_3d=use_3d)

    if state is None:
        return ValidationResult(rule.name, rule.message, rule.severity, True, angle, joints=rule.joints, is_3d=use_3d)

    if state.stage == Stage.DOWN and not getattr(state, "reached_bottom", False):
        msg = f"Go deeper — target <= {int(rule.min_rom_angle)} deg"
        return ValidationResult(rule.name, msg, rule.severity, False, angle, joints=rule.joints, is_3d=use_3d)

    if state.stage == Stage.RETURNING:
        msg = f"Extend fully — target >= {int(rule.max_rom_angle)} deg"
        return ValidationResult(rule.name, msg, rule.severity, False, angle, joints=rule.joints, is_3d=use_3d)

    return ValidationResult(rule.name, rule.message, rule.severity, True, angle, joints=rule.joints, is_3d=use_3d)


def evaluate_distance_rule(
    rule: DistanceValidationRule,
    image_landmarks,
    world_landmarks,
    width: int,
    height: int,
    use_3d: bool = True
) -> ValidationResult:
    """Evaluate distance rule - 3D ratio is more accurate (includes depth)."""
    
    ratio = None
    
    if use_3d and world_landmarks is not None:
        pts1_3d = get_points_3d(rule.measurement, world_landmarks)
        pts2_3d = get_points_3d(rule.reference, world_landmarks)
        if len(pts1_3d) >= 2 and len(pts2_3d) >= 2:
            ratio = calc_distance_ratio_3d(pts1_3d, pts2_3d)
    
    if ratio is None and image_landmarks is not None:
        pts1 = get_points(rule.measurement, image_landmarks, width, height)
        pts2 = get_points(rule.reference, image_landmarks, width, height)
        if len(pts1) >= 2 and len(pts2) >= 2:
            distance = calc_distance(pts1[0], pts1[1])
            reference_distance = calc_distance(pts2[0], pts2[1])
            if reference_distance != 0:
                ratio = distance / reference_distance

    if ratio is None:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=(), is_3d=use_3d)

    passed = rule.min_ratio <= ratio <= rule.max_ratio

    return ValidationResult(
        rule.name, rule.message, rule.severity, passed, ratio, joints=rule.measurement, is_3d=use_3d
    )


def evaluate_shrug_rule(
    rule: ShrugValidationRule,
    image_landmarks,
    world_landmarks,
    width: int,
    height: int,
    use_3d: bool = True
) -> ValidationResult:
    """Evaluate ShrugValidationRule - detects trap shrugging during lateral raises.
    
    3D mode: uses world landmarks Y difference in meters (more accurate, depth independent)
    2D mode: uses normalized image Y difference normalized by torso height
    """
    # Try 3D first if available
    if use_3d and world_landmarks is not None and len(world_landmarks) > 24:
        try:
            left_shoulder = world_landmarks[11]
            right_shoulder = world_landmarks[12]
            left_hip = world_landmarks[23]
            right_hip = world_landmarks[24]
            
            # World coordinates: Y is up/down in meters, origin at hips
            left_y = getattr(left_shoulder, 'y', 0)
            right_y = getattr(right_shoulder, 'y', 0)
            shoulder_delta = abs(left_y - right_y)
            
            # Normalize by torso height in 3D (shoulder to hip distance)
            hip_y = (getattr(left_hip, 'y', 0) + getattr(right_hip, 'y', 0)) / 2
            shoulder_y = (left_y + right_y) / 2
            torso_height = abs(shoulder_y - hip_y)
            
            if torso_height == 0:
                return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=(11,12), is_3d=True)
            
            normalized_delta = shoulder_delta / torso_height
            passed = normalized_delta <= rule.threshold
            
            return ValidationResult(
                rule.name, rule.message, rule.severity, passed, normalized_delta, joints=(11, 12), is_3d=True
            )
        except (IndexError, AttributeError):
            pass  # Fallback to 2D
    
    # 2D fallback (original friend's logic)
    if image_landmarks is None or len(image_landmarks) <= 24:
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=(11,12), is_3d=False)
    
    try:
        left_shoulder = image_landmarks[11]
        right_shoulder = image_landmarks[12]
        
        if getattr(left_shoulder, 'visibility', 1.0) < 0.5 or getattr(right_shoulder, 'visibility', 1.0) < 0.5:
            return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=(11,12), is_3d=False)
        
        left_y = left_shoulder.y
        right_y = right_shoulder.y
        shoulder_delta = abs(left_y - right_y)
        
        left_hip = image_landmarks[23]
        right_hip = image_landmarks[24]
        hip_y = (left_hip.y + right_hip.y) / 2
        shoulder_y = (left_y + right_y) / 2
        torso_height = abs(shoulder_y - hip_y)
        
        if torso_height == 0:
            return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=(11,12), is_3d=False)
        
        normalized_delta = shoulder_delta / torso_height
        passed = normalized_delta <= rule.threshold
        
        return ValidationResult(
            rule.name, rule.message, rule.severity, passed, normalized_delta, joints=(11, 12), is_3d=False
        )
    except (IndexError, AttributeError):
        return ValidationResult(rule.name, rule.message, rule.severity, True, None, joints=(11,12), is_3d=False)


def validate_all(
    rules: Iterable,
    image_landmarks,
    world_landmarks=None,
    width: int = 1000,
    height: int = 1000,
    states: dict | None = None,
    use_3d: bool = True
) -> list[ValidationResult]:
    """
    Run every validation rule - FULL 3D MODE with backward compat and Shrug support.
    """
    # Backward compatibility detection
    if isinstance(world_landmarks, int):
        states = height if isinstance(height, dict) else states
        height = width
        width = world_landmarks
        world_landmarks = image_landmarks
    elif isinstance(width, dict) and states is None:
        states = width
        width = 1000
        height = 1000
    
    results = []
    for rule in rules:
        if isinstance(rule, AngleROMValidationRule):
            state = (states or {}).get(rule.name) if states else None
            results.append(evaluate_rom_rule(rule, image_landmarks, world_landmarks, width, height, state, use_3d))
        elif isinstance(rule, DistanceValidationRule):
            results.append(evaluate_distance_rule(rule, image_landmarks, world_landmarks, width, height, use_3d))
        elif isinstance(rule, ShrugValidationRule):
            results.append(evaluate_shrug_rule(rule, image_landmarks, world_landmarks, width, height, use_3d))
        else:
            results.append(evaluate_rule(rule, image_landmarks, world_landmarks, width, height, use_3d))
    return results


def violations(results: Sequence[ValidationResult]) -> list[ValidationResult]:
    """Filter a batch of results down to the ones that failed."""
    return [r for r in results if not r.passed]
