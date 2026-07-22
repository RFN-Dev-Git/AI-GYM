"""Lat Pulldown exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Camera, Exercise, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class LatPulldownExercise(Exercise):
    name: str = "Lat Pulldown"
    camera: Camera = Camera.SIDE

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=165,      # Arms almost fully extended
                down_angle=65,     # Bar pulled to upper chest
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=145,
                max_angle=180,
                message="Keep your back straight",
                severity=Severity.ERROR,
            ),
            AngleValidationRule(
                name="avoid_locking_elbows",
                joints=PoseSegments.LEFT_ARM,
                min_angle=15,
                max_angle=175,
                message="Don't lock your elbows",
                severity=Severity.WARNING,
            ),
            AngleValidationRule(
                name="full_pull",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=75,
                message="Pull the bar all the way down",
                severity=Severity.WARNING,
            ),
        ]
    )

    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Lat Pulldown machine exercise.",
            muscle_groups=(
                "latissimus dorsi",
                "teres major",
                "trapezius",
                "rhomboids",
                "biceps",
            ),
        )
    )
