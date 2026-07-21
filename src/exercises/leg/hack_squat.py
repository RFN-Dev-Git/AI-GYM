"""Hack Squat exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ...core.pose_segments import PoseSegments
from ..exercise import Exercise
from ..rules import AngleCounterRule, AngleValidationRule

@dataclass
class HackSquatExercise(Exercise):
    name: str = "Hack Squat"
    camera: str = "side"
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                up_angle=130,
                down_angle=90,
            ),
            AngleCounterRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                up_angle=130,
                down_angle=90,
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="knee_unlocked_left",
                joints=PoseSegments.LEFT_LEG,
                min_angle=60,
                max_angle=170,
                message="Don't lock your left knee",
                severity="warning",
            ),
            AngleValidationRule(
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
