"""Leg Press exercise configuration (self-contained).

Counting logic:
  - DOWN phase: knee angle <= 110° (user is bending)
  - RETURNING: angle crosses back above 120°
  - Rep completes when angle >= 160° (fully extended)

ROM quality:
  - GOOD rep: must reach <= 80° at the bottom AND >= 160° at the top
  - BAD rep:  counted if the user reverses before reaching either extreme

Skeleton color:
  - Default (white) while at rest (UP stage, before rep starts)
  - RED while descending/returning but bottom not yet reached
  - GREEN once the bottom extreme (<= 80°) has been reached this rep
"""

from dataclasses import dataclass, field

from ...core.pose_segments import PoseSegments
from ..exercise import Camera, Exercise, DisplaySettings, ExerciseMetadata
from ..rules import AngleCounterRule, AngleROMValidationRule, Severity


@dataclass
class LegPressExercise(Exercise):
    name: str = "Leg Press"
    camera: Camera = Camera.SIDE

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                up_angle=120,       # crosses this going back up → RETURNING phase
                down_angle=110,     # <= 110° = DOWN phase begins
                min_rom_angle=80,   # must reach <= 80° for a GOOD rep (deep enough)
                max_rom_angle=160,  # must reach >= 160° for a GOOD rep (full extension)
            ),
            AngleCounterRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                up_angle=120,
                down_angle=110,
                min_rom_angle=80,
                max_rom_angle=160,
            ),
        ]
    )

    validation_rules: list[AngleROMValidationRule] = field(
        default_factory=lambda: [
            AngleROMValidationRule(
                name="knee_left",
                joints=PoseSegments.LEFT_LEG,
                min_rom_angle=80,
                max_rom_angle=160,
                message="Full range: bend to 80° and extend to 160°",
                severity=Severity.WARNING,
            ),
            AngleROMValidationRule(
                name="knee_right",
                joints=PoseSegments.RIGHT_LEG,
                min_rom_angle=80,
                max_rom_angle=160,
                message="Full range: bend to 80° and extend to 160°",
                severity=Severity.WARNING,
            ),
        ]
    )

    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Machine-based lower-body pushing exercise.",
            muscle_groups=("quadriceps", "glutes", "hamstrings"),
        )
    )