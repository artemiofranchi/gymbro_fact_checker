"""Biomechanical rules per exercise: keypoints -> FormIssues.

One worked example (squat). TODO(tema): deadlift, bench, overhead press;
calibrate thresholds on Fitness-AQA / own labels; handle side vs front camera.
"""
from __future__ import annotations

from typing import Callable, Optional

from ..schema import FormIssue
from .angles import angle, count_reps, smooth
from .pose import Keypoints


def _side(kp: Keypoints) -> str:
    """Use the body side that is better visible to the camera."""
    l = kp["left_hip"][3] + kp["left_knee"][3] + kp["left_ankle"][3]
    r = kp["right_hip"][3] + kp["right_knee"][3] + kp["right_ankle"][3]
    return "left" if l >= r else "right"


def _xy(kp: Keypoints, name: str):
    return kp[name][:2]


def squat(frames: list[Optional[Keypoints]]) -> tuple[list[FormIssue], Optional[int]]:
    valid = [(i, f) for i, f in enumerate(frames) if f]
    if len(valid) < 10:
        return [], None
    knee = []
    for _, f in valid:
        s = _side(f)
        knee.append(angle(_xy(f, f"{s}_hip"), _xy(f, f"{s}_knee"), _xy(f, f"{s}_ankle")))
    knee_s = smooth(knee)
    reps = count_reps(list(knee_s), low=110, high=150)

    issues: list[FormIssue] = []
    # Depth: hip crease should reach roughly knee level -> knee angle well below ~100 deg at the bottom.
    # TODO(tema): per-rep minima instead of global min; calibrate threshold.
    if knee_s.min() > 100:
        bottom = valid[int(knee_s.argmin())][0]
        issues.append(FormIssue(code="insufficient_depth", severity=0.6, frames=[bottom],
                                message=f"Squat depth looks shallow (min knee angle ≈ {knee_s.min():.0f}°)."))
    # TODO(tema): knee_valgus (front view: knee x vs ankle/hip x), heels lifting, excessive forward lean
    return issues, reps


RULES: dict[str, Callable[[list[Optional[Keypoints]]], tuple[list[FormIssue], Optional[int]]]] = {
    "Barbell_Squat": squat,
    # "Barbell_Deadlift": deadlift,
    # "Barbell_Bench_Press_-_Medium_Grip": bench,
    # "Standing_Military_Press": overhead_press,
}
