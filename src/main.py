"""AI Gym Trainer — entry point.

Usage
-----
  python -m src.main                               # uses .env defaults
  python -m src.main deadlift                      # deadlift, video from .env
  python -m src.main deadlift Deadlift3.mp4        # deadlift + video override
  python -m src.main cable_chest_fly Chest.mp4     # cable fly + video
  python -m src.main hack_squat leg.mp4            # hack squat + video

Available exercises
-------------------
  deadlift  cable_chest_fly  squat  pushup
  biceps_curl  lat_pulldown  leg_press  shoulder_press  hack_squat
"""

import sys

from .config import settings
from .core.colors import Colors
from .exercises import registry
from .services.gym_engine import GymEngine

DEFAULT_EXERCISE = "cable_chest_fly"


def main():
    args = sys.argv[1:]

    exercise_key = args[0].lower() if len(args) >= 1 else None
    video_path   = args[1]         if len(args) >= 2 else None

    # The CLI simply asks the registry for an exercise — it knows nothing about
    # which exercises exist. GymEngine stays completely unaware of the registry.
    if exercise_key and not registry.exists(exercise_key):
        print(f"Unknown exercise '{exercise_key}'.")
        print(f"Available: {', '.join(registry.list())}")
        sys.exit(1)

    exercise = (
        registry.get(exercise_key) if exercise_key else registry.get(DEFAULT_EXERCISE)
    )

    GymEngine(
        exercise,
        colors=Colors(),
        display_width=settings.DISPLAY_MAX_WIDTH,
    ).run(video_path=video_path)


if __name__ == "__main__":
    main()