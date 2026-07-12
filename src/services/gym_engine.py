"""Generic, exercise-agnostic training engine."""

import os

import cv2

from ..config import settings
from ..core import Colors
from ..exercises.exercise import Exercise
from ..exercises.validation import ValidationResult, validate_all, violations
from ..utils.geometry import ComputedAngle, calc_angle, get_points
from ..utils.render import draw_angle_arc, draw_angle_labels, draw_skeleton, draw_stats, fit_to_screen
from ..utils.history import HistoryWriter
from ..utils.camera_side import CameraSideDetector
from .pose_service import PoseService
from .rep_counter import RepCounter


class FrameResult:
    """Everything computed for a single frame, handed to the renderer."""

    def __init__(self, angles, states, results, views=None):
        self.angles = angles
        self.states = states
        self.results: list[ValidationResult] = results
        # One ComputedAngle per rule (counter + validation) for the renderer.
        self.views: list[ComputedAngle] = views or []


class GymEngine:
    """Runs any exercise described by an :class:`Exercise` configuration.

    GymEngine knows NOTHING about Push-Ups, Squats, or any specific movement.
    Its single responsibility is the loop: detect pose -> compute the angles the
    exercise asked for -> update the counter -> run the validation rules ->
    forward everything to the renderer. Behaviour comes entirely from the
    ``Exercise`` object passed in.

    This is the Open/Closed Principle in practice: to support a new exercise you
    add a new ``Exercise`` definition; you never modify this class.
    """

    def __init__(self, exercise: Exercise, colors: Colors | None = None, display_width: int = 1280):
        self.exercise = exercise
        self.counter = RepCounter(exercise.counter_rules)
        self.colors = colors or Colors()
        # Optional maximum display width (e.g. DISPLAY_MAX_WIDTH). The frame is
        # first auto-fit to the detected screen; this only caps it further.
        self.display_width = display_width
        self.history_writer = HistoryWriter(exercise.name)
        self.side_detector = CameraSideDetector(30) if exercise.camera == "side" else None
        self.rules_adapted = False if exercise.camera == "side" else True

    # ------------------------------------------------------------------
    # Analysis: pure logic, no I/O -> easy to unit test with fake landmarks.
    # ------------------------------------------------------------------
    def analyze(self, landmarks, width: int, height: int, frame_id: int) -> FrameResult:
        """Compute angles, update the counter, and run validation rules."""
        if self.side_detector and not self.rules_adapted:
            side = self.side_detector.process_frame(landmarks)
            if side:
                from ..utils.camera_side import adapt_rules
                self.exercise.counter_rules = adapt_rules(self.exercise.counter_rules, side)
                self.exercise.validation_rules = adapt_rules(self.exercise.validation_rules, side)
                self.counter = RepCounter(self.exercise.counter_rules)
                self.rules_adapted = True
            if not self.rules_adapted:
                return FrameResult(angles={}, states=self.counter.states, results=[], views=[])

        angles = {}
        views = []  # unified per-rule angle views for the renderer

        for rule in self.exercise.counter_rules:
            pts = get_points(rule.joints, landmarks, width, height)
            angle = calc_angle(*pts) if len(pts) >= 3 else 0.0
            angles[rule.name] = angle
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            # Counter angles are never "failed" -> drawn with the highlight colour.
            views.append(ComputedAngle(name=rule.name, vertex=vertex, angle=angle, is_error=False))

        # Track old counts to detect completion of a rep
        old_counts = {name: (state.good, state.bad) for name, state in self.counter.states.items()}

        results = validate_all(self.exercise.validation_rules, landmarks, width, height)
        has_violation = len(violations(results)) > 0

        self.counter.update(angles, has_violation)

        for res in results:
            pts = get_points(res.joints, landmarks, width, height)
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            views.append(
                ComputedAngle(name=res.rule_name, vertex=vertex, angle=res.angle, is_error=not res.passed)
            )

        # Record rep to history if completed
        if self.exercise.counter_rules:
            primary_name = self.exercise.counter_rules[0].name
            if primary_name in old_counts:
                old_good, old_bad = old_counts[primary_name]
                new_state = self.counter.states[primary_name]
                if new_state.good > old_good or new_state.bad > old_bad:
                    rep_type = "good" if new_state.good > old_good else "bad"
                    active_violations = [r.message for r in violations(results)]
                    self.history_writer.record(
                        rep_num=new_state.count,
                        result=rep_type,
                        frame_id=frame_id,
                        violations=active_violations
                    )

        return FrameResult(
            angles=angles, states=self.counter.states, results=results, views=views
        )

    # ------------------------------------------------------------------
    # Rendering: draws whatever the Exercise configuration describes.
    # ------------------------------------------------------------------
    def _render(self, frame, result: FrameResult, landmarks, width: int, height: int):
        bad = bool(violations(result.results))
        show = self.exercise.display

        # Skeleton for every joint set the exercise cares about.
        if show.show_skeleton:
            for rule in self.exercise.counter_rules + self.exercise.validation_rules:
                pts = get_points(rule.joints, landmarks, width, height)
                if len(pts) >= 3:
                    draw_skeleton(frame, pts, self.colors, is_bad=bad)

        # Live angle arcs for each counter rule (visual only; the numeric
        # value is drawn by draw_angle_labels for EVERY computed angle).
        if show.show_angle_arc:
            for rule in self.exercise.counter_rules:
                pts = get_points(rule.joints, landmarks, width, height)
                if len(pts) >= 3:
                    draw_angle_arc(frame, pts[0], pts[1], pts[2], self.colors, is_bad=bad)

        # Floating angle label for EVERY computed angle (counter + validation),
        # positioned at the rule's vertex joint. Fully automatic & rule-agnostic.
        draw_angle_labels(frame, result.views, self.colors, width, height)

        # Stats / coaching panel: a fixed bottom-left overlay (not anchored to
        # any body landmark). Layout lives in utils/render.py.
        primary = self.counter.primary
        issues = violations(result.results)
        feedback = [r.message for r in issues]
        draw_stats(
            frame,
            exercise_name=self.exercise.name,
            good=primary.good,
            bad=primary.bad,
            total=primary.count,
            stage=primary.stage,
            state="GOOD" if not issues else "BAD",
            angle=primary.angle,
            feedback=feedback,
            colors=self.colors,
        )

    # ------------------------------------------------------------------
    # Orchestration: video source + detection + render loop.
    # ------------------------------------------------------------------
    def run(self, video_path: str | None = None):
        if settings.USE_WEBCAM:
            cap = cv2.VideoCapture(settings.WEBCAM_INDEX)
        else:
            path = video_path or settings.VIDEO_PATH
            cap = cv2.VideoCapture(path)

        if not cap.isOpened():
            raise RuntimeError("Cannot open video source")

        fps = 25  # fixed for deterministic timestamps

        writer = None
        if settings.SAVE_OUTPUT:
            os.makedirs(os.path.dirname(settings.OUTPUT_PATH), exist_ok=True)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(settings.OUTPUT_PATH, fourcc, fps, (width, height))

        pose_service = PoseService(settings.MODEL_PATH)
        frame_id = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            timestamp = int((frame_id / fps) * 1000)

            result = pose_service.detect(frame, timestamp)

            if result and result.pose_landmarks:
                lm = result.pose_landmarks[0]
                frame_result = self.analyze(lm, w, h, frame_id)
                self._render(frame, frame_result, lm, w, h)

            if writer:
                writer.write(frame)

            # Display-only resize: pose math + saved output use the original frame.
            frame = fit_to_screen(frame, max_width=self.display_width)
            cv2.imshow("AI Gym Trainer", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            frame_id += 1

        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()

        # Save workout history to history.json
        primary = self.counter.primary
        self.history_writer.save(good=primary.good, bad=primary.bad)
