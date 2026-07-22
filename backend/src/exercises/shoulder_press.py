"""Shoulder Press exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import L_SHOULDER, R_SHOULDER, L_WRIST, R_WRIST, PoseSegments
from .exercise import Camera, DisplaySettings, Exercise, ExerciseMetadata, SegmentLine
from .rules import (
    AngleCounterRule,
    AngleValidationRule,
    AngleROMValidationRule,
    DistanceValidationRule,
    Severity,
)


@dataclass
class ShoulderPressExercise(Exercise):
    name: str = "Shoulder Press"
    camera: Camera = Camera.BOTH
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
                severity=Severity.ERROR,
            ),
            AngleROMValidationRule(
                name="right_shoulder_rom",
                joints=PoseSegments.RIGHT_ARM_DIRECTION,
                min_rom_angle=40,
                max_rom_angle=160,
                message="Shoulder: Reach 160° up, 40-80° down",
                severity=Severity.ERROR,
            ),
            # ROM validation for elbow angles
            AngleROMValidationRule(
                name="left_elbow_rom",
                joints=PoseSegments.LEFT_ARM,
                min_rom_angle=60,
                max_rom_angle=170,
                message="Elbow: Reach 170° up, 60° down",
                severity=Severity.ERROR,
            ),
            AngleROMValidationRule(
                name="right_elbow_rom",
                joints=PoseSegments.RIGHT_ARM,
                min_rom_angle=60,
                max_rom_angle=170,
                message="Elbow: Reach 170° up, 60° down",
                severity=Severity.ERROR,
            ),
            # Distance validation: wrists should be at least shoulder-width apart
            # Name starts with counter rule name to auto-poison reps
            DistanceValidationRule(
                name="left_shoulder_wrist_distance",
                measurement=(L_WRIST, R_WRIST),      # wrist span being checked
                reference=(L_SHOULDER, R_SHOULDER),  # normalized to shoulder width
                min_ratio=1.2,  # Must be at least 1.2x shoulder width (stricter)
                max_ratio=3.0,
                message="Keep wrists wider than shoulders",
                severity=Severity.ERROR,
            ),
        ]
    )
    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(
            # Only arm (counter) skeletons — ROM-validation joints are the same
            # arms, so drawing them adds visual noise.
            show_validation_skeleton=False,
            segment_lines=[
                # Wrist-to-wrist line while both arms are overhead; turns red
                # when the wrist-distance rule is failing.
                SegmentLine(
                    endpoints=(L_WRIST, R_WRIST),
                    active_angles=("left_shoulder", "right_shoulder"),
                    min_angle=90,
                    error_rule="left_shoulder_wrist_distance",
                ),
            ],
        )
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Overhead pressing exercise for the shoulders.",
            muscle_groups=("shoulders", "triceps", "upper chest"),
        )
    )
