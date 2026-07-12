"""Biceps Curl exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import CounterRule, ValidationRule


@dataclass
class BicepsCurlExercise(Exercise):
    name: str = "Biceps Curl"
    camera: str = "side"
    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,
                up_angle=160,
                down_angle=30,
            ),
        ]
    )
    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            ValidationRule(
                name="back_straight",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=150,
                max_angle=180,
                message="Keep your back straight",
                severity="error",
            ),
            ValidationRule(
                name="elbow_unlocked",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=170,
                message="Don't lock your elbows",
                severity="warning",
            ),
        ]
    )
    metadata: dict = field(
        default_factory=lambda: {
            "description": "Isolation exercise for the biceps.",
            "muscle_groups": ["biceps", "forearms"],
        }
    )
