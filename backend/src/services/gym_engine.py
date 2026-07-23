"""Generic, exercise-agnostic training engine - NOW FULL 3D.

Key change: Analysis uses 3D world landmarks (camera independent), 
Rendering uses 2D image landmarks (screen space).

GymEngine knows NOTHING about specific exercises. Its job is:
detect pose -> 3D angle calculation -> validation in 3D -> render in 2D
"""

import datetime
import time

import cv2

from ..config import settings
from ..core import Colors
from ..exercises.exercise import Camera, Exercise
from ..exercises.validation import ValidationResult, validate_all, violations
from ..exercises.rules import DistanceValidationRule, Severity, Stage
from ..utils.geometry import ComputedAngle, calc_angle, calc_angle_3d, get_points, get_points_3d
from ..utils.render import draw_angle_arc, draw_angle_labels, draw_skeleton, draw_stats, fit_to_screen, draw_segment_line
from ..utils.camera_side import CameraSideDetector
from ..utils.filters import WorldLandmarkSmoother
from .pose_service import PoseService
from .rep_counter import RepCounter
from .rep_judge import RepJudge
from .video_source import open_capture


class FrameResult:
    """Everything computed for a single frame, handed to the renderer."""

    def __init__(self, angles, states, results, views=None, is_3d=True):
        self.angles = angles  # Now 3D angles
        self.states = states
        self.results: list[ValidationResult] = results
        self.views: list[ComputedAngle] = views or []
        self.is_3d = is_3d


