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

from src.config import settings
from src.core.colors import Colors
from src.exercises import (
    BicepsCurlExercise, CableChestFlyExercise, DeadliftExercise,
    LatPulldownExercise, LegPressExercise, PushUpExercise,
    ShoulderPressExercise, SquatExercise, HackSquatExercise,  
)
from src.services.gym_engine import GymEngine

EXERCISES = {
    "deadlift":        DeadliftExercise,
    "cable_chest_fly": CableChestFlyExercise,
    "squat":           SquatExercise,
    "pushup":          PushUpExercise,
    "biceps_curl":     BicepsCurlExercise,
    "lat_pulldown":    LatPulldownExercise,
    "leg_press":       LegPressExercise,
    "hack_squat":      HackSquatExercise,  
    "shoulder_press":  ShoulderPressExercise,
}


def main():
    args = sys.argv[1:]

    exercise_key = args[0].lower() if len(args) >= 1 else None
    video_path   = args[1]         if len(args) >= 2 else None

    if exercise_key and exercise_key not in EXERCISES:
        print(f"Unknown exercise '{exercise_key}'.")
        print(f"Available: {', '.join(EXERCISES)}")
        sys.exit(1)

    ExerciseClass = EXERCISES[exercise_key] if exercise_key else CableChestFlyExercise

    GymEngine(
        ExerciseClass(),
        colors=Colors(),
        display_width=settings.DISPLAY_MAX_WIDTH,
    ).run(video_path=video_path)


if __name__ == "__main__":
    main()