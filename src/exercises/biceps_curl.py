"""Biceps Curl exercise configuration (self-contained).

Counting logic (LEFT_ARM — Shoulder → Elbow → Wrist angle):
  - UP stage:   angle >= 150° (arm extended / hanging down)
  - DOWN stage: angle <= 90°  (arm curled up toward shoulder)
  - A rep counts when the user goes DOWN → UP (curled → extended)
  - GOOD rep: must reach <= 60° at the curl AND >= 150° at the extension

Validation rules:
  1. elbow_too_tight: angle must stay >= 30° — if lower than 30° the forearm
     is jammed too close, losing bicep tension (bad form).
  2. elbow_hyperextended: angle must stay <= 170° — if higher than 170° the
     elbow is hyperextended or locked out too straight (wrong position).
  3. elbow_drift: Hip → Shoulder → Elbow angle must stay <= 15°.
     If the elbow drifts forward, the front shoulder takes over and bicep tension drops.

Speed check:
  - min_rep_frames=18 (~0.7 s at 25 fps). Reps faster than this are marked BAD.

Only ARM joints are drawn on screen (show_validation_skeleton=False).
"""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments, L_HIP, L_SHOULDER, L_ELBOW
from .exercise import Exercise, DisplaySettings
from .rules import AngleCounterRule, AngleValidationRule


# Hip → Shoulder → Elbow: detects elbow drift / forward swing
_LEFT_ELBOW_DRIFT = (L_HIP, L_SHOULDER, L_ELBOW)


@dataclass
class BicepsCurlExercise(Exercise):
    name: str = "Biceps Curl"
    camera: str = "side"

    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="elbow",
                joints=PoseSegments.LEFT_ARM,   # Shoulder → Elbow → Wrist
                up_angle=139,                   # arm extended — UP stage (angle >= 150)
                down_angle=90,                  # arm curled — DOWN stage (angle <= 90)
                up_stage="down",                # map large angle (extension) to "down"
                down_stage="up",                # map small angle (curl peak) to "up"
                rom_min_angle=150,               # must reach <= 60° for a GOOD rep
                rom_max_angle=50,              # must reach >= 150° for a GOOD rep
                min_rep_frames=12,              # < 12 frames = too fast → BAD
            ),
        ]
    )

    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            # ── Form check 1: elbow angle must stay above 30° ──────────
            AngleValidationRule(
                name="elbow_too_tight",
                joints=PoseSegments.LEFT_ARM,
                min_angle=30,
                max_angle=180,
                message="Don't curl too tight — keep elbow above 30°",
                severity="warning",
            ),
            # ── Form check 2: elbow angle must stay below 170° ─────────
            AngleValidationRule(
                name="elbow_hyperextended",
                joints=PoseSegments.LEFT_ARM,
                min_angle=0,
                max_angle=170,
                message="Don't lock or hyperextend your elbow (keep below 170°)",
                severity="warning",
            ),
            # ── Form check 3: elbow drift (Hip → Shoulder → Elbow) ─────
            # Upper arm stays vertical (parallel to torso) — angle <= 15°.
            AngleValidationRule(
                name="elbow_drift",
                joints=_LEFT_ELBOW_DRIFT,
                min_angle=0,
                max_angle=20,
                message="Keep elbow pinned to your side (drift < 20°)",
                severity="warning",
            ),
        ]
    )

    # Only draw the arm skeleton — the drift validation joints (Hip→Shoulder→Elbow)
    # would add a distracting second skeleton if allowed to render.
    display: DisplaySettings = field(
        default_factory=lambda: DisplaySettings(show_validation_skeleton=False)
    )

    metadata: dict = field(
        default_factory=lambda: {
            "description": "Isolation dumbbell exercise for the biceps brachii.",
            "muscle_groups": ["biceps brachii", "brachialis", "brachioradialis"],
            "technique_notes": (
                "Keep the upper arm stationary and elbow pinned to your side (drift < 15°). "
                "Full extension at the bottom (~150° - 170°) and full curl at the top (30° - 60°). "
                "Controlled tempo — avoid ballistic / momentum-driven reps."
            ),
        }
    )
