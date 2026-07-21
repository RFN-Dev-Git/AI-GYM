"""Cable Chest Fly exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Exercise
from .rules import AngleCounterRule, AngleValidationRule


@dataclass
class CableChestFlyExercise(Exercise):
    name: str = "Cable Chest Fly"

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="left",
                joints=PoseSegments.LEFT_ELBOW_ELEVATION,  # L_HIP -> L_SHOULDER -> L_ELBOW
                up_angle=110,
                down_angle=58,
                up_stage="open",
                down_stage="close",
            ),
            AngleCounterRule(
                name="right",
                joints=PoseSegments.RIGHT_ELBOW_ELEVATION,  # R_HIP -> R_SHOULDER -> R_ELBOW
                up_angle=110,
                down_angle=58,
                up_stage="open",
                down_stage="close",
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="chest_up",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=120,
                max_angle=180,
                message="Keep chest up — don't roll shoulders forward",
                severity="warning",
            ),
        ]
    )

    metadata: dict = field(
        default_factory=lambda: {
            "description": "Cable Chest Fly. Pectoral isolation via shoulder adduction.",
            "muscle_groups": ["pectorals", "anterior deltoid"],
        }
    )
