import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class PoseService:
    def __init__(self, model_path: str):
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
        )

        self.model = vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame, timestamp_ms: int):
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame,
        )

        return self.model.detect_for_video(mp_image, timestamp_ms)
