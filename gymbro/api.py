"""FastAPI app: POST /analyze {"url": "..."} -> VideoReport.

Run:  uvicorn gymbro.api:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from . import exercises
from .claims.pipeline import run_claims
from .form.pipeline import run_form
from .ingest.youtube import load
from .merge import build_report
from .schema import VideoReport

app = FastAPI(title="Gymbro Science Detector")


class AnalyzeRequest(BaseModel):
    url: str
    form_check: bool = True


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze", response_model=VideoReport)
def analyze(req: AnalyzeRequest) -> VideoReport:
    video = load(req.url, with_video=req.form_check)
    claims = run_claims(video.transcript)

    forms = []
    if req.form_check and video.local_path:
        # Segments to check = claims that mention a form-supported exercise.
        # TODO(tema): replace/extend with exercise detection on the video itself.
        segs = [(c.claim.exercise_id, c.claim.t_start, c.claim.t_end + 10)
                for c in claims if c.claim.exercise_id in exercises.SUPPORTED_FORM_EXERCISES]
        forms = run_form(video.local_path, segs)

    return build_report(video, claims, forms, muscles_of=exercises.muscles)
