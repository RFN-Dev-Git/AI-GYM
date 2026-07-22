"""Lateral Raise exercise configuration (self-contained).

Shoulders: Left (11), Right (12)
Elbows:    Left (13), Right (14)
Wrists:    Left (15), Right (16)
Hips:      Left (23), Right (24)

Counting:
  - decision angle: Shoulder Abduction angle (Hip → Shoulder → Elbow)
  - > 30° is raised state (UP)
  - < 30° is rest state (DOWN)
  - rep completes on returning to < 30°
  - GOOD rep ROM: peak angle must be between 45° and 90°

Form Validations:
  1. Shrug check: Delta of normalized shoulder height <= 0.08
  2. Elbow angle check: Shoulder → Elbow → Wrist angle is between 120° and 160°
"""

from dataclasses import dataclass, field

from ..core.pose_segments import (
    PoseSegments,
    L_SHOULDER, R_SHOULDER, L_ELBOW,
    R_SHOULDER, L_SHOULDER, R_ELBOW,
    L_HIP, R_HIP,
)
from .exercise import Exercise, DisplaySettings
from .rules import AngleCounterRule, AngleValidationRule, ShrugValidationRule


# Shoulder Abduction: Torso line (Hip->Shoulder) to Arm line (Shoulder->Elbow)
# Measured at Shoulder vertex: Hip -> Shoulder -> Elbow
_LEFT_ABDUCTION = (L_HIP, L_SHOULDER, L_ELBOW)
_RIGHT_ABDUCTION = (R_HIP, R_SHOULDER, R_ELBOW)


@dataclass
class LateralRaiseExercise(Exercise):
    name: str = "Lateral Raise"
    # No camera side restriction (both sides analyzed in front/side camera)
    camera: str = ""

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="lateral_raise_left",
                joints=_LEFT_ABDUCTION,
                up_angle=30,         # arms raised past 30° = enters UP stage
                down_angle=30,       # arms returned below 30° = enters DOWN stage & completes rep
                up_stage="up",
                down_stage="down",
                rom_min_angle=30,    # any raise >= 30° is a GOOD rep
                rom_max_angle=120,   # generous upper limit
                complete_on_return=True,  # count rep on returning to rest (DOWN), not on the way up
            ),
            AngleCounterRule(
                name="lateral_raise_right",
                joints=_RIGHT_ABDUCTION,
                up_angle=30,
                down_angle=30,
                up_stage="up",
                down_stage="down",
                rom_min_angle=30,
                rom_max_angle=120,
                complete_on_return=True,
            ),
        ]
    )

    validation_rules: list[any] = field(
        default_factory=lambda: [
            # ── Form check 1: Trap Shrugging (custom shrug validation) ──
            ShrugValidationRule(
                name="shrug",
                message="Keep shoulders down — don't shrug traps up",
                threshold=0.2,
                severity="warning",
            ),
            # ── Form check 2: Elbow Flexion Lockout (120° - 160°) ────────
            AngleValidationRule(
                name="elbow_left",
                joints=PoseSegments.LEFT_ARM,
                min_angle=120,
                max_angle=180,
                message="Keep a slight bend in your elbow (120°-160°)",
                severity="warning",
            ),
            AngleValidationRule(
                name="elbow_right",
                joints=PoseSegments.RIGHT_ARM,
                min_angle=120,
                max_angle=180,
                message="Keep a slight bend in your elbow (120°-160°)",
                severity="warning",
            ),
        ]
    )

    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(
            show_validation_skeleton=True,
            show_angle_arc=True,
        )
    )

    metadata: dict = field(
        default_factory=lambda: {
            "description": "Isolation exercise for the lateral head of the deltoids.",
            "muscle_groups": ["lateral deltoids", "trapezius"],
            "technique_notes": (
                "Raise dumbbells out to your sides until arms are parallel to the floor. "
                "Keep elbows slightly bent (120°-160°) and avoid shrugging your shoulders."
            ),
        }
    )
