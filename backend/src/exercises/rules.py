"""Rule dataclasses: the atomic, exercise-agnostic building blocks.

===============================================================================
DESIGN NOTES (read this before adding or changing a rule)
===============================================================================

A Rule is *pure configuration*: it describes **WHAT** should be true
("elbow angle must stay between 30° and 170°"), never **HOW** that is
checked or acted upon. Two consequences matter to every contributor:

*   Rules are immutable (``frozen=True``). They are shared, long-lived
    configuration — created once per exercise, reused for the whole session,
    and adapted by copy (``dataclasses.replace``) when the camera side is
    detected. Freezing guarantees a rule means the same thing on frame 1
    and frame 10,000.

*   Rules contain no evaluation logic (no ``validate()`` / ``evaluate()`` /
    ``count()`` methods). Behaviour-free configuration stays trivially
    testable, engine-agnostic, and open for extension: a new rule kind is a
    new frozen dataclass in this file plus one evaluator where rule kinds
    are interpreted — the rule classes themselves never change shape.

On grouping and naming
----------------------
Fields that only make sense together are grouped into named pairs/triplets
(:data:`LandmarkPair`, :data:`LandmarkTriplet`) instead of numbered
primitives (``point1``/``point2``/``reference1``/``reference2``). Range
bounds stay as separate ``min_*`` / ``max_*`` fields — the prefix names the
role, so a two-tuple would hide information, not add it. The ``min_`` /
``max_`` + concept naming is uniform across all rules:

    min_angle / max_angle  ·  min_rom_angle / max_rom_angle  ·  min_ratio / max_ratio

On the hierarchy
----------------
``ValidationRule`` is the shared base of the three validation kinds; it
exists because name/message/severity would otherwise be duplicated verbatim
across all three. There is deliberately NO ``CounterRule`` base class:
``AngleCounterRule`` is the only counting rule kind, and a one-member
hierarchy would be inheritance for its own sake. If a second counting kind
is ever added (e.g. tempo-based), factor out the common fields then.
"""

from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------------------------------------
# Landmark group aliases
#
# Anatomy beat primitive obsession: two or three landmark indices that only
# make sense *together* are modelled as one named group rather than numbered
# loose fields. These are documentation-bearing aliases, not new types —
# plain tuples of BlazePose landmark indices (see core/pose_segments.py).
# ---------------------------------------------------------------------------

#: Two BlazePose landmark indices between which a distance is measured.
LandmarkPair = tuple[int, int]

#: Three BlazePose landmark indices forming an angle: (first, vertex, second).
#: The measured angle is always the one *at the middle (vertex) index*.
LandmarkTriplet = tuple[int, int, int]


