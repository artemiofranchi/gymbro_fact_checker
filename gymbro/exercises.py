"""Exercise catalog (free-exercise-db) — the glue between claims and form.

Download it once:  python scripts/fetch_exercises.py
Each item has: id, name, primaryMuscles, secondaryMuscles, equipment, category, ...
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import config

# Exercises the form part supports. Keep ids in sync with form/rules.py.
SUPPORTED_FORM_EXERCISES = {
    "Barbell_Squat",
    "Barbell_Deadlift",
    "Barbell_Bench_Press_-_Medium_Grip",
    "Standing_Military_Press",
}


@lru_cache(maxsize=1)
def catalog(path: Path | None = None) -> dict[str, dict]:
    p = path or config.EXERCISES_PATH
    if not p.exists():
        raise FileNotFoundError(f"{p} not found — run `python scripts/fetch_exercises.py`")
    return {e["id"]: e for e in json.loads(p.read_text())}


def get(exercise_id: str) -> dict | None:
    return catalog().get(exercise_id)


def muscles(exercise_id: str) -> list[str]:
    e = get(exercise_id) or {}
    return list(e.get("primaryMuscles", [])) + list(e.get("secondaryMuscles", []))


def find_by_name(name: str, limit: int = 5) -> list[dict]:
    """Naive fuzzy lookup by name; good enough to map 'back squat' -> Barbell_Squat candidates."""
    words = [w for w in name.lower().split() if len(w) > 2]
    scored = []
    for e in catalog().values():
        n = e["name"].lower()
        score = sum(w in n for w in words)
        if score:
            scored.append((score, -len(n), e))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [e for _, _, e in scored[:limit]]