class GymEngine:
    """
    Runs any exercise - NOW FULL 3D MODE.
    
    Analysis: 3D world landmarks (meters) -> true body angles, camera independent
    Rendering: 2D image landmarks (pixels) -> skeleton drawn on screen
    """

    def __init__(self, exercise: Exercise, colors: Colors | None = None, display_width: int = 1280, use_3d: bool | None = None, smooth: bool | None = None):
        self.exercise = exercise
        self.counter = RepCounter(exercise.counter_rules)
        self.judge = RepJudge()
        self.colors = colors or Colors()
        self.display_width = display_width
        # If not specified, read from settings (.env) -> USE_3D, ENABLE_SMOOTHING
        self.use_3d = use_3d if use_3d is not None else settings.USE_3D
        self.smooth_enabled = smooth if smooth is not None else settings.ENABLE_SMOOTHING
        
        # 3D Smoother for world landmarks (reduces z jitter)
        self.smoother = WorldLandmarkSmoother(min_cutoff=1.2, beta=0.02) if smooth else None
        
        self.side_detector = CameraSideDetector(30) if exercise.camera == Camera.SIDE else None
        self.rules_adapted = False if exercise.camera == Camera.SIDE else True
        
        self._distance_rule_names = {
            r.name for r in exercise.validation_rules
            if isinstance(r, DistanceValidationRule)
        }
        self._distance_violation_in_current_rep = False
        self._distance_violation_results = {}

    # ------------------------------------------------------------------
    # Analysis: FULL 3D - pure logic, no I/O
    # ------------------------------------------------------------------
    def analyze(self, image_landmarks, world_landmarks=None, width: int = 1000, height: int = 1000, frame: int = 0, timestamp_ms: int = None) -> FrameResult:
        """
        Compute 3D angles, update counter, run validation in 3D.
        Backward compatible with old 2D signature: analyze(landmarks, width, height, frame)
        
        Args:
            image_landmarks: 2D landmarks for rendering (x,y normalized) - or old single landmarks
            world_landmarks: 3D world landmarks (x,y,z in meters) for analysis, or width in old API
            width, height: frame dimensions for 2D projection
            frame: frame number
            timestamp_ms: timestamp for smoother
        """
        # Backward compatibility: old signature analyze(landmarks, width, height, frame)
        if isinstance(world_landmarks, int):
            # Shift args: world_landmarks is actually width
            frame = height
            height = width
            width = world_landmarks
            world_landmarks = None  # No world in old API, will fallback to 2D
        
        # If world_landmarks is actually a landmark list but is None for image, handle
        if world_landmarks is None and image_landmarks is not None:
            try:
                if image_landmarks and hasattr(image_landmarks[0], 'z'):
                    world_landmarks = image_landmarks
            except (IndexError, AttributeError, TypeError):
                pass
        # Side detection still uses 2D visibility (most reliable)
        if self.side_detector and not self.rules_adapted:
            side = self.side_detector.process_frame(image_landmarks)
            if side:
                from ..utils.camera_side import adapt_rules
                self.exercise.counter_rules = adapt_rules(self.exercise.counter_rules, side)
                self.exercise.validation_rules = adapt_rules(self.exercise.validation_rules, side)
                self.counter = RepCounter(self.exercise.counter_rules)
                self.rules_adapted = True
            if not self.rules_adapted:
                return FrameResult(angles={}, states=self.counter.states, results=[], views=[], is_3d=self.use_3d)

        # Optional smoothing for world landmarks (critical for 3D stability)
        if self.smoother and world_landmarks is not None:
            world_landmarks = self.smoother.smooth(world_landmarks, timestamp_ms)

        angles = {}
        views = []

        # ---- 3D Rep Counting ----
        for rule in self.exercise.counter_rules:
            angle = None
            pts_2d = []
            
            # Primary: 3D angle from world landmarks
            if self.use_3d and world_landmarks is not None:
                pts_3d = get_points_3d(rule.joints, world_landmarks)
                if len(pts_3d) >= 3:
                    angle = calc_angle_3d(*pts_3d)
            
            # Fallback: 2D angle if 3D fails
            pts_2d = get_points(rule.joints, image_landmarks, width, height)
            if angle is None and len(pts_2d) >= 3:
                angle = calc_angle(*pts_2d)
            
            angles[rule.name] = angle
            
            # Vertex for drawing is ALWAYS 2D pixel (for screen)
            vertex = pts_2d[1] if len(pts_2d) >= 3 else (0, 0)
            views.append(ComputedAngle(name=rule.name, vertex=vertex, angle=angle, is_error=False, is_3d=self.use_3d))

        # ---- 3D Validation ----
        results = validate_all(
            self.exercise.validation_rules, 
            image_landmarks, 
            world_landmarks, 
            width, height, 
            states=self.counter.states,
            use_3d=self.use_3d
        )

        # Views for validation results (vertex from 2D for rendering)
        for res in results:
            pts = get_points(res.joints, image_landmarks, width, height)
            vertex = pts[1] if len(pts) >= 3 else (0, 0)
            views.append(
                ComputedAngle(name=res.rule_name, vertex=vertex, angle=res.angle, is_error=not res.passed, is_3d=res.is_3d)
            )

        # ---- Rep quality tracking ----
        # RepJudge collects failures and complete evaluations
        # Observe must be called every frame to collect violations for reporting
        # This collects ALL failures (ERROR, WARNING, INFO) for score calculation
        self.judge.observe(results, frame)

        # For GOOD/BAD classification, only ERROR should make BAD
        # WARNING/INFO only reduce score but rep remains GOOD (as per docs and desired behavior)
        # So we split violations: all for scoring, ERROR-only for counting as BAD
        all_violation_names = {r.rule_name for r in violations(results)}
        error_violation_names = {r.rule_name for r in results if not r.passed and r.severity == Severity.ERROR}
        
        # For distance tracking, use all violations (distance rules are typically ERROR anyway)
        violation_names_for_distance = all_violation_names
        
        # For counter BAD determination, use only ERROR (WARNING doesn't make BAD)
        violation_names_for_counter = error_violation_names
        
        prev_good  = self.counter.primary.good
        prev_count = self.counter.primary.count

        # Record already called inside observe() above - evaluations tracked

        if self._distance_rule_names & violation_names_for_distance:
            self._distance_violation_in_current_rep = True
            for r in results:
                if not r.passed and r.rule_name in self._distance_rule_names:
                    self._distance_violation_results[r.rule_name] = r

        self.counter.update(angles, violation_names_for_counter)

        if self.counter.primary.count > prev_count:
            if self._distance_violation_in_current_rep:
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
                    from ..exercises.validation import ValidationResult
                    self.judge.observe([
                        ValidationResult(
                            rule_name=self.exercise.counter_rules[0].name + "_too_fast",
                            message="Too fast — control the movement",
                            severity=Severity.WARNING,
                            passed=False,
                            angle=None,
                            is_3d=self.use_3d
                        )
                    ], frame)
                self.judge.finalize_rep(
                    self.counter.primary.count,
                    frame,
                    force_good=rep_was_good,
                )

        return FrameResult(
            angles=angles, states=self.counter.states, results=results, views=views, is_3d=self.use_3d
        )

    # ------------------------------------------------------------------
    # Rendering: ALWAYS 2D - draws on image
    # ------------------------------------------------------------------
    def _render(self, frame, result: FrameResult, image_landmarks, width: int, height: int):
        """Rendering is ALWAYS 2D - draws skeleton on frame."""
        bad = bool(violations(result.results))
        show = self.exercise.display

        if show.show_skeleton:
            drawn_joints = set()
            for rule in self.exercise.counter_rules:
                pts = get_points(rule.joints, image_landmarks, width, height)
                if len(pts) >= 3:
                    custom_color = None
                    if bad:
                        custom_color = self.colors.ERROR
                    elif hasattr(rule, 'min_rom_angle') and rule.min_rom_angle is not None:
                        state = self.counter.states.get(rule.name)
                        if state is not None:
                            if state.stage in (rule.up_stage,):
                                custom_color = None
                            elif state.reached_bottom:
                                custom_color = self.colors.HIGHLIGHT
                            else:
                                custom_color = self.colors.ERROR
                    draw_skeleton(frame, pts, self.colors, is_bad=bad, custom_color=custom_color)
                    drawn_joints.add(tuple(sorted(rule.joints)))

            if show.show_validation_skeleton:
                for rule in self.exercise.validation_rules:
                    if hasattr(rule, 'joints'):
                        joints_key = tuple(sorted(rule.joints))
                        if joints_key not in drawn_joints:
                            pts = get_points(rule.joints, image_landmarks, width, height)
                            if len(pts) >= 3:
                                draw_skeleton(frame, pts, self.colors, is_bad=bad)
                                drawn_joints.add(joints_key)

        if show.show_angle_arc:
            for rule in self.exercise.counter_rules:
                pts = get_points(rule.joints, image_landmarks, width, height)
                if len(pts) >= 3:
                    draw_angle_arc(frame, pts[0], pts[1], pts[2], self.colors, is_bad=bad)

        # Labels show 3D angles but positioned at 2D vertices
        draw_angle_labels(frame, result.views, self.colors, width, height)

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
            pts = get_points(seg.endpoints, image_landmarks, width, height)
            if len(pts) == 2:
                draw_segment_line(frame, pts[0], pts[1], self.colors, line_color)

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

    def _export_session(self, report: "SessionReport") -> None:
        from ..analytics.exporters import JsonSessionExporter

        if settings.EXPORT_FORMAT.lower() != "json":
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
    # Orchestration: video source + 3D detection + 2D render loop
    # ------------------------------------------------------------------
    def run(self, video_path: str | None = None):
        cap = open_capture(
            video_path=video_path or settings.VIDEO_PATH,
            use_webcam=settings.USE_WEBCAM,
            webcam_index=settings.WEBCAM_INDEX,
        )

        fps = 25
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

        print(f"=== AI Gym Trainer - {'3D' if self.use_3d else '2D'} MODE - {self.exercise.name} ===")
        print(f"3D Calculation: {'ENABLED' if self.use_3d else 'DISABLED (2D fallback)'}")
        print(f"Smoothing: {'ENABLED' if self.smooth_enabled and self.use_3d else 'DISABLED'}")
        print(f"Rendering: 2D (always)")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            timestamp = int((frame_id / fps) * 1000)

            detection = pose_service.detect(frame, timestamp)

            if detection and detection.pose_landmarks:
                # 3D analysis + 2D rendering
                frame_result = self.analyze(
                    detection.pose_landmarks, 
                    detection.world_landmarks,
                    w, h, frame_id, timestamp
                )
                self._render(frame, frame_result, detection.pose_landmarks, w, h)

            if writer:
                writer.write(frame)

            # Display handling - supports headless (Ubuntu server, WSL, Docker)
            # If running on machine without GUI, skip imshow gracefully
            try:
                display_frame = fit_to_screen(frame, max_width=self.display_width)
                # Check if we can actually show window
                if hasattr(cv2, 'imshow'):
                    cv2.imshow(f"AI Gym Trainer 3D - {self.exercise.name}", display_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        print("Stopped by user (q)")
                        break
                else:
                    # Headless opencv - just print progress
                    if frame_id % 30 == 0:
                        print(f"Processing frame {frame_id} | Reps: {self.judge.total_reps} | Angle: {self.counter.primary.angle}")
            except cv2.error as e:
                # Headless mode - opencv_python_headless doesn't support imshow
                # Continue processing without display, video will still be saved if SAVE_OUTPUT=true
                if "not implemented" in str(e).lower() or "gtk" in str(e).lower() or "cocoa" in str(e).lower():
                    if frame_id == 0:
                        print("⚠️  Headless mode detected (no display available).")
                        print("   Processing without preview window...")
                        print("   - Video will be processed and report exported")
                        print("   - If SAVE_OUTPUT=true, annotated video saved to output/videos/")
                        print("   - Press Ctrl+C to stop")
                    if frame_id % 60 == 0:
                        primary = self.counter.primary
                        print(f"Frame {frame_id} | Reps: {self.judge.total_reps} (Good:{self.judge.good_reps} Bad:{self.judge.bad_reps}) | Stage: {primary.stage} | Angle: {primary.angle}")
                else:
                    raise

            frame_id += 1

        elapsed = time.perf_counter() - start_time
        frames_processed = frame_id
        if settings.USE_WEBCAM:
            input_source = f"Webcam (index {settings.WEBCAM_INDEX}) {'3D' if self.use_3d else '2D'}"
        else:
            src = video_path or settings.VIDEO_PATH
            input_source = str(src) if src is not None else "none"

        print(self.judge.session_report(
            exercise_name=self.exercise.name,
            input_source=input_source,
            total_frames=frames_processed,
            elapsed_seconds=elapsed,
        ))

        if settings.EXPORT_SESSION:
            from ..analytics.analyzer import SessionAnalyzer

            report = SessionAnalyzer().build_report(
                self.judge.history,
                exercise=self.exercise,
                fps=settings.ANALYTICS_FPS,
                total_duration=elapsed,
            )
            self._export_session(report)

        print(f"\n{'3D' if self.use_3d else '2D'} Metrics: {self.judge.total_reps} total, {self.judge.good_reps} good, {self.judge.bad_reps} bad")
        print(self.judge.history)
        cap.release()
        if writer:
            writer.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass  # Headless - ignore
