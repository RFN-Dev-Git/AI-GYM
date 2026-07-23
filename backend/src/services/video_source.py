"""Video-source resolution & diagnostics for engine runs.

This module is the single source of truth for *how* a run locates its input.
It is shared by the desktop CLI (``src.main``), the engine orchestrator
(:class:`~src.services.gym_engine.GymEngine`) and the WebSocket live runner
(``src.server.live_runner``) so that all three report **identical, actionable
errors** instead of a bare ``Cannot open video source`` traceback.

Path resolution order for a user-supplied video argument
--------------------------------------------------------
1. **as given** — an absolute path, or a path relative to the current working
   directory (preserves the historic "path relative to where you launched the
   CLI" behaviour);
2. **inside the project videos directory** — ``assets/videos/<arg>`` (covers
   ``videos/x.mp4``-style arguments);
3. **by file name** — ``assets/videos/<name>`` (covers bare names such as
   ``hackw.mp4`` and stale ``assets/videos/x.mp4``-style arguments).

The first existing candidate wins. If none exists, callers raise
:class:`VideoSourceError` (or print :func:`diagnose_video_error` directly) with
every tried path plus a live overview of what *is* inside ``assets/videos/``.

The module performs **no OpenCV import at module level** (only inside
:func:`open_capture`), so the pure-path helpers stay importable in environments
without OpenCV — e.g. the unit-test sandbox.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Union

from ..config.app_settings import VIDEOS_DIR

PathLike = Union[str, Path]

# Candidate source of the BlazePose landmarker model, surfaced to the user
# when MODEL_PATH points at a file that does not exist.
MODEL_ZOO_URL = (
    "https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models"
)


class VideoSourceError(RuntimeError):
    """Raised when no usable video source (file or webcam) can be opened.

    Subclasses :class:`RuntimeError` for backward compatibility: callers that
    caught the engine's historical ``RuntimeError("Cannot open video source")``
    keep working. The string form of the exception is a complete, human
    actionable diagnosis (paths tried, directory contents, how to fix).
    """


# ---------------------------------------------------------------------------
# Path resolution (pure — no OpenCV required)
# ---------------------------------------------------------------------------
def _resolution_candidates(arg: PathLike, videos_dir: Path) -> List[Path]:
    """Return the ordered, de-duplicated candidate paths for ``arg``."""
    p = Path(arg)
    candidates: List[Path] = []

    def add(path: Path) -> None:
        if path not in candidates:
            candidates.append(path)

    if p.is_absolute():
        add(p)
    else:
        add(Path.cwd() / p)          # 1. as given, relative to the launch CWD
        add(videos_dir / p)          # 2. inside the project videos directory
        if p.name != str(p):         # 3. by bare file name
            add(videos_dir / p.name)
    return candidates


def resolve_video_path(arg: PathLike, videos_dir: Path = VIDEOS_DIR) -> Optional[Path]:
    """Resolve a user-supplied video argument to an existing file.

    Returns the first existing candidate per the documented resolution order,
    or ``None`` when no candidate exists on disk.
    """
    for candidate in _resolution_candidates(arg, videos_dir):
        if candidate.is_file():
            return candidate
    return None


def _videos_dir_overview(videos_dir: Path, limit: int = 10) -> str:
    """Human-readable summary of the project videos directory's contents."""
    if not videos_dir.is_dir():
        return (
            f"The project videos directory does not exist: {videos_dir}\n"
            f"Create it (mkdir -p {videos_dir}) and drop your clips there."
        )
    names = sorted(p.name for p in videos_dir.iterdir() if p.is_file())
    if not names:
        return f"The project videos directory ({videos_dir}) exists but is empty."
    shown = "\n".join(f"  {n}" for n in names[:limit])
    extra = f"\n  … and {len(names) - limit} more" if len(names) > limit else ""
    return f"The project videos directory ({videos_dir}) currently contains:\n{shown}{extra}"