class Severity(str, Enum):
    """How severe a failed validation is.

    Drives feedback emphasis. A ``str`` Enum so members compare equal to the
    plain literals they replace (``Severity.ERROR == "error"`` is ``True``);
    string comparisons, dict keys, and JSON/CSV exports are unaffected.
    Extend freely (e.g. a new level) without touching consumers.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Stage(str, Enum):
    """The rep-progress vocabulary: where a repetition currently is.

    UP ↔ DOWN are the rest/end positions of a repetition; RETURNING is the
    transit from DOWN back towards UP. Distinct from per-rule *display*
    labels (e.g. "open"/"close"), which are exercise presentation and live
    on the counter rule itself.

    A ``str`` Enum, so ``Stage.UP == "up"`` is ``True`` and string
    comparisons keep working.
    """

    UP = "up"
    DOWN = "down"
    RETURNING = "returning"


@dataclass(frozen=True)
class AngleCounterRule:
    """One repetition, counted from the angle of a single joint.

    *What it represents:* the complete definition of "one rep" for one joint
    movement — when the measured angle crosses ``down_angle`` after having
    been above ``up_angle``, one repetition has happened.

    *What it measures:* the angle (in degrees) at the vertex landmark of
    ``joints``.

    *Why it exists:* everything needed to count a rep is four numbers and
    two labels, so a plain frozen description is the simplest honest
    model — no behaviour, no state, nothing to test beyond construction.

    *When a rep counts:* the angle leaves the ``up`` half and enters the
    ``down`` half of the range. With ``min_rom_angle`` / ``max_rom_angle``
    set, a rep additionally only counts as GOOD when both extremes were
    actually reached, and with ``min_rep_frames`` set, when it spanned at
    least that many frames.

    Attributes:
        name:          Stable id of this counter (e.g. "knee", "elbow").
        joints:        The triplet forming the measured angle (angle is
                       taken at the middle landmark).
        up_angle:      Angle (deg) marking the "up" end of the movement.
        down_angle:    Angle (deg) marking the "down" end of the movement.
        up_stage:      Display label for the up end (default "up"; exercises
                       may rename it, e.g. "open", "lockout").
        down_stage:    Display label for the down end (default "down").
        min_rom_angle: Optional bottom extreme (deg) a GOOD rep must reach.
        max_rom_angle: Optional top extreme (deg) a GOOD rep must reach.
        min_rep_frames: Minimum frames a rep may span (0 = no speed limit).
        sync_group:    Optional group name; rules sharing a group count only
                       when all of them reach their thresholds together.
    """

    name: str
    joints: LandmarkTriplet
    up_angle: float
    down_angle: float
    up_stage: str = Stage.UP
    down_stage: str = Stage.DOWN
    min_rom_angle: float | None = None
    max_rom_angle: float | None = None
    min_rep_frames: int = 0   # minimum frames a rep must span (0 = no check)
    sync_group: str | None = None  # optional synchronization group


@dataclass(frozen=True, kw_only=True)
class ValidationRule:
    """Base contract of every form-check rule: identity, feedback, emphasis.

    Every validation rule — regardless of what it measures — needs the same
    three things: a *name* to identify it, a *message* to coach the user
    when it fails, and a *severity* to say how much a failure matters. This
    base holds exactly those shared fields and nothing else.

    Defined with ``kw_only=True`` so subclasses can add their own required
    measurement fields after the defaulted ``severity``.

    Attributes:
        name:       Stable id of the check (e.g. "back_straight").
        message:    Coaching cue shown to the user while the rule fails.
        severity:   How much a failure matters (default ``Severity.ERROR``).
    """

    name: str
    message: str
    severity: str = Severity.ERROR


@dataclass(frozen=True, kw_only=True)
class AngleValidationRule(ValidationRule):
    """A per-frame form check: one joint angle inside an acceptable range.

    *What it represents:* "this joint should stay between X° and Y° while
    exercising" — e.g. keep the back straight, don't lock the elbows.

    *What it measures:* the angle (in degrees) at the vertex landmark of
    ``joints``, evaluated independently on each observation — the rule has
    no memory.

    *Why it exists:* most form cues are simple acceptable ranges on one
    angle; such a cue is fully described by a triplet and two bounds.

    *When it is satisfied:* whenever the measured angle lies inside
    [``min_angle``, ``max_angle``] (inclusive).

    Attributes:
        joints:     The triplet forming the measured angle (angle is taken
                    at the middle landmark).
        min_angle:  Lower bound of the acceptable range (deg, inclusive).
        max_angle:  Upper bound of the acceptable range (deg, inclusive).
    """

    joints: LandmarkTriplet
    min_angle: float
    max_angle: float


@dataclass(frozen=True, kw_only=True)
class AngleROMValidationRule(ValidationRule):
    """A Range-Of-Motion check: a rep must actually reach both extremes.

    *What it represents:* "go all the way down AND all the way up" — the
    check is on the *achievement of a range across a whole repetition*, not
    on the angle of any single frame (that is :class:`AngleValidationRule`).

    *What it measures:* the angle progression at the vertex of ``joints``
    over the course of a rep, against the bottom and top extremes.

    *Why it exists:* partial reps are the most common form fault and cannot
    be detected by any single-frame range check — every frame of a half-rep
    can look "in range".

    *When it is satisfied:* a rep reaches at least ``min_rom_angle`` at its
    bottom (angle small enough) AND at least ``max_rom_angle`` at its top
    (angle large enough). While the rep is short of the bottom extreme the
    rule reports "go deeper"; short of the top it reports "extend fully".

    Attributes:
        name:          Stable id matching the corresponding counter rule.
        joints:        The triplet forming the measured angle (angle is
                       taken at the middle landmark).
        min_rom_angle: Bottom threshold (deg) the rep must reach.
        max_rom_angle: Top threshold (deg) the rep must reach.
    """

    joints: LandmarkTriplet
    min_rom_angle: float
    max_rom_angle: float


@dataclass(frozen=True, kw_only=True)
class DistanceValidationRule(ValidationRule):
    """A spatial form check: one body distance relative to another.

    *What it represents:* "these two landmarks should stay between X× and
    Y× as far apart as those two" — e.g. wrists at least 1.2× shoulder
    width apart during an overhead press.

    *What it measures:* the distance between the ``measurement`` landmarks,
    expressed as a RATIO to the distance between the ``reference``
    landmarks. Because only a ratio is checked, the rule is independent of
    camera distance and body size — 1.2× shoulder width is 1.2× whether the
    person stands near or far.

    *Why it exists:* some form faults are about relative position, not
    angles (grip too narrow, knees caving inwards); a reference-normalized
    distance expresses them in the body's own units.

    *When it is satisfied:* whenever
    ``min_ratio <= dist(measurement) / dist(reference) <= max_ratio``.

    Attributes:
        measurement: The landmark pair whose distance is being checked.
        reference:   The landmark pair providing the normalizing distance
                     (e.g. the shoulders — a stable body-proportional unit).
        min_ratio:   Minimum acceptable ratio (inclusive).
        max_ratio:   Maximum acceptable ratio (inclusive).
    """

    measurement: LandmarkPair
    reference: LandmarkPair
    min_ratio: float
    max_ratio: float
