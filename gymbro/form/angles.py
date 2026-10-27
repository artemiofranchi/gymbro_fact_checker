"""Joint-angle maths on 2D/3D keypoints. Pure numpy, easy to unit-test."""
from __future__ import annotations

import numpy as np


def angle(a, b, c) -> float:
    """Angle ABC in degrees (vertex at b), e.g. knee angle = angle(hip, knee, ankle)."""
    a, b, c = (np.asarray(p, dtype=float) for p in (a, b, c))
    ba, bc = a - b, c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0:
        return float("nan")
    cos = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos)))


def smooth(xs: list[float], k: int = 5) -> np.ndarray:
    """Moving average to kill keypoint jitter."""
    x = np.asarray(xs, dtype=float)
    if len(x) < k:
        return x
    pad = k // 2
    xp = np.pad(x, (pad, k - 1 - pad), mode="edge")  # edge padding: no fake dips at the ends
    return np.convolve(xp, np.ones(k) / k, mode="valid")


def count_reps(signal: list[float], low: float, high: float) -> int:
    """Count reps on an angle signal with hysteresis: a rep = goes below `low`, then back above `high`."""
    reps, down = 0, False
    for v in signal:
        if not down and v < low:
            down = True
        elif down and v > high:
            reps += 1
            down = False
    return reps
