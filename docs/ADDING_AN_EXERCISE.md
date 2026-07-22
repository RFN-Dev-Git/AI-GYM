# Adding a New Exercise
> **Path conventions:** code paths in this document (`src/…`, `tests/…`) are relative to `backend/`; data paths (`assets/…`, `output/…`, `uploads/…`) are relative to the **repository root**.


This guide walks you through adding a brand-new exercise to AI-GYM.

The most important thing to know first: **an exercise is pure configuration**.
You never touch `GymEngine`, the counter, the validator, or the CLI. Adding an
exercise is always exactly three steps:

1. **Create** one config file in `src/exercises/`.
2. **Register** it in `src/exercises/registry.py`.
3. **Run** it by name.

```
┌────────────────────────┐   register   ┌──────────────────┐   get(name)   ┌────────────┐
│ src/exercises/*.py     │ ───────────► │ ExerciseRegistry │ ────────────► │ GymEngine  │
│ (your Exercise config) │              │ (registry.py)    │               │ (+ CLI)    │
└────────────────────────┘              └──────────────────┘               └────────────┘
```

The engine consumes an already-built `Exercise` object and never knows which
exercise it is — that is the whole extensibility story.

---

## 1. Where everything lives

| What                        | Where                                                        |
| --------------------------- | ------------------------------------------------------------ |
| Exercise configs            | `src/exercises/<exercise_name>.py` (families may use a subpackage, e.g. `src/exercises/leg/`) |
| Registry (the list of exercises) | `src/exercises/registry.py`                             |
| Rule types                  | `src/exercises/rules.py` (read its docstring first!)         |
| `Exercise` / metadata / display | `src/exercises/exercise.py`                              |
| BlazePose landmarks & joint triplets | `src/core/pose_segments.py`                         |
| Evaluation logic *(don't touch)* | `src/exercises/validation.py`, `src/services/rep_counter.py`, `src/services/additional_casses.py` |
| Tests                       | `tests/`                                                      |

---

## 2. Step by step

### Step 1 — Pick the joints (landmarks)

Everything is measured from the 33-point BlazePose model. **Never scatter raw
numbers in your config** — use the named aliases in
`src/core/pose_segments.py`:

| Alias                    | Landmarks                    | Measures                                          |
| ------------------------ | ---------------------------- | ------------------------------------------------- |
| `LEFT_ARM` / `RIGHT_ARM` | shoulder → elbow → wrist     | elbow bend (curls, presses, push-ups)             |
| `LEFT_LEG` / `RIGHT_LEG` | hip → knee → ankle           | knee bend (squats, leg press)                     |
| `LEFT_TORSO` / `RIGHT_TORSO` | shoulder → hip → knee    | trunk/back straightness                           |
| `LEFT_ARM_DIRECTION` / `RIGHT_ARM_DIRECTION` | hip → shoulder → elbow | arm raised vs. hanging (raises, overhead press)   |
| `LEFT_ELBOW_ELEVATION` / `RIGHT_ELBOW_ELEVATION` | hip → shoulder → elbow | elbow vs. shoulder line (flys)            |
| `LEFT_NECK_ALIGN` / `RIGHT_NECK_ALIGN` | ear → shoulder → hip | neck neutrality (deadlift)                          |
| `LEFT_HIP_ALIGN` / `RIGHT_HIP_ALIGN` | hip → hip → knee       | hip/knee alignment proxies                        |

Individual landmark constants are also exported (`L_SHOULDER`, `R_WRIST`,
`L_HIP`, …). A triplet is always **`(first, vertex, second)`** — the measured
angle is the one at the **middle (vertex)** index.

> Need a joint combination that doesn't exist yet? Add a named alias (with a
> comment saying what it measures) to `PoseSegments` in
> `src/core/pose_segments.py`. These are anatomical constants, not exercise
> logic, so that's the right home for them.

### Step 2 — Pick the camera mode

