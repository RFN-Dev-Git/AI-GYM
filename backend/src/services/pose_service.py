import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PoseDetectionResult:
    """
    Holds both 2D image landmarks (for rendering) and 3D world landmarks (for analysis).
    
    - pose_landmarks: normalized x,y (0-1) + visibility - for drawing on 2D image
    - world_landmarks: x,y,z in meters, origin at hips center - for true angle calculation
    Both are lists of 33 landmarks, but we store only first person detected.
    """
    pose_landmarks: List  # 2D image space, 33 landmarks
    world_landmarks: List  # 3D world space, 33 landmarks
    raw_result: any = None  # original mediapipe result for debug

    @property
    def has_world(self) -> bool:
        return self.world_landmarks is not None and len(self.world_landmarks) >= 33


class PoseService:
    def __init__(self, model_path: str | Path):
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            output_segmentation_masks=False,
        )
        self.model = vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame, timestamp_ms: int) -> Optional[PoseDetectionResult]:
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame,
        )
        result = self.model.detect_for_video(mp_image, timestamp_ms)
        
        # Handle different API versions:
        # New API (0.10.18+): result.pose_landmarks, result.pose_world_landmarks
        # Old API: result.pose_landmarks as property? check both
        pose_lms_list = getattr(result, 'pose_landmarks', None) or getattr(result, 'pose_landmarks', [])
        world_lms_list = (
            getattr(result, 'pose_world_landmarks', None) or 
            getattr(result, 'world_landmarks', None) or
            getattr(result, 'pose_world_landmarks', None)
        )
        
        if not pose_lms_list or len(pose_lms_list) == 0:
            return None
        
        # Extract first person
        pose_lms = pose_lms_list[0]
        world_lms = world_lms_list[0] if world_lms_list and len(world_lms_list) > 0 else None
        
        return PoseDetectionResult(
            pose_landmarks=pose_lms,
            world_landmarks=world_lms,
            raw_result=result
        )

    def detect_legacy(self, frame, timestamp_ms: int):
        """Legacy method for backward compatibility - returns raw mediapipe result"""
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame,
        )
        return self.model.detect_for_video(mp_image, timestamp_ms)
