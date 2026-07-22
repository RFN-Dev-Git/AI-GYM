# Assets — runtime inputs (repository root)

This directory holds runtime **inputs** that are not tracked in the repo.
It lives at the repository root; every relative path in `backend/.env`
resolves against that root.

## `videos/` — developer sample clips (CLI path)

Drop dev/test clips here for the engine CLI. `make run VIDEO=<name>` and the
`VIDEO_PATH` setting resolve bare file names against this directory.

The **web application does not read this folder**: users upload their own
videos from the live page (`POST /api/uploads` → `uploads/videos/`).

## `models/` — pose model (required)

Place the BlazePose pose-landmarker model here and point `MODEL_PATH`
(`backend/.env`) at it, e.g.:

```
MODEL_PATH=assets/models/pose_landmarker_full.task
```

Download it from the MediaPipe model zoo:
https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models

Without this file every run aborts in preflight with a "Pose model file not
found" message.
