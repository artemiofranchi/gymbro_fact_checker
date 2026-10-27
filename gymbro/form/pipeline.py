"""Form part (owner: Tema): video + exercise segments -> list[FormResult].

Where do segments come from? Options (TODO(tema), pick one):
  1. from claims part: claims that mention an exercise give exercise_id + time window
  2. exercise classification on keypoints / frames (VLM: "which exercise is shown?")
  3. manual segments from data/gold/form_gold.csv for the demo
"""
from __future__ import annotations

from typing import Optional

from ..schema import FormResult, FormVerdict
from .pose import extract_keypoints
from .rules import RULES


def check_segment(video_path: str, exercise_id: Optional[str], t_start: float, t_end: float) -> FormResult:
    rule = RULES.get(exercise_id or "")
    if rule is None:
        return FormResult(exercise_id=exercise_id, t_start=t_start, t_end=t_end,
                          verdict=FormVerdict.not_assessable,
                          explanation="Exercise not supported by form checks yet.")
    frames, _fps = extract_keypoints(video_path, t_start, t_end)
    if sum(f is not None for f in frames) < 10:
        return FormResult(exercise_id=exercise_id, t_start=t_start, t_end=t_end,
                          verdict=FormVerdict.not_assessable, explanation="Person not visible enough.")
    issues, reps = rule(frames)
    # TODO(tema): LLM (MODEL_FAST) turns issues into a short coach-style explanation
    return FormResult(exercise_id=exercise_id, t_start=t_start, t_end=t_end, reps=reps,
                      verdict=FormVerdict.issues if issues else FormVerdict.ok, issues=issues)


def run_form(video_path: str, segments: list[tuple[Optional[str], float, float]]) -> list[FormResult]:
    """segments: [(exercise_id, t_start, t_end), ...]"""
    return [check_segment(video_path, ex, a, b) for ex, a, b in segments]


if __name__ == "__main__":
    import sys

    # python -m gymbro.form.pipeline path/to/video.mp4 Barbell_Squat 0 20
    path, ex, a, b = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    print(check_segment(path, ex, a, b).model_dump_json(indent=2))
