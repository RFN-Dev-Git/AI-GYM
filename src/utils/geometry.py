import math
from dataclasses import dataclass


@dataclass
class ComputedAngle:
    """One computed angle, ready for the renderer to draw.

    This is the single contract between the analysis layer and the rendering
    layer: ``GymEngine`` produces one ``ComputedAngle`` per ``AngleCounterRule`` and
    per ``AngleValidationRule``, and the renderer iterates over them without knowing
    which exercise or rule produced them. Adding a rule (or a whole new
    exercise) therefore needs zero renderer changes.
    """

    name: str
    vertex: tuple          # pixel (x, y) of the middle/vertex joint
    angle: float | None   # None when the angle could not be computed
    is_error: bool         # True -> draw with the error colour


def calc_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag1 = math.hypot(*ba)
    mag2 = math.hypot(*bc)

    if mag1 == 0 or mag2 == 0:
        # Degenerate geometry (overlapping joints) -> angle is undefined.
        return None

    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_theta))


def get_points(indices, landmarks, w, h, threshold: float = 0.3):
    pts = []
    for i in indices:
        lm = landmarks[i]
        if hasattr(lm, "visibility") and lm.visibility < threshold:
            continue
        pts.append((int(lm.x * w), int(lm.y * h)))
    return pts


def calc_distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])
