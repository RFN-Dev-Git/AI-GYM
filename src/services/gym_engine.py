"""Generic, exercise-agnostic training engine."""

import datetime
import time

import cv2

from ..analytics.analyzer import SessionAnalyzer
from ..analytics.session_summary import SessionSummary
from ..config import settings
from ..core import Colors
from ..exercises.exercise import Exercise
from ..exercises.validation import ValidationResult, validate_all, violations
from ..utils.geometry import ComputedAngle, calc_angle, get_points
from ..utils.render import draw_angle_arc, draw_angle_labels, draw_skeleton, draw_stats, fit_to_screen
from .pose_service import PoseService
from .rep_counter import RepCounter
from .rep_judge import RepJudge


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
        self.judge = RepJudge()
        self.colors = colors or Colors()
        # Optional maximum display width (e.g. DISPLAY_MAX_WIDTH). The frame is
        # first auto-fit to the detected screen; this only caps it further.
        self.display_width = display_width

    # ------------------------------------------------------------------
    # Analysis: pure logic, no I/O -> easy to unit test with fake landmarks.
    # ------------------------------------------------------------------
    def analyze(self, landmarks, width: int, height: int, frame: int) -> FrameResult:
        """Compute angles, update the counter, run validation, and judge reps."""
        angles = {}
        views = []  # unified per-rule angle views for the renderer

        for rule in self.exercise.counter_rules:
            pts = get_points(rule.joints, landmarks, width, height)
            angle = calc_angle(*pts) if len(pts) >= 3 else None
            angles[rule.name] = angle
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            # Counter angles are never "failed" -> drawn with the highlight colour.
            views.append(ComputedAngle(name=rule.name, vertex=vertex, angle=angle, is_error=False))

        results = validate_all(self.exercise.validation_rules, landmarks, width, height)

        for res in results:
            pts = get_points(res.joints, landmarks, width, height)
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            views.append(
                ComputedAngle(name=res.rule_name, vertex=vertex, angle=res.angle, is_error=not res.passed)
            )

        # ── Rep quality tracking (orchestration only) ──────────────────
        # GymEngine feeds validation results to the judge every frame and tells
        # the judge when a rep completed. Completion is detected here by reading
        # RepCounter's rep count -- RepCounter remains the sole authority on
        # counting and is never told about validation. All GOOD/BAD logic lives
        # in RepJudge, so nothing in this class decides rep quality.
        self.judge.observe(results, frame)

        prev_count = self.counter.primary.count
        self.counter.update(angles)  # RepCounter detects completion
        if self.counter.primary.count > prev_count:
            self.judge.finalize_rep(self.counter.primary.count, frame)

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
        # any body landmark). Layout lives in utils/render.py. Rep-quality
        # figures come from RepJudge (history is the single source of truth).
        primary = self.counter.primary
        issues = violations(result.results)
        feedback = [r.message for r in issues]
        last = self.judge.last_rep
        current_rep = (
            "GOOD" if (last is not None and last.good)
            else "BAD" if last is not None
            else "—"
        )
        draw_stats(
            frame,
            exercise_name=self.exercise.name,
            reps=self.judge.total_reps,
            good_reps=self.judge.good_reps,
            bad_reps=self.judge.bad_reps,
            current_rep=current_rep,
            stage=primary.stage,
            angle=primary.angle,
            feedback=feedback,
            colors=self.colors,
        )

    # ------------------------------------------------------------------
    # Session analytics + export (orchestration only — no logic here).
    # ------------------------------------------------------------------
    def _export_session(self, summary: "SessionSummary") -> None:
        """Persist ``summary`` using the configured exporter (opt-in)."""
        from ..analytics.exporters import CsvSessionExporter, JsonSessionExporter

        settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.exercise.name)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target = settings.EXPORT_DIR / f"{safe_name}_{stamp}"
        exporter = (
            JsonSessionExporter() if settings.EXPORT_FORMAT.lower() == "json"
            else CsvSessionExporter()
        )
        out_path = exporter.export(summary, target)
        print(f"Session summary exported to {out_path}")

    # ------------------------------------------------------------------
    # Orchestration: video source + detection + render loop.
    # ------------------------------------------------------------------
    def run(self, video_path: str | None = None):
        if settings.USE_WEBCAM:
            cap = cv2.VideoCapture(settings.WEBCAM_INDEX)
        else:
            src = video_path or settings.VIDEO_PATH
            cap = cv2.VideoCapture(str(src) if src is not None else None)

        if not cap.isOpened():
            raise RuntimeError("Cannot open video source")

        fps = 25  # fixed for deterministic timestamps

        writer = None
        if settings.SAVE_OUTPUT:
            settings.OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(settings.OUTPUT_PATH), fourcc, fps, (width, height))

        pose_service = PoseService(settings.MODEL_PATH)
        start_time = time.perf_counter()
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

        # ── Session report (built entirely from RepJudge.history) ─────
        # GymEngine only supplies engine-level context (exercise, source,
        # frames, time); all rep-quality figures are derived by RepJudge so no
        # state is duplicated here.
        elapsed = time.perf_counter() - start_time
        frames_processed = frame_id
        if settings.USE_WEBCAM:
            input_source = f"Webcam (index {settings.WEBCAM_INDEX})"
        else:
            src = video_path or settings.VIDEO_PATH
            input_source = str(src) if src is not None else "none"

        print(self.judge.session_report(
            exercise_name=self.exercise.name,
            input_source=input_source,
            total_frames=frames_processed,
            elapsed_seconds=elapsed,
        ))

        # ── Session analytics + optional export ──────────────────────
        # GymEngine only *orchestrates*: it hands the finished session
        # (RepJudge.history) to the analytics module and, if enabled, asks an
        # exporter to persist the resulting SessionSummary. No analytics logic
        # lives in the engine.
        if settings.EXPORT_SESSION:
            summary = SessionAnalyzer().analyze(
                self.judge.history,
                exercise_name=self.exercise.name,
                fps=settings.ANALYTICS_FPS,
                total_duration=elapsed,
            )
            self._export_session(summary)

        print(self.judge.history)
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
