"""Push-Up exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Camera, Exercise, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class PushUpExercise(Exercise):
    name: str = "Push-Up"
    camera: Camera = Camera.SIDE
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=160,
                down_angle=90,
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=150,
                max_angle=180,
                message="Keep your back straight",
                severity=Severity.ERROR,
            ),
            AngleValidationRule(
                name="elbow_unlocked",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=170,
                message="Don't lock your elbows",
                severity=Severity.WARNING,
            ),
        ]
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Bodyweight chest, triceps and core exercise.",
            muscle_groups=("chest", "triceps", "shoulders", "core"),
        )
    )
