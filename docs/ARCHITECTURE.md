# Architecture (post-refactor)
> **Path conventions:** code paths in this document (`src/…`, `tests/…`) are relative to `backend/`; data paths (`assets/…`, `output/…`, `uploads/…`) are relative to the **repository root**.


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
  exercises/      << config-driven >>  pure configuration, zero logic
    rules.py         AngleCounterRule, AngleValidationRule dataclasses
    exercise.py      Exercise dataclass (+ DisplaySettings)
    validation.py    evaluate_rule / validate_all  (the ONE extension point)
    pushup.py         PushUpExercise
    squat.py          SquatExercise
    shoulder_press.py ShoulderPressExercise
    biceps_curl.py    BicepsCurlExercise
    cable_chest_fly.py CableChestFlyExercise
    deadlift.py        DeadliftExercise
    latpulldown.py      LatPulldownExercise
    leg/               lower-body exercises subpackage
      __init__.py       re-exports the subpackage
      leg_press.py       LegPressExercise
      hack_squat.py      HackSquatExercise
  services/
    pose_service.py  MediaPipe wrapper                         [unchanged]
    rep_counter.py   RepCounter driven by list[AngleCounterRule]    [refactored]
    rep_judge.py     RepJudge + RepResult — repetition quality [new]
    gym_engine.py    GymEngine(exercise) — generic orchestrator[refactored]
    video_source.py  open_capture + path resolution & run diagnostics [new]
  utils/
    geometry.py      calc_angle / get_points + ComputedAngle   [unchanged]
    render.py        drawing helpers + fit_to_screen           [refactored]
  main.py          CLI: python -m src.main <exercise> [video]  [refactored]
requirements.txt  pinned deps (mediapipe, opencv, pydantic-settings)
```

## The configuration objects

### `AngleCounterRule` (one repetition counter)
```python
@dataclass(frozen=True)
class AngleCounterRule:
    name: str
    joints: tuple[int, int, int]   # 3 pose landmarks forming an angle
    up_angle: float                # "top" of a rep
    down_angle: float              # "bottom" of a rep
    up_stage: str = "up"           # configurable stage vocabulary
    down_stage: str = "down"
```
Frozen dataclass = immutable config. A `AngleCounterRule` is completely
exercise-agnostic — it only knows three landmarks and two thresholds.

### `ValidationRule` + its concrete kinds
```python
@dataclass(frozen=True, kw_only=True)
class ValidationRule:            # shared base: identity + feedback + emphasis
    name: str
    message: str
    severity: str = Severity.ERROR   # Severity: str Enum (ERROR/WARNING/INFO)

@dataclass(frozen=True, kw_only=True)
class AngleValidationRule(ValidationRule):     # stateless per-frame range check
    joints: tuple[int, int, int]
    min_angle: float
    max_angle: float

@dataclass(frozen=True, kw_only=True)
class AngleROMValidationRule(ValidationRule):  # stateful, uses live RepState
    joints: tuple[int, int, int]
    min_rom_angle: float
    max_rom_angle: float

@dataclass(frozen=True, kw_only=True)
class DistanceValidationRule(ValidationRule):  # landmark-distance ratio check
    measurement: LandmarkPair            # pair whose distance is checked
    reference: LandmarkPair              # pair that normalizes the ratio
    min_ratio: float; max_ratio: float
```
Each rule is self-contained: what to measure + the acceptable range +
the coaching cue. Rules never reference each other, stay behaviour-free
(configuration only), and are immutable so they can be shared safely for a
whole session. `Severity`/`Stage`/`Camera` are `str` Enums, so members
compare equal to the legacy literals they replace. See the module docstring
in `src/exercises/rules.py` for the full architecture guide.

### `Exercise` (the only thing the engine needs)
```python
@dataclass
class Exercise:
    name: str
    counter_rules: list[AngleCounterRule]      # supports multiple angles
    validation_rules: list[AngleValidationRule]  # supports multiple checks
    display: DisplaySettings              # optional presentation knobs
    metadata: ExerciseMetadata            # frozen; description + muscle_groups
    camera: str = Camera.BOTH             # Camera.BOTH | Camera.SIDE
```
An `Exercise` is *pure data*. `GymEngine` consumes it and never asks which
exercise it is.

## Why `GymEngine` is now generic

`GymEngine.__init__(self, exercise, colors=None, display_width=1280)` receives
only an `Exercise`. Its single job is the loop:

1. `PoseService` detects the pose.
2. `analyze()` computes **only the angles the exercise asked for** (from
   `counter_rules`).
3. `validate_all()` runs **every** validation rule -> one `ValidationResult`
   per rule.
4. `RepJudge.observe()` records the frame's validation failures (de-duplicated
   by rule name).
5. `RepCounter.update()` advances the repetition count. `GymEngine` reads the
   new count; when it increased it calls `RepJudge.finalize_rep()` to classify
   the completed repetition as GOOD/BAD and store a `RepResult`.
6. `_render()` draws whatever the configuration describes, including the live
   coaching messages and the rep-quality overlay (Total / Good / Bad / Current
   Rep).
7. The frame is **auto-fitted to the screen** via `fit_to_screen()` (preserves
   aspect ratio, never upscales, respects a margin, and caches the detected
   screen size). Pose math — and, when `SAVE_OUTPUT` is on, the recorded video —
   always use the **original-resolution** frame; only the displayed frame is
   resized.

`analyze()` is pure logic with no I/O, so it is trivially unit-testable with
fake landmarks. `run(video_path=None)` owns the video source (an explicit
`video_path` overrides `settings.VIDEO_PATH` / webcam), the optional writer,
and the `cv2` window.

## Adding a new exercise

1. **Define** the config in its own module, e.g. `exercises/pushup.py`:

```python
@dataclass
class PlankExercise(Exercise):
    name: str = "Plank"
    counter_rules: list[AngleCounterRule] = field(default_factory=lambda: [
        AngleCounterRule("elbow", PoseSegments.LEFT_ARM, up_angle=160, down_angle=90),
    ])
    validation_rules: list[AngleValidationRule] = field(default_factory=lambda: [
        AngleValidationRule("back_straight", PoseSegments.LEFT_TORSO,
                       min_angle=150, max_angle=180,
                       message="Keep your back straight", severity="error"),
    ])