| Mode          | Use when                                   | Consequence                                                                 |
| ------------- | ------------------------------------------ | --------------------------------------------------------------------------- |
| `Camera.BOTH` | Filmed front-on; both body sides visible   | Write `left_*` **and** `right_*` rules explicitly (see `shoulder_press.py`). |
| `Camera.SIDE` | Filmed from one side (profile view)        | Write **LEFT-side rules only**. The engine spends the first ~30 frames detecting the visible side (`CameraSideDetector`) and then mirrors your left rules onto the right automatically (`adapt_rules`). Nothing counts during that detection window. |

> ⚠️ For `Camera.SIDE`, do **not** also define right-side twins of your rules:
> when a same-named rule already exists on the visible side, the off-side rule
> is dropped rather than flipped (a documented `adapt_rules` behaviour). One
> side's rules per exercise is the convention.

### Step 3 — Define how a rep counts: `AngleCounterRule`

One `AngleCounterRule` = one rep counted from one joint angle.
All fields (defaults shown):

```python
AngleCounterRule(
    name="elbow",                    # stable id; keys the engine, counters and the report
    joints=PoseSegments.LEFT_ARM,    # (first, vertex, second)
    up_angle=160,                    # angle (deg) marking the "up" end of the movement
    down_angle=90,                   # angle (deg) marking the "down" end
    up_stage="up",                   # display label for the up end  (e.g. "open", "lockout")
    down_stage="down",               # display label for the down end
    min_rom_angle=None,              # optional bottom extreme a GOOD rep must reach (deg)
    max_rom_angle=None,              # optional top extreme a GOOD rep must reach (deg)
    min_rep_frames=0,                # optional min frames a rep may span (0 = no speed check)
    sync_group=None,                 # optional group: count only when all members cross together
)
```

**Which counting path you get** (chosen automatically by `RepCounter`):

| Your counter rules…            | Path                | Rep classification behaviour                                                                                                     |
| ------------------------------ | ------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| set **neither** `max_rom_angle` **nor** `min_rep_frames` | **Simple** | A rep counts on the DOWN→UP crossing. Every counted rep defaults to GOOD; form violations do not downgrade it — **except** a `DistanceValidationRule` failing during the rep, which always marks that rep BAD. Classify quality via validation rules + rep score in the report. |
| set `max_rom_angle` → and/or `min_rep_frames > 0` | **Managed** (`CustomCounterHelper`) | Full quality judging: a rep is GOOD only if it reached both ROM extremes (`min_rom_angle`/`max_rom_angle`), no violation fired during the rep window, and it spanned ≥ `min_rep_frames`. The rep counts on **direction reversal at the top extreme** (DOWN → RETURNING → reversal), not on the plain UP crossing. |

Real references: simple path → `pushup.py`, `squat.py`; managed path →
`biceps_curl.py`, `leg_press.py`.

**Tips**

- `sync_group` is for "count only when both sides move together" (Shoulder
  Press counts only when left *and* right arm both cross the threshold). Give
  each member the same group string and tight thresholds (91/89) so the group
  acts like a gate.
- `up_stage`/`down_stage` are pure display labels — Biceps Curl maps the large
  angle (extended arm) to `"down"` so the HUD reads naturally.
- Pick `up_angle`/`down_angle` from real footage: watch the live angle HUD and
  leave hysteresis margin between the two so jitter can't double-count.

### Step 4 — Define the form checks: validation rules

Three kinds, all keyword-only (`name=`, `message=`, `severity=` are keywords):

| Kind                     | Question it answers                                            | Checked        | Key fields                              |
| ------------------------ | -------------------------------------------------------------- | -------------- | --------------------------------------- |
| `AngleValidationRule`    | "Is this joint inside an acceptable range **right now**?"      | every frame    | `joints`, `min_angle`, `max_angle`      |
| `AngleROMValidationRule` | "Did the rep actually **reach both extremes**?"                | across the rep | `name` (match the counter rule), `joints`, `min_rom_angle`, `max_rom_angle` |
| `DistanceValidationRule` | "Is distance A between X× and Y× of reference distance B?"     | every frame    | `measurement`, `reference`, `min_ratio`, `max_ratio` |

Notes:

- **Severity**: `Severity.ERROR` = serious form fault (drives red feedback and
  weighs 50 in the report score), `Severity.WARNING` = should fix (20),
  `Severity.INFO` = hint (10).
