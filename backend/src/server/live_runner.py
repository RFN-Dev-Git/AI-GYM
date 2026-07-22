"""Live coaching session runner — streams an engine session over a queue.

A single background thread drives the *existing* pipeline exactly the way
``GymEngine.run`` does (PoseService -> GymEngine.analyze -> overlay render),
but instead of ``cv2.imshow`` it publishes events for the WebSocket layer:

* ``bytes``  — one JPEG per processed frame (binary WS message)
* ``dict``   — JSON state updates: ``{"type": "state" | "end" | "error"}``

Nothing here reimplements counting, validation, or rendering — the engine's
own methods produce everything; this class only pumps and packages.
"""

import queue
import threading
import time
from typing import Any, Dict, List, Optional

import cv2

from ..config import RENDERED_DIR, settings
from ..exercises.exercise import Camera
from ..exercises.rules import Severity
from ..exercises.validation import violations
from ..services.gym_engine import GymEngine
from ..services.video_source import VideoSourceError, open_capture
from ..services.pose_service import PoseService
from ..utils.render import fit_to_screen

# Live state is throttled: frames stream at capture rate, metrics at ~15 Hz.
_STATE_EVERY_N_FRAMES = 2
_STREAM_MAX_WIDTH = 960
_JPEG_QUALITY = 70

_DEFAULT_WEIGHTS = {"error": 50.0, "warning": 20.0, "info": 10.0}


