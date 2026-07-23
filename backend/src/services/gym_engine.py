"""Generic, exercise-agnostic training engine."""

import datetime
import time

import cv2

from ..config import settings
from ..core import Colors
from ..exercises.exercise import Camera, Exercise
from ..exercises.validation import ValidationResult, validate_all, violations
from ..exercises.rules import DistanceValidationRule, Severity, Stage
from ..utils.geometry import ComputedAngle, calc_angle, get_points
from ..utils.render import draw_angle_arc, draw_angle_labels, draw_skeleton, draw_stats, fit_to_screen, draw_segment_line
from ..utils.camera_side import CameraSideDetector
from .pose_service import PoseService
from .rep_counter import RepCounter
from .rep_judge import RepJudge
from .video_source import open_capture


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
        self.side_detector = CameraSideDetector(30) if exercise.camera == Camera.SIDE else None
        self.rules_adapted = False if exercise.camera == Camera.SIDE else True
        # ── Distance-based form rules (exercise-agnostic) ──────────────
        # Every DistanceValidationRule declared by the exercise participates:
        # a violation of any of them poisons the repetition it occurs in.
        # Exercises without distance rules get an empty set here and are
        # completely unaffected by this machinery.
        self._distance_rule_names = {
            r.name for r in exercise.validation_rules
            if isinstance(r, DistanceValidationRule)
        }
        # Set when any distance rule fails; consumed when the rep completes.
        self._distance_violation_in_current_rep = False
        # Failing results kept per rule name so the rep report can explain
        # *why* (the rule may pass again by the frame the rep completes on).
        self._distance_violation_results = {}

    # ------------------------------------------------------------------
    # Analysis: pure logic, no I/O -> easy to unit test with fake landmarks.
    # ------------------------------------------------------------------
    def analyze(self, landmarks, width: int, height: int, frame: int) -> FrameResult:
        """Compute angles, update the counter, run validation, and judge reps."""
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
            angle = calc_angle(*pts) if len(pts) >= 3 else None
            angles[rule.name] = angle
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            # Counter angles are never "failed" -> drawn with the highlight colour.
            views.append(ComputedAngle(name=rule.name, vertex=vertex, angle=angle, is_error=False))

        results = validate_all(self.exercise.validation_rules, landmarks, width, height, states=self.counter.states)

        for res in results:
            pts = get_points(res.joints, landmarks, width, height)
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            views.append(
                ComputedAngle(name=res.rule_name, vertex=vertex, angle=res.angle, is_error=not res.passed)
            )

        # ── Rep quality tracking ───────────────────────────────────────
        # RepCounter owns counting AND quality (good/bad) decisions.
        # Pass violation_names (set of failing rule names) — not a single global
        # bool — so each counter rule only accumulates violations for its own joints.
        violation_names = {r.rule_name for r in violations(results)}
        prev_good  = self.counter.primary.good
        prev_count = self.counter.primary.count

        # Preserve every rule outcome of this frame in the rep's complete
        # evaluation record. Pure data collection for reporting — it does not
        # affect classification or any other decision.
        self.judge.record(results, frame)

        # ── Distance-violation tracking (works for ANY exercise) ────────
        # Accumulate: a distance failure at any point during the current rep
        # marks the whole rep. The flag is only consumed (and cleared) when a
        # rep completes below — never reset per-frame, so a violation at the
        # top of a press still poisons the rep that is counted on the way down.
        if self._distance_rule_names & violation_names:
            self._distance_violation_in_current_rep = True
            for r in results:
                if not r.passed and r.rule_name in self._distance_rule_names:
                    self._distance_violation_results[r.rule_name] = r

        self.counter.update(angles, violation_names)

        if self.counter.primary.count > prev_count:
            # Rep just completed - check if there was a distance violation
            if self._distance_violation_in_current_rep:
                # Hand the stored failing result(s) to the judge so the
                # session report explains *why* this rep is bad, then force
                # the rep to be bad.
                self.judge.observe(
                    list(self._distance_violation_results.values()), frame,
                )
                self.judge.finalize_rep(
                    self.counter.primary.count,
                    frame,
                    force_good=False,
                )
                self._distance_violation_in_current_rep = False
                self._distance_violation_results.clear()
            else:
                rep_was_good = self.counter.primary.good > prev_good
                if self.counter.primary.speed_warning:
                    # Inject a speed violation warning
                    from ..exercises.validation import ValidationResult
                    self.judge.observe([
                        ValidationResult(
                            rule_name=self.exercise.counter_rules[0].name + "_too_fast",
                            message="Too fast — control the movement",
                            severity=Severity.WARNING,
                            passed=False,
                            angle=None
                        )
                    ], frame)
                self.judge.finalize_rep(
                    self.counter.primary.count,
                    frame,
                    force_good=rep_was_good,
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
            drawn_joints = set()
            for rule in self.exercise.counter_rules:
                pts = get_points(rule.joints, landmarks, width, height)
                if len(pts) >= 3:
                    custom_color = None
                    if bad:
                        custom_color = self.colors.ERROR
                    elif hasattr(rule, 'min_rom_angle') and rule.min_rom_angle is not None:
                        state = self.counter.states.get(rule.name)
                        if state is not None:
                            # Only show RED/GREEN feedback when actively in a rep
                            # (DOWN or RETURNING stage). At UP/rest, use default color.
                            if state.stage in (rule.up_stage,):
                                custom_color = None  # resting — default white
                            elif state.reached_bottom:
                                custom_color = self.colors.HIGHLIGHT   # GREEN — depth reached
                            else:
                                custom_color = self.colors.ERROR        # RED — need to go deeper
                    draw_skeleton(frame, pts, self.colors, is_bad=bad, custom_color=custom_color)
                    drawn_joints.add(tuple(sorted(rule.joints)))

            # Validation-rule skeletons (e.g. back angle for deadlift).
            # Can be suppressed per-exercise via DisplaySettings.show_validation_skeleton.
            if show.show_validation_skeleton:
                for rule in self.exercise.validation_rules:
                    # Only draw skeletons for rules with joints attribute (AngleValidationRule)
                    if hasattr(rule, 'joints'):
                        joints_key = tuple(sorted(rule.joints))
                        if joints_key not in drawn_joints:
                            pts = get_points(rule.joints, landmarks, width, height)
                            if len(pts) >= 3:
                                draw_skeleton(frame, pts, self.colors, is_bad=bad)
                                drawn_joints.add(joints_key)

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

        # Declarative landmark-to-landmark segment lines (e.g. the wrist line
        # at the top of a shoulder press). Driven entirely by
        # DisplaySettings.segment_lines — the engine knows nothing about
        # which exercise configured them.
        for seg in show.segment_lines:
            active = all(
                (result.angles.get(name) or 0.0) >= seg.min_angle
                for name in seg.active_angles
            )
            if not active:
                continue
            failed = seg.error_rule is not None and any(
                r.rule_name == seg.error_rule and not r.passed
                for r in result.results
            )
            line_color = self.colors.ERROR if failed else self.colors.HIGHLIGHT
            pts = get_points(seg.endpoints, landmarks, width, height)
            if len(pts) == 2:
                draw_segment_line(frame, pts[0], pts[1], self.colors, line_color)

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
        display_stage = primary.stage
        if self.exercise.counter_rules:
            rule = self.exercise.counter_rules[0]
            if primary.stage == Stage.UP:
                display_stage = rule.up_stage
            elif primary.stage == Stage.DOWN:
                display_stage = rule.down_stage

        draw_stats(
            frame,
            exercise_name=self.exercise.name,
            reps=self.judge.total_reps,
            good_reps=self.judge.good_reps,
            bad_reps=self.judge.bad_reps,
            current_rep=current_rep,
            stage=display_stage,
            angle=primary.angle,
            feedback=feedback,
            colors=self.colors,
        )

    # ------------------------------------------------------------------
    # Session analytics + export (orchestration only — no logic here).
    # ------------------------------------------------------------------
    def _export_session(self, report: "SessionReport") -> None:
        """Persist the complete session ``report`` as JSON (opt-in)."""
        from ..analytics.exporters import JsonSessionExporter

        if settings.EXPORT_FORMAT.lower() != "json":
            # CSV export was removed: a complete session history is nested
            # data and cannot be flattened without losing information. The
            # report is always written as JSON.
            print(
                f"EXPORT_FORMAT '{settings.EXPORT_FORMAT}' is no longer supported"
                " for session reports — writing JSON instead."
            )

        settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.exercise.name)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target = settings.EXPORT_DIR / f"{safe_name}_{stamp}"
        out_path = JsonSessionExporter().export(report, target)
        print(f"Session report exported to {out_path}")

    # ------------------------------------------------------------------
    # Orchestration: video source + detection + render loop.
    # ------------------------------------------------------------------
    def run(self, video_path: str | None = None):
        # Source acquisition + failure diagnostics live in video_source, so the
        # CLI, the engine and the live server all produce identical, actionable
        # errors (which path was tried, what assets/videos actually contains).
        cap = open_capture(
            video_path=video_path or settings.VIDEO_PATH,
            use_webcam=settings.USE_WEBCAM,
            webcam_index=settings.WEBCAM_INDEX,
        )

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
        # (RepJudge.history + the exercise it ran) to the analytics module
        # and, if enabled, asks an exporter to persist the resulting
        # SessionReport. No analytics logic lives in the engine.
        if settings.EXPORT_SESSION:
            # Imported lazily (like the exporters) so analytics stays an
            # optional, one-way dependency of the engine and import cycles
            # with the services package are avoided.
            from ..analytics.analyzer import SessionAnalyzer

            report = SessionAnalyzer().build_report(
                self.judge.history,
                exercise=self.exercise,
                fps=settings.ANALYTICS_FPS,
                total_duration=elapsed,
            )
            self._export_session(report)

        print(self.judge.history)
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
