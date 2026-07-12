import functools
import math

import cv2

from .geometry import ComputedAngle


# ── Stats overlay layout ────────────────────────────────────────────────────
# Centralized here (the rendering module) so these values are never scattered
# as magic numbers across the project.
STATS_MARGIN = 20          # distance from left & bottom frame edges (px)
STATS_PADDING = 10         # inner padding inside the box (px)
STATS_LINE_HEIGHT = 25     # vertical space reserved per text line (px)
STATS_FONT = cv2.FONT_HERSHEY_SIMPLEX
STATS_FONT_SCALE = 0.6
STATS_THICKNESS = 2
STATS_BG_ALPHA = 0.5       # opacity of the semi-transparent background


def draw_skeleton(frame, pts, colors, is_bad=False):
    if len(pts) < 3:
        return

    # ── Visual constants — matched pixel-by-pixel to the reference design ─────
    # Dodger-blue  BGR = (235, 145, 30)  →  RGB(30,145,235)  bright blue
    SKEL_COLOR  = (255, 255, 255)
    line_color  = colors.ERROR if is_bad else SKEL_COLOR
    point_color = colors.ERROR if is_bad else SKEL_COLOR

    LINE_W   = 5    # thin line — exactly like the reference image
    RADIUS   = 12   # circle radius slightly bigger than line width
    BORDER_W = 8    # circle border — same weight as the lines

    def _edge_point(src, dst, r):
        """Point on the edge of the circle at *src* facing *dst*.
        Lines are drawn FROM here so they never cross into the circle."""
        dx, dy = dst[0] - src[0], dst[1] - src[1]
        dist = math.hypot(dx, dy)
        if dist < 1:
            return src
        return (int(src[0] + dx / dist * r),
                int(src[1] + dy / dist * r))

    p0, p1, p2 = pts[0], pts[1], pts[2]

    # ① Lines drawn FIRST — sit behind the circles
    cv2.line(frame,
             _edge_point(p0, p1, RADIUS), _edge_point(p1, p0, RADIUS),
             line_color, LINE_W, cv2.LINE_AA)
    cv2.line(frame,
             _edge_point(p1, p2, RADIUS), _edge_point(p2, p1, RADIUS),
             line_color, LINE_W, cv2.LINE_AA)

    # ② Hollow circles drawn LAST — always on top, clean edges, never filled
    for p in pts:
        cv2.circle(frame, p, RADIUS, point_color, BORDER_W, cv2.LINE_AA)


