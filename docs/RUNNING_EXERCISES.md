# Running Exercises Guide

This guide explains how to run specific exercises using the AI-GYM system, including video/camera options and saving output.

## Running Exercises via CLI (Engine Mode)

### Basic Command Structure

```bash
make run EXERCISE=<exercise_name> [VIDEO=<video_path>] [c]
```

### Exercise Names

Available exercises (case-insensitive):
- `biceps_curl` - Biceps Curl
- `cable_chest_fly` - Cable Chest Fly
- `cable_straight_arm_pulldown` - Cable Straight-Arm Pulldown
- `deadlift` - Deadlift
- `hack_squat` - Hack Squat
- `lateral_raise` - Lateral Raise
- `leg_press` - Leg Press
- `lat_pulldown` - Lat Pulldown
- `pushup` - Push-Up
- `shoulder_press` - Shoulder Press
- `squat` - Squat

### Video Source Options

#### 1. Using a Video File

```bash
# Using a video from assets/videos/
make run EXERCISE=hack_squat VIDEO=hackw.mp4

# Using a relative path
make run EXERCISE=biceps_curl VIDEO=../my_videos/curl.mp4

# Using an absolute path
make run EXERCISE=deadlift VIDEO=D:/videos/deadlift.mp4
```

**Video Resolution Order:**
1. As given (absolute path or relative to current directory)
2. Inside `assets/videos/<filename>`
3. By bare filename in `assets/videos/`

#### 2. Using Webcam

```bash
# Use default webcam (index 0)
make run EXERCISE=squat c

# Specify webcam index in backend/.env if needed
# WEBCAM_INDEX=0 (default) or WEBCAM_INDEX=1 for second camera
```

### Saving Output

To save the rendered video with annotations, set `SAVE_OUTPUT=true` in `backend/.env`:

```env
SAVE_OUTPUT=true
OUTPUT_PATH=output/videos/rendered_session.mp4
```

The output will be saved to the path specified in `OUTPUT_PATH`.

### Configuration via .env

Edit `backend/.env` to configure default behavior:

```env
# Video source
VIDEO_PATH=assets/videos/sample.mp4
USE_WEBCAM=false
WEBCAM_INDEX=0

# Output
SAVE_OUTPUT=false
OUTPUT_PATH=output/videos/session.mp4

# Model
MODEL_PATH=assets/models/pose_landmarker_full.task

# Export
EXPORT_SESSION=false
EXPORT_FORMAT=json
EXPORT_DIR=output/sessions
ANALYTICS_FPS=25
```

### Examples

```bash
# Run hack squat with video file
make run EXERCISE=hack_squat VIDEO=hackw.mp4

# Run biceps curl with webcam
make run EXERCISE=biceps_curl c

# Run lateral raise with custom video and save output
# (ensure SAVE_OUTPUT=true in .env)
make run EXERCISE=lateral_raise VIDEO=../lateral_raise.mp4
```

## Running Exercises via Frontend (Web Mode)

### Starting the Backend

```bash
cd backend
pip install -r requirements.txt
make backend
```

This starts the FastAPI server at `http://localhost:8000` with:
- REST API endpoints at `/api/*`
- WebSocket endpoint at `/ws/live`

### Starting the Frontend

```bash
cd frontend
npm install
make frontend
```

This starts the React dev server at `http://localhost:5173` (proxies API/WS to backend).

### Using the Web Interface

1. Open `http://localhost:5173` in your browser
2. Select an exercise from the dropdown
3. Choose input source:
   - **Webcam**: Live camera feed
   - **Video**: Upload a video file from your computer
4. Configure options (if available):
   - Enable/disable output saving
5. Click "Start Workout"
6. The session report opens automatically when workout ends
7. Download rendered video if `SAVE_OUTPUT=true`

### Frontend Features

- **Dashboard**: Overview of workout history and progress
- **Exercises**: Browse and select exercises
- **Live Mode**: Real-time coaching with skeleton overlay
- **History**: View past sessions with detailed reports
- **Settings**: Configure runtime settings

## Troubleshooting

### Video Not Found

If you get "Video file not found" error:
1. Check the video path is correct
2. Place video in `assets/videos/` and use bare filename
3. Use absolute path if relative path fails

### Webcam Not Opening

If webcam fails to open:
1. Check camera is not in use by another application
2. Verify camera permissions in OS settings
3. Try different `WEBCAM_INDEX` in `.env` (0, 1, 2...)

### Model Not Found

If you get "Pose model file not found":
1. Download `pose_landmarker_full.task` from [MediaPipe Model Zoo](https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models)
2. Place it in `assets/models/`
3. Set `MODEL_PATH=assets/models/pose_landmarker_full.task` in `.env`

### Port Already in Use

If port 8000 or 5173 is already in use:
```bash
# Kill process on port (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different ports in configuration
```

## Session Reports

After each workout, a session report is generated (if `EXPORT_SESSION=true`):

- **Location**: `output/sessions/<exercise_name>_YYYYMMDD_HHMMSS.json`
- **Contents**: Rep counts, good/bad reps, violations, timing, frame statistics
- **View**: Open via frontend History page or parse JSON directly

## Tips

- For side-view exercises (squat, deadlift, etc.), position camera at 90 degrees to body
- For front-view exercises (lateral raise), position camera directly in front
- Ensure good lighting and clear visibility of body joints
- Use `SAVE_OUTPUT=true` to review form and debug issues
- Check `backend/.env` for all configuration options
