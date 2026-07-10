# Architecture (post-refactor)

The project was refactored to be **fully configuration-driven**. The engine no
longer knows anything about any specific exercise. Adding a new exercise is a
pure data task — no engine code is touched.

## Package map

```
src/
  config/        AppSettings (pydantic) + .env loading        [unchanged]
  core/
    colors.py        Colors dataclass                          [unchanged]
    pose_segments.py MediaPipe landmark indices + named chains [cleaned up]
  exercises/      << NEW >>  pure configuration, zero logic
    rules.py         CounterRule, ValidationRule dataclasses
    exercise.py      Exercise dataclass (+ DisplaySettings)
    validation.py    evaluate_rule / validate_all  (the ONE extension point)
    pushup.py         PushUpExercise
    squat.py          SquatExercise
    leg_press.py      LegPressExercise
    shoulder_press.py ShoulderPressExercise
    biceps_curl.py    BicepsCurlExercise
  services/
    pose_service.py  MediaPipe wrapper                         [unchanged]
    rep_counter.py   RepCounter driven by list[CounterRule]    [refactored]
    gym_engine.py    GymEngine(exercise) — generic orchestrator[refactored]
  utils/
    geometry.py      calc_angle / get_points                   [unchanged]
    render.py        drawing helpers (draw_stats now shows issues) [refactored]
  main.py          GymEngine(PushUpExercise())                 [refactored]
```

## The configuration objects

### `CounterRule` (one repetition counter)
```python
@dataclass(frozen=True)
class CounterRule:
    name: str
    joints: tuple[int, int, int]   # 3 pose landmarks forming an angle
    up_angle: float                # "top" of a rep
    down_angle: float              # "bottom" of a rep
    up_stage: str = "up"           # configurable stage vocabulary
    down_stage: str = "down"
```
Frozen dataclass = immutable config. A `CounterRule` is completely
exercise-agnostic — it only knows three landmarks and two thresholds.

### `ValidationRule` (one independent form-check)
```python
@dataclass(frozen=True)
class ValidationRule:
    name: str
    joints: tuple[int, int, int]
    min_angle: float
    max_angle: float
    message: str
    severity: str = "error"   # "error" | "warning" | "info"
```
Each rule is self-contained: which angle to measure + the acceptable range +
the coaching cue. Rules never reference each other.

### `Exercise` (the only thing the engine needs)
```python
@dataclass
class Exercise:
    name: str
    counter_rules: list[CounterRule]      # supports multiple angles
    validation_rules: list[ValidationRule]  # supports multiple checks
    display: DisplaySettings              # optional presentation knobs
    metadata: dict                        # free-form, engine ignores it
```
An `Exercise` is *pure data*. `GymEngine` consumes it and never asks which
exercise it is.

## Why `GymEngine` is now generic

`GymEngine.__init__(self, exercise, colors=None, display_width=1280)` receives
only an `Exercise`. Its single job is the loop:

1. `PoseService` detects the pose.
2. `analyze()` computes **only the angles the exercise asked for** (from
   `counter_rules`).
3. `RepCounter` updates the repetition count.
4. `validate_all()` runs **every** validation rule.
5. `_render()` draws whatever the configuration describes and shows live
   coaching messages.

`analyze()` is pure logic with no I/O, so it is trivially unit-testable with
fake landmarks (see the notes in the PR / review). `run()` owns the video
source, writer, and `cv2` window.

## Adding a new exercise

Create one dataclass subclass in its own module, e.g. `exercises/pushup.py`:

```python
@dataclass
class PlankExercise(Exercise):
    name: str = "Plank"
    counter_rules: list[CounterRule] = field(default_factory=lambda: [
        CounterRule("elbow", PoseSegments.LEFT_ARM, up_angle=160, down_angle=90),
    ])
    validation_rules: list[ValidationRule] = field(default_factory=lambda: [
        ValidationRule("back_straight", PoseSegments.LEFT_TORSO,
                       min_angle=150, max_angle=180,
                       message="Keep your back straight", severity="error"),
    ])
```

Then `GymEngine(PlankExercise())` just works. **No engine change.**

> Why a dataclass subclass instead of a factory function or an abstract base
> class? The brief asks for "dataclasses, composition" and to avoid factories /
> unnecessary inheritance. A thin dataclass subclass supplies only default field
> values — it carries no behaviour, so it is the lightest possible form of
> configuration-as-code and yields the exact `PushUpExercise()` call site
> requested, without a factory.

## Floating angle labels (per-rule)

Every computed angle — from **both** `CounterRule`s and `ValidationRule`s — gets
a small floating label showing its value (e.g. `165°`) next to the vertex joint.
It is implemented so the renderer never names a specific rule or exercise:

- `analyze()` builds a `ComputedAngle` view for **every** rule (counter + validation)
  and attaches them to `FrameResult.views`.
- `render.draw_angle_labels(frame, views, colors, w, h)` iterates that list and
  draws one boxed label per entry, positioned at the rule's middle/vertex joint
  (so it tracks the person) with a small offset so it never covers the joint.
- Colour follows the rule state: `HIGHLIGHT` for normal/counter angles,
  `ERROR` for a failed validation. A dark, semi-transparent backing keeps the
  text readable on any background, and the label size scales with the source
  resolution so on-screen size is constant after the final resize.

Because the labels are driven entirely by `FrameResult.views`, an exercise with
`1 CounterRule + 4 ValidationRule` automatically shows **5** labels with **zero**
renderer or engine changes.

## Future extensibility (requirement 10)

| Future feature | How it slots in (no `GymEngine` change) |
|---|---|
| Multiple counter angles | already supported — `counter_rules` is a list |
| Multiple validation angles | already supported — `validation_rules` is a list |
| Distance / alignment / symmetry rules | add a new rule dataclass in `rules.py` and branch in `evaluate_rule()` (see the EXTENSION POINT comment). `GymEngine` only calls `validate_all`, so it is untouched |
| Richer feedback messages | `ValidationRule.message` is already free text; add fields as needed |
| Exercise metadata | `Exercise.metadata` dict already exists; engine ignores it |

## Design decisions & SOLID rationale

- **Single Responsibility (SRP).** `PoseService` = detection, `RepCounter` =
  counting, `validate_all` = validation, `render` = drawing, `GymEngine` =
  orchestration only. The old `GymEngine` did IO + detection + counting +
  rendering in one class.
- **Open/Closed (OCP).** `GymEngine` is closed for modification but open for
  extension: new exercises/rule-kinds are added as *data* (and one evaluator
  branch), never by editing the engine.
- **No hardcoded values.** Joints, thresholds, and exercise names all live in
  `Exercise` config. `main.py` no longer contains `LEFT_ARM`, `130`, `70`, etc.
- **Simple, not over-engineered.** Plain dataclasses + composition. No abstract
  base classes, no inheritance hierarchies, no design-pattern machinery. The only
  "indirection" is delegating rule evaluation to `validate_all` — and that
  exists purely to keep the engine open for new rule kinds.
- **Removed dead coupling.** `core/__init__.py` no longer imports MediaPipe just
  to re-export an unused `PoseLandmark`, so configuration/exercise modules can
  be imported and unit-tested without the ML dependency present.

## Known limitations (intentionally left as-is)

- `geometry.get_points` scales `x` by frame width and `y` by frame height, so
  computed angles are in anisotropic pixel space (inherited from the original
  code). Real landmark aspect ratio could be normalized later if desired; it
  does not affect the architecture.
- Angle thresholds in each exercise module (e.g. `pushup.py`) are reasonable starting points and should be
  calibrated to your own form criteria.
