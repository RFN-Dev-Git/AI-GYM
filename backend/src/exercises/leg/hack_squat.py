"""Hack Squat exercise configuration (self-contained).

Counting logic (LEFT_LEG — Hip → Knee → Ankle angle, MANAGED ROM path):
  - DOWN phase begins when the angle drops to <= 90° (rep window starts).
  - RETURNING begins when the angle crosses back above 130°.
  - The rep COMPLETES when the angle reaches >= 150° and starts decreasing
    again (direction reversal at the top — the next descent has begun).
  - Bailing out early (angle falls back to <= 90° before reaching 150°)
    counts the rep BAD.

Rep quality:
  - GOOD rep: reached <= 85° at the bottom AND >= 150° at the top, with no
    validation violation during the rep window.
  - BAD rep: too shallow (never <= 85°), incomplete lockout (bailed before
    150°), or ``knee_unlocked`` failed anywhere inside the window.
  - ``min_rep_frames`` stays 0 — no tempo gate for now (set > 0 to judge
    speed as well).

Design notes
------------
* SINGLE LEFT-side rule set, by project convention: the exercise is filmed in
  profile (Camera.SIDE), so CameraSideDetector picks the visible side within
  the first ~30 frames and adapt_rules mirrors these LEFT rules onto the
  right automatically. Twin ``knee_left``/``knee_right`` rules would be
  redundant — adaptation keeps exactly one effective rule either way — and,
  worse, would make the exported rule names swap with the detected side.
  One LEFT rule keeps report names stable ("knee", "knee_unlocked") no matter
  which side is filmed, while the post-adaptation landmarks (and therefore
  every counted/measured angle) are identical to the old twin setup.
* Stage triggers (90/130) are the author's calibration for the machine's
  travel and did not change with the ROM upgrade. The ROM extremes are the
  judgment band around them: 85° demands going a little deeper than the
  DOWN trigger, 150° demands more extension than the 130° RETURNING trigger
  (lockout beyond 170° is separately flagged by ``knee_unlocked``). Tune the
  85/150 band against real footage if it proves too strict or too lenient.
* There is deliberately NO paired ``AngleROMValidationRule``: leg_press
  pairs one with its counter and, because RepJudge's record keeps a failed
  outcome sticky for the whole rep, its transient "go deeper" live cues end
  up exported as failed evaluations on *perfect* reps (score 80, and
  "most common error" on every rep). Here the counter's own ROM gate is the
  sole ROM judge — the same pattern biceps_curl uses. Consequence, mirrored
  by design: a rep judged BAD purely on ROM (e.g. only reached 88°) carries
  no failed validation evaluation, so its exported score stays 100 — rep
  classification comes from the counter, scores from validation rules.
* ``knee_unlocked`` spans 60°–170°: above 170° the knee is locked/
  hyperextended at the top; below 60° is beyond safe machine depth. The
  message is deliberately side-neutral — after mirroring it coaches whichever
  leg is visible.

Only the counter (knee) skeleton is drawn — the validation rule measures the
same joints, so drawing both would be visual noise
(``show_validation_skeleton=False``).
"""

from dataclasses import dataclass, field

from ...core.pose_segments import PoseSegments
from ..exercise import Camera, DisplaySettings, Exercise, ExerciseMetadata
from ..rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class HackSquatExercise(Exercise):
    name: str = "Hack Squat"
    camera: Camera = Camera.SIDE
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            AngleCounterRule(
                name="knee",
                joints=PoseSegments.LEFT_LEG,   # Hip → Knee → Ankle
                up_angle=130,                   # crossing back above -> RETURNING phase
                down_angle=90,                  # <= 90° -> DOWN phase begins (rep window starts)
                min_rom_angle=85,               # GOOD rep must reach <= 85° at the bottom
                max_rom_angle=150,              # ... and >= 150° at full extension before reversing
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            # Lockout / over-depth guard on the same measured angle. On this
            # managed counter a failure inside the rep window also poisons
            # the rep (marks it BAD), not just the exported score.
            AngleValidationRule(
                name="knee_unlocked",
                joints=PoseSegments.LEFT_LEG,
                min_angle=60,
                max_angle=170,
                message="Don't lock your knee — stay between 60° and 170°",
                severity=Severity.WARNING,
            ),
        ]
    )
    display: DisplaySettings = field(
        # Validation joints == counter joints: one skeleton, not two.
        default_factory=lambda: DisplaySettings(show_validation_skeleton=False)
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Machine-guided squat emphasizing the quadriceps through the sled's fixed path.",
            muscle_groups=("quadriceps", "glutes", "hamstrings"),
        )
    )
