"""Cable Straight-Arm Pulldown exercise configuration (self-contained).

Also known as Rope Lat Pulldown / Cable Lat Pushdown.

Counting logic (LEFT_ARM_DIRECTION — Hip → Shoulder → Elbow angle):
  - UP stage:   angle >= 160° (arms extended overhead)
  - DOWN stage: angle <= 70°  (arms pulled down to sides)
  - A rep counts when the user goes UP → DOWN → UP (overhead → down → back overhead)
  - GOOD rep: must reach <= 60° at the bottom AND >= 160° at the top
  - BAD rep:  if user reverses before reaching either extreme

Validation rules:
  1. elbow_straight: Shoulder → Elbow → Wrist angle must stay >= 150°.
     Arms should remain straight throughout the movement to target lats effectively.
  2. hip_stable: Shoulder → Hip → Knee angle must stay between 80°-180°.
     Prevents excessive swinging or hip thrusting to generate momentum.

Speed check:
  - min_rep_frames=18 (~0.7 s at 25 fps). Reps faster than this are marked BAD.

Only ARM and HIP joints are drawn on screen (show_validation_skeleton=False).
"""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments, L_HIP, L_SHOULDER, L_ELBOW, L_KNEE, R_HIP, R_SHOULDER, R_ELBOW, R_KNEE
from .exercise import Camera, Exercise, DisplaySettings, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


# Hip → Shoulder → Elbow: detects arm position (overhead vs down)
_LEFT_ARM_DIRECTION = (L_HIP, L_SHOULDER, L_ELBOW)
_RIGHT_ARM_DIRECTION = (R_HIP, R_SHOULDER, R_ELBOW)
# Shoulder → Hip → Knee: detects hip stability
_LEFT_HIP_STABILITY = (L_SHOULDER, L_HIP, L_KNEE)
_RIGHT_HIP_STABILITY = (R_SHOULDER, R_HIP, R_KNEE)


@dataclass
class CableStraightArmPulldownExercise(Exercise):
    name: str = "Cable Straight-Arm Pulldown"
    camera: Camera = Camera.SIDE

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="shoulder_left",
                joints=_LEFT_ARM_DIRECTION,   # Hip → Shoulder → Elbow
                up_angle=60,                  # arms overhead — UP stage (angle >= 160)
                down_angle=45,                 # arms pulled down — DOWN stage (angle <= 70)
                up_stage="up",                 # large angle = overhead position
                down_stage="down",             # small angle = down position
                min_rom_angle=20,              # must reach <= 60° for a GOOD rep (deep enough)
                max_rom_angle=100,             # must reach >= 160° for a GOOD rep (full extension)
                min_rep_frames=18,             # < 18 frames = too fast → BAD
            ),
            AngleCounterRule(
                name="shoulder_right",
                joints=_RIGHT_ARM_DIRECTION,   # Hip → Shoulder → Elbow
                up_angle=60,
                down_angle=45,
                up_stage="up",
                down_stage="down",
                min_rom_angle=20,
                max_rom_angle=100,
                min_rep_frames=18,
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            # ── Form check 1: elbow must stay straight (left) ─────────────────
            AngleValidationRule(
                name="elbow_straight_left",
                joints=PoseSegments.LEFT_ARM,   # Shoulder → Elbow → Wrist
                min_angle=100,
                max_angle=180,
                message="Keep arms straight — don't bend elbows (stay above 150°)",
                severity=Severity.WARNING,
            ),
            # ── Form check 1: elbow must stay straight (right) ────────────────
            AngleValidationRule(
                name="elbow_straight_right",
                joints=PoseSegments.RIGHT_ARM,   # Shoulder → Elbow → Wrist
                min_angle=130,
                max_angle=180,
                message="Keep arms straight — don't bend elbows (stay above 150°)",
                severity=Severity.WARNING,
            ),
            # ── Form check 2: hip stability (prevent swinging) - left ───────────
            AngleValidationRule(
                name="hip_stable_left",
                joints=_LEFT_HIP_STABILITY,     # Shoulder → Hip → Knee
                min_angle=100,
                max_angle=165,
                message="Keep hips stable — don't swing or thrust",
                severity=Severity.WARNING,
            ),
            # ── Form check 2: hip stability (prevent swinging) - right ──────────
            AngleValidationRule(
                name="hip_stable_right",
                joints=_RIGHT_HIP_STABILITY,     # Shoulder → Hip → Knee
                min_angle=100,
                max_angle=165,
                message="Keep hips stable — don't swing or thrust",
                severity=Severity.WARNING,
            ),
        ]
    )

    # Only draw the arm and hip skeleton — the stability validation joints
    # would add a distracting second skeleton if allowed to render.
    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(show_validation_skeleton=False)
    )

    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Isolation cable exercise for the latissimus dorsi using straight-arm pulldown motion.",
            muscle_groups=("latissimus dorsi", "teres major", "posterior deltoid", "triceps"),
        )
    )
