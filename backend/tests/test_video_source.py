"""Video-source resolution & diagnostics verification.

Covers ``src/services/video_source.py`` — the shared source-acquisition layer
used by the CLI (``src.main``), ``GymEngine.run`` and the WebSocket live
runner:

  1. Resolution order: as-given (cwd) → videos_dir/<arg> → videos_dir/<name>.
  2. Missing inputs yield ``None`` from resolve_video_path, not exceptions.
  3. ``VideoSourceError`` is a ``RuntimeError`` (backward-compatible catching).
  4. Diagnosis messages name every tried path, describe the real contents of
     the videos directory, and suggest actionable fixes (file/.env/webcam).
  5. ``open_capture`` raises actionable errors for: no source, missing file,
     undecodable file, unopenable webcam — and returns an *opened* capture,
     applying the frame size, on success.

Run from backend/:  python tests/test_video_source.py
"""

import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/

os.environ.setdefault("MODEL_PATH", "assets/models/pose_landmarker_lite.task")

# ── Stub mediapipe (importing src.services pulls in gym_engine → pose_service)
_mp = types.ModuleType("mediapipe")
_mp_tasks = types.ModuleType("mediapipe.tasks")
_mp_python = types.ModuleType("mediapipe.tasks.python")
_mp_python.vision = types.ModuleType("mediapipe.tasks.python.vision")
_mp.tasks = _mp_tasks
_mp_tasks.python = _mp_python
sys.modules.update({
    "mediapipe": _mp,
    "mediapipe.tasks": _mp_tasks,
    "mediapipe.tasks.python": _mp_python,
    "mediapipe.tasks.python.vision": _mp_python.vision,
})

import shutil
import tempfile

from src.services.video_source import (
    VideoSourceError,
    diagnose_model_error,
    diagnose_video_error,
    open_capture,
    resolve_video_path,
)

try:
    import cv2
except ImportError:  # pragma: no cover - OpenCV optional for part of the suite
    cv2 = None


class FakeCap:
    """Minimal cv2.VideoCapture stand-in for the webcam tests."""
    instances = []

    def __init__(self, opened):
        self._opened = opened
        self.released = False
        self.sets = []
        FakeCap.instances.append(self)

    def set(self, prop, value):
        self.sets.append((prop, value))

    def isOpened(self):
        return self._opened

    def release(self):
        self.released = True


def _fake_cv2(cap: FakeCap) -> types.ModuleType:
    mod = types.ModuleType("cv2")
    mod.VideoCapture = lambda *_a, **_k: cap
    mod.CAP_PROP_FRAME_WIDTH = 3
    mod.CAP_PROP_FRAME_HEIGHT = 4
    return mod


def expect_raises(exc_type, fn, needle=None):
    try:
        fn()
    except exc_type as exc:
        if needle is not None:
            assert needle.lower() in str(exc).lower(), f"missing {needle!r} in:\n{exc}"
        return exc
    raise AssertionError(f"expected {exc_type.__name__}")


# --------------------------------------------------------------------------
# 1. Resolution order
# --------------------------------------------------------------------------
def test_resolution_order(tmp: Path):
    cwd_dir = tmp / "cwd"
    videos = tmp / "videos"
    cwd_file = cwd_dir / "clip.mp4"
    vid_file = videos / "clip.mp4"
    cwd_dir.mkdir(parents=True)
    videos.mkdir()
    cwd_file.write_bytes(b"cwd")
    vid_file.write_bytes(b"videos")

    old_cwd = os.getcwd()
    os.chdir(cwd_dir)
    try:
        # absolute path: returned verbatim
        assert resolve_video_path(str(vid_file), videos) == vid_file
        # as-given (cwd) beats the videos directory
        assert resolve_video_path("clip.mp4", videos) == cwd_file
        # videos_dir/<arg> step: argument with a directory part
        nested = videos / "sessions"
        nested.mkdir()
        (nested / "s.mp4").write_bytes(b"x")
        assert resolve_video_path("sessions/s.mp4", videos) == nested / "s.mp4"
    finally:
        os.chdir(old_cwd)

    # name fallback: stale 'assets/videos/x.mp4'-style argument
    stale_arg = "assets/videos/clip.mp4"
    # (videos/assets/videos/clip.mp4 must NOT exist for the name step to win)
    assert resolve_video_path(stale_arg, videos) == vid_file

    # nothing exists → None (and an absolute miss does not scan videos_dir)
    assert resolve_video_path("nope.mp4", videos) is None
    assert resolve_video_path(str(tmp / "abs" / "nope.mp4"), videos) is None
    print("1. resolution order: OK")


# --------------------------------------------------------------------------
# 2. Error type compatibility
# --------------------------------------------------------------------------
def test_error_type():
    assert issubclass(VideoSourceError, RuntimeError)
    print("2. VideoSourceError is a RuntimeError: OK")


