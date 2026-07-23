"""
3D Landmark smoothing filters for world landmarks.

World landmarks (z) from MediaPipe are noisy. Without filtering, 
3D angles jitter +-5 degrees causing unstable rep counting.

We provide two options:
- MovingAverageFilter: simple, no params
- OneEuroFilter: adaptive, best for pose (from Google paper)
"""

import math
from collections import deque, defaultdict
from dataclasses import dataclass, field


class OneEuroFilter:
    """
    One Euro Filter for signal smoothing.
    From https://cristal.univ-lille.fr/~casiez/1euro/ 
    Adaptive filter that reduces lag when signal moves fast.
    Perfect for pose landmarks.
    """

    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    @staticmethod
    def _alpha(cutoff, dt):
        r = 2 * math.pi * cutoff * dt
        return r / (r + 1)

    def __call__(self, x, t=None):
        # t is timestamp in seconds
        if t is None:
            dt = 1/30.0  # assume 30fps if no timestamp
        else:
            if self.t_prev is None:
                self.t_prev = t
                dt = 1/30.0
            else:
                dt = t - self.t_prev
                self.t_prev = t
                if dt <= 0:
                    dt = 1/30.0

        if self.x_prev is None:
            self.x_prev = x
            self.dx_prev = 0.0
            return x

        # derivative
        dx = (x - self.x_prev) / dt
        # filter derivative
        alpha_d = self._alpha(self.d_cutoff, dt)
        dx_hat = alpha_d * dx + (1 - alpha_d) * self.dx_prev

        # adapt cutoff based on speed
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        alpha = self._alpha(cutoff, dt)

        # filter signal
        x_hat = alpha * x + (1 - alpha) * self.x_prev

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        return x_hat


@dataclass
class Landmark3D:
    x: float
    y: float
    z: float
    visibility: float = 1.0


class WorldLandmarkSmoother:
    """
    Smooths 33 world landmarks independently.
    Uses OneEuroFilter per axis per landmark for best quality.
    
    Usage:
        smoother = WorldLandmarkSmoother()
        smoothed_world = smoother.smooth(world_landmarks, timestamp_ms)
    """

    def __init__(self, min_cutoff=1.2, beta=0.02):
        # 33 landmarks * 3 axes = 99 filters
        self.filters = defaultdict(lambda: {
            'x': OneEuroFilter(min_cutoff=min_cutoff, beta=beta),
            'y': OneEuroFilter(min_cutoff=min_cutoff, beta=beta),
            'z': OneEuroFilter(min_cutoff=min_cutoff * 0.8, beta=beta * 1.5)  # z needs more smoothing
        })
        self.enabled = True

    def smooth(self, world_landmarks, timestamp_ms=None):
        if not self.enabled or world_landmarks is None:
            return world_landmarks

        t = timestamp_ms / 1000.0 if timestamp_ms else None
        smoothed = []

        for idx, lm in enumerate(world_landmarks):
            f = self.filters[idx]
            # Handle both mediapipe landmark objects and our own
            x = getattr(lm, 'x', 0)
            y = getattr(lm, 'y', 0)
            z = getattr(lm, 'z', 0)
            vis = getattr(lm, 'visibility', 1.0)

            # Low visibility = don't smooth too aggressively, keep last
            if hasattr(lm, 'visibility') and lm.visibility < 0.5:
                smoothed.append(lm)
                continue

            sx = f['x'](x, t)
            sy = f['y'](y, t)
            sz = f['z'](z, t)

            # Create new landmark with smoothed values
            # Preserve original type if possible
            try:
                # If it's mediapipe object, create copy
                import copy
                new_lm = copy.copy(lm)
                new_lm.x = sx
                new_lm.y = sy
                new_lm.z = sz
                smoothed.append(new_lm)
            except (AttributeError, TypeError, ValueError):
                smoothed.append(Landmark3D(sx, sy, sz, vis))

        return smoothed

    def reset(self):
        self.filters.clear()


class SimpleMovingAverageSmoother:
    """
    Lightweight fallback: moving average over N frames.
    Faster but more lag than OneEuro.
    """

    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    def smooth(self, world_landmarks, timestamp_ms=None):
        if world_landmarks is None:
            return None
        self.history.append([(lm.x, lm.y, lm.z) for lm in world_landmarks])
        
        if len(self.history) < 2:
            return world_landmarks

        # Average
        avg_points = []
        for idx in range(len(world_landmarks)):
            xs = [frame[idx][0] for frame in self.history]
            ys = [frame[idx][1] for frame in self.history]
            zs = [frame[idx][2] for frame in self.history]
            avg_x = sum(xs) / len(xs)
            avg_y = sum(ys) / len(ys)
            avg_z = sum(zs) / len(zs)
            
            new_lm = world_landmarks[idx]
            try:
                import copy
                new_lm = copy.copy(world_landmarks[idx])
                new_lm.x = avg_x
                new_lm.y = avg_y
                new_lm.z = avg_z
            except (AttributeError, TypeError, ValueError):
                # Fallback: keep original if copy fails
                pass
            avg_points.append(new_lm)
        
        return avg_points