class LiveSession(threading.Thread):
    """One live workout: capture + analyze + render + publish until stopped.

    Args:
        exercise:  Registry key of the exercise to run.
        source:    ``"webcam"`` (index from settings) or ``"video"``
                   (``video_path`` / settings.VIDEO_PATH).
        events:    Thread-safe queue the WS handler drains (bytes | dict).
        video_path: Explicit video override (only used when source="video").
    """

    def __init__(self, exercise: str, source: str, events: "queue.Queue", video_path: Optional[str] = None) -> None:
        super().__init__(daemon=True)
        self.exercise_key = exercise
        self.source = source
        self.video_path = video_path
        self.events = events
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------
    def _publish(self, event) -> None:
        """Drop-oldest publish: a slow consumer never stalls the workout."""
        try:
            self.events.put_nowait(event)
        except queue.Full:
            try:
                self.events.get_nowait()
            except queue.Empty:
                pass
            try:
                self.events.put_nowait(event)
            except queue.Full:
                pass

    @staticmethod
    def _live_score(results, weights) -> Optional[float]:
        """Instant form score from the CURRENT frame's failing rules."""
        penalty = sum(weights.get(r.severity, weights.get(str(r.severity), 0.0))
                      for r in results if not r.passed)
        return max(0.0, 100.0 - penalty)

    def _state(self, engine: GymEngine, results, elapsed: float, fps: float) -> Dict[str, Any]:
        primary = engine.counter.primary
        last = engine.judge.last_rep
        rule = engine.exercise.counter_rules[0] if engine.exercise.counter_rules else None
        stage_map = {
            "up": getattr(rule, "up_stage", "up"),
            "down": getattr(rule, "down_stage", "down"),
        }
        failing = violations(results)
        return {
            "type": "state",
            "exercise": engine.exercise.name,
            "elapsed": round(elapsed, 1),
            "fps": round(fps, 1),
            "reps": engine.counter.primary.count,
            "good": engine.judge.good_reps,
            "bad": engine.judge.bad_reps,
            "stage": stage_map.get(primary.stage, primary.stage),
            "angle": round(primary.angle, 1),
            "last_rep": ("good" if last.good else "bad") if last else None,
            "live_score": self._live_score(results, _DEFAULT_WEIGHTS),
            "side": (engine.side_detector.detected_side if engine.side_detector else "both"),
            "adapting": not engine.rules_adapted,
            "feedback": [r.message for r in failing][:3],
            "rules": [
                {
                    "name": r.rule_name,
                    "passed": r.passed,
                    "severity": str(getattr(r.severity, "value", r.severity)),
                    "message": r.message,
                    "value": round(r.angle, 1) if r.angle is not None else None,
                }
                for r in results
            ],
        }

    # ------------------------------------------------------------------
    # Main loop (mirrors GymEngine.run's composition, output = queue)
    # ------------------------------------------------------------------
    def run(self) -> None:
        from ..exercises.registry import registry

        try:
            engine = GymEngine(registry.get(self.exercise_key))
        except Exception as exc:  # unknown exercise
            self._publish({"type": "error", "message": f"Unknown exercise: {exc}"})
            return

        try:
            cap = open_capture(
                video_path=self.video_path
                or (str(settings.VIDEO_PATH) if settings.VIDEO_PATH else None),
                use_webcam=self.source == "webcam",
                webcam_index=settings.WEBCAM_INDEX,
            )
        except VideoSourceError as exc:
            self._publish({"type": "error", "message": str(exc)})
            return

        # Optional rendered-video output (mirrors GymEngine.run: mp4v, 25 fps):
        # annotated frames are written per-session under output/videos/ so the
        # web app can offer the user a download after the workout. Best-effort:
        # a writer failure never kills the workout or the report export.
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in engine.exercise.name)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        writer = None
        rendered_name: Optional[str] = None
        rendered_error: Optional[str] = None
        if settings.SAVE_OUTPUT:
            try:
                RENDERED_DIR.mkdir(parents=True, exist_ok=True)
                rendered_name = f"{safe_name}_{stamp}.mp4"
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(RENDERED_DIR / rendered_name), fourcc, 25.0, (width, height))
                if not writer.isOpened():
                    writer.release()
                    writer, rendered_name = None, None
                    rendered_error = "OpenCV could not create the output video"
            except Exception as exc:
                writer, rendered_name = None, None
                rendered_error = str(exc)

        try:
            pose_service = PoseService(settings.MODEL_PATH)
        except Exception as exc:
            cap.release()
            if writer is not None:
                writer.release()
                (RENDERED_DIR / rendered_name).unlink(missing_ok=True)
            self._publish({"type": "error", "message": f"Pose model unavailable: {exc}"})
            return

        fps = 25.0
        results: List = []
        frame_id, frames_tick = 0, 0
        start = time.perf_counter()
        last_fps_check = start
        live_fps = 0.0

        while not self._stop.is_set():
            ok, frame = cap.read()
            if not ok:
                break
            h, w = frame.shape[:2]
            timestamp = int((frame_id / fps) * 1000)
            detected = pose_service.detect(frame, timestamp)
            frame_result = None
            if detected and detected.pose_landmarks:
                lm = detected.pose_landmarks[0]
                frame_result = engine.analyze(lm, w, h, frame_id)
                results = frame_result.results
                engine._render(frame, frame_result, lm, w, h)

            if writer is not None:
                writer.write(frame)
            stream = fit_to_screen(frame, max_width=_STREAM_MAX_WIDTH)
            ok_jpg, jpg = cv2.imencode(
                ".jpg", stream, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY]
            )
            if ok_jpg:
                self._publish(jpg.tobytes())
            if frame_result is not None and frame_id % _STATE_EVERY_N_FRAMES == 0:
                elapsed = time.perf_counter() - start
                self._publish(self._state(engine, results, elapsed, live_fps))
            frame_id += 1
            frames_tick += 1
            now = time.perf_counter()
            if now - last_fps_check >= 1.0:
                live_fps = frames_tick / (now - last_fps_check)
                frames_tick, last_fps_check = 0, now

        cap.release()
        if writer is not None:
            writer.release()

        # ── Finalize & export (always: the app depends on the report) ──
        elapsed = time.perf_counter() - start
        ended: Dict[str, Any] = {"type": "end", "reps": engine.judge.total_reps}
        if rendered_name is not None:
            ended["rendered_video"] = rendered_name
        if rendered_error is not None:
            ended["rendered_error"] = rendered_error
        try:
            from ..analytics.analyzer import SessionAnalyzer
            from ..analytics.exporters import JsonSessionExporter

            report = SessionAnalyzer().build_report(
                engine.judge.history,
                exercise=engine.exercise,
                fps=settings.ANALYTICS_FPS,
                total_duration=elapsed,
            )
            settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            target = settings.EXPORT_DIR / f"{safe_name}_{stamp}"
            out = JsonSessionExporter().export(report, target)
            ended["session_id"] = report.session.id if report.session else out.stem
        except Exception as exc:
            ended["export_error"] = str(exc)
        self._publish(ended)