- **`AngleROMValidationRule`'s `name` should mirror the counter rule it judges**
  (Shoulder Press uses `left_shoulder_rom` for the `left_shoulder` counter) —
  the engine pairs them by name prefix for live ROM cues.
- **`DistanceValidationRule` needs zero extra wiring**: the engine tracks every
  distance rule generically — any distance failure *during* a rep marks that
  rep BAD and records the violations in the session history. Ratios are
  normalized to the `reference` pair (e.g. shoulder width), so thresholds are
  camera-distance and body-size independent.
- Rules are **frozen configuration**: no methods, no state. If you need a check
  the three kinds can't express, that's a design conversation (new rule kind in
  `rules.py` + one evaluator in `validation.py`) — not logic bolted onto a config.

### Step 5 — Display (optional)

`DisplaySettings` tweaks what the overlay draws; it never affects logic:

```python
display=DisplaySettings(
    show_angle_arc=False,              # draw the live angle arc at the vertex
    show_skeleton=True,
    show_validation_skeleton=True,     # False hides extra validation-rule joints (less noise)
    segment_lines=[                    # optional landmark-to-landmark lines
        SegmentLine(
            endpoints=(L_WRIST, R_WRIST),
            active_angles=("left_shoulder", "right_shoulder"),  # draw only while these >= min_angle
            min_angle=90,
            error_rule="left_shoulder_wrist_distance",          # red while this rule fails
        ),
    ],
)
```

### Step 6 — Metadata

```python
metadata=ExerciseMetadata(
    description="One-line human description.",
    muscle_groups=("primary", "secondary"),   # tuple, priority order
)
```

This feeds the `exercise` block of the exported session report — write it for
humans reading the JSON/dashboard.

### Step 7 — Register and run

In `src/exercises/registry.py`:

```python
from .lateral_raise import LateralRaiseExercise
...
registry.register("lateral_raise", LateralRaiseExercise())
```

- The **registry key is the CLI word** — use snake_case (`"lateral_raise"`).
  Lookup is case-insensitive; registering the same key twice raises `ValueError`.
- No CLI, engine, analytics, or settings changes are needed.

Run it:

```bash
make run EXERCISE=lateral_raise VIDEO=my_set.mp4
# or directly
uv run python -m src.main lateral_raise my_set.mp4   # bare name → <repo-root>/assets/videos/
# webcam instead of a video file
uv run python -m src.main lateral_raise c
```

---

## 3. Full worked example — Lateral Raise

A complete, minimal exercise (verified end-to-end against the counter and the
registry):

```python
"""Lateral Raise exercise configuration (self-contained)."""

from dataclasses import dataclass, field

from ..core.pose_segments import PoseSegments
from .exercise import Camera, Exercise, ExerciseMetadata
from .rules import AngleCounterRule, AngleValidationRule, Severity


@dataclass
class LateralRaiseExercise(Exercise):
    name: str = "Lateral Raise"
    camera: Camera = Camera.SIDE
    counter_rules: list[AngleCounterRule] = field(
        default_factory=lambda: [
            # Hip → Shoulder → Elbow: arm at side ≈ small angle, raised ≈ 80-90°
            AngleCounterRule(
                name="arm",
                joints=PoseSegments.LEFT_ARM_DIRECTION,
                up_angle=80,
                down_angle=20,
            ),
        ]
    )
    validation_rules: list[AngleValidationRule] = field(
        default_factory=lambda: [
            AngleValidationRule(
                name="torso_upright",
                joints=PoseSegments.LEFT_TORSO,
                min_angle=150,
                max_angle=180,
                message="Don't lean — keep your torso upright",
                severity=Severity.WARNING,
            ),
        ]
    )
    metadata: ExerciseMetadata = field(
        default_factory=lambda: ExerciseMetadata(
            description="Isolation raise for the lateral deltoid.",
            muscle_groups=("lateral deltoid", "trapezius"),
        )
    )
```

Save as `src/exercises/lateral_raise.py`, add the import +
`registry.register("lateral_raise", LateralRaiseExercise())` to `registry.py`,
and `make run EXERCISE=lateral_raise VIDEO=my_set.mp4` works immediately.