```

2. **Re-export** it from `exercises/__init__.py` (one import line) so callers can
   do `from src.exercises import PlankExercise`.
3. **(Optional) Register** it in `main.py`'s `EXERCISES` dict (name → class) so it
   is selectable from the CLI: `python -m src.main plank`.

Related exercises can be grouped into a subpackage — e.g. the lower-body moves
live in `exercises/leg/` (`leg_press.py`, `hack_squat.py`), whose `__init__.py`
re-exports them and is itself re-exported from `exercises/__init__.py`.

Then `GymEngine(PlankExercise())` just works. **No engine change.**

> Why a dataclass subclass instead of a factory function or an abstract base
> class? The brief asks for "dataclasses, composition" and to avoid factories /
> unnecessary inheritance. A thin dataclass subclass supplies only default field
> values — it carries no behaviour, so it is the lightest possible form of
> configuration-as-code and yields the exact `PushUpExercise()` call site
> requested, without a factory.

## Floating angle labels (per-rule)

Every computed angle — from **both** `AngleCounterRule`s and `AngleValidationRule`s — gets
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
`1 AngleCounterRule + 4 AngleValidationRule` automatically shows **5** labels with **zero**
renderer or engine changes.

## RepJudge — repetition quality (RepResult)

Counting and quality are **separate concerns** handled by separate services:

- `RepCounter` detects *that* a repetition happened (count, stage) and knows
  nothing about form.
- `validate_all` / `ValidationResult` evaluate the pose for *one* frame.
- `RepJudge` (`services/rep_judge.py`) watches the per-frame `ValidationResult`s,
  remembers which rules failed during the **current** repetition, and — once
  `GymEngine` tells it a rep completed (via `finalize_rep`) — emits a single
  `RepResult` and resets for the next rep.

```python
@dataclass
class RepResult:
    number: int                      # 1-based, matches on-screen rep counter
    good: bool                      # False iff any violation has severity "error"
    violations: list[ValidationResult]   # de-duplicated by rule name (raw objects)
    start_frame: int | None = None
    end_frame:   int | None = None
```

Key behaviours:

- **De-duplication.** The same rule failing across many frames is stored once.
  When severities differ we keep the *worst* (`error` > `warning` > `info`) so an
  error is never masked by an earlier warning.
- **Classification.** A rep is BAD iff at least one stored violation has
  `severity == "error"`. Warnings alone leave it GOOD.
- **History is the single source of truth.** `RepJudge` keeps `history:
  list[RepResult]` and derives `total_reps` / `good_reps` / `bad_reps` /
  `last_rep` as read-only properties. There are **no** `good_reps` / `bad_reps`
  / `total_reps` counters to drift out of sync.
- **Independence.** `RepJudge` never imports `RepCounter` and vice-versa. The
  only coupling is in `GymEngine.analyze`, which calls `judge.observe(results,
  frame)` every frame, compares `RepCounter.primary.count` before/after
  `counter.update`, and calls `judge.finalize_rep(...)` on a detected completion.

## Future extensibility (requirement 10)

| Future feature | How it slots in (no `GymEngine` change) |
|---|---|
| Multiple counter angles | already supported — `counter_rules` is a list |
| Multiple validation angles | already supported — `validation_rules` is a list |
| Distance / alignment / symmetry rules | add a new rule dataclass in `rules.py` and branch in `evaluate_rule()` (see the EXTENSION POINT comment). `GymEngine` only calls `validate_all`, so it is untouched |
| Richer feedback messages | `AngleValidationRule.message` is already free text; add fields as needed |
| Exercise metadata | `Exercise.metadata` (typed `ExerciseMetadata`) already exists; engine ignores it |
| Form Score | fold `RepResult.violations` (e.g. weighted by severity) into a per-rep score; aggregate over `RepJudge.history` — pure function, no engine change |
| Tempo Analysis / Time Under Tension | use `start_frame`/`end_frame` (already on `RepResult`) + frame rate; compute per rep, aggregate over `history` |
| Range of Motion | extend `RepResult` with the min/max angle captured during the rep, or read it from the stored `ValidationResult`s |
| Session Reports / Exercise Analytics / Progress Tracking | already shipped: `SessionAnalyzer.build_report()` assembles a complete `SessionReport` (session identity + exercise info + summary + rule definitions stored once + per-rep evaluations referencing them with explicit `judged_by` semantics + dashboard aggregates — per-rule success rates and score extremes) exported as one normalized, unversioned JSON document |
| Most Common Errors | `Counter(dict).update(r.violations for r in history)` — the raw objects are stored, so no re-derivation needed |

## Design decisions & SOLID rationale

- **Single Responsibility (SRP).** `PoseService` = detection, `RepCounter` =
  counting, `validate_all` = validation, `RepJudge` = repetition-quality
  judging, `render` = drawing, `GymEngine` = orchestration only. The old
  `GymEngine` did IO + detection + counting + rendering in one class.
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
