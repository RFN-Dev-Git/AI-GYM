"""Squat exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import CounterRule, ValidationRule


@dataclass
class SquatExercise(Exercise):
    name: str = "Squat"
    camera: str = "side"
    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="knee",
                joints=PoseSegments.LEFT_LEG,
                up_angle=160,
                down_angle=70,
            ),
        ]
    )
    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            ValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=60,
                max_angle=180,
                message="Keep your back straight",
                severity="error",
            ),
            ValidationRule(
                name="knee_aligned",
                joints=PoseSegments.LEFT_LEG,
                min_angle=30,
                max_angle=180,
                message="Keep your knee aligned",
                severity="warning",
            ),
        ]
    )
    metadata: dict = field(
        default_factory=lambda: {
            "description": "Compound lower-body strength exercise.",
            "muscle_groups": ["quadriceps", "glutes", "hamstrings", "core"],
        }
    )
