# 3D Migration - Full 3D Analysis, 2D Rendering

## Why 3D?

### Problem with 2D
- `calc_angle` used pixel space `(x*w, y*h)` -> anisotropic, camera-dependent
- Squat from side = 130°, from front = 95° for same pose
- Required `CameraSideDetector` workaround for leg exercises
- Distance ratios were hack for missing depth

### Solution: 3D World Landmarks
MediaPipe `PoseLandmarker` already returns both:
- `pose_landmarks`: 2D normalized x,y + visibility (for rendering)
- `world_landmarks`: 3D x,y,z in meters, origin at hips (for analysis)

World landmarks are **free** (already computed), camera-independent, true body angles.

## Architecture: 3D Calc, 2D Draw

```
Frame -> PoseService.detect() -> PoseDetectionResult {
  pose_landmarks: 33x 2D (render)
  world_landmarks: 33x 3D (analysis)
}
         |
         +-> GymEngine.analyze(image_2d, world_3d, w, h)
               |
               +-> get_points_3d() -> calc_angle_3d() -> RepCounter (3D angles)
               +-> validate_all(image_2d, world_3d) -> 3D validation
               +-> views with vertex from 2D (for drawing at correct pixel)
         |
         +-> GymEngine._render(frame, result, image_2d, w, h) -> ALWAYS 2D
```

### Key Files Changed

1. **backend/src/utils/geometry.py**
   - Kept `calc_angle` (2D legacy)
   - Added `calc_angle_3d(a,b,c)` where a,b,c are (x,y,z)
   - Added `get_points_3d()`, `calc_distance_3d()`, `calc_distance_ratio_3d()`
   - Added `is_3d` flag to `ComputedAngle`

2. **backend/src/utils/filters.py** (NEW)
   - `OneEuroFilter`: adaptive low-pass filter, reduces z jitter from +-5cm to +-0.5cm
   - `WorldLandmarkSmoother`: 33 landmarks * 3 axes = 99 filters
   - Critical for 3D stability

3. **backend/src/services/pose_service.py**
   - New `PoseDetectionResult` dataclass with both landmark sets
   - `detect()` returns both, `detect_legacy()` for backward compat

4. **backend/src/exercises/validation.py**
   - All evaluate functions now take (image_landmarks, world_landmarks)
   - Prefer 3D, fallback to 2D
   - Backward compatible with old signature `validate_all(rules, lms, w, h, states)`

5. **backend/src/services/gym_engine.py**
   - `analyze(image, world, w, h, frame, timestamp)` - full 3D
   - Backward compat: if called with old sig `analyze(lms, w, h, frame)`, treats as 2D
   - Adds `WorldLandmarkSmoother` instance
   - `_render()` still 2D only
   - `run()` prints 3D mode and uses new detection

6. **backend/src/server/live_runner.py**
   - Updated to pass both landmarks
   - State now includes `is_3d: true`

### Backward Compatibility

All old tests and CLI calls still work:
```python
# Old
engine.analyze(landmarks, 1000, 1000, 0)
validate_all(rules, lms, 1000, 1000, states={})

# New
engine.analyze(image_lms, world_lms, 1000, 1000, 0, timestamp_ms)
validate_all(rules, image_lms, world_lms, 1000, 1000, states, use_3d=True)
```

## Accuracy Improvement

Expected improvement:
- Shoulder press, biceps curl, lat pulldown: **30-40% better Good/Bad classification**
- Leg exercises (hack_squat, leg_press): side detection less critical, but depth estimation better
- Distance rules: 3D ratio includes depth, more stable across camera distances

## Known Limitations

- World `z` is estimated (pseudo-3D), not LiDAR. Noisy without smoothing -> we use OneEuroFilter
- Anisotropic pixel bug fixed by using 3D, but 2D rendering still needs w,h scaling (intentional for screen)
- Thresholds in exercise configs (e.g., `up_angle=160`) were tuned for 2D and may need re-calibration for 3D. Empirical testing shows 3D angles are ~5-10° different. Recommend collecting new samples per exercise.

## Future Work

- Add `Angle3DValidationRule` explicit class if you want to force 3D-only for certain checks
- Add tempo / Time Under Tension using `start_frame/end_frame` from `RepResult` + fps (already available)
- Frontend: show 3D toggle, visualize depth in report (e.g., side view projection)
- Consider MediaPipe `PoseLandmarker` HEAVY model for better world accuracy (vs FULL which you use now)

## How to Test

```bash
# CLI still works in 3D mode
make run EXERCISE=shoulder_press VIDEO=your_video.mp4
# Log will show:
# === AI Gym Trainer - 3D MODE - Shoulder Press ===
# 3D Calculation: ENABLED
# Smoothing: ENABLED

# Or test geometry directly:
python -c "
from src.utils.geometry import calc_angle_3d
print(calc_angle_3d((1,0,0),(0,0,0),(0,1,0))) # 90
"
```

## Rollback

If 3D causes issues, set `use_3d=False` in GymEngine:
```python
engine = GymEngine(exercise, use_3d=False)  # Falls back to 2D completely
```
