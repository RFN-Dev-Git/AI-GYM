"""AI Gym Trainer — entry point.

Usage
-----
  python -m src.main                               # uses .env defaults
  python -m src.main deadlift                      # deadlift, video from .env
  python -m src.main deadlift Deadlift3.mp4        # bare name: assets/videos/
  python -m src.main cable_chest_fly /path/Chest.mp4   # explicit path
  python -m src.main hack_squat leg.mp4            # hack squat + video
  python -m src.main hack_squat c                  # webcam ('s' saves output)

Video arguments are resolved in order: as given (relative to the launch
directory), inside ``assets/videos/``, then by bare file name inside
``assets/videos/``. A missing video or pose model aborts with an actionable
message (paths tried, directory contents, how to fix) — no traceback.

Available exercises
-------------------
  deadlift  cable_chest_fly  squat  pushup
  biceps_curl  lat_pulldown  leg_press  shoulder_press  hack_squat
"""

import sys
from pathlib import Path

from .config import settings
from .core.colors import Colors
from .exercises.registry import registry
from .services.gym_engine import GymEngine
from .services.video_source import (
    VideoSourceError,
    diagnose_model_error,
    diagnose_video_error,
    resolve_video_path,
)

DEFAULT_EXERCISE = "cable_chest_fly"


def main():
    args = sys.argv[1:]

    exercise_key = args[0].lower() if len(args) >= 1 else None

    # Parse CLI flags: 'c' for webcam, 's' for saving output
    lower_args = [arg.lower() for arg in args[1:]]
    save_flag = "s" in lower_args
    settings.SAVE_OUTPUT = save_flag

    use_webcam_flag = "c" in lower_args
    if use_webcam_flag:
        settings.USE_WEBCAM = True
        video_path = None
    else:
        remaining_args = [arg for arg in args[1:] if arg.lower() not in ("s", "c")]
        video_path = remaining_args[0] if remaining_args else None

    # The CLI simply asks the registry for an exercise — it knows nothing about
    # which exercises exist. GymEngine stays completely unaware of the registry.
    if exercise_key and not registry.exists(exercise_key):
        print(f"Unknown exercise '{exercise_key}'.")
        print(f"Available: {', '.join(registry.list())}")
        sys.exit(1)

    exercise = (
        registry.get(exercise_key) if exercise_key else registry.get(DEFAULT_EXERCISE)
    )

    # ── Preflight: fail fast with an actionable message, not a traceback ────
    # (Resolution shared with the engine and the live server: video_source.)
    if not settings.USE_WEBCAM:
        source_arg = video_path or settings.VIDEO_PATH
        resolved = resolve_video_path(source_arg) if source_arg else None
        if resolved is None:
            print(diagnose_video_error(source_arg))
            sys.exit(2)
        video_path = str(resolved)

    if not Path(settings.MODEL_PATH).is_file():
        print(diagnose_model_error(settings.MODEL_PATH))
        sys.exit(2)

    try:
        GymEngine(
            exercise,
            colors=Colors(),
            display_width=settings.DISPLAY_MAX_WIDTH,
        ).run(video_path=video_path)
    except VideoSourceError as exc:
        # File existed at preflight but could not be opened (e.g. undecodable
        # codec) — same clean, actionable output, no traceback.
        print(exc)
        sys.exit(2)


if __name__ == "__main__":
    main()
