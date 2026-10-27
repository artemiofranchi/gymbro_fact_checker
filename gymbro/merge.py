"""Join claims + form into UI cards, and detect said-vs-shown mismatches."""
from __future__ import annotations

from typing import Callable, Optional

from .schema import ClaimResult, FormResult, Mismatch, SegmentCard, Video, VideoReport

# Synonyms from creator language -> free-exercise-db muscle names. TODO: extend.
MUSCLE_ALIASES = {
    "pecs": "chest", "upper chest": "chest", "lower chest": "chest", "chest": "chest",
    "quads": "quadriceps", "hamstrings": "hamstrings", "glutes": "glutes", "butt": "glutes",
    "abs": "abdominals", "core": "abdominals", "belly": "abdominals",
    "lats": "lats", "back": "middle back", "traps": "traps",
    "shoulders": "shoulders", "delts": "shoulders", "biceps": "biceps", "triceps": "triceps",
    "calves": "calves", "lower back": "lower back",
}


def normalise_muscle(m: str) -> str:
    m = m.lower().strip()
    if m in MUSCLE_ALIASES:
        return MUSCLE_ALIASES[m]
    for k, v in sorted(MUSCLE_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if k in m:
            return v
    return m


def detect_mismatch(claimed: list[str], actual: list[str]) -> Optional[Mismatch]:
    if not claimed or not actual:
        return None
    actual_n = {a.lower() for a in actual}
    missing = [c for c in claimed if normalise_muscle(c) not in actual_n]
    if not missing:
        return None
    return Mismatch(claimed_muscles=claimed, actual_muscles=actual,
                    message=f"Says it works {', '.join(missing)}, but this exercise mainly trains "
                            f"{', '.join(actual[:3])}.")


def _overlap(a0, a1, b0, b1) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def build_report(video: Video, claims: list[ClaimResult], forms: list[FormResult],
                 muscles_of: Callable[[str], list[str]]) -> VideoReport:
    cards: list[SegmentCard] = []
    used_forms: set[int] = set()
    for cr in sorted(claims, key=lambda c: c.claim.t_start):
        c = cr.claim
        # attach the form check that overlaps this claim in time (same exercise if known)
        best, best_ov = None, 0.0
        for i, f in enumerate(forms):
            if c.exercise_id and f.exercise_id and c.exercise_id != f.exercise_id:
                continue
            ov = _overlap(c.t_start, c.t_end, f.t_start, f.t_end)
            if ov > best_ov:
                best, best_ov = i, ov
        form = forms[best] if best is not None else None
        if best is not None:
            used_forms.add(best)
        ex = c.exercise_id or (form.exercise_id if form else None)
        mismatch = detect_mismatch(c.claimed_muscles, muscles_of(ex)) if ex else None
        cards.append(SegmentCard(t_start=c.t_start, t_end=c.t_end, exercise_id=ex,
                                 claims=[cr], form=form, mismatch=mismatch))
    for i, f in enumerate(forms):  # form checks with no claim nearby still get a card
        if i not in used_forms:
            cards.append(SegmentCard(t_start=f.t_start, t_end=f.t_end, exercise_id=f.exercise_id, form=f))
    cards.sort(key=lambda k: k.t_start)
    return VideoReport(video=video, cards=cards)