def draw_stats(
    frame,
    *,
    exercise_name: str,
    good: int,
    bad: int,
    total: int,
    stage: str,
    state: str,
    angle: float,
    feedback: list[str] | None = None,
    colors,
):
    """Draw the stats / coaching overlay in the bottom-left corner.

    The box is positioned with a small margin from the left and bottom edges
    and is clamped so it always stays fully inside the frame, regardless of
    resolution. It is intentionally NOT anchored to any body landmark — its
    position is fixed on screen.

    Core lines: exercise name, Reps, Stage, State, Current Angle.
    Exercise-specific feedback (validation cues) is appended below.
    """
    h, w = frame.shape[:2]
    feedback = feedback or []

    lines = [
        exercise_name,
        f"Good Reps: {good}",
        f"Bad Reps: {bad}",
        f"Total Reps: {total}",
        f"Stage: {stage}",
        f"State: {state}",
        f"Angle: {int(angle)} deg",
    ]
    # Exercise-specific feedback below the core information.
    for msg in feedback:
        lines.append(f"- {msg}")

    def line_color(text: str):
        if text.startswith("- "):
            return colors.ERROR
        if text.startswith("State: GOOD"):
            return colors.HIGHLIGHT
        if text.startswith("State: BAD"):
            return colors.ERROR
        return colors.TEXT

    # Measure the box from the actual text.
    sizes = [
        cv2.getTextSize(t, STATS_FONT, STATS_FONT_SCALE, STATS_THICKNESS)[0]
        for t in lines
    ]
    box_width = max(s[0] for s in sizes) + STATS_PADDING * 2
    box_height = len(lines) * STATS_LINE_HEIGHT + STATS_PADDING * 2

    # Bottom-left, then clamp so the whole box stays on screen.
    box_x = STATS_MARGIN
    box_y = h - STATS_MARGIN - box_height
    box_x = max(STATS_MARGIN, min(box_x, w - STATS_MARGIN - box_width))
    box_y = max(STATS_MARGIN, min(box_y, h - STATS_MARGIN - box_height))

    # Semi-transparent background (readable on both dark and bright frames).
    overlay = frame.copy()
    cv2.rectangle(overlay, (box_x, box_y), (box_x + box_width, box_y + box_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, STATS_BG_ALPHA, frame, 1 - STATS_BG_ALPHA, 0, frame)

    for i, text in enumerate(lines):
        cv2.putText(
            frame, text,
            (box_x + STATS_PADDING, box_y + STATS_PADDING + (i + 1) * STATS_LINE_HEIGHT - 5),
            STATS_FONT, STATS_FONT_SCALE, line_color(text), STATS_THICKNESS, cv2.LINE_AA,
        )


# ── Screen-fit display ──────────────────────────────────────────────────────
# Centralized, cross-platform helpers so frame fitting is computed in exactly
# one place (never scattered around the project). No magic numbers: the margin
# and fallback values are exposed as constants below.
SCREEN_MARGIN_RATIO = 0.05   # fraction of the screen kept as margin on each side
SCREEN_MARGIN_PX = 50        # minimum margin in pixels (wins on tiny screens)
DEFAULT_SCREEN_WIDTH = 1280  # fallback if the screen size can't be detected
DEFAULT_SCREEN_HEIGHT = 720


@functools.lru_cache(maxsize=1)
def get_screen_size():
    """Return the primary screen ``(width, height)`` in pixels.

    Cached with :func:`functools.lru_cache` so detection runs **only once**.
    Uses Tkinter (part of the Python stdlib, available on Windows / Linux /
    macOS). Falls back to :data:`DEFAULT_SCREEN_WIDTH` x
    :data:`DEFAULT_SCREEN_HEIGHT` when no display/GUI is reachable.
    """
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()          # avoid flashing a window
        root.update_idletasks()  # ensure geometry is computed
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.destroy()
        if w > 0 and h > 0:
            return (w, h)
    except Exception:
        pass
    return (DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)


def fit_to_screen(frame, max_width=None,
                  margin_ratio=SCREEN_MARGIN_RATIO, margin_px=SCREEN_MARGIN_PX):
    """Resize ``frame`` to fit the screen while preserving aspect ratio.

    Behaviour:
    * Only **downscales** — small videos are never upscaled (scale capped at 1).
    * Respects a margin so the window never touches the screen edges.
    * ``max_width`` (optional) adds an extra maximum-width cap on top of the
      screen fit (e.g. the ``DISPLAY_MAX_WIDTH`` setting).
    * The returned frame is for **display only**; pose math and video recording
      continue to use the original-resolution frame.

    Returns the original ``frame`` unchanged when no downscaling is needed.
    """
    screen_w, screen_h = get_screen_size()
    margin_x = max(int(screen_w * margin_ratio), margin_px)
    margin_y = max(int(screen_h * margin_ratio), margin_px)
    avail_w = max(1, screen_w - 2 * margin_x)
    avail_h = max(1, screen_h - 2 * margin_y)

    h, w = frame.shape[:2]
    caps = [avail_w / w, avail_h / h, 1.0]   # 1.0 => never upscale
    if max_width is not None:
        caps.append(max_width / w)
    scale = min(caps)

    if scale >= 1.0:
        return frame
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def draw_angle_arc(frame, a, b, c, colors, is_bad=False, radius=20):
    """Draw the visual angle arc at point B between BA and BC.

    The arc radius is set LARGER than the skeleton circle (RADIUS=22) so the
    arc appears clearly OUTSIDE the joint circle — never overlapping it.
    Only the arc is drawn here; the numeric label is rendered by draw_angle_labels.
    """
    # Arc must be bigger than the skeleton circle radius (22px) to sit outside it
    ARC_RADIUS = 42   # clearly outside the 22px skeleton circle

    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    angle1 = math.degrees(math.atan2(ba[1], ba[0]))
    angle2 = math.degrees(math.atan2(bc[1], bc[0]))

    start_angle = int(angle1)
    end_angle   = int(angle2)

    # Always draw the smallest arc (the actual angle, not the reflex)
    if end_angle < start_angle:
        end_angle += 360
    if end_angle - start_angle > 180:
        start_angle, end_angle = end_angle, start_angle + 360

    color = colors.ERROR if is_bad else colors.HIGHLIGHT

    cv2.ellipse(frame, b, (ARC_RADIUS, ARC_RADIUS),
                0, start_angle, end_angle, color, 2, cv2.LINE_AA)


# ── Floating angle-label layout ──────────────────────────────────────────────
# Centralized so these values are not scattered as magic numbers across files.
ANGLE_FONT = cv2.FONT_HERSHEY_SIMPLEX
ANGLE_BASE_SCALE = 0.9      # font scale at a 1280px-wide frame (see _scale)
ANGLE_PADDING = 6           # inner padding of the label box (px)
ANGLE_OFFSET = 14           # push the label away from the joint (px)
ANGLE_BG_ALPHA = 0.65       # opacity of the semi-transparent backing
ANGLE_MIN_SCALE = 0.7
ANGLE_MAX_SCALE = 2.0


def _angle_scale(width: int) -> float:
    """Keep on-screen label size constant regardless of source resolution.

    The frame is later resized to ``display_width`` (1280) before display, so
    scaling the font by the *source* width makes the final on-screen size
    resolution-independent.
    """
    return max(ANGLE_MIN_SCALE, min(ANGLE_MAX_SCALE, width / 1280.0))


def draw_angle_labels(frame, views: list[ComputedAngle], colors, width: int, height: int):
    """Draw a small floating angle box for EVERY computed angle.

    ``views`` already contains one entry per CounterRule and per
    ValidationRule (built by GymEngine.analyze), so this function is completely
    exercise/rule-agnostic: add a rule or a whole new exercise and the labels
    appear automatically with no change here.

    Colour: highlight for normal angles and counter rules; error for failed
    validation. Each label sits at the rule's vertex joint (so it tracks the
    person) with a small offset so it doesn't cover the joint.
    """
    scale = _angle_scale(width)
    font_scale = ANGLE_BASE_SCALE * scale
    thickness = max(1, round(2 * scale))
    padding = round(ANGLE_PADDING * scale)
    offset = round(ANGLE_OFFSET * scale)
    border = max(1, round(2 * scale))

    for v in views:
        color = colors.ERROR if v.is_error else colors.HIGHLIGHT
        text = f"{int(round(v.angle))} deg"

        (tw, th), _ = cv2.getTextSize(text, ANGLE_FONT, font_scale, thickness)
        box_w = tw + padding * 2
        box_h = th + padding * 2

        # Anchor up-and-right of the vertex so the box clears the joint.
        bx = v.vertex[0] + offset
        by = v.vertex[1] - offset - box_h
        # Keep the whole label on screen.
        bx = max(0, min(bx, width - box_w))
        by = max(0, min(by, height - box_h))

        # Dark, semi-transparent backing -> readable on light or dark frames.
        overlay = frame.copy()
        cv2.rectangle(overlay, (bx, by), (bx + box_w, by + box_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, ANGLE_BG_ALPHA, frame, 1 - ANGLE_BG_ALPHA, 0, frame)

        # State colour on the border + text (project palette).
        cv2.rectangle(frame, (bx, by), (bx + box_w, by + box_h), color, border)
        cv2.putText(
            frame, text, (bx + padding, by + padding + th),
            ANGLE_FONT, font_scale, color, thickness, cv2.LINE_AA,
        )