def diagnose_video_error(arg: Optional[PathLike], videos_dir: Path = VIDEOS_DIR) -> str:
    """Build the full actionable message for an unresolvable/missing source."""
    if arg is None or str(arg).strip() == "":
        return (
            "No video source configured.\n\n"
            "Provide one of:\n"
            f"  • a video file:  python -m src.main <exercise> <file>\n"
            f"                   (bare names are looked up in {videos_dir})\n"
            "  • VIDEO_PATH:    set it in backend/.env\n"
            "  • the webcam:    USE_WEBCAM=true in backend/.env,\n"
            "                   or the 'c' flag: python -m src.main <exercise> c"
        )

    tried = "\n".join(f"  - {c}" for c in _resolution_candidates(arg, videos_dir))
    return (
        f"Video file not found: {arg}\n\n"
        f"Tried:\n{tried}\n\n"
        f"{_videos_dir_overview(videos_dir)}\n\n"
        "Fix it by either:\n"
        f"  • placing the file at {videos_dir / Path(arg).name}\n"
        "  • passing a path that exists:  python -m src.main <exercise> <path-to-video>\n"
        "  • setting VIDEO_PATH in backend/.env\n"
        "  • using the webcam instead:    python -m src.main <exercise> c"
    )


def diagnose_model_error(model_path: PathLike) -> str:
    """Build the actionable message for a missing pose-model file."""
    return (
        f"Pose model file not found: {model_path}\n\n"
        "Download a BlazePose pose-landmarker .task model and place it at that "
        f"path — see the MediaPipe model zoo:\n  {MODEL_ZOO_URL}\n"
        "then point MODEL_PATH at it (backend/.env)."
    )


def _diagnose_undecodable(path: Path) -> str:
    """Message for a file that exists but OpenCV fails to open."""
    size = path.stat().st_size
    human = f"{size / 1e6:.1f} MB" if size >= 1e6 else f"{size / 1e3:.1f} KB"
    return (
        f"Video file exists but OpenCV could not decode it: {path} ({human})\n\n"
        "The file is corrupted or uses a codec this OpenCV build cannot read "
        "(e.g. HEVC/AV1 in some builds). Re-encode to H.264:\n"
        f"  ffmpeg -i {path.name} -c:v libx264 -pix_fmt yuv420p fixed_{path.name}"
    )


def _diagnose_webcam(index: int) -> str:
    """Message for an unopenable webcam."""
    return (
        f"Cannot open webcam at index {index}.\n\n"
        "Check that a camera is connected, is not held by another application, "
        "and that the OS grants camera permission. Adjust WEBCAM_INDEX in "
        "backend/.env, or use a video file instead (USE_WEBCAM=false + "
        "VIDEO_PATH / CLI argument)."
    )


# ---------------------------------------------------------------------------
# Source acquisition (OpenCV imported lazily)
# ---------------------------------------------------------------------------
def open_capture(
    *,
    video_path: Optional[PathLike] = None,
    use_webcam: bool = False,
    webcam_index: int = 0,
    frame_size: Optional[Tuple[int, int]] = (1280, 720),
    videos_dir: Path = VIDEOS_DIR,
):
    """Open an already-*opened* ``cv2.VideoCapture`` for a run.

    ``video_path`` arguments are resolved via :func:`resolve_video_path`, so
    bare file names are looked up in the project videos directory. On any
    failure a :class:`VideoSourceError` carrying the full diagnosis is raised
    instead of returning a silently-closed capture.

    ``cv2`` is imported lazily so the pure-path helpers above remain usable
    without OpenCV installed.
    """
    import cv2

    if use_webcam:
        cap = cv2.VideoCapture(webcam_index)
        if frame_size is not None:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_size[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_size[1])
        if not cap.isOpened():
            cap.release()
            raise VideoSourceError(_diagnose_webcam(webcam_index))
        return cap

    if video_path is None or str(video_path).strip() == "":
        raise VideoSourceError(diagnose_video_error(None, videos_dir))

    resolved = resolve_video_path(video_path, videos_dir)
    if resolved is None:
        raise VideoSourceError(diagnose_video_error(video_path, videos_dir))

    cap = cv2.VideoCapture(str(resolved))
    if not cap.isOpened():
        cap.release()
        raise VideoSourceError(_diagnose_undecodable(resolved))
    return cap
