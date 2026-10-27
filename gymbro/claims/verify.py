"""Step 3: grade a claim against retrieved evidence."""
from __future__ import annotations

import re

from .. import config, llm
from ..schema import Claim, ClaimResult, ClaimVerdict, Evidence

PROMPT = """You are a sports-science fact checker. Judge the claim ONLY using the studies below.

Claim: "{claim}"
Creator's words: "{quote}"

Studies:
{studies}

Verdicts:
- supported: good evidence (ideally meta-analysis / RCTs) backs the claim as stated
- overstated: some truth, but the effect, population or certainty is smaller/narrower than claimed
  (e.g. study on untrained people only, tiny sample, short duration, small effect)
- not_supported: the evidence contradicts the claim
- no_evidence: the studies are not relevant enough to judge
- not_checkable: opinion or not a factual claim

Return JSON:
{{"verdict": "...", "confidence": 0.0-1.0,
  "explanation": "2-3 plain-English sentences for a gym-goer",
  "used": [{{"idx": <study number>, "note": "population, n, duration, key finding"}}]}}"""


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "")


def verify(claim: Claim, evidence: list[tuple[Evidence, str]], max_studies: int = 6) -> ClaimResult:
    if not evidence:
        return ClaimResult(claim=claim, verdict=ClaimVerdict.no_evidence, confidence=0.3,
                           explanation="No relevant studies found.")
    ev = evidence[:max_studies]
    studies = "\n\n".join(
        f"[{i}] {e.title} ({e.year}, {e.level.value})\n{_strip_html(abstract)[:1500]}"
        for i, (e, abstract) in enumerate(ev))
    data = llm.chat_json(PROMPT.format(claim=claim.text, quote=claim.quote, studies=studies),
                         model=config.MODEL_SMART)
    used = []
    for u in data.get("used", []):
        i = u.get("idx")
        if isinstance(i, int) and 0 <= i < len(ev):
            used.append(ev[i][0].model_copy(update={"note": u.get("note")}))
    return ClaimResult(
        claim=claim,
        verdict=ClaimVerdict(data.get("verdict", "no_evidence")),
        confidence=float(data.get("confidence", 0.5)),
        explanation=data.get("explanation", ""),
        evidence=used,
    )