# --------------------------------------------------------------------------
# 3. Diagnosis messages
# --------------------------------------------------------------------------
def test_diagnoses(tmp: Path):
    videos = tmp / "videos"

    # no source configured
    msg = diagnose_video_error(None, videos)
    assert "No video source configured" in msg
    for needle in ("VIDEO_PATH", "USE_WEBCAM", "src.main <exercise> c"):
        assert needle in msg, needle

    # missing file → tried paths + directory overview + fixes
    videos.mkdir(parents=True)
    (videos / "demo.mp4").write_bytes(b"x")
    arg = tmp / "missing.mp4"
    msg = diagnose_video_error(str(arg), videos)
    assert f"Video file not found: {arg}" in msg
    assert f"  - {arg}" in msg                      # tried path listed
    assert "demo.mp4" in msg                         # real contents shown
    assert str(videos / arg.name) in msg             # 'place the file at' fix
    for needle in ("VIDEO_PATH", "backend/.env", "webcam"):
        assert needle in msg, needle

    # missing directory overview
    gone = tmp / "gone"
    msg = diagnose_video_error("x.mp4", gone)
    assert f"does not exist: {gone}" in msg
    assert "mkdir" in msg

    # relative argument also lists the videos_dir/<name> candidate
    vids2 = tmp / "vids2"
    msg = diagnose_video_error("assets/videos/x.mp4", vids2)
    assert str(vids2 / "x.mp4") in msg

    # model error
    msg = diagnose_model_error(tmp / "models" / "pose.task")
    assert f"Pose model file not found: {tmp / 'models' / 'pose.task'}" in msg
    assert "MODEL_PATH" in msg and "http" in msg
    print("3. diagnosis messages: OK")


# --------------------------------------------------------------------------
# 4. open_capture failure modes (+ successful acquisition when OpenCV exists)
# --------------------------------------------------------------------------
def test_open_capture(tmp: Path):
    videos = tmp / "videos"
    videos.mkdir(parents=True)

    # no source at all
    expect_raises(VideoSourceError, lambda: open_capture(), "No video source")
    expect_raises(
        VideoSourceError,
        lambda: open_capture(video_path=""),
        "No video source",
    )
    # missing file
    expect_raises(
        VideoSourceError,
        lambda: open_capture(video_path="ghost.mp4", videos_dir=videos),
        "not found",
    )

    if cv2 is None:
        print("4. open_capture failures: OK  (cv2 absent — success paths skipped)")
        test_webcam(FakeCap(False))
        return

    # undecodable file: exists, but OpenCV can't open it
    junk = videos / "broken.mp4"
    junk.write_bytes(os.urandom(4096))
    expect_raises(
        VideoSourceError,
        lambda: open_capture(video_path=str(junk)),
        "could not decode",
    )

    # successful acquisition: bare name resolved via videos_dir, capture opened
    clip = _write_clip(videos / "clip.mp4")
    if clip is None:
        print("4. open_capture failures: OK  (mp4v writer unavailable — e2e skipped)")
    else:
        cap = open_capture(video_path="clip.mp4", videos_dir=videos)
        assert cap.isOpened()
        ok, frame = cap.read()
        assert ok and frame is not None and frame.shape[2] == 3
        cap.release()
        print("4. open_capture: failures + real-clip acquisition: OK")

    test_webcam(FakeCap(False))


def _write_clip(path: Path):
    """Write a tiny readable mp4v clip; None when the codec is unavailable."""
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"mp4v"), 25.0, (64, 48)
    )
    if not writer.isOpened():
        writer.release()
        return None
    import numpy as np

    frame = np.zeros((48, 64, 3), dtype="uint8")
    for _ in range(3):
        writer.write(frame)
    writer.release()
    return path


# --------------------------------------------------------------------------
# 5. Webcam diagnostics via a stubbed cv2 (no hardware required)
# --------------------------------------------------------------------------
def test_webcam(cap: FakeCap):
    real = sys.modules.get("cv2")
    sys.modules["cv2"] = _fake_cv2(cap)
    try:
        expect_raises(
            VideoSourceError,
            lambda: open_capture(use_webcam=True, webcam_index=3),
            "webcam at index 3",
        )
        # frame size applied before the open check, capture released after
        assert len(cap.sets) == 2
        assert cap.released is True
    finally:
        if real is not None:
            sys.modules["cv2"] = real
        else:
            del sys.modules["cv2"]
    print("5. webcam diagnostics (stubbed cv2): OK")


def main():
    tmp_root = Path(tempfile.mkdtemp(prefix="ai_gym_video_src_"))
    try:
        test_resolution_order(tmp_root / "t1")
        test_error_type()
        test_diagnoses(tmp_root / "t3")
        test_open_capture(tmp_root / "t4")
        # success-path webcam: stubbed cv2 reports an opened camera
        cap = FakeCap(True)
        real = sys.modules.get("cv2")
        sys.modules["cv2"] = _fake_cv2(cap)
        try:
            opened = open_capture(use_webcam=True, webcam_index=0, frame_size=None)
            assert opened is cap and cap.sets == []  # frame_size=None → no set()
        finally:
            if real is not None:
                sys.modules["cv2"] = real
            else:
                del sys.modules["cv2"]
        print("6. webcam success path (stubbed cv2): OK")
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    print("\nAll video_source tests passed ✔")


if __name__ == "__main__":
    main()
