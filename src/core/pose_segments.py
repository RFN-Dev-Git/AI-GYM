"""MediaPipe BlazePose landmark indices and common joint segments.

These are *anatomical* constants, not exercise logic. Exercises reference them
when building their AngleCounterRule / AngleValidationRule configurations, which keeps the
raw landmark numbers out of the exercise definitions and out of GymEngine.
"""

# --- Individual BlazePose landmarks (33-point model) ---
NOSE = 0
L_EYE_INNER = 1
L_EYE = 2
L_EYE_OUTER = 3
R_EYE_INNER = 4
R_EYE = 5
R_EYE_OUTER = 6
L_EAR = 7
R_EAR = 8
L_MOUTH = 9
R_MOUTH = 10
L_SHOULDER = 11
R_SHOULDER = 12
L_ELBOW = 13
R_ELBOW = 14
L_WRIST = 15
R_WRIST = 16
L_PINKY = 17
R_PINKY = 18
L_INDEX = 19
R_INDEX = 20
L_THUMB = 21
R_THUMB = 22
L_HIP = 23
R_HIP = 24
L_KNEE = 25
R_KNEE = 26
L_ANKLE = 27
R_ANKLE = 28
L_HEEL = 29
R_HEEL = 30
L_FOOT = 31
R_FOOT = 32


class PoseSegments:
    """Tuples of landmark indices describing a kinematic chain / angle."""

    LEFT_ARM = (L_SHOULDER, L_ELBOW, L_WRIST)
    RIGHT_ARM = (R_SHOULDER, R_ELBOW, R_WRIST)

    LEFT_LEG = (L_HIP, L_KNEE, L_ANKLE)
    RIGHT_LEG = (R_HIP, R_KNEE, R_ANKLE)

    # 4-point chains kept for convenience / future multi-angle features.
    LEFT_CHAIN = (L_SHOULDER, L_ELBOW, L_WRIST, L_HIP)
    RIGHT_CHAIN = (R_SHOULDER, R_ELBOW, R_WRIST, R_HIP)

    # Torso proxies: shoulder-hip-knee angle is a simple "is the back/trunk
    # reasonably straight?" check for many exercises.
    LEFT_TORSO = (L_SHOULDER, L_HIP, L_KNEE)
    RIGHT_TORSO = (R_SHOULDER, R_HIP, R_KNEE)

    # Hip / knee alignment proxies (placeholders for true symmetry checks).
    LEFT_HIP_ALIGN = (L_HIP, R_HIP, R_KNEE)
    RIGHT_HIP_ALIGN = (R_HIP, L_HIP, L_KNEE)

    # ----- Deadlift-specific segments -----
    # Neck / cervical-spine neutrality: Ear → Shoulder → Hip.
    # A neutral neck sits at ~160-180°; values below that flag forward-head.
    LEFT_NECK_ALIGN  = (L_EAR, L_SHOULDER, L_HIP)
    RIGHT_NECK_ALIGN = (R_EAR, R_SHOULDER, R_HIP)

    # Hip-hinge (abdomen / anterior-thigh angle): Shoulder → Hip → Knee.
    # Reuses LEFT_TORSO / RIGHT_TORSO; explicit aliases for readability.
    LEFT_HIP_HINGE  = (L_SHOULDER, L_HIP, L_KNEE)   # same as LEFT_TORSO
    RIGHT_HIP_HINGE = (R_SHOULDER, R_HIP, R_KNEE)   # same as RIGHT_TORSO

    # Elbow elevation: Hip -> Shoulder -> Elbow (Cable Chest Fly)
    # Flags when the elbow drops below the shoulder line.
    LEFT_ELBOW_ELEVATION  = (L_HIP, L_SHOULDER, L_ELBOW)
    RIGHT_ELBOW_ELEVATION = (R_HIP, R_SHOULDER, R_ELBOW)