Two reps of synthetic angles through the counter confirm the config:

```python
counter = RepCounter(LateralRaiseExercise().counter_rules)
for angle in [15]*5 + [85]*5 + [15]*5 + [85]*5:   # two full down→up swings
    counter.update({"arm": angle})
assert counter.primary.count == 2
```

For feature-rich reference configs see `shoulder_press.py` (BOTH camera,
sync_group, ROM + distance rules, SegmentLine) and `biceps_curl.py` (SIDE
camera, managed ROM counter, speed check, custom stage labels).

---

## 4. Verify with a test (recommended)

Add `tests/exercises/test_<exercise>.py` following the repo's test
conventions (path insert, `MODEL_PATH` default, mediapipe stub). Template:

```python
"""Smoke test for the <exercise> exercise configuration.

Run from backend/:  python tests/exercises/test_<exercise>.py
"""

import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/

import os
os.environ.setdefault("MODEL_PATH", "assets/models/pose_landmarker_lite.task")

# ── Stub mediapipe (only PoseService needs it; these tests never touch it) ──
_mp = types.ModuleType("mediapipe")
_mp_tasks = types.ModuleType("mediapipe.tasks")
_mp_python = types.ModuleType("mediapipe.tasks.python")
_mp_python.vision = types.ModuleType("mediapipe.tasks.python.vision")
_mp.tasks = _mp_tasks
_mp_tasks.python = _mp_python
sys.modules.update({
    "mediapipe": _mp,
    "mediapipe.tasks": _mp_tasks,
    "mediapipe.tasks.python": _mp_python,
    "mediapipe.tasks.python.vision": _mp_python.vision,
})

from src.exercises.<exercise> import <Exercise>Exercise
from src.exercises.registry import registry
from src.services.rep_counter import RepCounter


def test_registered():
    ex = registry.get("<exercise>")
    assert isinstance(ex, <Exercise>Exercise)

def test_counts_reps():
    counter = RepCounter(<Exercise>Exercise().counter_rules)
    for angle in [<below down_angle>]*5 + [<above up_angle>]*5:
        counter.update({"<counter name>": angle})
    assert counter.primary.count == 1
```

For full pipeline confidence (landmarks → engine → session history), copy the
synthetic-landmark approach of `tests/services/test_distance_handling.py`.

---

## 5. Pitfall checklist

- [ ] **Mutable defaults**: always `field(default_factory=lambda: [...])` for
      rule lists — never `counter_rules=[...]` directly on the dataclass.
- [ ] **Keyword-only rules**: validation rules take `name=`, `message=`,
      `severity=` as keywords (`kw_only=True` base). Positional use fails at
      import time — which is good, it's loud.
- [ ] **`Camera.SIDE` → LEFT-side rules only.** Mirroring is automatic;
      right-side twins get dropped (documented `adapt_rules` behaviour).
- [ ] **Setting `max_rom_angle` or `min_rep_frames` switches the counting
      path.** Managed counting judges quality (BAD reps become possible) and
      counts on direction reversal — sanity-check thresholds against real footage.
- [ ] **Stable snake_case rule names.** Names are the keys everywhere: counter
      state, violation matching, the `rules`/`history` sections of the exported
      JSON report. Renaming a rule breaks dashboards reading old exports.
- [ ] **No logic on rules.** Rules stay behaviour-free frozen config; execution
      lives exclusively in `validation.py`, `rep_counter.py`, `gym_engine.py`.
      (Read the "DESIGN NOTES" block at the top of `rules.py` before adding
      anything.)
- [ ] **Angles are measured at the middle (vertex) landmark** of each triplet —
      double-check your `(first, vertex, second)` order.
- [ ] **`sync_group` members need the same group string** on every rule and
      tight up/down thresholds — the group counts only when all members cross
      together.
- [ ] **New joint combos belong in `src/core/pose_segments.py`** as named,
      commented aliases — not as raw indices inside your config.
- [ ] Optional cosmetics: add your exercise to the "Available exercises" list
      in the `src/main.py` docstring, and mention it in `ARCHITECTURE.md`.
