"""Hack Squat exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from src.core.pose_segments import PoseSegments
from src.exercises.exercise import Exercise
from src.exercises.rules import CounterRule, ValidationRule

@dataclass
class HackSquatExercise(Exercise):
    name: str = "Hack Squat"
    camera: str = "side"
    counter_rules: list[CounterRule] = field(
        default_factory=lambda: [
            CounterRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                up_angle=130,
                down_angle=90,
            ),
            CounterRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                up_angle=130,
                down_angle=90,
            ),
        ]
    )
    validation_rules: list[ValidationRule] = field(
        default_factory=lambda: [
            ValidationRule(
                name="knee_unlocked_left",
                joints=PoseSegments.LEFT_LEG,
                min_angle=60,
                max_angle=170,
                message="Don't lock your left knee",
                severity="warning",
            ),
            ValidationRule(
                name="knee_unlocked_right",
                joints=PoseSegments.RIGHT_LEG,
                min_angle=60,
                max_angle=170,
                message="Don't lock your right knee",
                severity="warning",
            )
        ]
    )
    metadata: dict = field(
        default_factory=lambda: {
            "description": "Machine-based lower-body squatting exercise emphasizing the quadriceps with dynamic hip movement.",
            "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        }
    )