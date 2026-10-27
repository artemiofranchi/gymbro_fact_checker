"""Step 1: pull checkable, science-flavoured claims out of the transcript."""
from __future__ import annotations

from .. import config, llm
from ..schema import Claim, TranscriptSegment

PROMPT = """You analyse transcripts of fitness videos.
Extract every FACTUAL claim about training, nutrition, physiology or exercise effects
that could be checked against scientific research (e.g. "crunches burn belly fat",
"you must eat protein within 30 minutes after training", "this exercise targets the lower chest").
Skip greetings, jokes, pure opinions and calls to subscribe.

For each claim return:
- "text": the claim restated as a short, self-contained sentence
- "quote": the exact words from the transcript
- "seg_ids": list of segment ids the quote comes from
- "exercise": exercise name if the claim is about a specific exercise, else null
- "claimed_muscles": muscles the creator says it works, else []

Transcript (id | start-end s | text):
{transcript}

Return JSON: {{"claims": [ ... ]}}"""


def _format(segments: list[TranscriptSegment]) -> str:
    return "\n".join(f"{i} | {s.t_start:.1f}-{s.t_end:.1f} | {s.text}" for i, s in enumerate(segments))


def extract_claims(segments: list[TranscriptSegment]) -> list[Claim]:
    if not segments:
        return []
    data = llm.chat_json(PROMPT.format(transcript=_format(segments)), model=config.MODEL_FAST)
    claims = []
    for c in data.get("claims", []):
        ids = [i for i in c.get("seg_ids", []) if 0 <= i < len(segments)] or [0]
        claims.append(Claim(
            text=c["text"], quote=c.get("quote", c["text"]),
            t_start=segments[min(ids)].t_start, t_end=segments[max(ids)].t_end,
            exercise_id=None,  # resolved later via exercises.find_by_name(c["exercise"])
            claimed_muscles=c.get("claimed_muscles") or [],
        ))
        # TODO(artem): map c["exercise"] -> exercise_id via exercises.find_by_name + LLM pick
    return claims
