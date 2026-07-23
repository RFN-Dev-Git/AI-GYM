"""Squat exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Camera, Exercise, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class SquatExercise(Exercise):
    name: str = "Squat"
    camera: Camera = Camera.SIDE
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee",
                joints=PoseSegments.LEFT_LEG,
                up_angle=160,
                down_angle=70,
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=60,
                max_angle=180,
                message="Keep your back straight",
                severity=Severity.ERROR,
            ),
            AngleValidationRule(
                name="knee_aligned",
                joints=PoseSegments.LEFT_LEG,
                min_angle=30,
                max_angle=180,
                message="Keep your knee aligned",
                severity=Severity.WARNING,
            ),
        ]
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Compound lower-body strength exercise.",
            muscle_groups=("quadriceps", "glutes", "hamstrings", "core"),
        )
    )
