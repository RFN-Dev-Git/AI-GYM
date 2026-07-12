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


def adapt_rules(rules, target_side: str):
    adapted = []
    target_side_normalized_names = set()
    for rule in rules:
        side = get_joints_side(rule.joints)
        if side == target_side:
            target_side_normalized_names.add(normalize_name(rule.name))

    for rule in rules:
        side = get_joints_side(rule.joints)
        if side == target_side or side == "both":
            adapted.append(rule)
        elif side != "both":
            norm_name = normalize_name(rule.name)
            if norm_name not in target_side_normalized_names:
                new_joints = []
                for j in rule.joints:
                    if j >= 7 and j <= 32:
                        is_odd = (j % 2 != 0)
                        if target_side == "left" and not is_odd:
                            new_joints.append(j - 1)
                        elif target_side == "right" and is_odd:
                            new_joints.append(j + 1)
                        else:
                            new_joints.append(j)
                    else:
                        new_joints.append(j)
                new_rule = dataclasses.replace(rule, joints=tuple(new_joints))
                adapted.append(new_rule)
    return adapted
