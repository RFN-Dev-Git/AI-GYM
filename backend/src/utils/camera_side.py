import dataclasses

class CameraSideDetector:
    def __init__(self, target_frames: int = 30):
        self.target_frames = target_frames
        self.frame_count = 0
        self.left_vis_sum = 0.0
        self.right_vis_sum = 0.0
        self.detected_side = None

    def process_frame(self, landmarks) -> str | None:
        if self.detected_side is not None:
            return self.detected_side

        left_joints = [11, 13, 15, 23, 25, 27]
        right_joints = [12, 14, 16, 24, 26, 28]

        l_vis = sum(landmarks[i].visibility for i in left_joints) / len(left_joints)
        r_vis = sum(landmarks[i].visibility for i in right_joints) / len(right_joints)

        self.left_vis_sum += l_vis
        self.right_vis_sum += r_vis
        self.frame_count += 1

        if self.frame_count >= self.target_frames:
            if self.left_vis_sum > self.right_vis_sum:
                self.detected_side = "left"
            else:
                self.detected_side = "right"
            return self.detected_side

        return None


def normalize_name(name: str) -> str:
    for suffix in ["_left", "_right", "_l", "_r"]:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def get_joints_side(joints) -> str:
    left_count = sum(1 for j in joints if j >= 7 and j <= 32 and j % 2 != 0)
    right_count = sum(1 for j in joints if j >= 7 and j <= 32 and j % 2 == 0)
    if left_count > right_count:
        return "left"
    elif right_count > left_count:
        return "right"
    return "both"


# Landmark-group fields a rule may carry: an angle triplet (angle-style
# rules) or measurement/reference pairs (DistanceValidationRule).
_LANDMARK_FIELDS = ("joints", "measurement", "reference")


def _rule_landmarks(rule) -> tuple[int, ...]:
    """All BlazePose landmark indices referenced by a rule, whatever its shape."""
    indices: list[int] = []
    for field in _LANDMARK_FIELDS:
        value = getattr(rule, field, None)
        if value is None:
            continue
        indices.extend(value if isinstance(value, (tuple, list)) else (value,))
    return tuple(indices)


def _flip_index(j: int, target_side: str) -> int:
    """Mirror a single landmark index onto ``target_side`` (L/R swap)."""
    if 7 <= j <= 32:
        is_odd = (j % 2 != 0)
        if target_side == "left" and not is_odd:
            return j - 1
        if target_side == "right" and is_odd:
            return j + 1
    return j


def adapt_rules(rules, target_side: str):
    adapted = []
    target_side_normalized_names = set()
    for rule in rules:
        side = get_joints_side(_rule_landmarks(rule))
        if side == target_side:
            target_side_normalized_names.add(normalize_name(rule.name))

    for rule in rules:
        side = get_joints_side(_rule_landmarks(rule))
        if side == target_side or side == "both":
            adapted.append(rule)
        elif side != "both":
            norm_name = normalize_name(rule.name)
            if norm_name not in target_side_normalized_names:
                remapped = {}
                for field in _LANDMARK_FIELDS:
                    value = getattr(rule, field, None)
                    if value is None:
                        continue
                    if isinstance(value, (tuple, list)):
                        remapped[field] = tuple(_flip_index(j, target_side) for j in value)
                    else:
                        remapped[field] = _flip_index(value, target_side)
                new_rule = dataclasses.replace(rule, **remapped)
                adapted.append(new_rule)
    return adapted
