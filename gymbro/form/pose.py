"""Video -> per-frame body keypoints with MediaPipe Pose.

Output: list of frames, each a dict {landmark_name: (x, y, z, visibility)} or None
if no person was detected. Coordinates are normalised to [0, 1] image space.

TODO(tema): if `mp.solutions` is gone in your mediapipe version, switch to the
Tasks API (mediapipe.tasks.python.vision.PoseLandmarker) — same 33 landmarks.
"""
from __future__ import annotations

from typing import Optional

# MediaPipe's 33 landmarks — the ones we actually use
LANDMARKS = {
    "nose": 0,
    "left_shoulder": 11, "right_shoulder": 12,
    "left_elbow": 13, "right_elbow": 14,
    "left_wrist": 15, "right_wrist": 16,
    "left_hip": 23, "right_hip": 24,
    "left_knee": 25, "right_knee": 26,
    "left_ankle": 27, "right_ankle": 28,
    "left_foot_index": 31, "right_foot_index": 32,
}

Keypoints = dict[str, tuple[float, float, float, float]]


def extract_keypoints(video_path: str, t_start: float = 0.0, t_end: Optional[float] = None,
                      stride: int = 2) -> tuple[list[Optional[Keypoints]], float]:
    """Returns (frames, fps_of_returned_frames). Processes every `stride`-th frame."""
    import cv2
    import mediapipe as mp

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, t_start * 1000)
    frames: list[Optional[Keypoints]] = []
    with mp.solutions.pose.Pose(model_complexity=1, min_detection_confidence=0.5) as pose:
        i = 0
        while True:
            ok, img = cap.read()
            if not ok or (t_end is not None and cap.get(cv2.CAP_PROP_POS_MSEC) > t_end * 1000):
                break
            if i % stride == 0:
                res = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                if res.pose_landmarks:
                    lm = res.pose_landmarks.landmark
                    frames.append({n: (lm[j].x, lm[j].y, lm[j].z, lm[j].visibility)
                                   for n, j in LANDMARKS.items()})
                else:
                    frames.append(None)
            i += 1
    cap.release()
    return frames, fps / stride
