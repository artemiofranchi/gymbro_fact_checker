"""Shared data contract between the claims part and the form part.

Both pipelines write into these models; `merge.py` joins them by
`exercise_id` + time overlap and the API returns a `VideoReport`.
Change this file only after agreeing with each other.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------- input ----------

class TranscriptSegment(BaseModel):
    t_start: float  # seconds
    t_end: float
    text: str


class Video(BaseModel):
    url: str
    video_id: str
    title: Optional[str] = None
    transcript: list[TranscriptSegment] = []
    local_path: Optional[str] = None  # downloaded file, for the form part


# ---------- claims (Artem) ----------

class ClaimVerdict(str, Enum):
    supported = "supported"
    overstated = "overstated"          # partly true, but the evidence is weaker / narrower than claimed
    not_supported = "not_supported"    # evidence contradicts it
    no_evidence = "no_evidence"        # nothing relevant found
    not_checkable = "not_checkable"    # opinion / not a factual claim


class EvidenceLevel(str, Enum):
    meta_analysis = "meta_analysis"
    systematic_review = "systematic_review"
    rct = "rct"
    observational = "observational"
    other = "other"


class Evidence(BaseModel):
    source: str = "europepmc"          # europepmc | pubmed | tavily
    id: Optional[str] = None           # PMID / DOI / URL
    title: str
    year: Optional[int] = None
    level: EvidenceLevel = EvidenceLevel.other
    url: Optional[str] = None
    note: Optional[str] = None         # e.g. "12 untrained men, 8 weeks"


class Claim(BaseModel):
    text: str                          # normalised claim, e.g. "Crunches burn belly fat"
    quote: str                         # what the creator actually said
    t_start: float
    t_end: float
    exercise_id: Optional[str] = None  # id from the exercise catalog, if an exercise is mentioned
    claimed_muscles: list[str] = []    # e.g. ["lower chest"] for said-vs-shown


class ClaimResult(BaseModel):
    claim: Claim
    verdict: ClaimVerdict
    confidence: float = Field(ge=0, le=1)
    explanation: str
    evidence: list[Evidence] = []


# ---------- form (Tema) ----------

class FormVerdict(str, Enum):
    ok = "ok"
    issues = "issues"
    not_assessable = "not_assessable"  # bad angle, body out of frame, unsupported exercise


class FormIssue(BaseModel):
    code: str                          # e.g. "insufficient_depth", "knee_valgus"
    message: str                       # human-readable explanation
    frames: list[int] = []             # frame indices where it was detected
    severity: float = Field(default=0.5, ge=0, le=1)


class FormResult(BaseModel):
    exercise_id: Optional[str]
    t_start: float
    t_end: float
    verdict: FormVerdict
    issues: list[FormIssue] = []
    reps: Optional[int] = None
    explanation: Optional[str] = None


# ---------- merged ----------

class Mismatch(BaseModel):
    claimed_muscles: list[str]
    actual_muscles: list[str]
    message: str


class SegmentCard(BaseModel):
    """One card in the UI: what was said + what was shown in the same time window."""
    t_start: float
    t_end: float
    exercise_id: Optional[str] = None
    claims: list[ClaimResult] = []
    form: Optional[FormResult] = None
    mismatch: Optional[Mismatch] = None


class VideoReport(BaseModel):
    video: Video
    cards: list[SegmentCard]
