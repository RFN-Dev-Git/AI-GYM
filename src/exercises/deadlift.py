"""Deadlift: Dissected — exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import CounterRule, ValidationRule


@dataclass
class DeadliftExercise(Exercise):
    name: str = "Deadlift: Dissected"

    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="knee",
                joints=PoseSegments.RIGHT_LEG,   # R_HIP -> R_KNEE -> R_ANKLE
                up_angle=165,
                down_angle=80,
                up_stage="lockout",
                down_stage="setup",
            ),
        ]
    )

    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            # Shoulder -> Hip -> Knee: detects back rounding under load
            ValidationRule(
                name="back_straight",
                joints=PoseSegments.RIGHT_HIP_HINGE,
                min_angle=40,
                max_angle=180,
                message="Keep your back straight — avoid rounding the lumbar spine",
                severity="error",
            ),
            # Ear -> Shoulder -> Hip: detects forward head / neck drop
            ValidationRule(
                name="neck_neutral",
                joints=PoseSegments.RIGHT_NECK_ALIGN,
                min_angle=140,
                max_angle=180,
                message="Keep your neck neutral — chin should follow the spine",
                severity="error",
            ),
        ]
    )

    metadata: dict = field(
        default_factory=lambda: {
            "description": "Deadlift: Dissected. Compound posterior-chain exercise.",
            "muscle_groups": ["hamstrings", "glutes", "erector spinae", "trapezius", "core"],
        }
    )
