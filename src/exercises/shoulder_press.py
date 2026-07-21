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
