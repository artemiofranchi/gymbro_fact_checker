"""Fast tests, no network / API keys needed:  pytest -q"""
import math

from gymbro.form.angles import angle, count_reps
from gymbro.form.rules import squat
from gymbro.llm import parse_json
from gymbro.merge import build_report, detect_mismatch
from gymbro.schema import (Claim, ClaimResult, ClaimVerdict, FormResult, FormVerdict, Video)


def test_angle_right_and_straight():
    assert math.isclose(angle((1, 0), (0, 0), (0, 1)), 90, abs_tol=1e-6)
    assert math.isclose(angle((0, 1), (0, 0), (0, -1)), 180, abs_tol=1e-6)


def test_count_reps():
    sig = [170, 140, 100, 90, 120, 160, 170, 95, 165]
    assert count_reps(sig, low=110, high=150) == 2


def _kp(knee_deg):
    """Fake side-view keypoints with a given knee angle (thigh horizontal-ish, shin vertical)."""
    a = math.radians(knee_deg)
    knee, ankle = (0.5, 0.7), (0.5, 0.95)
    hip = (knee[0] + 0.2 * math.sin(a), knee[1] + 0.2 * math.cos(a))
    pts = {"hip": hip, "knee": knee, "ankle": ankle}
    kp = {}
    for side in ("left", "right"):
        for n, (x, y) in pts.items():
            kp[f"{side}_{n}"] = (x, y, 0.0, 0.9)
    return kp


def _reps(bottom_deg, n_reps=3, frames_per_rep=30, top_deg=170):
    """Knee angle going top -> bottom -> top, ~30 frames per rep like a real 15 fps clip."""
    out = []
    for _ in range(n_reps):
        for i in range(frames_per_rep):
            phase = (1 - math.cos(2 * math.pi * i / frames_per_rep)) / 2  # 0 -> 1 -> 0
            out.append(top_deg - (top_deg - bottom_deg) * phase)
    return out


def test_squat_depth_rule():
    issues, _ = squat([_kp(d) for d in _reps(bottom_deg=118)])
    assert [i.code for i in issues] == ["insufficient_depth"]
    issues, reps = squat([_kp(d) for d in _reps(bottom_deg=80)])
    assert issues == [] and reps == 3


def test_parse_json_handles_fences_and_think():
    assert parse_json('<think>hmm</think>\n```json\n{"a": 1}\n```') == {"a": 1}


def test_mismatch():
    assert detect_mismatch(["lower chest"], ["quadriceps", "glutes"]) is not None
    assert detect_mismatch(["quads"], ["quadriceps", "glutes"]) is None


def test_build_report_joins_by_time():
    video = Video(url="u", video_id="x")
    claim = ClaimResult(
        claim=Claim(text="Squats work your lower chest", quote="...", t_start=5, t_end=9,
                    exercise_id="Barbell_Squat", claimed_muscles=["lower chest"]),
        verdict=ClaimVerdict.not_supported, confidence=0.9, explanation="...")
    form = FormResult(exercise_id="Barbell_Squat", t_start=6, t_end=20, verdict=FormVerdict.ok)
    rep = build_report(video, [claim], [form], muscles_of=lambda _: ["quadriceps", "glutes"])
    assert len(rep.cards) == 1
    card = rep.cards[0]
    assert card.form is not None and card.mismatch is not None
